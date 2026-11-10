# SPDX-License-Identifier: BSD-2-Clause
""" Provides a filter of the history of a repository. """

# Copyright (C) 2026 embedded brains GmbH & Co. KG
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

import contextlib
import dataclasses
import functools
import logging
import subprocess
from typing import Any, Iterable

import git_filter_repo  # type: ignore[import-untyped]
from specitems import EnabledSet, Item, data_digest, is_enabled
from specware import run_command

from .contentfilter import (ContentFilter, Files, RunAttributeActions,
                            Substitute)

_REF = "refs/heads/repository-filter"

_WARN_PATH_LIMIT = 10

_FILE_MODES = (b"100644", b"100755")


def _decode(path: bytes) -> str:
    return path.decode("utf-8", "surrogateescape")


@dataclasses.dataclass
class RepositoryFilter:
    """
    Represents the enabled rules of a repository filter item.

    A rule element which ends with a slash is a directory prefix.  Any other
    element is an exact path.  The longest element which matches a path
    decides whether the path is kept.  A path which no element matches is
    kept.  An item which an item closure drops decides before the elements.
    The content rules apply to each kept file.
    """
    uid: str
    baseline: str
    path_rules: dict[str, bool]
    content_rules: list[dict] = dataclasses.field(default_factory=list)
    content_filter: ContentFilter = dataclasses.field(
        default_factory=ContentFilter)

    def digest(self) -> str:
        """ Return the digest of the enabled rules. """
        data: dict[str, Any] = {
            "baseline": self.baseline,
            "path-rules": dict(sorted(self.path_rules.items())),
        }
        if self.content_rules:
            data["content-rules"] = self.content_rules
        return data_digest(data)

    def keep(self, path: str) -> bool:
        """ Return true, if the path passes the filter. """
        if path in self.content_filter.dropped_paths:
            return False
        keep = self.path_rules.get(path)
        end = path.rfind("/")
        while keep is None and end >= 0:
            keep = self.path_rules.get(path[:end + 1])
            end = path.rfind("/", 0, end)
        return True if keep is None else keep

    def _warn_baseline_paths(self, directory: str) -> None:
        output = subprocess.run(
            ["git", "ls-tree", "-r", "-z", "--name-only", self.baseline],
            cwd=directory,
            check=True,
            capture_output=True).stdout
        paths = [path for path in map(_decode, output.split(b"\0")) if path]
        dropped = [path for path in paths if not self.keep(path)]
        if dropped:
            more = ", ..." if len(dropped) > _WARN_PATH_LIMIT else ""
            logging.warning(
                "%s: the rules drop %d paths of the baseline %s, they stay "
                "unchanged up to the first filtered commit which changes them:"
                " %s%s", self.uid, len(dropped), self.baseline,
                ", ".join(dropped[:_WARN_PATH_LIMIT]), more)
        kept = [path for path in paths if self.keep(path)]
        for uid, index, kind, count in self.content_filter.count_selected(
                kept):
            logging.warning(
                "%s: the content rule %d of kind '%s' of %s selects %d files "
                "of the baseline %s, they stay unchanged up to the first "
                "filtered commit which changes them", self.uid, index, kind,
                uid, count, self.baseline)

    def prepare_content_filter(self, files: Files) -> None:
        """
        Prepare the content filter with the files of the tip.  The files map
        each path to the reader of its content.
        """
        self.content_filter.reset()
        self.content_filter.prepare({
            path: read
            for path, read in files.items() if self.keep(path)
        })

    def _prepare_content_filter(self, directory: str, commit: str) -> None:
        if not self.content_filter:
            return
        output = subprocess.run(
            ["git", "ls-tree", "-r", "-z", "--name-only", commit],
            cwd=directory,
            check=True,
            capture_output=True).stdout

        def _read(path: str) -> bytes:
            return subprocess.run(
                ["git", "cat-file", "blob", f"{commit}:{path}"],
                cwd=directory,
                check=True,
                capture_output=True).stdout

        self.prepare_content_filter({
            path: functools.partial(_read, path)
            for path in map(_decode, output.split(b"\0")) if path
        })

    def is_ancestor_of_baseline(self, directory: str, commit: str) -> bool:
        """
        Return true, if the commit is the baseline or an ancestor of it in
        the repository of the directory.
        """
        return run_command(
            ["git", "merge-base", "--is-ancestor", commit, self.baseline],
            directory) == 0

    def run(self, directory: str, commit: str) -> str:
        """
        Filter the commits which follow the baseline up to the commit in the
        bare repository of the directory.  Return the filtered commit.
        """
        if run_command(
            ["git", "merge-base", "--is-ancestor", self.baseline, commit],
                directory) != 0:
            raise ValueError(f"{self.uid}: the baseline {self.baseline} is "
                             f"no ancestor of commit {commit}")
        status = run_command(["git", "update-ref", _REF, commit], directory)
        assert status == 0
        self._prepare_content_filter(directory, commit)
        self._warn_baseline_paths(directory)
        filtered_blobs: dict[tuple[bytes, bytes], bytes] = {}

        def filename_callback(filename: bytes) -> bytes | None:
            if self.keep(_decode(filename)):
                return filename
            return None

        def file_info_callback(filename: bytes, mode: bytes, blob_id: bytes,
                               value: Any) -> tuple[bytes, bytes, bytes]:
            if mode in _FILE_MODES and self.content_filter.matches(
                    _decode(filename)):
                key = (filename, blob_id)
                filtered = filtered_blobs.get(key)
                if filtered is None:
                    content = value.get_contents_by_identifier(blob_id)
                    new_content = self.content_filter.apply(
                        _decode(filename), content)
                    filtered = blob_id if new_content == content else (
                        value.insert_file_with_contents(new_content))
                    filtered_blobs[key] = filtered
                blob_id = filtered
            return filename, mode, blob_id

        logging.info("%s: filter the commits from %s to %s in: %s", self.uid,
                     self.baseline, commit, directory)
        args = git_filter_repo.FilteringOptions.parse_args(
            ["--force", "--quiet", "--refs", f"{self.baseline}..{_REF}"])
        with contextlib.chdir(directory):
            git_filter_repo.RepoFilter(
                args,
                filename_callback=filename_callback,
                file_info_callback=file_info_callback).run()
        stdout: list[str] = []
        status = run_command(["git", "rev-parse", _REF], directory, stdout)
        assert status == 0
        return stdout[0].strip()


