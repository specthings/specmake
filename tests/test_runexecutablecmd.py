# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the perfimages module. """

# Copyright (C) 2025 embedded brains GmbH & Co. KG
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

from pathlib import Path

from specitems import Item

from specmake import PackageBuildDirector, TestRunner

from .util import create_package

TestRunner.__test__ = False


class _TestRunner(TestRunner):

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self._toggle = True

    def get_run_command(self, executable: str) -> None | list[str]:
        toggle = self._toggle
        self._toggle = not toggle
        if toggle:
            return None
        return [executable]


def test_runexecutablecmd(caplog, tmpdir):
    tmp_dir = Path(tmpdir)
    package = create_package(
        caplog, tmp_dir, Path("spec-packagebuild"),
        ["aggregate-test-results", "run-executable-command"])
    director = package.director
    director.factory.add_constructor("pkg/test-runner/test", _TestRunner)
    build_item = director["/pkg/deployment/run"]
    director.build_package(only=[build_item.uid])
    with open(build_item.file, "r") as src:
        assert src.read() == '''#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
""" Runs the executable on the target. """

# Copyright (C) 2024 embedded brains GmbH & Co. KG
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

import argparse
import base64
import json
import hashlib
import os
import subprocess
import sys

_TARGETS_BY_BSP: dict[str, str] = {
    'sparc-gr712rc-smp-extra': 'sparc/gr712rc/smp',
    'sparc-gr712rc-smp-qual-only': 'sparc/gr712rc/smp'
}

_TEST_LOGS_BY_TARGET: dict[str, str] = {
    'sparc/gr712rc/smp': ['${package-directory}/test-log-bsp.json']
}

_COMMANDS: dict[str, list[str]] = {'sparc/gr712rc/smp/one': ['$${executable}']}


def _hash_file(path: str) -> str:
    file_hash = hashlib.sha512()
    if os.path.islink(path):
        file_hash.update(os.readlink(path).encode("utf-8"))
    else:
        buf = bytearray(65536)
        memview = memoryview(buf)
        with open(path, "rb", buffering=0) as src:
            for size in iter(lambda: src.readinto(memview), 0):  # type: ignore
                file_hash.update(memview[:size])
    return base64.urlsafe_b64encode(file_hash.digest()).decode("ascii")


def main(script: str, argv: list[str]) -> int:
    """ Runs the executables on the target. """
    package_directory = os.path.normpath(
        os.path.join(os.path.dirname(__file__), ".."))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runner-type",
        default="simulator",
        type=str,
        help=f"the type of the executable runner (default: simulator)")
    parser.add_argument(
        "--package-directory",
        default=package_directory,
        type=str,
        help=f"the package directory (default: {package_directory})")
    parser.add_argument("--do-not-use-test-logs",
                        action="store_true",
                        help=f"do not use the test logs to look up a report")
    parser.add_argument("target",
                        metavar="TARGET",
                        nargs=1,
                        help="the target on which the executables should run; "
                        "the target is the name of an installed BSP "
                        f"(one of {list(_TARGETS_BY_BSP.keys())}) "
                        f"or a runner (one of {list(_COMMANDS.keys())})")
    parser.add_argument("executables",
                        metavar="EXECUTABLES",
                        nargs="+",
                        help="the executable files to run")
    args = parser.parse_args(argv)
    target = args.target[0]
    target = _TARGETS_BY_BSP.get(target, target)
    try:
        command = _COMMANDS[target]
    except KeyError:
        command = _COMMANDS.get(f"{target}/{args.runner_type}", None)
    reports_by_hash: dict = {}
    if not args.do_not_use_test_logs:
        for test_log_file in _TEST_LOGS_BY_TARGET.get(target, []):
            path = test_log_file.replace("${package-directory}",
                                         args.package_directory)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    for report in json.load(file)["reports"]:
                        digest = report["executable-sha512"]
                        if digest not in reports_by_hash:
                            reports_by_hash[digest] = report["output"]
            except FileNotFoundError:
                pass
    for executable in args.executables:
        digest = _hash_file(executable)
        report = reports_by_hash.get(digest, None)
        if report is None:
            if command is None:
                print(
                    f"{script}: in your environment, "
                    "there is no service available to run the executable "
                    f"on the target '{target}'; "
                    f"available runner targets are: {list(_COMMANDS.keys())} ",
                    file=sys.stderr)
                return 1
            command = [
                arg.replace("${executable}",
                            executable).replace("${package-directory}",
                                                args.package_directory)
                for arg in command
            ]
            subprocess.run(command, check=True, stdin=subprocess.DEVNULL)
        else:
            print("\\n".join(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[0], sys.argv[1:]))
'''
