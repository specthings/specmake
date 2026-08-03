# SPDX-License-Identifier: BSD-2-Clause
""" Tests the Common Test Report Format conversion. """

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

import json
from pathlib import Path
import re

import pytest

import specmake.ctrf

from specmake.ctrf import (convert_test_log, ctrf_epoch_milliseconds,
                           ctrf_markdown_summary, ctrf_milliseconds,
                           get_ctrf_tool_version, make_ctrf_summary,
                           report_to_ctrf_tests)

_TEST_FILES = Path(__file__).parent / "test-files"


def _load(name):
    with open(_TEST_FILES / "pkg" / name, "r", encoding="utf-8") as src:
        return json.load(src)


def _by_name(tests):
    return {test["name"]: test for test in tests}


def test_milliseconds():
    assert ctrf_milliseconds(1.5) == 1500
    assert ctrf_milliseconds(0.000121) == 0

    # A test which reported no duration has the unreported marker
    assert ctrf_milliseconds("?") == 0

    # Any other value is invalid and does not silently become a zero
    with pytest.raises(ValueError):
        ctrf_milliseconds("nonsense")


def test_epoch_milliseconds():
    assert ctrf_epoch_milliseconds("1970-01-01T00:00:00.000000") == 0
    assert ctrf_epoch_milliseconds("1970-01-01T00:00:01.500000") == 1500
    assert ctrf_epoch_milliseconds("1970-01-01T00:00:01.500000+00:00") == 1500

    # A report of an executable which did not run has no start time
    assert ctrf_epoch_milliseconds("") == 0

    # Any other value is invalid and does not silently become the epoch
    with pytest.raises(ValueError):
        ctrf_epoch_milliseconds("not a time stamp")


def test_did_not_run():
    tests = report_to_ctrf_tests({
        "executable": "/a/b/did-not-run.exe",
        "command-line": "",
        "output": ["This executable did not run."],
        "info": {}
    })
    assert tests == [{
        "name": "did-not-run.exe",
        "status": "skipped",
        "duration": 0,
        "filePath": "did-not-run.exe",
        "message": "the executable did not run",
        "extra": {
            "executable": "/a/b/did-not-run.exe"
        }
    }]


def test_runner_error():
    tests = report_to_ctrf_tests({
        "executable": "/a/b/timeout.exe",
        "command-line": ["sis", "timeout.exe"],
        "error": "timeout",
        "duration": 2.0,
        "start-time": "1970-01-01T00:00:00.000000",
        "info": {}
    })
    assert len(tests) == 1
    assert tests[0]["status"] == "failed"
    assert tests[0]["message"] == "timeout"
    assert tests[0]["duration"] == 2000
    assert tests[0]["start"] == 0
    assert tests[0]["stop"] == 2000


def test_no_end_of_test():
    tests = report_to_ctrf_tests({
        "executable": "/a/b/crash.exe",
        "command-line": ["sis", "crash.exe"],
        "duration": 1.0,
        "start-time": "1970-01-01T00:00:00.000000",
        "info": {
            "line-begin-of-test": 9,
            "name": "CRASH"
        }
    })
    assert len(tests) == 1
    assert tests[0]["status"] == "failed"
    assert tests[0]["message"] == "no end of test message"
    assert tests[0]["suite"] == ["CRASH"]


def test_no_begin_of_test():
    tests = report_to_ctrf_tests({
        "executable": "/a/b/silent.exe",
        "command-line": ["sis", "silent.exe"],
        "duration": 1.0,
        "info": {}
    })
    assert len(tests) == 1
    assert tests[0]["status"] == "failed"
    assert tests[0]["message"] == "no begin of test message"
    assert "suite" not in tests[0]


def test_plain_program():
    tests = report_to_ctrf_tests({
        "executable": "/a/b/hello.exe",
        "command-line": ["sis", "hello.exe"],
        "duration": 0.013939452997874469,
        "start-time": "1970-01-01T00:00:10.000000",
        "info": {
            "line-begin-of-test": 9,
            "line-end-of-test": 16,
            "name": "HELLO WORLD"
        }
    })
    assert tests == [{
        "name": "hello.exe",
        "status": "passed",
        "duration": 14,
        "filePath": "hello.exe",
        "start": 10000,
        "stop": 10014,
        "suite": ["HELLO WORLD"],
        "extra": {
            "executable": "/a/b/hello.exe"
        }
    }]