def export_no_data(_item: Item, _present: bool, _built_later: bool) -> None:
    """ Export no data of a repository filter item. """
    return None


def _add_elements(uid: str, path_rules: dict[str, bool], elements: list[str],
                  keep: bool) -> None:
    for element in elements:
        other = path_rules.setdefault(element, keep)
        if other != keep:
            raise ValueError(f"{uid}: the path rule element '{element}' "
                             "is in an enabled drop and keep list")


def _add_content_rules(item: Item, enabled_set: EnabledSet,
                       repository_filter: RepositoryFilter,
                       substitute: Substitute,
                       run_attribute_actions: RunAttributeActions) -> None:
    for index, rule in enumerate(item.get("content-rules", [])):
        if is_enabled(enabled_set, rule["enabled-by"]):
            repository_filter.content_rules.append(rule)
            repository_filter.content_filter.add_rule(item.uid, index, rule,
                                                      substitute,
                                                      run_attribute_actions)


def _add_item(item: Item, enabled_set: EnabledSet,
              path_rules: dict[str, bool]) -> None:
    uid = item.uid
    for rule in item["path-rules"]:
        if is_enabled(enabled_set, rule["enabled-by"]):
            _add_elements(uid, path_rules, rule["drop"], False)
            _add_elements(uid, path_rules, rule["keep"], True)


def load_repository_filter(
        uid: str, items: Iterable[Item], enabled_set: EnabledSet,
        substitute: Substitute,
        run_attribute_actions: RunAttributeActions) -> RepositoryFilter | None:
    """
    Load the enabled rules of the repository filter items.  Return None
    without an item.  The substitute function substitutes the subprocess of
    a content rule.  The attribute actions of a structure rule run through
    run_attribute_actions.
    """
    baseline: str | None = None
    path_rules: dict[str, bool] = {}
    items = list(items)
    for item in items:
        if baseline is None:
            baseline = item["baseline"]
        elif baseline != item["baseline"]:
            raise ValueError(f"{item.uid}: the baseline {item['baseline']} "
                             f"differs from the baseline {baseline} of the "
                             f"other repository filters of {uid}")
        _add_item(item, enabled_set, path_rules)
    if baseline is None:
        return None
    repository_filter = RepositoryFilter(uid, baseline, path_rules)
    for item in items:
        _add_content_rules(item, enabled_set, repository_filter, substitute,
                           run_attribute_actions)
    return repository_filter
