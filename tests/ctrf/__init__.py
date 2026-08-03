# SPDX-License-Identifier: BSD-2-Clause
""" Provides support to validate reports of the Common Test Report Format. """

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

import functools
import json
from pathlib import Path

import jsonschema

# The schema of https://github.com/ctrf-io/ctrf, MIT licensed,
# Copyright (c) 2024 Matthew Poulton-White
_SCHEMA_FILE = Path(__file__).parent / "ctrf.schema.json"


@functools.lru_cache(maxsize=None)
def _load_schema():
    """ Load the schema of the Common Test Report Format. """
    with open(_SCHEMA_FILE, "r", encoding="utf-8") as src:
        return json.load(src)


def _validator(schema):
    return jsonschema.validators.validator_for(schema)(schema)


def validate_ctrf_report(report):
    """ Assert that the report satisfies the schema. """
    errors = sorted(_validator(_load_schema()).iter_errors(report), key=str)
    assert not errors, "\n".join(
        f"{list(error.absolute_path)}: {error.message}" for error in errors)


def validate_ctrf_property(name, value):
    """ Assert that the value satisfies the schema of the property. """
    schema = _load_schema()
    _validator(schema["properties"][name]).validate(value)
