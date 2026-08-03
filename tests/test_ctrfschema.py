# SPDX-License-Identifier: BSD-2-Clause
""" Validates the produced reports against the CTRF JSON schema. """

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

import pytest

from specmake.ctrf import CTRF_SPEC_VERSION, convert_test_log

from .ctrf import validate_ctrf_property, validate_ctrf_report

_TESTS = Path(__file__).parent

_TEST_LOGS = sorted(path.name for path in (_TESTS / "test-files" /
                                           "pkg").glob("test-log-*.json"))

_ENVIRONMENTS = [
    None,
    {},
    {
        "appName": "app",
        "buildName": "build"
    },
    # An empty value is dropped, so it does not reach the report
    {
        "appName": "",
        "buildName": ""
    },
]


def test_the_specification_version_is_the_schema_version():
    # The schema requires the MAJOR.MINOR.PATCH form, so the version of this
    # package cannot be used
    validate_ctrf_property("specVersion", CTRF_SPEC_VERSION)


@pytest.mark.parametrize("name", _TEST_LOGS)
@pytest.mark.parametrize("environment", _ENVIRONMENTS)
def test_a_converted_test_log_is_valid(name, environment):
    with open(_TESTS / "test-files" / "pkg" / name, "r",
              encoding="utf-8") as src:
        test_log = json.load(src)
    validate_ctrf_report(convert_test_log(test_log, "1.5.16.dev1",
                                          environment))
