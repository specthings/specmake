# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the testrunner module. """

# Copyright (C) 2023, 2025 embedded brains GmbH & Co. KG
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

import logging
from pathlib import Path
import subprocess
import tarfile
from typing import NamedTuple

import pytest
from specitems import Item

import specmake
from specmake import (PackageBuildDirector, Executable, Report, TestRunner)

from .util import create_package, get_and_clear_log

TestRunner.__test__ = False


class _TestRunner(TestRunner):

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self.run_count = 0

    def run_tests(self, executables: list[Executable]) -> list[Report]:
        logging.info("executables: %s", executables)
        super().run_tests(executables)
        self.run_count += 1
        if self.run_count == 1:
            return []
        if self.run_count == 2:
            return [{
                "executable":
                executables[0].path,
                "output": [
                    "*** BEGIN OF GCOV INFO BASE64 ***", "foobar",
                    "*** END OF GCOV INFO BASE64 ***"
                ]
            }, {
                "executable": executables[1].path,
                "error": "blubb",
                "output": []
            }]
        if self.run_count == 3:
            return [{
                "executable":
                executables[0].path,
                "output": [
                    "*** BEGIN OF TEST TS ***", "*** TEST VERSION: V",
                    "*** TEST STATE: EXPECTED_PASS", "*** TEST BUILD:",
                    "*** TEST TOOLS: C", "A:TS", "S:Platform:RTEMS",
                    "S:Compiler:C", "S:Version:V", "S:BSP:bsp",
                    "S:BuildLabel:DEFAULT",
                    "S:TargetHash:SHA256:qYOFDHUGg5--JyB28V7llk_t6WYeA3VAogeqwGLZeCM=",
                    "S:RTEMS_DEBUG:0", "S:RTEMS_MULTIPROCESSING:0",
                    "S:RTEMS_POSIX_API:0", "S:RTEMS_PROFILING:0",
                    "S:RTEMS_SMP:0", "Z:TS:C:0:N:0:F:0:D:0.014590",
                    "Y:ReportHash:SHA256:JlS-9kM8jYqTjFvRbuUDzHpfph6PznxFxCLx30NkcoI="
                ]
            }]
        return [{
            "executable": executable.path,
            "executable-sha512": executable.digest,
            "output": []
        } for executable in executables]


class _Subprocess(NamedTuple):
    stdout: bytes


def _subprocess_run(command, check, stdin, stdout, timeout):
    if command[2] == "a.exe":
        raise Exception("foobar")
    if command[2] == "b.exe":
        raise subprocess.TimeoutExpired(command[2], timeout, b"")
    if command[2] == "c.exe":
        raise subprocess.TimeoutExpired(command[2], timeout, None)
    return _Subprocess(b"u\r\nv\nw\n")