def test_retries():
    tests = report_to_ctrf_tests({
        "executable":
        "/a/b/flaky.exe",
        "command-line": ["sis", "flaky.exe"],
        "duration":
        1.0,
        "failed-attempts": [{
            "error": "timeout"
        }, {
            "error": "timeout"
        }],
        "info": {
            "line-begin-of-test": 9,
            "line-end-of-test": 16,
            "name": "FLAKY"
        }
    })
    assert tests[0]["retries"] == 2
    assert tests[0]["flaky"] is True


def test_the_summary_counts_the_flaky_tests():
    tests = [{
        "name": "a",
        "status": "passed",
        "duration": 0,
        "suite": ["S"],
        "flaky": True
    }, {
        "name": "b",
        "status": "passed",
        "duration": 0,
        "suite": ["S"]
    }, {
        "name": "c",
        "status": "failed",
        "duration": 0
    }]
    summary = make_ctrf_summary(tests, 0, 0)
    assert summary["flaky"] == 1

    # The two tests of suite S count once, the test without a suite not at all
    assert summary["suites"] == 1


def test_a_trace_of_a_failed_executable():
    tests = report_to_ctrf_tests({
        "executable":
        "/a/b/crash.exe",
        "command-line": ["sis", "crash.exe"],
        "duration":
        1.0,
        "output": ["boot", "*** BEGIN OF TEST CRASH ***", "run", "crash"],
        "info": {
            "line-begin-of-test": 1,
            "name": "CRASH"
        }
    })
    assert tests[0]["trace"] == "*** BEGIN OF TEST CRASH ***\nrun\ncrash"


def test_a_trace_leaves_out_a_data_range():
    tests = report_to_ctrf_tests({
        "executable":
        "/a/b/crash.exe",
        "command-line": ["sis", "crash.exe"],
        "duration":
        1.0,
        "output": [
            "begin", "*** BEGIN OF RECORDS BASE64 ***", "AAAA", "BBBB",
            "*** END OF RECORDS BASE64 ***", "crash"
        ],
        "data-ranges": [(2, 3)],
        "info": {
            "line-begin-of-test": 0
        }
    })
    assert tests[0]["trace"] == ("begin\n*** BEGIN OF RECORDS BASE64 ***\n"
                                 "*** END OF RECORDS BASE64 ***\ncrash")


def test_a_long_trace_keeps_its_last_lines():
    tests = report_to_ctrf_tests({
        "executable":
        "/a/b/crash.exe",
        "command-line": ["sis", "crash.exe"],
        "duration":
        1.0,
        "output": [f"line {index}" for index in range(100)],
        "info": {
            "line-begin-of-test": 0
        }
    })
    lines = tests[0]["trace"].split("\n")
    assert lines[0] == "[...]"
    assert len(lines) == 41
    assert lines[-1] == "line 99"


def test_a_passed_test_has_no_trace():
    tests = report_to_ctrf_tests({
        "executable": "/a/b/hello.exe",
        "command-line": ["sis", "hello.exe"],
        "duration": 1.0,
        "output": ["a", "b"],
        "info": {
            "line-begin-of-test": 0,
            "line-end-of-test": 1
        }
    })
    assert "trace" not in tests[0]


def _suite_report(line_end_of_test):
    # The parser adds a test case only once it ended, so a test case always has
    # a line range
    report = {
        "executable": "/a/b/ts-fail.exe",
        "command-line": ["sis", "ts-fail.exe"],
        "duration": 1.0,
        "start-time": "1970-01-01T00:00:10.000000",
        "output": [f"line {index}" for index in range(41)],
        "info": {
            "line-begin-of-test": 9,
            "name": "TestsuitesFail"
        },
        "test-suite": {
            "name":
            "TestsuitesFail",
            "step-count":
            2,
            "failed-steps-count":
            1,
            "test-cases": [{
                "name": "CasePass",
                "line-begin": 10,
                "line-end": 12,
                "step-count": 1,
                "failed-steps-count": 0,
                "duration": 0.0001
            }, {
                "name": "CaseFail",
                "line-begin": 13,
                "line-end": 15,
                "step-count": 1,
                "failed-steps-count": 1,
                "duration": 0.0001
            }]
        }
    }
    if line_end_of_test:
        report["info"]["line-end-of-test"] = line_end_of_test
    return report


