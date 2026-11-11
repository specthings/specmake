# SPDX-License-Identifier: BSD-2-Clause
""" Tests the agent test runner through a Git bridge. """

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

import dataclasses
import json
import logging
from pathlib import Path

import pytest
from spectestrunner import gitclient, gitwire, image, steps

import specmake
from specmake import AgentTestRunner
from specmake.runtests import RunnerExecutable

from .util import create_package


@dataclasses.dataclass
class _Result:
    stdout = """01234567 T bsp_reset
"""


def _subprocess_run(args, check=True, capture_output=False, text=False):
    if args[0].endswith("strip"):
        Path(args[3]).write_bytes(b"stripped")
    return _Result()


class _Client:

    counter = 0

    requests: list[tuple] = []

    events: list[str] = []

    pending: dict[str, tuple[str, int]] = {}

    def __init__(self, repo, remote, submitter, wait_timeout, poll_interval):
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-positional-arguments
        assert repo is not None
        assert submitter
        assert poll_interval > 0.0
        self.remote = remote
        self.wait_timeout = wait_timeout

    def describe_target(self, target):
        _Client.counter += 1
        if _Client.counter % 2 == 0:
            return f"{target} at {self.remote}"
        raise gitclient.WaitTimeout("no response")

    def submit_run_steps(self, target, timeout, request_steps, data):
        _Client.requests.append(
            (target, timeout, request_steps, data, self.wait_timeout))
        _Client.counter += 1
        request_id = f"r{_Client.counter}"
        _Client.events.append(f"submit {request_id}")
        _Client.pending[request_id] = (request_steps[0]["path"],
                                       _Client.counter % 4)
        return request_id

    def collect_run_steps(self, request_id):
        _Client.events.append(f"collect {request_id}")
        path, outcome = _Client.pending.pop(request_id)
        if outcome == 1:
            raise gitclient.Rejected("the reason")
        if outcome == 2:
            return [{
                "kind": steps.STEP_IMAGE,
                "path": path,
                "status": "unreached: UNAVAILABLE"
            }]
        status = "success" if outcome == 0 else "error"
        return [{
            "kind": steps.STEP_IMAGE,
            "path": path,
            "status": status,
            "output": b"line\r\nend",
            "load_duration_in_seconds": 1.0,
            "execution_duration_in_seconds": 2.0
        }]


def test_testrunnergit(caplog, tmp_path, monkeypatch):
    _Client.counter = 0
    _Client.requests = []
    _Client.events = []
    _Client.pending = {}
    monkeypatch.setattr(specmake.testrunneragent.subprocess, "run",
                        _subprocess_run)
    monkeypatch.setattr(specmake.testrunneragent.gitclient, "Client", _Client)
    package = create_package(caplog, tmp_path, Path("spec-packagebuild"),
                             ["test-runner-git"])
    test_logs_uid = "/pkg/test-logs/test-runner-git"
    director = package.director
    director.build_package(only=[test_logs_uid])

    runner = director["/pkg/test-runner/git"]
    assert isinstance(runner, AgentTestRunner)
    assert runner.substitute("${.:/target-name}") == "the/target"

    outstanding = 0
    for event in _Client.events:
        outstanding += 1 if event.startswith("submit") else -1
        assert 0 <= outstanding <= 2
    first, second, third = _Client.events[:3]
    assert first.startswith("submit")
    assert second.startswith("submit")
    assert third == first.replace("submit", "collect")

    target, timeout, request_steps, data, wait_timeout = _Client.requests[0]
    assert target == "the/target"
    assert timeout == 180.0
    assert wait_timeout == 60.0
    assert data == {0: b"stripped"}
    assert request_steps == [{
        "kind": steps.STEP_IMAGE,
        "path": request_steps[0]["path"],
        "digest": image.get_digest(b"stripped"),
        "breakpoints": [0x01234567]
    }]

    log = director[test_logs_uid]
    with open(log.file, "r", encoding="utf-8") as src:
        log_data = json.load(src)
    assert log_data["test-runner-description"] == (
        "Requesting the target description of ``the/target`` through the "
        "Git bridge at /iris.git failed: no response.")
    reports = {
        Path(report["executable"]).name: report
        for report in log_data["reports"]
    }
    report_a = reports["a.exe"]
    assert report_a["error"] == "error"
    assert report_a["output"] == ["line", "end"]
    assert report_a["load-duration-in-seconds"] == 1.0
    assert report_a["execution-duration-in-seconds"] == 2.0
    unreached, _, rejected = report_a["failed-attempts"]
    assert unreached["error"] == "unreached: UNAVAILABLE"
    assert unreached["output"] == []
    assert "load-duration-in-seconds" not in unreached
    assert rejected["error"] == "the reason"
    assert rejected["output"] == []
    report_b = reports["b.exe"]
    assert "error" not in report_b
    assert report_b["output"] == ["line", "end"]
    assert [attempt["error"] for attempt in report_b["failed-attempts"]
            ] == ["error", "error", "unreached: UNAVAILABLE"]

    assert runner.describe() == (
        "Requesting the target description of ``the/target`` through the "
        "Git bridge at /iris.git failed: no response.")
    assert runner.describe() == "the/target at /iris.git"


class _FailingClient(_Client):

    cleaned: list[str] = []

    def submit_run_steps(self, target, timeout, request_steps, data):
        if request_steps[0]["path"] in ("b.exe", "e.exe"):
            raise gitwire.GitError("push refused")
        return super().submit_run_steps(target, timeout, request_steps, data)

    def collect_run_steps(self, request_id):
        if _Client.pending[request_id][0] == "d.exe":
            raise RuntimeError("interrupted")
        return super().collect_run_steps(request_id)

    def cleanup(self, request_id):
        _FailingClient.cleaned.append(request_id)
        raise gitwire.GitError("delete refused")


def test_testrunnergit_failures(caplog, tmp_path, monkeypatch):
    _Client.counter = 0
    _Client.requests = []
    _Client.events = []
    _Client.pending = {}
    monkeypatch.setattr(specmake.testrunneragent.subprocess, "run",
                        _subprocess_run)
    monkeypatch.setattr(specmake.testrunneragent.gitclient, "Client",
                        _FailingClient)
    package = create_package(caplog, tmp_path, Path("spec-packagebuild"),
                             ["test-runner-git"])
    runner = package.director["/pkg/test-runner/git"]
    assert isinstance(runner, AgentTestRunner)

    # A failed submission yields the report of its executable
    reports = runner.run_tests([
        RunnerExecutable("a.exe", "0", 1.0),
        RunnerExecutable("b.exe", "0", 1.0),
        RunnerExecutable("c.exe", "0", 1.0)
    ])
    assert [report["executable"]
            for report in reports] == ["a.exe", "b.exe", "c.exe"]
    assert reports[1]["error"] == "push refused"
    assert reports[1]["output"] == []
    assert not _FailingClient.cleaned

    # An abort withdraws the requests which wait on the remote
    caplog.set_level(logging.WARNING)
    with pytest.raises(RuntimeError, match="interrupted"):
        runner.run_tests([
            RunnerExecutable("d.exe", "0", 1.0),
            RunnerExecutable("e.exe", "0", 1.0)
        ])
    assert _FailingClient.cleaned == ["r3"]
    assert "could not withdraw r3: delete refused" in caplog.text
