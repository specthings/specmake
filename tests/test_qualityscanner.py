# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the qualityscanner module. """

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

from .util import create_package, get_and_clear_log


def _summary(run: dict, result: dict) -> tuple:
    location = result["locations"][0]
    artifact_location = location["physicalLocation"]["artifactLocation"]
    artifact = run["artifacts"][artifact_location["index"]]
    assert artifact["location"]["uri"] == artifact_location["uri"]
    justifications = [
        entry["justification"] for entry in result.get("suppressions", [])
    ]
    if artifact["properties"]["kind"] == "item":
        properties = location["properties"]
        assert location["logicalLocations"] == [{
            "fullyQualifiedName":
            f"{artifact['properties']['uid']}:{properties['attribute']}",
            "kind": "member"
        }]
        return (artifact["properties"]["uid"], properties["attribute"],
                result["ruleId"], properties["line-in-value"],
                properties["column-in-value"], properties["text"],
                justifications)
    region = location["physicalLocation"]["region"]
    assert region["endColumn"] == region["startColumn"] + 3
    return (artifact["properties"]["uid"], artifact["properties"]["path"],
            result["ruleId"], region["startLine"], region["startColumn"],
            region["snippet"]["text"], justifications)


def test_qualityscanner(caplog, tmpdir):
    tmp_dir = Path(tmpdir)
    package = create_package(caplog, tmp_dir, Path("spec-packagebuild"),
                             ["quality-scanner"])
    director = package.director
    director.build_package()
    log = get_and_clear_log(caplog)
    assert ("WARNING /pkg/deployment/quality-scanner: suppression without "
            "occurrence: uid '/glossary/tbd', attribute '/text', path "
            "'None', line None") in log

    scanner = director["/pkg/deployment/quality-scanner"]
    sarif_file = Path(scanner.file)
    assert sarif_file.name == "tbd-tbc-in-documentation-sources.sarif"
    with open(sarif_file, "r", encoding="utf-8") as src:
        sarif = json.load(src)
    assert sarif["version"] == "2.1.0"
    assert len(sarif["runs"]) == 1
    run = sarif["runs"][0]
    assert run["columnKind"] == "unicodeCodePoints"
    driver = run["tool"]["driver"]
    assert driver["name"] == "QualityScanner"
    assert [rule["id"] for rule in driver["rules"]] == ["TBD", "TBC"]

    properties = [artifact["properties"] for artifact in run["artifacts"]]
    documents = [entry for entry in properties if entry["kind"] == "document"]
    assert documents == [{
        "kind": "document",
        "path": "source/chapter.md",
        "uid": "/pkg/source/quality-scanner-document"
    }, {
        "kind": "document",
        "path": "source/chapter.rst",
        "uid": "/pkg/source/quality-scanner-document"
    }]
    item_uids = [
        entry["uid"] for entry in properties if entry["kind"] == "item"
    ]
    assert "/glossary/tbd" in item_uids
    assert "/pkg/deployment/quality-scanner" not in item_uids
    assert len(item_uids) == len(set(item_uids))

    for result in run["results"]:
        assert result["level"] == "note"
        assert result["message"]["text"] == f"{result['ruleId']} found"
        assert driver["rules"][result["ruleIndex"]]["id"] == result["ruleId"]
    assert [_summary(run, result) for result in run["results"]] == [
        ("/glossary/tbd", "/term", "TBD", 1, 1, "TBD",
         ["The glossary defines the term."]),
        ("/pkg/source/quality-scanner-document", "source/chapter.rst", "TBD",
         4, 14, "The value is TBD and TBC, but not TBDX, XTBC or tbd.", []),
        ("/pkg/source/quality-scanner-document", "source/chapter.rst", "TBC",
         4, 22, "The value is TBD and TBC, but not TBDX, XTBC or tbd.", []),
        ("/pkg/source/quality-scanner-document", "source/chapter.rst", "TBD",
         5, 7, "It is TBD.", ["The line explains the words."]),
    ]
