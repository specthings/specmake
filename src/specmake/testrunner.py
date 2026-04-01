# SPDX-License-Identifier: BSD-2-Clause
""" Run tests. """

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

import datetime
import json
import logging
import math
import multiprocessing
import os
import re
from pathlib import Path
import queue
import subprocess
from subprocess import run as subprocess_run
import tarfile
import time
import threading
from typing import Any, NamedTuple

from specitems import is_enabled, Item, ItemGetValueContext

from .directorystate import DirectoryState
from .pkgitems import BuildItem, PackageBuildDirector
from .testoutputparser import augment_report

Report = dict[str, Any]


def _now_utc() -> str:
    return datetime.datetime.utcnow().isoformat()


class Executable(NamedTuple):
    """ Represents a test executable. """
    path: str
    digest: str
    timeout: float


class TestLog(DirectoryState):
    """ Maintains a test log. """

    def get_reports_by_hash(self) -> tuple[dict[str, Report], str, str]:
        """
        Get the reports by executable hash and the test runner description.
        """
        reports_by_hash: dict[str, Report] = {}
        description = "There is no description available."
        runner_hash = ""
        try:
            with open(self.file, "r", encoding="utf-8") as src:
                data = json.load(src)
                description = data.get("test-runner-description", description)
                runner_hash = data.get("test-runner-hash", runner_hash)
                for report in data["reports"]:
                    digest = report["executable-sha512"]
                    assert digest not in reports_by_hash
                    assert isinstance(digest, str)
                    reports_by_hash[digest] = report
        except FileNotFoundError:
            pass
        return reports_by_hash, description, runner_hash


