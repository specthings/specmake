# SPDX-License-Identifier: BSD-2-Clause
""" Runs test executables in subprocesses and retries invalid test runs. """

# Copyright (C) 2022, 2026 embedded brains GmbH & Co. KG
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
import math
import multiprocessing
from pathlib import Path
import queue
import re
import subprocess
from subprocess import run as subprocess_run
import threading
import time
from typing import Any, Callable, NamedTuple, Optional

from specitems import is_enabled

from .testoutputparser import augment_report
from .util import now_utc

RunnerReport = dict[str, Any]


class RunnerExecutable(NamedTuple):
    """ Represents a test executable. """
    path: str
    digest: str
    timeout: float


class _Job:
    # pylint: disable=too-few-public-methods
    def __init__(self, executable: RunnerExecutable, command: list[str]):
        self.report: RunnerReport = {
            "executable": executable.path,
            "executable-sha512": executable.digest,
            "command-line": command
        }
        self.timeout = executable.timeout


def _worker(work_queue: queue.Queue, discard_patterns: list, uid: str) -> None:
    while True:
        try:
            job = work_queue.get_nowait()
        except queue.Empty:
            return
        logging.info("%s: run: '%s'", uid,
                     "' '".join(job.report["command-line"]))
        job.report["start-time"] = now_utc()
        begin = time.monotonic()
        try:
            process = subprocess_run(job.report["command-line"],
                                     check=False,
                                     stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE,
                                     timeout=job.timeout)
            stdout = process.stdout.decode("latin-1")
        except subprocess.TimeoutExpired as timeout:
            job.report["error"] = "timeout"
            if timeout.stdout is not None:
                stdout = timeout.stdout.decode("latin-1")
            else:
                stdout = ""
        except Exception as err:  # pylint: disable=broad-exception-caught
            job.report["error"] = str(err)
            stdout = ""
        for pattern in discard_patterns:
            if is_enabled([Path(job.report["executable"]).name],
                          pattern["enabled-by"]) and re.search(
                              pattern["pattern"], stdout, re.DOTALL):
                job.report["error"] = ("discarded due to "
                                       f"match with: {pattern['pattern']}")
        output = stdout.rstrip().replace("\r\n", "\n").split("\n")
        job.report["output"] = output
        job.report["duration"] = time.monotonic() - begin
        logging.debug("%s: done: %s", uid, job.report["executable"])
        work_queue.task_done()


def run_subprocess_tests(executables: list[RunnerExecutable],
                         get_command: Callable[[RunnerExecutable], list[str]],
                         discard_patterns: list,
                         max_process_count: int,
                         uid: str = "run-tests") -> list[RunnerReport]:
    """
    Run the test executables in subprocesses and return the reports.

    The command of an executable is obtained by get_command().  A report of an
    executable which matches a discard pattern gets an error attribute.  The
    worker thread count is the processor count divided by the process count
    used by one test run.
    """
    work_queue: queue.Queue[_Job] = queue.Queue()
    jobs: list[_Job] = []
    for executable in executables:
        job = _Job(executable, get_command(executable))
        jobs.append(job)
        work_queue.put(job)
    worker_count = int(
        math.ceil(multiprocessing.cpu_count() / float(max_process_count)))
    logging.info("%s: use %s worker threads", uid, worker_count)
    for _ in range(min(worker_count, len(executables))):
        threading.Thread(target=_worker,
                         args=(work_queue, discard_patterns, uid),
                         daemon=True).start()
    work_queue.join()
    return [job.report for job in jobs]


def _must_retry(report: Optional[RunnerReport], path: str, uid: str) -> bool:
    if report is None:
        logging.warning("%s: executable '%s': no report", uid, path)
        return True
    if "error" in report:
        logging.warning("%s: executable '%s': %s", uid, path, report["error"])
        return True
    if ("line-begin-of-test" in report["info"]
            and "line-end-of-test" not in report["info"]):
        logging.warning("%s: executable '%s': missing end of test line", uid,
                        path)
        return True
    if report.get("gcov-info-hash",
                  "") != report.get("gcov-info-hash-calculated", ""):
        logging.warning("%s: executable '%s': gcov info is corrupt", uid, path)
        return True
    test_suite = report.get("test-suite", {})
    if test_suite.get("report-hash",
                      "") != test_suite.get("report-hash-calculated", ""):
        logging.warning("%s: executable '%s': test suite report is corrupt",
                        uid, path)
        return True
    return False


def run_tests_with_retries(executables: list[RunnerExecutable],
                           run_tests: Callable[[list[RunnerExecutable]],
                                               list[RunnerReport]],
                           max_run_count: int,
                           uid: str = "run-tests") -> list[RunnerReport]:
    """
    Run the test executables and retry those which produced no valid report.

    A report of a retried executable gets a failed-attempts attribute which
    contains the reports of the previous attempts.
    """
    reports_by_path: dict[str, RunnerReport] = {}
    while executables and max_run_count:
        for new_report in run_tests(executables):
            augment_report(new_report, new_report["output"])
            previous_report = reports_by_path.get(new_report["executable"])
            if previous_report is not None:
                new_report["failed-attempts"] = previous_report.pop(
                    "failed-attempts", []) + [previous_report]
            reports_by_path[new_report["executable"]] = new_report
        executables = [
            executable for executable in executables
            if _must_retry(reports_by_path.get(executable.path, None),
                           executable.path, uid)
        ]
        max_run_count -= 1
    return list(reports_by_path.values())
