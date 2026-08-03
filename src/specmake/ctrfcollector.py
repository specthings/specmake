# SPDX-License-Identifier: BSD-2-Clause
""" Collects test results in the Common Test Report Format. """

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
import os
from typing import Any, Iterator, NamedTuple

from .ctrf import (ctrf_epoch_milliseconds, ctrf_milliseconds,
                   get_ctrf_tool_version, make_ctrf_report,
                   report_to_ctrf_tests)
from .directorystate import DirectoryState
from .testaggregator import TestAggregator
from .util import write_json

_Data = dict[str, Any]


class _Collected(NamedTuple):
    """ Represents the tests collected for one report file. """
    tests: list[_Data]
    start: int
    stop: int
    build_label: str


def _reports_of_config(config_data: _Data) -> Iterator[tuple[_Data, str]]:
    """ Yield the test report and specification UID of the configuration. """
    for uid, suite_data in sorted(config_data["test-suites"].items()):
        yield suite_data["report"], uid
    for uid, report in sorted(config_data["test-programs"].items()):
        yield report, uid
    for _, report in sorted(config_data["other-programs"].items()):
        yield report, ""


def _time_range(reports: list[_Data]) -> tuple[int, int]:
    """ Get the start and stop of the reports in milliseconds. """
    starts = [
        ctrf_epoch_milliseconds(report.get("start-time", ""))
        for report in reports
    ]
    starts = [start for start in starts if start]
    if not starts:
        return 0, 0
    stops = [
        ctrf_epoch_milliseconds(report.get("start-time", "")) +
        ctrf_milliseconds(report.get("duration", 0.0)) for report in reports
    ]
    return min(starts), max(stops)


class CTRFCollector(DirectoryState):
    """ Collects test results in the Common Test Report Format. """

    def _collect(self, config_data: _Data, target_key: str,
                 by_file: dict[str, _Collected]) -> None:
        """
        Collect the tests of the build configuration of the target.

        Build configurations which share a report file base share a report
        file.  Their tests accumulate, so that no test result is lost.
        """
        base = os.path.basename(config_data["report-file-base"])
        file_name = f"{base}.ctrf.json"
        tests: list[_Data] = []
        reports: list[_Data] = []
        for report, uid in _reports_of_config(config_data):
            tests.extend(report_to_ctrf_tests(report, uid))
            reports.append(report)
        start, stop = _time_range(reports)
        logging.info("%s: collect %s tests of target %s and configuration %s",
                     self.uid, len(tests), target_key,
                     config_data["config-key"])
        collected = by_file.get(file_name, None)
        if collected is None:
            by_file[file_name] = _Collected(tests, start, stop,
                                            config_data["build-label"])
            return
        logging.warning(
            "%s: the build configuration %s of target %s shares the report "
            "file %s", self.uid, config_data["config-key"], target_key,
            file_name)
        collected.tests.extend(tests)
        by_file[file_name] = collected._replace(
            start=min(collected.start, start) if start else collected.start,
            stop=max(collected.stop, stop))

    def run(self) -> None:
        environment = {
            "appName": self.substitute("${.:/component/package-directory}")
        }
        by_file: dict[str, _Collected] = {}
        for test_aggregator in self.inputs("test-aggregation"):
            assert isinstance(test_aggregator, TestAggregator)
            for target_data in test_aggregator.targets.values():
                for config_data in target_data["configs"]:
                    self._collect(config_data, target_data["key"], by_file)
        tool_version = get_ctrf_tool_version()
        self.set_files(sorted(by_file.keys()))
        for file_name, collected in by_file.items():
            write_json(
                os.path.join(self.directory, file_name),
                make_ctrf_report(
                    collected.tests, tool_version, collected.start,
                    collected.stop, {
                        **environment, "buildName": collected.build_label
                    }))
        self.description.add("""Collect the test results in the Common Test
Report Format.""")
