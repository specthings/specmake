# SPDX-License-Identifier: BSD-2-Clause
""" Builds an archive file from directory states. """

# Copyright (C) 2021 EDISOFT
# Copyright (C) 2020, 2024 embedded brains GmbH & Co. KG
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
import graphlib
import itertools
import pickle
import logging
import lzma
import os
import stat
import tarfile

from specitems import save_data

from .directorystate import DirectoryState

_FileInfo = list[tuple[str, str, bool]]
_ArchiveFiles = dict[str, _FileInfo]


def _check_for_duplicates(uid: str, file_path: str,
                          file_info: _FileInfo) -> None:
    if len(file_info) == 1:
        return
    logging.info("%s: duplicates in directory states %s for file: %s", uid,
                 list(info[1] for info in file_info), file_path)
    for index, info in enumerate(file_info):
        for info_2 in file_info[index + 1:]:
            if info[0] != info_2[0]:
                logging.error(
                    "%s: inconsistent file hashes %s (of %s) "
                    "and %s (of %s) for file: %s", uid, info[0], info[1],
                    info_2[0], info_2[1], file_path)


_SCRIPT_HEAD = f"""#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
\"\"\" Verifies the files of the package. \"\"\"

# Copyright (C) 2021, 2022 embedded brains GmbH & Co. KG
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
import binascii
import argparse
import hashlib
import pickle
import logging
import lzma
import os
import sys


# This is a list of (<file-path>, <binary-hash>) tuples,
# which was serialized using the Python pickle protocol \
{pickle.DEFAULT_PROTOCOL},
# then compressed using LZMA,
# and finally encoded as base85.
_B85_DATA = """

_SCRIPT_TAIL = """

def _hash_file(path: str) -> bytes:
    file_hash = hashlib.sha512()
    if os.path.islink(path):
        file_hash.update(os.readlink(path).encode("utf-8"))
    else:
        buf = bytearray(65536)
        memview = memoryview(buf)
        with open(path, "rb", buffering=0) as src:
            for size in iter(lambda: src.readinto(memview), 0):  # type: ignore
                file_hash.update(memview[:size])
    return file_hash.digest()


def _hex(digest: bytes) -> str:
    return binascii.hexlify(digest).decode("ascii")


def _check_file(file_path: str, expected_files: dict[str, bytes]) -> int:
    expected_hash = expected_files[file_path]
    actual_hash = _hash_file(file_path)
    if expected_hash != actual_hash:
        logging.error(
            "expected hash is %s, actual hash is %s for file: %s",
            _hex(expected_hash), _hex(actual_hash), file_path)
        return 1
    return 0


def _verify_files(script: str, expected_files: dict[str, bytes]) -> int:
    status = 0
    script = os.path.normpath(script)
    for path, dirs, files in os.walk("."):
        dirs.sort()
        for name in sorted(files):
            file_path = os.path.normpath(os.path.join(path, name))
            if file_path in expected_files:
                status = _check_file(file_path, expected_files)
                del expected_files[file_path]
            elif file_path != script:
                logging.warning("unexpected file: %s", file_path)
    for maybe_missing in expected_files.keys():
        if os.path.islink(maybe_missing):
            status = _check_file(maybe_missing, expected_files)
            continue
        logging.error("missing file: %s", maybe_missing)
        status = 1
    return status


def main(script: str, argv: list[str]) -> int:
    \"\"\" Verifies the files of the package. \"\"\"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        type=str.upper,
        default="WARNING",
        help="log level")
    parser.add_argument("--log-file",
                        type=str,
                        default=None,
                        help="log to this file")
    parser.add_argument("--list-files",
                        action="store_true",
                        help="list the files of the package")
    parser.add_argument("--list-files-and-hashes",
                        action="store_true",
                        help="list the files of the package "
                        "with the SHA512 digest of each file")
    args = parser.parse_args(argv)
    logging.basicConfig(filename=args.log_file, level=args.log_level)
    data = pickle.loads(lzma.decompress(base64.b85decode(_B85_DATA)))
    expected_files = dict((os.path.normpath(x[0]), x[1]) for x in data)
    status = 0
    if args.list_files_and_hashes:
        for file_path, hash_value in expected_files.items():
            print(f"{file_path}\t{_hex(hash_value)}")
    elif args.list_files:
        for file_path in expected_files.keys():
            print(file_path)
    else:
        status = _verify_files(script, expected_files)
    return status



if __name__ == "__main__":
    status = main(sys.argv[0], sys.argv[1:])
    sys.exit(status)
"""