class TestRunner(BuildItem):
    """ Runs tests. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self._executable = "/dev/null"
        self._executables: list[Executable] = []
        self.mapper.add_get_value(f"{self.item.type}:/test-executable",
                                  self._get_test_executable)

    def _get_test_executable(self, _ctx: ItemGetValueContext) -> str:
        return self._executable

    def describe(self) -> str:
        """ Return a description of the test runner. """
        return "This test procedure cannot run tests."

    def get_runner_hash(self) -> str:
        """
        Get a hash of the test runner.

        The runner hash is stored in the test log.  If the current runner hash
        differs from the hash in the test log, the test reports are not reused
        and all tests are run again.
        """
        return self.digest()

    def run_tests(self, executables: list[Executable]) -> list[Report]:
        """
        Run the test executables and returns a list of test reports.
        """
        start_time = _now_utc()
        return [{
            "executable": executable.path,
            "executable-sha512": executable.digest,
            "command-line": "",
            "start-time": start_time,
            "output": ["This executable did not run."],
            "duration": 0.0
        } for executable in executables]

    def get_run_command(self, _executable: str) -> None | list[str]:
        """ Get the command to run an executable. """
        return None

    def _get_config_and_timeout_keys(self) -> tuple[str, str]:
        config = self.input("build-configuration")

        # Get timeout key for the enabled set
        for timeout_key in config["test-timeout-key"]:
            if is_enabled(self.enabled_set, timeout_key["enabled-by"]):
                return config["config-key"], timeout_key["key"]

        raise ValueError(
            f"{self.uid}: for enabled set {list(self.enabled_set)} "
            f"and build configuration {config.uid}, there is no timeout key "
            f"in {config['test-timeout-key']}")

    def _get_reports_and_executables(
            self, target: Item, previous_reports_by_hash: dict[str, Report],
            report_runner_hash: str,
            timeout_key: str) -> tuple[list[Report], list[Executable]]:
        # pylint: disable=too-many-locals
        timeouts = target.parent("test-timeouts")["timeouts"]
        source = self.input("source")
        assert isinstance(source, DirectoryState)
        reports: list[Report] = []
        executables: list[Executable] = []
        do_not_run = self["do-not-run"]
        default_timeout = self["default-timeout-in-seconds"]
        min_timeout = self["min-timeout-in-seconds"]
        timeout_scaler = self["timeout-scaler"]
        cannot_reuse_reports = self.get_runner_hash() != report_runner_hash
        if cannot_reuse_reports:
            logging.info(
                "%s: cannot reuse reports with "
                "runner hash %s and report hash %s", self.uid,
                self.get_runner_hash(), report_runner_hash)
        for path, digest in source.files_and_hashes():
            if not path.endswith(".exe") or path.endswith(".norun.exe"):
                continue
            assert digest
            name = Path(path).name

            # Use previous report if the executable hash did not change.  Reuse
            # also reports which contain an "error" attribute to avoid running
            # them in CI jobs.  Resolving failed tests is a manual activity.
            report = previous_reports_by_hash.get(digest, None)
            if report is None or cannot_reuse_reports:
                if name in do_not_run:
                    logging.info("%s: do not run: %s", self.uid, path)
                    report = TestRunner.run_tests(
                        self, [Executable(path, digest, 0.0)])[0]
                    augment_report(report, report["output"])
                    reports.append(report)
                else:
                    logging.debug("%s: run: %s", self.uid, path)
                    try:
                        timeout = max(timeouts[timeout_key][name])
                    except KeyError:
                        timeout = default_timeout
                    timeout = timeout_scaler * max(timeout, min_timeout)
                    executables.append(Executable(path, digest, timeout))
            else:
                logging.info("%s: use previous report for: %s", self.uid, path)
                report["executable"] = path
                reports.append(report)
        return reports, executables

    def run(self) -> None:
        start_time = _now_utc()
        begin = time.monotonic()
        log = self.output("log")
        assert isinstance(log, TestLog)
        target = self.item.parent("target")
        assert target.uid == self.input("target").uid
        config_key, timeout_key = self._get_config_and_timeout_keys()
        (reports_by_hash, description,
         report_runner_hash) = log.get_reports_by_hash()
        reports, executables = self._get_reports_and_executables(
            target, reports_by_hash, report_runner_hash, timeout_key)

        # Run the tests with changed executable hashes
        if executables:
            description = self.describe()
            reports.extend(self._run_tests(executables))

        # Save the reports
        os.makedirs(os.path.dirname(log.file), exist_ok=True)
        with open(log.file, "w", encoding="utf-8") as dst:
            data = {
                "build-configuration": config_key,
                "timeout-key": timeout_key,
                "duration": time.monotonic() - begin,
                "end-time": _now_utc(),
                "reports": sorted(reports, key=lambda x: x["executable"]),
                "start-time": start_time,
                "test-runner-description": description,
                "test-runner-hash": self.get_runner_hash(),
                "target": target.uid
            }
            json.dump(data, dst, sort_keys=True, indent=2)

        self.description.add(f"""Run tests and produce test result file
{self.description.path(log.file)}""")

    def _run_tests(self, executables: list[Executable]) -> list[Report]:
        max_run_count = self["max-retry-count-per-executable"] + 1
        reports_by_path: dict[str, Report] = {}
        while executables and max_run_count:
            self._executables = executables
            for new_report in self.run_tests(executables):
                augment_report(new_report, new_report["output"])
                reports_by_path[new_report["executable"]] = new_report
            next_executables: list[Executable] = []
            for executable in executables:
                report = reports_by_path.get(executable.path, None)
                if report is None:
                    next_executables.append(executable)
                    logging.warning("%s: executable '%s': no report", self.uid,
                                    executable.path)
                    continue
                if "error" in report:
                    next_executables.append(executable)
                    logging.warning("%s: executable '%s': %s", self.uid,
                                    executable.path, report["error"])
                    continue
                if report.get("gcov-info-hash",
                              "") != report.get("gcov-info-hash-calculated",
                                                ""):
                    next_executables.append(executable)
                    logging.warning(
                        "%s: executable '%s': gcov info is corrupt", self.uid,
                        executable.path)
                    continue
                test_suite = report.get("test-suite", {})
                if test_suite.get("report-hash", "") != test_suite.get(
                        "report-hash-calculated", ""):
                    next_executables.append(executable)
                    logging.warning(
                        "%s: executable '%s': test suite report is corrupt",
                        self.uid, executable.path)
                    continue
            executables = next_executables
            max_run_count -= 1
        return list(reports_by_path.values())


class GRMONManualTestRunner(TestRunner):
    """ Provides scripts to run the tests using GRMON. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self.mapper.add_get_value(f"{self.item.type}:/test-executables-grmon",
                                  self._get_test_executables_grmon)

    def _get_test_executables_grmon(self, _ctx: ItemGetValueContext) -> str:
        return " \\\n".join(
            os.path.basename(executable.path)
            for executable in self._executables)

    def describe(self) -> str:
        return """This test procedure creates an archive with test programs, a
GRMON test script, and a shell script to run the tests manually."""

    def run_tests(self, executables: list[Executable]) -> list[Report]:
        base = self["script-base-path"]
        dir_name = os.path.basename(base)
        grmon_name = f"{base}.grmon"
        shell_name = f"{base}.sh"
        tar_name = f"{base}.tar.xz"
        os.makedirs(os.path.dirname(base), exist_ok=True)
        with tarfile.open(tar_name, "w:xz") as tar_file:
            with open(grmon_name, "w", encoding="utf-8") as grmon_file:
                grmon_file.write(self["grmon-script"])
            tar_file.add(grmon_name, os.path.join(dir_name, "run.grmon"))
            with open(shell_name, "w", encoding="utf-8") as shell_file:
                shell_file.write(self["shell-script"])
            tar_file.add(shell_name, os.path.join(dir_name, "run.sh"))
            for executable in executables:
                tar_file.add(
                    executable.path,
                    os.path.join(dir_name, os.path.basename(executable.path)))
        raise IOError(f"Run the tests provided by {tar_name}")


