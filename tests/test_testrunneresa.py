# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the testrunneresa module. """

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

import datetime
import logging
import os
import pytest

from specitems import Item, EmptyItemCache, Link

import specmake
from specmake import (BuildItemFactory, BuildItemTypeProvider, ESATestRunner,
                      Executable, PackageComponent, PackageBuildDirector,
                      RepositoryState)


def _gethostname():
    return "host"


_NOW = datetime.datetime(1970, 1, 1)


class _Datetime:

    @classmethod
    def utcnow(cls):
        return _NOW


_GIT_NEW_BRANCH = (
    [
        'git',
        'checkout',
        '-B',
        'pkg-Name-host-1970-01-01-00-00-00-000000',
        'a412700fd90e6195c255aea2048ae2ef37244df5',
    ],
    0,
    [],
)

_GIT_BASE_BRANCH = (
    [
        'git',
        'checkout',
        'b',
    ],
    0,
    [],
)

_GIT_PUSH_BRANCH = (
    [
        'git',
        'push',
        'origin',
        'pkg-Name-host-1970-01-01-00-00-00-000000',
    ],
    0,
    [],
)

_GIT_RESET_BRANCH = (
    [
        'git',
        'reset',
        '--hard',
        'origin/pkg-Name-host-1970-01-01-00-00-00-000000',
    ],
    0,
    [],
)

_GIT_DELETE_BRANCH = (
    [
        'git',
        'branch',
        '-D',
        'pkg-Name-host-1970-01-01-00-00-00-000000',
    ],
    0,
    [],
)

_GIT_DELETE_REMOTE_BRANCH = (
    [
        'git',
        'push',
        '-d',
        'origin',
        'pkg-Name-host-1970-01-01-00-00-00-000000',
    ],
    0,
    [],
)


def _strip(exe):
    return [
        'strip',
        str(exe),
        '-o',
        str(exe),
    ], 0, []


def _add(exes):
    return ['git', 'add'] + [f"{exe.name}.bz2"
                             for exe in exes] + ["request.yaml"], 0, []


def _commit(counter):
    return ['git', 'commit', '-m', f"Request {counter}"], 0, []


def _fetch(status):
    return (
        [
            'git',
            'fetch',
            'origin',
            'pkg-Name-host-1970-01-01-00-00-00-000000',
        ],
        status,
        [],
    )


def _log(stdout):
    return ([
        'git',
        'log',
        'HEAD..origin/pkg-Name-host-1970-01-01-00-00-00-000000',
        '--oneline',
    ], 0, stdout)


def _monotonic():
    return 0


def _sleep(interval):
    pass