def _create_verification_script(script_file: str,
                                archive_files: _ArchiveFiles) -> None:
    script_dir = os.path.dirname(script_file)
    with open(script_file, "w", encoding="utf-8") as out:
        out.write(_SCRIPT_HEAD)
        data = [(os.path.relpath(file_path, script_dir),
                 base64.urlsafe_b64decode(info[-1][0]))
                for file_path, info in sorted(archive_files.items())]
        pickle_data = pickle.dumps(data)
        lzma_data = lzma.compress(pickle_data)
        b85_data = base64.b85encode(lzma_data).decode("ascii")
        for i in range(0, len(b85_data), 76):
            out.write(f"\\\n\"{b85_data[i:i + 76]}\"")
        out.write(_SCRIPT_TAIL)
    os.chmod(script_file, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)


class Archiver(DirectoryState):
    """
    The archiver adds the file of its directory state member inputs to an
    archive file.
    """

    def _gather_files(self, dir_state: DirectoryState,
                      dependencies: dict[str, set[str]],
                      archive_files: _ArchiveFiles) -> None:
        dir_state_uid = dir_state.uid
        logging.info("%s: gather files of directory state: %s", self.uid,
                     dir_state_uid)
        for file_path, hash_value in dir_state.files_and_hashes():
            link_targets = dependencies.setdefault(file_path, set())
            try:
                target = os.readlink(file_path)
            except OSError:
                pass
            else:
                link_targets.add(
                    os.path.normpath(
                        os.path.join(os.path.dirname(file_path), target)))
            assert hash_value
            archive_files.setdefault(file_path, []).append(
                (hash_value, dir_state_uid, os.path.islink(file_path)))

    def _export_spec(self, dependencies: dict[str, set[str]],
                     archive_files: _ArchiveFiles) -> str:
        try:
            spec_output = self.output("spec-export")
        except KeyError:
            return ""
        assert isinstance(spec_output, DirectoryState)
        directory = spec_output.directory
        logging.info("%s: export specification to directory: %s", self.uid,
                     directory)
        member_uids = set(member.uid for member in self.inputs("member"))
        files: list[str] = []
        factory = self.director.factory
        build_order = self.item.view["package-build-order"]
        item_cache = self.director.item_cache
        for uid, item in itertools.chain(item_cache.items(),
                                         item_cache.proxies.items()):
            if item.type.startswith("spec"):
                continue
            data = factory.export_data(item, uid in member_uids, build_order)
            uid_path = f"{uid[1:]}.yml"
            path = os.path.join(directory, uid_path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            save_data(path, data)
            files.append(uid_path)
        spec_output.set_files(files)
        spec_output.load()
        self._gather_files(spec_output, dependencies, archive_files)
        return ("Export the specification items to directory\n"
                f"{self.description.path(directory)}.")

    def _create_verification_script(self, tar_file: tarfile.TarFile,
                                    strip_prefix: str,
                                    archive_files: _ArchiveFiles) -> str:
        try:
            script_output = self.output("verify-script")
        except KeyError:
            return ""
        assert isinstance(script_output, DirectoryState)
        script_output.set_files((self["verification-script"], ))
        script_path = script_output.file
        logging.info("%s: create the verification script: %s", self.uid,
                     script_path)
        _create_verification_script(script_path, archive_files)
        tar_file.add(script_path, os.path.relpath(script_path, strip_prefix))
        return ("Create the archive verification script\n"
                f"{self.description.path(script_path)}.")

    def run(self) -> None:
        dependencies: dict[str, set[str]] = {}
        archive_files: _ArchiveFiles = {}
        for dir_state in self.inputs("member"):
            assert isinstance(dir_state, DirectoryState)
            self._gather_files(dir_state, dependencies, archive_files)
        export_description = self._export_spec(dependencies, archive_files)

        self.set_files((self["archive-file"], ))
        archive_path = self.file
        logging.info("%s: create archive: %s", self.uid, archive_path)
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        with tarfile.open(archive_path, "w:xz") as tar_file:
            strip_prefix = self["archive-strip-prefix"]

            # On some Windows versions, symbolic links have to be created after
            # the link target exists.  Sort the files accordingly.
            dependencies = dict(sorted(dependencies.items()))
            for file_path in graphlib.TopologicalSorter(
                    dependencies).static_order():
                try:
                    archive_files[file_path]
                except KeyError:
                    # This is a symbolic link target outside our control
                    logging.warning(
                        "%s: symbolic link target is "
                        "outside the archive scope: %s", self.uid, file_path)
                    continue
                _check_for_duplicates(self.uid, file_path,
                                      archive_files[file_path])
                tar_file.add(file_path,
                             os.path.relpath(file_path, strip_prefix))

            script_description = self._create_verification_script(
                tar_file, strip_prefix, archive_files)
        logging.info("%s: finished to create archive: %s", self.uid,
                     archive_path)

        self.description.add(f"""Create the archive file
{self.description.path(archive_path)}.
{script_description}
{export_description}""")