def test_a_failed_test_case_is_reported_once():
    # The test suite ran to its end, so the failed test case reports the
    # failure and there is no second test for the executable
    tests = report_to_ctrf_tests(_suite_report(40))
    assert [(test["name"], test["status"])
            for test in tests] == [("CasePass", "passed"),
                                   ("CaseFail", "failed")]

    # The trace of a test case is the output of its line range
    assert tests[1]["trace"] == "line 13\nline 14\nline 15"
    assert "trace" not in tests[0]


def test_an_incomplete_test_suite_reports_its_executable():
    # The test suite stopped in the middle, which no test case reports
    tests = report_to_ctrf_tests(_suite_report(0))
    assert [(test["name"], test["status"])
            for test in tests] == [("CasePass", "passed"),
                                   ("CaseFail", "failed"),
                                   ("ts-fail.exe", "failed")]
    assert tests[-1]["message"] == "no end of test message"


def test_failed_steps_outside_a_test_case_report_the_executable():
    # No test case failed, so the failed step of the test suite would be lost
    report = _suite_report(40)
    for test_case in report["test-suite"]["test-cases"]:
        test_case["failed-steps-count"] = 0
    tests = report_to_ctrf_tests(report)
    assert [(test["name"], test["status"])
            for test in tests] == [("CasePass", "passed"),
                                   ("CaseFail", "passed"),
                                   ("ts-fail.exe", "failed")]
    assert tests[-1]["message"] == ("1 of 2 test steps failed outside a "
                                    "test case")


def test_an_incomplete_test_suite_report_reports_the_executable():
    # The program printed the end of test message, but the test suite never
    # reported its step counts.  Every test case is clean, so only a test for
    # the executable can report the anomaly.  smpmulticast01.exe and
    # ttest01.exe of the gr740 test logs are such reports.
    report = _suite_report(40)
    report["test-suite"]["failed-steps-count"] = "?"
    report["test-suite"]["step-count"] = "?"
    for test_case in report["test-suite"]["test-cases"]:
        test_case["failed-steps-count"] = 0
    tests = report_to_ctrf_tests(report)
    assert tests[-1]["name"] == "ts-fail.exe"
    assert tests[-1]["status"] == "failed"
    assert tests[-1]["message"] == "the test steps are incomplete"


def test_only_the_unaccounted_failed_steps_report_the_executable():
    # One step failed in CaseFail and one outside of any test case.  The test
    # case reports its own step, the executable reports the other one.
    report = _suite_report(40)
    report["test-suite"]["failed-steps-count"] = 2
    tests = report_to_ctrf_tests(report)
    assert [(test["name"], test["status"])
            for test in tests] == [("CasePass", "passed"),
                                   ("CaseFail", "failed"),
                                   ("ts-fail.exe", "failed")]
    assert tests[-1]["message"] == ("1 of 2 test steps failed outside a "
                                    "test case")


def test_sample_test_log():
    test_log = _load("test-log-sample.json")
    report = convert_test_log(test_log, "1.2.3", {
        "appName": "a",
        "buildName": ""
    })
    assert report["reportFormat"] == "CTRF"

    # The specification version is the version of the report format
    assert report["specVersion"] == "1.0.0"
    results = report["results"]
    assert results["tool"] == {"name": "specmake", "version": "1.2.3"}

    # An empty environment value is dropped
    assert results["environment"] == {"appName": "a"}

    summary = results["summary"]
    assert summary["tests"] == len(results["tests"])
    assert summary["tests"] == (summary["passed"] + summary["failed"] +
                                summary["skipped"])
    assert summary["pending"] == 0
    assert summary["other"] == 0
    assert summary["flaky"] == 0

    # Every distinct suite of the tests counts once
    assert summary["suites"] == len(
        {tuple(test.get("suite", []))
         for test in results["tests"]} - {()})

    # A run duration over reused reports would not be a duration
    assert "duration" not in summary

    tests = _by_name(results["tests"])

    # A test case of a test suite
    case = tests["RtemsValTestCaseNoSpec"]
    assert case["status"] == "passed"
    assert case["suite"] in (["TestsuitesTestSuiteFail"],
                             ["TestsuitesTestSuiteNoSpec"])
    assert case["extra"]["failed-steps-count"] == 0

    # A test case which did not report its end
    case = tests["RtemsValTestCaseFail"]
    assert case["status"] == "failed"
    assert case["message"] == "the test steps are incomplete"

    # A test suite which stopped in the middle also yields an executable test
    assert tests["ts-fail.exe"]["status"] == "failed"

    # A plain test program
    assert tests["hello.exe"]["status"] == "passed"


