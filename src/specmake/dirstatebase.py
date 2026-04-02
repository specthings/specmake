# SPDX-License-Identifier: BSD-2-Clause
""" Maintains a directory state. """

# Copyright (C) 2020, 2026 embedded brains GmbH & Co. KG
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import base64
import fnmatch
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import stat
import tarfile
from typing import Any, Callable, Iterable, Iterator, Optional

from specitems import (Item, ItemGetValueContext, ItemValueProvider,
                       base64_to_hex_text, hash_file)

from .pkgitems import (BuildItem, BuildItemFactory, BuildItemMapper,
                       PackageBuildDirector, export_data)

_Path = Path | str


def _get_file_path(ctx: ItemGetValueContext) -> str:
    index = max(ctx.index, 0)
    return ctx.substitute_and_transform(
        f"{ctx.item['directory']}/{ctx.item['files'][index]['file']}")


def _get_file_path_without_extension(ctx: ItemGetValueContext) -> str:
    return os.path.splitext(_get_file_path(ctx))[0]


def _get_sha512(ctx: ItemGetValueContext) -> str:
    index = max(ctx.index, 0)
    digest = ctx.item["files"][index]["hash"]
    assert digest is not None
    return base64_to_hex_text(digest)


def _do_glob(ctx: ItemGetValueContext) -> list[str]:
    files: list[str] = []
    directory = ctx.mapper.substitute(ctx.item["directory"])
    include_patterns = ctx.unpack_args_list()
    for file_info in ctx.item["files"]:
        path = os.path.join("/", file_info["file"])
        for pattern in include_patterns:
            if fnmatch.fnmatch(path, pattern):
                files.append(os.path.join(directory, file_info["file"]))
                break
    return sorted(files)


def _get_glob(ctx: ItemGetValueContext) -> list[str]:
    files = _do_glob(ctx)
    logging.info("%s: glob files: %s", ctx.item.uid, files)
    return files


def _get_glob_executables(ctx: ItemGetValueContext) -> list[str]:
    files: list[str] = []
    executable = stat.S_IXUSR
    for path in _do_glob(ctx):
        if os.stat(path).st_mode & executable:
            files.append(path)
    logging.info("%s: glob executable files: %s", ctx.item.uid, files)
    return files


def _file_nop(_source: _Path, _target: _Path) -> None:
    pass


def _export_data(item: Item, present: bool, built_later: bool) -> Any:
    data = export_data(item, present, built_later)
    if not present or built_later:
        if "patterns" in item:
            data["files"] = []
        else:
            for file_info in data["files"]:
                file_info["hash"] = None
    if built_later:
        data["hash"] = None
    return data