class _Job:
    # pylint: disable=too-few-public-methods
    def __init__(self, executable: Executable, command: list[str]):
        self.report: Report = {
            "executable": executable.path,
            "executable-sha512": executable.digest,
            "command-line": command
        }
        self.timeout = executable.timeout


def _worker(work_queue: queue.Queue, item: BuildItem):
    discard_patterns = item.item["discard-patterns"]
    while True:
        try:
            job = work_queue.get_nowait()
        except queue.Empty:
            return
        logging.info("%s: run: '%s'", item.uid,
                     "' '".join(job.report["command-line"]))
        job.report["start-time"] = _now_utc()
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
        logging.debug("%s: done: %s", item.uid, job.report["executable"])
        work_queue.task_done()


class SubprocessTestRunner(TestRunner):
    """ Runs tests in subprocesses. """

    def describe(self) -> str:
        self._executable = "${test-program}"
        command = " ".join(f"'{part}'" if " " in part else part
                           for part in self["command"])
        return f"""For each test program (indicated by ``${{test-program}}``),
this test procedure runs the following command as a subprocess on the machine
building the package and captures the output:

.. code-block:: none

    {command}"""

    def run_tests(self, executables: list[Executable]) -> list[Report]:
        work_queue: queue.Queue[_Job] = queue.Queue()
        jobs: list[_Job] = []
        for executable in executables:
            self._executable = executable.path
            job = _Job(executable, self["command"])
            jobs.append(job)
            work_queue.put(job)
        worker_count = int(
            math.ceil(multiprocessing.cpu_count() /
                      float(self["max-process-count"])))
        logging.info("%s: use %s worker threads", self.uid, worker_count)
        for _ in range(min(worker_count, len(executables))):
            threading.Thread(target=_worker,
                             args=(work_queue, self),
                             daemon=True).start()
        work_queue.join()
        return [job.report for job in jobs]

    def get_run_command(self, executable: str) -> None | list[str]:
        self._executable = executable
        return self["command"]