def test_summary_widens_to_the_tests():
    # The test log reused the report of a previous run, so the report is older
    # than the test log
    test_log = {
        "start-time":
        "1970-01-02T00:00:00.000000",
        "end-time":
        "1970-01-02T00:00:01.000000",
        "reports": [{
            "executable": "/a/b/old.exe",
            "command-line": ["sis", "old.exe"],
            "duration": 1.0,
            "start-time": "1970-01-01T00:00:10.000000",
            "info": {
                "line-begin-of-test": 9,
                "line-end-of-test": 16,
                "name": "OLD"
            }
        }]
    }
    summary = convert_test_log(test_log, "1.2.3")["results"]["summary"]
    assert summary["start"] == 10000
    assert summary["stop"] == 86401000


def test_empty_test_log():
    report = convert_test_log(_load("test-log-empty.json"), "1.2.3")
    assert report["results"]["tests"] == []
    assert report["results"]["summary"]["tests"] == 0
    assert "environment" not in report["results"]


def test_test_case_start_accumulates():
    report = convert_test_log(_load("test-log-perf.json"), "1.2.3")
    tests = [test for test in report["results"]["tests"] if "start" in test]
    assert tests
    for test in tests:
        assert test["stop"] == test["start"] + test["duration"]


_SEPARATOR = re.compile(r"(?<!\\)\|")


def _rows(text):
    """
    Get the rows of the tables of the CommonMark text.

    A cell is padded to the width of its column, so strip the padding.  Leave
    out the separator row of the header.
    """
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in _SEPARATOR.split(line.strip("|"))]
        if not all(set(cell) == {"-"} for cell in cells):
            rows.append(cells)
    return rows


def test_markdown_summary_without_failures():
    report = convert_test_log(_load("test-log-empty.json"), "1.2.3")
    text = ctrf_markdown_summary(report)
    assert "# Test results" in text
    assert _rows(text) == [["Tests", "Passed", "Failed", "Skipped"],
                           ["0", "0", "0", "0"]]
    assert "## Failures" not in text


def test_markdown_summary_limits_the_failures():
    tests = [{
        "name": f"case-{index}",
        "status": "failed",
        "duration": 0,
        "message": "a | b"
    } for index in range(5)]
    text = ctrf_markdown_summary(
        {
            "results": {
                "summary": make_ctrf_summary(tests, 0, 0),
                "tests": tests
            }
        },
        max_failures=2)

    # A cell of a table escapes a cell separator
    assert _rows(text) == [["Tests", "Passed", "Failed", "Skipped"],
                           ["5", "0", "5", "0"], ["Test", "Suite", "Reason"],
                           ["case-0", "", "a \\| b"],
                           ["case-1", "", "a \\| b"]]
    assert "3 more failed tests are not listed." in text


def test_markdown_summary_with_failures():
    report = convert_test_log(_load("test-log-sample.json"), "1.2.3")
    text = ctrf_markdown_summary(report)
    assert "## Failures" in text
    assert [
        "RtemsValTestCaseFail", "TestsuitesTestSuiteFail",
        "the test steps are incomplete"
    ] in _rows(text)


def test_get_tool_version():
    assert get_ctrf_tool_version() != ""


def test_get_tool_version_of_an_uninstalled_package(monkeypatch):

    def _version(_name):
        raise specmake.ctrf.PackageNotFoundError()

    monkeypatch.setattr(specmake.ctrf, "metadata_version", _version)
    assert get_ctrf_tool_version() == "unknown"