class DirectoryStateBase(BuildItem):
    """ Maintains a directory state. """

    # pylint: disable=too-many-public-methods
    @classmethod
    def prepare_factory(cls, factory: BuildItemFactory,
                        type_name: str) -> None:
        BuildItem.prepare_factory(factory, type_name)
        factory.add_get_value(f"{type_name}:/file", _get_file_path)
        factory.add_get_value(f"{type_name}:/file-without-extension",
                              _get_file_path_without_extension)
        factory.add_get_value(f"{type_name}:/sha512", _get_sha512)
        factory.add_get_value(f"{type_name}:/glob", _get_glob)
        factory.add_get_value(f"{type_name}:/glob-executables",
                              _get_glob_executables)
        factory.add_export_data(type_name, _export_data)

    def __init__(self,
                 director: PackageBuildDirector,
                 item: Item,
                 mapper: Optional[BuildItemMapper] = None) -> None:
        super().__init__(director, item, mapper)
        DirectoryStateValueProvider(self)
        self._discarded_files: set[str] = set()
        self._files: dict[str, Optional[str]] = dict(
            (file_info["file"], file_info["hash"])
            for file_info in item.get("files", []))
        if self.item.get("directory-state-load-before-use", False):
            self.load()

    def __iter__(self):
        yield from self.files()

    @property
    def directory(self) -> str:
        """ Is the base directory of the directory state. """
        return self["directory"]

    @property
    def file(self) -> str:
        """ Is the path of the first file of the directory state. """
        return next(self.files())

    def digest(self) -> str:
        the_digest = self.item["hash"]
        if the_digest is None:
            return super().digest()
        return the_digest

    def _get_hash(self, _base: str, relative_file_path: str) -> str:
        digest = self._files[relative_file_path]
        assert digest is not None
        return digest

    def _hash_file(self, base: str, relative_file_path: str) -> str:
        file_path = os.path.join(base, relative_file_path)
        digest = hash_file(file_path)
        self._files[relative_file_path] = digest
        return digest

    def _add_hashes(self, base: str, hash_file_handler: Callable[[str, str],
                                                                 str]) -> str:
        overall_hash = hashlib.sha512()
        overall_hash.update(base.encode("utf-8"))
        for relative_file_path in sorted(self._files):
            digest = hash_file_handler(base, relative_file_path)
            overall_hash.update(relative_file_path.encode("utf-8"))
            overall_hash.update(digest.encode("ascii"))
        for associate in self.inputs("associate"):
            overall_hash.update(associate.digest().encode("ascii"))
        self._update_item_files()
        digest = base64.urlsafe_b64encode(
            overall_hash.digest()).decode("ascii")
        self.item["hash"] = digest
        return digest

    def _directory_state_exclude(self, base: str, files: set[str]) -> None:
        for exclude_item in self.item.parents("directory-state-exclude"):
            exclude_state = self.director[exclude_item.uid]
            assert isinstance(exclude_state, DirectoryStateBase)
            exclude_files = files.intersection(
                os.path.relpath(path, base) for path in exclude_state)
            logging.info(
                "%s: exclude files of directory state %s: %s", self.uid,
                exclude_item.uid,
                [os.path.join(base, path) for path in sorted(exclude_files)])
            files.difference_update(exclude_files)

    def _load_from_patterns(self, base: str, patterns: Any) -> None:
        """
        Load the files of the directory state according to the pattern
        definition.

        String patterns, whether given directly or in a list, are treated as
        include patterns.  For dictionary patterns, ``include`` must be
        specified explicitly, while ``exclude`` is optional.  The following
        pattern variants are supported:

        .. code-block:: yaml

            patterns: a.b

        .. code-block:: yaml

            patterns:
              - a.b
              - c.d

        .. code-block:: yaml

            patterns:
              exclude:
                - a.b
                - c.d
              include: e.f

        .. code-block:: yaml

            patterns:
              exclude:
                - a.b
                - c.d
              include:
                - e.f
                - g.h

        .. code-block:: yaml

            patterns:
              - exclude: []
                include: a.b
              - include:
                  - c.d
                  - e.f
        """
        logging.info("%s: load pattern defined directory state: %s", self.uid,
                     base)
        files: set[str] = set()
        base_path = Path(base)
        if isinstance(patterns, (dict, str)):
            patterns = (patterns, )
        for include_exclude in patterns:
            more: set[str] = set()
            if isinstance(include_exclude, str):
                includes: Iterable[str] | str = include_exclude
                excludes: Iterable[str] = tuple()
            else:
                includes = include_exclude["include"]
                excludes = include_exclude.get("exclude", tuple())
            if isinstance(includes, str):
                includes = (includes, )
            for include in includes:
                logging.info("%s: add files matching '%s' in: %s", self.uid,
                             include, base)
                more.update(
                    os.path.relpath(path, base)
                    for path in base_path.glob(include)
                    if path.is_symlink() or not path.is_dir())
            for exclude in excludes:
                exclude_files = set(
                    path for path in more
                    if fnmatch.fnmatch(os.path.join("/", path), exclude))
                logging.info("%s: exclude files for pattern '%s': %s",
                             self.uid, exclude, [
                                 os.path.join(base, path)
                                 for path in sorted(exclude_files)
                             ])
                more.difference_update(exclude_files)
            files.update(more)
        self._directory_state_exclude(base, files)
        self._files = dict.fromkeys(files, None)

    def load(self) -> str:
        """ Load the directory state and returns the overall hash. """
        base = self.directory
        patterns = self.get("patterns", None)
        if patterns is not None:
            self._load_from_patterns(base, patterns)
        else:
            logging.info("%s: load explicit directory state: %s", self.uid,
                         base)
        return self._add_hashes(base, self._hash_file)

    def lazy_load(self) -> str:
        """
        Load the directory state if the overall hash is not present and
        returns the overall hash.
        """
        digest = self.item["hash"]
        if digest is not None:
            return digest
        return self.load()

    def files(self, base: Optional[str] = None) -> Iterator[str]:
        """ Yield the file paths of the directory state. """
        if base is None:
            base = self.directory
        for file_path in sorted(self._files):
            yield os.path.join(base, file_path)

    def files_and_hashes(
            self,
            base: Optional[str] = None) -> Iterator[tuple[str, Optional[str]]]:
        """ Yield the file paths and hashes of the directory state. """
        if base is None:
            base = self.directory
        for file_path, file_hash in sorted(self._files.items()):
            yield os.path.join(base, file_path), file_hash

    def compact(self) -> None:
        """
        Remove the common prefix from the files and adds it to the base
        directory.
        """
        prefix = os.path.commonprefix(list(self._files.keys())).rstrip("/")
        if prefix and not os.path.isabs(prefix):
            self.item["directory"] = os.path.join(self.item["directory"],
                                                  prefix)
            self.item["hash"] = None
            self._files = dict(
                (os.path.relpath(path, prefix), None) for path in self._files)
            self._update_item_files()

    def _update_item_files(self):
        self.item["files"] = list({
            "file": path,
            "hash": digest
        } for path, digest in sorted(self._files.items()))

    def clear(self) -> None:
        """ Clear the file set of the directory state. """
        logging.info("%s: clear directory state", self.uid)
        self.item["hash"] = None
        self._files.clear()
        self._update_item_files()

    def invalidate(self) -> None:
        """ Invalidate the directory state. """
        logging.info("%s: invalidate directory state", self.uid)
        self.item["hash"] = None
        if "patterns" in self:
            self._files.clear()
        else:
            self._files = dict.fromkeys(self._files.keys(), None)
        self._update_item_files()

    def remove_files(self) -> list[str]:
        """ Remove the files of the directory state. """
        removed_files: list[str] = []
        if not self._files:
            return removed_files
        base = self.directory
        for file in sorted(self._files):
            path = os.path.join(base, file)
            logging.info("%s: remove: %s", self.uid, path)
            try:
                os.remove(path)
            except FileNotFoundError:
                if "patterns" in self:
                    logging.warning("%s: file not found: %s", self.uid, path)
                else:
                    logging.debug("%s: file not found: %s", self.uid, path)
            else:
                removed_files.append(file)
        return removed_files

    def add_files(self, files: Iterable[_Path]) -> None:
        """ Add the files to the file set of the directory state. """
        self.item["hash"] = None
        more = set(os.path.normpath(name) for name in files)
        self._directory_state_exclude(self.directory, more)
        self._files.update(dict.fromkeys(more, None))
        self._update_item_files()

    def set_files(self, files: Iterable[_Path]) -> None:
        """ Set the file set of the directory state to the files. """
        self.clear()
        self.add_files(files)

    def _copy_file(self, source: _Path, target: _Path) -> None:
        logging.info("%s: copy '%s' to '%s'", self.uid, source, target)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(source, target, follow_symlinks=False)

    def _move_file(self, source: _Path, target: _Path) -> None:
        logging.info("%s: move '%s' to '%s'", self.uid, source, target)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        os.replace(source, target)

    def copy_file(self, source: _Path, target: _Path) -> None:
        """
        Copy the file from the source path to the target path.

        Adds the target file to the file set of the directory state.  The
        target path is relative to the base directory of the directory state.
        """
        self._copy_file(source, os.path.join(self.directory, target))
        self.add_files([target])

    def copy_files(self,
                   root_dir: _Path,
                   files: Iterable[_Path],
                   prefix: _Path = ".") -> None:
        """
        Copy the files relative to the root directory to the base directory
        of the directory state using the prefix.

        The base directory of the directory state and the prefix is prepended
        to the file path for each file before it is added to the directory
        state.  Adds the target files to the file set of the directory state.
        """
        file_list: list[str] = []
        base = self.directory
        for name in files:
            file_source = os.path.join(root_dir, name)
            file_list_path = os.path.join(prefix, name)
            file_list.append(file_list_path)
            file_target = os.path.join(base, file_list_path)
            self._copy_file(file_source, file_target)
        self.add_files(file_list)

    def _add_tree(self,
                  root_dir: _Path,
                  prefix: _Path,
                  file_op: Callable[[_Path, _Path], None],
                  excludes: Optional[list[str]] = None) -> None:
        file_list: list[str] = []
        base = self.directory
        for path, _, files in os.walk(os.path.abspath(root_dir)):
            for name in files:
                file_source = os.path.join(path, name)
                file_list_path = os.path.join(
                    prefix, os.path.relpath(file_source, root_dir))
                file_target = os.path.join(base, file_list_path)
                if excludes is None:
                    file_list.append(file_list_path)
                    file_op(file_source, file_target)
                else:
                    match_path = os.path.normpath(
                        os.path.join("/", file_list_path))
                    for exclude in excludes:
                        if fnmatch.fnmatch(match_path, exclude):
                            logging.info(
                                "%s: exclude file for pattern '%s': %s",
                                self.uid, exclude, file_target)
                            break
                    else:
                        file_list.append(file_list_path)
                        file_op(file_source, file_target)
        self.add_files(file_list)

    def add_tree(self,
                 root_dir: _Path,
                 prefix: _Path = ".",
                 excludes: Optional[list[str]] = None) -> None:
        """
        Add the files of the directory tree starting at the root directory
        to the file set of the directory state.

        The added file path is relative to the root directory.  The prefix is
        prepended to the file path for each file before it is added to the
        directory state.  The files are not copied or moved.
        """
        self._add_tree(root_dir, prefix, _file_nop, excludes)

    def copy_tree(self,
                  root_dir: _Path,
                  prefix: _Path = ".",
                  excludes: Optional[list[str]] = None) -> None:
        """
        Add the files of the directory tree starting at the root directory
        to the file set of the directory state.

        The added file path is relative to the root directory.  The prefix is
        prepended to the file path for each file before it is added to the
        directory state.  The files are copied.
        """
        self._add_tree(root_dir, prefix, self._copy_file, excludes)

    def move_tree(self,
                  root_dir: _Path,
                  prefix: _Path = ".",
                  excludes: Optional[list[str]] = None) -> None:
        """
        Add the files of the directory tree starting at the root directory
        to the file set of the directory state.

        The added file path is relative to the root directory.  The prefix is
        prepended to the file path for each file before it is added to the
        directory state.  The files are moved.
        """
        self._add_tree(root_dir, prefix, self._move_file, excludes)

    def add_tarfile_members(self, archive: _Path, prefix: _Path,
                            extract: bool) -> None:
        """
        Append the members of the archive to the file list of the directory
        state.

        For each member the prefix path and the member path are joined and then
        added to the file list of the directory state.  If extract is true,
        then the members of the archive are extracted to the prefix path.
        """
        extract_info = "and extract " if extract else ""
        logging.info("%s: add %smembers of '%s' using prefix '%s'", self.uid,
                     extract_info, archive, prefix)

        uid = os.getuid()
        gid = os.getgid()

        def member_filter(info: tarfile.TarInfo,
                          _path: str) -> tarfile.TarInfo:
            info.uid = uid
            info.gid = gid
            return info

        with tarfile.open(archive, "r") as tar_file:
            base = self.directory
            file_list = [
                os.path.relpath(os.path.join(prefix, info.name), base)
                for info in tar_file.getmembers() if not info.isdir()
            ]
            if extract:
                tar_file.extractall(prefix,
                                    numeric_owner=True,
                                    filter=member_filter)
            self.add_files(file_list)

    def create_symbolic_links(
            self, symbolic_link_list: list[dict[str, str]]) -> None:
        """
        Create the specified symbolic links in the directory state.
        """
        base = self.directory
        for symbolic_link in symbolic_link_list:
            link_name = symbolic_link["link-name"]
            target = symbolic_link["target"]
            link_path = os.path.join(base, link_name)
            target_path = os.path.join(base, target)
            target_path = os.path.relpath(target_path,
                                          os.path.dirname(link_path))
            logging.info("%s: create symbolic link from '%s' to '%s'",
                         self.uid, link_path, target_path)
            os.symlink(target_path, link_path)
            self.add_files([link_name])

    def _get_files_and_reverse_mapping(
        self, file_mappings: Optional[list[dict]]
    ) -> tuple[dict[str, str | None], dict[str, str]]:
        if not file_mappings:
            return self._files.copy(), {}
        mapped_files: dict[str, str | None] = {}
        reverse_mapping: dict[str, str] = {}
        mappings: list[tuple] = []
        for file_mapping in file_mappings:
            mappings.append(
                (re.compile(file_mapping["pattern"]),
                 file_mapping["replacement"], file_mapping.get("count", 0),
                 file_mapping.get("continue", False)))
        for file, digest in self._files.items():
            file_2 = file
            for index, mapping in enumerate(mappings):
                file_3 = file_2
                file_2, count = mapping[0].subn(mapping[1],
                                                file_2,
                                                count=mapping[2])
                if count:
                    logging.info("%s: mapping %s maps %s to %s", self.uid,
                                 index, file_3, file_2)
                    if not mapping[3]:
                        break
            mapped_files[file_2] = digest
            reverse_mapping[file_2] = file
        return mapped_files, reverse_mapping

    def lazy_clone(self,
                   other: "DirectoryStateBase",
                   file_mappings: Optional[list[dict]] = None) -> str:
        """ Lazily clone the directory state. """
        # pylint: disable=protected-access
        logging.info("%s: lazy clone from: %s", self.uid, other.uid)
        mapped_files, reverse_mapping = other._get_files_and_reverse_mapping(
            file_mappings)
        current = set(self._files.keys())
        new = set(mapped_files.keys())
        base = self.directory
        other_base = other.directory
        for file in sorted(current.difference(new)):
            target = os.path.join(base, file)
            try:
                logging.info("%s: remove: %s", self.uid, target)
                os.remove(target)
            except FileNotFoundError:
                logging.warning("%s: file not found: %s", self.uid, target)
        for file in sorted(new.difference(current)):
            source = reverse_mapping.get(file, file)
            target = os.path.join(base, file)
            self._copy_file(os.path.join(other_base, source), target)
        for file in sorted(current.intersection(new)):
            source = reverse_mapping.get(file, file)
            target = os.path.join(base, file)
            if self._files[file] == mapped_files[file]:
                logging.info("%s: keep as is: %s", self.uid, target)
            else:
                self._copy_file(os.path.join(other_base, source), target)
        self._files = mapped_files
        return self._add_hashes(base, self._get_hash)

    def json_dump(self, data: Any) -> None:
        """ Dump the data into the file of the directory state. """
        file_path = self.file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, sort_keys=True, indent=2)

    def json_load(self) -> Any:
        """ Load the data from the file of the directory state. """
        with open(self.file, "r", encoding="utf-8") as file:
            return json.load(file)

    def save(self) -> None:
        """ Save the directory state to the item file. """
        self.item.save()

    def needs_build(self) -> bool:
        return self.item["hash"] is None

    def is_present(self) -> bool:
        if not self._files:
            return False
        for digest in self._files.values():
            if digest is None:
                return False
        return True

    def discard(self) -> None:
        """ Discard the directory state. """
        logging.info("%s: discard", self.uid)
        self._discarded_files.update(self.remove_files())
        self.invalidate()
        self.save()

    def refresh(self) -> None:
        logging.info("%s: refresh", self.uid)
        self.load()
        count = len(self._files)
        if count == 1:
            self.description.add(
                f"Represent the file {self.description.path(self.file)}.")
        elif count < 14:
            self.description.add_list(
                [self.description.path(name) for name in self.files()],
                "Represent the files:")
        else:
            self.description.add(f"""Represent {count} files in directory
{self.description.path(self.directory)}.""")

    def commit(self, reason: str) -> None:
        files = self._discarded_files.union(self._files.keys())
        self._discarded_files.clear()
        if files:
            base = self.directory
            self.git_add([os.path.join(base, path) for path in sorted(files)])
        super().commit(reason)


