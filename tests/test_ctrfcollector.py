# SPDX-License-Identifier: BSD-2-Clause
""" Tests the collector of test results in the Common Test Report Format. """

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

from .ctrf import validate_ctrf_report
from .util import create_package


def test_ctrfcollector(caplog, tmpdir):
    tmp_dir = Path(tmpdir)
    package = create_package(caplog, tmp_dir, Path("spec-packagebuild"),
                             ["aggregate-test-results", "ctrf"])
    uid = "/pkg/deployment/ctrf"
    director = package.director
    director.build_package(only=[uid])

    files = list(director[uid].files())
    assert files == [
        f"{tmpdir}/pkg/ctrf/a-build-config-key.ctrf.json",
        f"{tmpdir}/pkg/ctrf/a-empty-key.ctrf.json",
    ]

    # The fixture has two build configurations with the config key
    # build-config-key, so their tests share one report file
    assert ("the build configuration build-config-key of target a shares the "
            "report file a-build-config-key.ctrf.json" in caplog.text)

    with open(files[0], "r", encoding="utf-8") as src:
        report = json.load(src)

    validate_ctrf_report(report)

    assert report["reportFormat"] == "CTRF"
    results = report["results"]
    assert results["tool"]["name"] == "specmake"
    assert results["environment"] == {
        "appName": "pkg",
        "buildName": "build-label"
    }

    summary = results["summary"]
    tests = results["tests"]
    assert summary["tests"] == len(tests)
    assert summary["tests"] > 0
    assert summary["tests"] == (summary["passed"] + summary["failed"] +
                                summary["skipped"])
    assert summary["stop"] >= summary["start"]

    # The specification UID of an aggregated result is available
    assert any(test.get("extra", {}).get("spec-uid", "") for test in tests)