def test_testrunner(caplog, tmpdir, monkeypatch):
    monkeypatch.setattr(specmake.testrunner, "subprocess_run", _subprocess_run)
    tmp_dir = Path(tmpdir)
    package = create_package(caplog, tmp_dir, Path("spec-packagebuild"),
                             ["run-tests"])
    director = package.director
    director.factory.add_constructor("pkg/test-runner/test", _TestRunner)

    # Test GRMONManualTestRunner
    grmon_manual_runner = director["/pkg/test-runner/grmon-manual"]
    assert "GRMON" in grmon_manual_runner.describe()
    exe = tmp_dir / "a.exe"
    exe.touch()
    with pytest.raises(IOError):
        executables = [
            Executable(
                str(exe), "QvahP3YJU9bvpd7DYxJDkRBLJWbEFMEoH5Ncwu6UtxA"
                "_l9EQ1zLW9yQTprx96BTyYE2ew7vV3KECjlRg95Ya6A==", 456)
        ]
        grmon_manual_runner._executables = executables
        with grmon_manual_runner.component_scope(package):
            grmon_manual_runner.run_tests(executables)
    with tarfile.open(tmp_dir / "tests.tar.xz", "r:*") as archive:
        assert archive.getnames() == [
            "tests/run.grmon", "tests/run.sh", "tests/a.exe"
        ]
        with archive.extractfile("tests/run.grmon") as src:
            assert src.read() == b"a.exe\n"
        with archive.extractfile("tests/run.sh") as src:
            assert src.read() == b"abc\n"

    # Test SubprocessTestRunner
    subprocess_runner = director["/pkg/test-runner/subprocess"]
    assert subprocess_runner.describe(
    ) == """For each test program (indicated by ``${test-program}``),
this test procedure runs the following command as a subprocess on the machine
building the package and captures the output:

.. code-block:: none

    foo bar ${test-program}"""
    assert subprocess_runner.get_run_command("exe") == ["foo", "bar", "exe"]
    reports = subprocess_runner.run_tests([
        Executable(
            "a.exe", "QvahP3YJU9bvpd7DYxJDkRBLJWbEFMEoH5Ncwu6UtxA"
            "_l9EQ1zLW9yQTprx96BTyYE2ew7vV3KECjlRg95Ya6A==", 1),
        Executable(
            "b.exe", "4VgX6KGWuDyG5vmlO4J-rdbHpOJoIIYLn_3oSk2BKAc"
            "Au5RXTg1IxhHjiPO6Yzl8u4GsWBh0qc3flRwEFcD8_A==", 2),
        Executable(
            "c.exe", "YtTC0r1DraKOn9vNGppBAVFVTnI9IqS6jFDRBKVucU_"
            "W_dpQF0xtC_mRjGV7t5RSQKhY7l3iDGbeBZJ-lV37bg==", 3),
        Executable(
            "d.exe", "ZtTC0r1DraKOn9vNGppBAVFVTnI9IqS6jFDRBKVucU_"
            "W_dpQF0xtC_mRjGV7t5RSQKhY7l3iDGbeBZJ-lV37bg==", 4)
    ])
    reports[0]["start-time"] = "c"
    reports[0]["duration"] = 2.
    reports[1]["start-time"] = "d"
    reports[1]["duration"] = 3.
    reports[2]["start-time"] = "e"
    reports[2]["duration"] = 4.
    reports[3]["start-time"] = "f"
    reports[3]["duration"] = 5.
    assert reports == [{
        "command-line": ["foo", "bar", "a.exe"],
        "duration":
        2.0,
        "error":
        "foobar",
        "executable":
        "a.exe",
        "executable-sha512":
        "QvahP3YJU9bvpd7DYxJDkRBLJWbEFMEoH5Ncwu6UtxA_"
        "l9EQ1zLW9yQTprx96BTyYE2ew7vV3KECjlRg95Ya6A==",
        "output": [""],
        "start-time":
        "c"
    }, {
        "command-line": ["foo", "bar", "b.exe"],
        "duration":
        3.,
        "error":
        "timeout",
        "executable":
        "b.exe",
        "executable-sha512":
        "4VgX6KGWuDyG5vmlO4J-rdbHpOJoIIYLn_3oSk2BKAcA"
        "u5RXTg1IxhHjiPO6Yzl8u4GsWBh0qc3flRwEFcD8_A==",
        "output": [""],
        "start-time":
        "d"
    }, {
        "command-line": ["foo", "bar", "c.exe"],
        "duration":
        4.,
        "error":
        "timeout",
        "executable":
        "c.exe",
        "executable-sha512":
        "YtTC0r1DraKOn9vNGppBAVFVTnI9IqS6jFDRBKVucU_W"
        "_dpQF0xtC_mRjGV7t5RSQKhY7l3iDGbeBZJ-lV37bg==",
        "output": [""],
        "start-time":
        "e"
    }, {
        "command-line": ["foo", "bar", "d.exe"],
        "duration":
        5.,
        'error':
        'discarded due to match with: u.*v.*w',
        "executable":
        "d.exe",
        "executable-sha512":
        "ZtTC0r1DraKOn9vNGppBAVFVTnI9IqS6jFDRBKVucU_W"
        "_dpQF0xtC_mRjGV7t5RSQKhY7l3iDGbeBZJ-lV37bg==",
        "output": ["u", "v", "w"],
        "start-time":
        "f"
    }]

    # Test TestRunner
    build_bsp = director["/pkg/build/bsp"]
    build_bsp.load()
    director.build_package()
    log = get_and_clear_log(caplog)
    assert ": cannot reuse reports" in log
    assert ": blubb" in log
    assert ": no report" in log
    assert ": gcov info is corrupt" in log
    assert ": test suite report is corrupt" in log
    assert (f"executables: [Executable(path='{build_bsp.directory}"
            "/a.exe', digest='z4PhNX7vuL3xVChQ1m2AB9Yg5AULVxXcg_SpIdNs6c5H0NE8"
            "XYXysP-DGNKHfuwvY7kxvUdBeoGlODJ6-SfaPg==', timeout=180.0), "
            f"Executable(path='{build_bsp.directory}/b.exe', "
            "digest='hopqxuHQKT10-tB_bZWVKz4B09MVPbZ3p12Ad5g_1OMNtr_Im3YIqT-yZ"
            "GkjOp8aCVctaHqcXaeLID6xUQQKFQ==', timeout=16.0)]") in log
    (tmp_dir / "pkg/test-log-bsp.json").unlink()
    director.build_package(force=["/pkg/test-logs/bsp"])
    log = get_and_clear_log(caplog)
    assert f": no report" in log
    director.build_package(force=["/pkg/test-logs/bsp"])
    log = get_and_clear_log(caplog)
    assert f"use previous report for: {build_bsp.directory}/a.exe" in log


def test_testrunner_dummy(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("spec-packagebuild"),
                             ["run-tests-dummy"])
    director = package.director
    director.factory.add_constructor("pkg/test-runner/test", _TestRunner)

    # Test TestRunner
    dummy_runner = director["/pkg/test-runner/dummy"]
    assert dummy_runner.run_tests([]) == []
    assert dummy_runner.get_run_command("foobar") == None
    with pytest.raises(ValueError, match="there is no timeout key"):
        director.build_package(only=["/pkg/test-logs/test-runner-dummy"])