def _make_digest(value: Optional[str]) -> str:
    assert value is not None
    return base64_to_hex_text(value)


def _gather_files_and_hashes(build_item: BuildItem, names: list[str],
                             base: Optional[str], relpath: str,
                             files_and_hashes: set[tuple[str, str]]) -> None:
    if not names:
        return
    for name in names[0].split(" "):
        for input_item in build_item.inputs(name):
            if isinstance(input_item, DirectoryStateBase):
                files_and_hashes.update(
                    (os.path.relpath(file, relpath), _make_digest(digest))
                    for file, digest in input_item.files_and_hashes(base))
            _gather_files_and_hashes(input_item, names[1:], base, relpath,
                                     files_and_hashes)


class DirectoryStateValueProvider(ItemValueProvider):
    """ Provides values related to directory states. """

    # pylint: disable=too-few-public-methods

    def __init__(self, build_item: BuildItem) -> None:
        mapper = build_item.mapper
        super().__init__(mapper)
        self._build_item = build_item
        type_name = build_item.item.type
        mapper.add_get_value(f"{type_name}:/input-file-list",
                             self._get_input_files)
        mapper.add_get_value(f"{type_name}:/input-file-list-with-hashes",
                             self._get_input_files_and_hashes)

    def _files_and_hashes(self,
                          ctx: ItemGetValueContext) -> list[tuple[str, str]]:
        files_and_hashes: set[tuple[str, str]] = set()
        args, kwargs = ctx.unpack_args_dict(ctx.mapper.substitute)
        base = kwargs.get("base")
        relpath = kwargs.get("relpath", "/")
        _gather_files_and_hashes(self._build_item, args, base, relpath,
                                 files_and_hashes)
        return sorted(files_and_hashes)

    def _get_input_files(self, ctx: ItemGetValueContext) -> str:
        mapper = self.mapper
        assert isinstance(mapper, BuildItemMapper)
        content = mapper.create_content()
        content.add_list(f"{content.path(file)}"
                         for file, _ in self._files_and_hashes(ctx))
        return content.join()

    def _get_input_files_and_hashes(self, ctx: ItemGetValueContext) -> str:
        mapper = self.mapper
        assert isinstance(mapper, BuildItemMapper)
        content = mapper.create_content()
        content.add_list(
            f"{content.path(file)} with an SHA512 digest of {digest}"
            for file, digest in self._files_and_hashes(ctx))
        return content.join()