def test_testrunneresa(monkeypatch, tmp_path):
    commands = []

    def _run_command(args, cwd=None, stdout=None, status=None):
        expected_args, status, the_stdout = commands.pop(0)
        if stdout is not None:
            stdout.extend(the_stdout)
        logging.critical("actual %s, expected %s", args, expected_args)
        assert args == expected_args
        return status

    monkeypatch.setattr(specmake.testrunneresa, "run_command", _run_command)
    monkeypatch.setattr(specmake.testrunneresa.datetime, "datetime", _Datetime)
    monkeypatch.setattr(specmake.testrunneresa.socket, "gethostname",
                        _gethostname)
    monkeypatch.setattr(specmake.testrunneresa.time, "monotonic", _monotonic)
    monkeypatch.setattr(specmake.testrunneresa.time, "sleep", _sleep)

    item_cache = EmptyItemCache(type_provider=BuildItemTypeProvider({}))
    factory = BuildItemFactory()
    factory.add_constructor("pkg/component/generic", PackageComponent)
    factory.add_constructor("pkg/directory-state/repository", RepositoryState)
    factory.add_constructor("pkg/test-runner/esa", ESATestRunner)
    director = PackageBuildDirector(item_cache, "?", factory)
    base = os.path.abspath(os.path.dirname(__file__))
    item_cache.add_item(
        "/component", {
            "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
            "arch": "Arch",
            "bsp": "BSP",
            "component-type": "generic",
            "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
            "enabled-by": True,
            "enabled-set": [],
            "links": [],
            "name": "Name",
            "pkg-type": "component",
            "type": "pkg",
        })
    repo_item = item_cache.add_item(
        "/repository", {
            "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
            "branch": "b",
            "commit": "a412700fd90e6195c255aea2048ae2ef37244df5",
            "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
            "copyrights-by-license": {},
            "description": "d",
            "directory": str(tmp_path),
            "directory-state-type": "repository",
            "enabled-by": True,
            "files": [],
            "hash": None,
            "links": [],
            "origin-branch": None,
            "origin-commit": None,
            "origin-commit-url": None,
            "origin-url": None,
            "patterns": [],
            "pkg-type": "directory-state",
            "type": "pkg"
        })
    item_cache.add_item(
        "/runner", {
            "SPDX-License-Identifier":
            "CC-BY-SA-4.0 OR BSD-2-Clause",
            "bsp-to-target-board": {
                "Arch/BSP": "Board"
            },
            "default-timeout-in-seconds":
            90.0,
            "delete-remote-branch":
            True,
            "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
            "description":
            "Description.",
            "do-not-run": [],
            "enabled-by":
            True,
            "files": [{
                "file": "hello.py",
                "hash": None
            }],
            "git-fetch-polling-interval-in-seconds":
            60,
            "hash":
            None,
            "links": [{
                "role": "input",
                "hash": None,
                "name": "component",
                "uid": "/component"
            }, {
                "role": "weak-package-build-dependency",
                "uid": "/repository"
            }],
            "max-overall-timeout-in-seconds":
            10,
            "max-request-delay-in-seconds":
            0,
            "max-retry-count-per-executable":
            0,
            "min-timeout-in-seconds":
            10.0,
            "name":
            "Name",
            "params": {},
            "pkg-type":
            "test-runner",
            "request-policy": {
                "policy": "use-timeouts",
            },
            "strip-program-path":
            "strip",
            "test-runner-type":
            "esa",
            "timeout-scaler":
            2.0,
            "type":
            "pkg",
        })
    runner = director["/runner"]
    assert isinstance(runner, ESATestRunner)

    assert runner.describe(
    ) == """This test procedure requests the `ESA run tests service
<https://gitlab.esa.int/flight-software/fsw-boards-server/FSWBoardsServerRemoteExecution_Binaries.git>`__
to run the test programs on the ``Board`` target board."""

    logging.critical("empty request with remote branch delete")
    assert not commands
    commands.extend([
        _GIT_NEW_BRANCH,
        _GIT_DELETE_REMOTE_BRANCH,
        _GIT_BASE_BRANCH,
        _GIT_DELETE_BRANCH,
    ])
    runner.run_tests([])

    runner.item["delete-remote-branch"] = False

    logging.critical("empty request without remote branch delete")
    assert not commands
    commands.extend([
        _GIT_NEW_BRANCH,
        _GIT_BASE_BRANCH,
        _GIT_DELETE_BRANCH,
    ])
    runner.run_tests([])

    logging.critical("request with timeout")
    exe_a = tmp_path / "a.exe"
    exe_a.write_bytes(b"a")
    assert not commands
    commands.extend([
        _GIT_NEW_BRANCH,
        _strip(exe_a),
        _add([exe_a]),
        _commit(0),
        _GIT_PUSH_BRANCH,
        _GIT_RESET_BRANCH,
        _GIT_BASE_BRANCH,
        _GIT_DELETE_BRANCH,
    ])
    runner.run_tests([Executable(str(exe_a), "", 0)])

    logging.critical("request without timeout")
    exe_a = tmp_path / "a.exe"
    exe_a.write_bytes(b"a")
    assert not commands
    commands.extend([
        _GIT_NEW_BRANCH,
        _strip(exe_a),
        _add([exe_a]),
        _commit(0),
        _GIT_PUSH_BRANCH,
        _fetch(1),
        _log([]),
        _fetch(0),
        _log(["x"]),
        _GIT_RESET_BRANCH,
        _GIT_BASE_BRANCH,
        _GIT_DELETE_BRANCH,
    ])
    runner.run_tests([Executable(str(exe_a), "", 1)])

    logging.critical("single request")
    exe_a = tmp_path / "a.exe"
    exe_a.write_bytes(b"a")
    exe_b = tmp_path / "b.exe"
    exe_b.write_bytes(b"b")
    assert not commands
    commands.extend([
        _GIT_NEW_BRANCH,
        _strip(exe_a),
        _strip(exe_b),
        _add([exe_a, exe_b]),
        _commit(0),
        _GIT_PUSH_BRANCH,
        _fetch(0),
        _log(["x"]),
        _GIT_RESET_BRANCH,
        _GIT_BASE_BRANCH,
        _GIT_DELETE_BRANCH,
    ])
    runner.run_tests(
        [Executable(str(exe_a), "", 1),
         Executable(str(exe_b), "", 1)])

    logging.critical("split request using timeouts")
    exe_a = tmp_path / "a.exe"
    exe_a.write_bytes(b"a")
    exe_b = tmp_path / "b.exe"
    exe_b.write_bytes(b"b")
    assert not commands
    commands.extend([
        _GIT_NEW_BRANCH,
        _strip(exe_a),
        _strip(exe_b),
        _add([exe_a]),
        _commit(0),
        _GIT_PUSH_BRANCH,
        _fetch(0),
        _log(["x"]),
        _GIT_RESET_BRANCH,
        _add([exe_b]),
        _commit(1),
        _GIT_PUSH_BRANCH,
        _fetch(0),
        _log(["x"]),
        _GIT_RESET_BRANCH,
        _GIT_BASE_BRANCH,
        _GIT_DELETE_BRANCH,
    ])
    runner.run_tests(
        [Executable(str(exe_a), "", 1),
         Executable(str(exe_b), "", 20)])

    logging.critical("split request limit executable count")
    runner.item["request-policy"] = {
        "policy": "limit-executable-count",
        "max-executable-count": 1,
    }
    exe_a = tmp_path / "a.exe"
    exe_a.write_bytes(b"a")
    exe_b = tmp_path / "b.exe"
    exe_b.write_bytes(b"b")
    assert not commands
    commands.extend([
        _GIT_NEW_BRANCH,
        _strip(exe_a),
        _strip(exe_b),
        _add([exe_a]),
        _commit(0),
        _GIT_PUSH_BRANCH,
        _fetch(0),
        _log(["x"]),
        _GIT_RESET_BRANCH,
        _add([exe_b]),
        _commit(1),
        _GIT_PUSH_BRANCH,
        _fetch(0),
        _log(["x"]),
        _GIT_RESET_BRANCH,
        _GIT_BASE_BRANCH,
        _GIT_DELETE_BRANCH,
    ])
    runner.run_tests(
        [Executable(str(exe_a), "", 1),
         Executable(str(exe_b), "", 20)])
