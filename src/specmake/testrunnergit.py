# SPDX-License-Identifier: BSD-2-Clause
""" This module provides a test runner using a Git bridge.  """

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

import logging
import time
from typing import Any

from spectestrunner import gitclient, gitproto, gitwire, image, steps

from .testrunner import RunnerExecutable, RunnerReport
from .testrunnergrpc import GRPCTestRunner, get_symbols
from .util import now_utc

_POLL_INTERVAL_IN_SECONDS = 10.0

_ERRORS = (gitclient.RequestGone, gitclient.Rejected, gitclient.WaitTimeout,
           gitproto.ProtocolError, gitwire.GitError)


def _get_report_output(result: dict[str, Any]) -> list[str]:
    output = result.get("output")
    if output is None:
        return []
    return [
        line.removesuffix("\r")
        for line in output.decode("latin-1").split("\n")
    ]


class GitTestRunner(GRPCTestRunner):
    """ Runs the tests using an agent through a Git bridge.  """

    def _client(self, repo: gitwire.Repository) -> gitclient.Client:
        return gitclient.Client(repo, self._get_optional_value("remote"),
                                gitproto.get_default_submitter(),
                                self["wait-timeout-in-seconds"],
                                _POLL_INTERVAL_IN_SECONDS)

    def describe(self) -> str:
        remote = self._get_optional_value("remote")
        target_id = self._get_optional_value("target")
        try:
            with gitclient.repository() as repo:
                description = self._client(repo).describe_target(target_id)
        except _ERRORS as err:
            return (f"Requesting the target description of ``{target_id}`` "
                    f"through the Git bridge at {remote} failed: {err}.")
        logging.debug("%s: received target description for: %s", self.uid,
                      target_id)
        return description

    def _run_executable(self, client: gitclient.Client, target_id: str,
                        executable: RunnerExecutable) -> RunnerReport:
        start_time = now_utc()
        monotonic_begin = time.monotonic()
        logging.debug("%s: send request for: %s", self.uid, executable.path)
        data = self._get_executable_data(executable)
        breakpoints = get_symbols(
            executable.path, self["nm"])[self._get_optional_value("reset")]
        step = {
            "kind": steps.STEP_IMAGE,
            "path": executable.path,
            "digest": image.get_digest(data),
            "breakpoints": breakpoints
        }
        report: RunnerReport = {
            "command-line": [],
            "executable": executable.path,
            "executable-sha512": executable.digest,
            "start-time": start_time
        }
        try:
            result = client.run_steps(target_id, executable.timeout, [step],
                                      {0: data})[0]
            logging.debug("%s: received response for: %s", self.uid,
                          executable.path)
        except _ERRORS as err:
            report["output"] = []
            report["error"] = str(err)
        else:
            report["output"] = _get_report_output(result)
            if result["status"] != "success":
                report["error"] = result["status"]
            for key in ("load", "execution"):
                value = result.get(f"{key}_duration_in_seconds")
                if value is not None:
                    report[f"{key}-duration-in-seconds"] = value
        report["duration"] = time.monotonic() - monotonic_begin
        return report

    def run_tests(self,
                  executables: list[RunnerExecutable]) -> list[RunnerReport]:
        target_id = self._get_optional_value("target")
        with gitclient.repository() as repo:
            client = self._client(repo)
            return [
                self._run_executable(client, target_id, executable)
                for executable in executables
            ]
