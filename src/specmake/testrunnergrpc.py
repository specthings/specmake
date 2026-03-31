# SPDX-License-Identifier: BSD-2-Clause
""" This module provides a test runner using gRPC.  """

# Copyright (C) 2024, 2025 embedded brains GmbH & Co. KG
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
from pathlib import Path
import subprocess
import tempfile
import time
import grpc  # type: ignore

from specitems import is_enabled, Item, ItemGetValueContext

# pylint: disable=no-name-in-module
from spectestrunner import (GRPCDescribeTargetRequest, GRPCRunImageRequest,
                            GRPCServiceStub)  # type: ignore

from .pkgitems import PackageBuildDirector
from .testrunner import Executable, Report, TestRunner


def _now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _get_symbols(exe_path: str, nm_path: str) -> dict[str, list[int]]:
    """ Return the symbols of the executable using the nm tool. """
    result = subprocess.run([nm_path, exe_path],
                            check=True,
                            capture_output=True,
                            text=True)
    symbols: dict[str, list[int]] = {}
    for line in result.stdout.split("\n"):
        try:
            address, _, name = line.split(None, 2)
        except ValueError:
            pass
        else:
            try:
                symbols.setdefault(name, []).append(int(address, 16))
            except ValueError:
                pass
    return symbols


class GRPCTestRunner(TestRunner):
    """ Runs the tests using an agent through gRPC.  """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self.mapper.add_get_value(f"{self.item.type}:/target-name",
                                  self._get_target_name)

    def _get_optional_value(self, key: str) -> str:
        for optional_value in self[key]:
            if is_enabled(self.enabled_set, optional_value["enabled-by"]):
                return optional_value["value"]
        raise ValueError(f"{self.uid}: there is no value for attribute {key} "
                         f"and enabled set {sorted(self.enabled_set)}")

    def _get_target_name(self, _ctx: ItemGetValueContext) -> str:
        return self._get_optional_value("target")

    def describe(self) -> str:
        server_address = self._get_optional_value("server-address")
        target_id = self._get_optional_value("target")
        with grpc.insecure_channel(server_address) as channel:
            stub = GRPCServiceStub(channel)
            try:
                response = stub.request_describe_target(
                    GRPCDescribeTargetRequest(target_id=target_id))
                logging.debug("%s: received target description for: %s",
                              self.uid, target_id)
            except grpc.RpcError as err:
                return (
                    f"Requesting the target description of ``{target_id}`` "
                    f"from the test server at {server_address} "
                    f"failed: {err}.")
            return response.description

    def _get_executable_data(self, executable: Executable) -> bytes:
        original = Path(executable.path)
        strip = self["strip"]
        if strip is None:
            return original.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            stripped = Path(directory) / "stripped"
            subprocess.run(
                [self["strip"], "-g", "-o",
                 str(stripped),
                 str(original)],
                check=True)
            return stripped.read_bytes()

    # pylint: disable=too-many-locals
    def run_tests(self, executables: list[Executable]) -> list[Report]:
        reports: list[Report] = []
        target_id = self._get_optional_value("target")
        nm = self["nm"]
        reset = self._get_optional_value("reset")
        server_address = self._get_optional_value("server-address")
        with grpc.insecure_channel(server_address) as channel:
            stub = GRPCServiceStub(channel)
            for executable in executables:
                start_time = _now_utc()
                monotonic_begin = time.monotonic()
                logging.debug("%s: send request for: %s", self.uid,
                              executable.path)
                breakpoints = _get_symbols(executable.path, nm)[reset]
                report: Report = {
                    "command-line": [],
                    "executable": executable.path,
                    "executable-sha512": executable.digest,
                    "start-time": start_time
                }
                try:
                    response = stub.request_run_image(
                        GRPCRunImageRequest(
                            target_id=target_id,
                            breakpoints=breakpoints,
                            path=executable.path,
                            digest=executable.digest,
                            data=self._get_executable_data(executable),
                            execution_timeout_in_seconds=executable.timeout))
                    logging.debug("%s: received response for: %s", self.uid,
                                  executable.path)
                except grpc.RpcError as err:
                    report["output"] = []
                    report["error"] = str(err)
                else:
                    report["output"] = [
                        line.removesuffix("\r") for line in
                        response.output.decode("latin-1").split("\n")
                    ]
                    if response.status != "success":
                        report["error"] = response.status
                    report["load-duration-in-seconds"] = \
                        response.load_duration_in_seconds
                    report["execution-duration-in-seconds"] = \
                        response.execution_duration_in_seconds
                report["duration"] = time.monotonic() - monotonic_begin
                reports.append(report)
        return reports
