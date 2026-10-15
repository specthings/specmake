# SPDX-License-Identifier: BSD-2-Clause
""" Scans items and documents for TBD and TBC. """

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

import importlib.metadata
import logging
import os
from pathlib import Path
import re
from typing import Any, Iterator, Optional

from specitems import Item

from .directorystate import DirectoryState

_SCHEMA = ("https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/"
           "schemas/sarif-schema-2.1.0.json")

_RULES = ({
    "id": "TBD",
    "shortDescription": {
        "text": "To be defined"
    }
}, {
    "id": "TBC",
    "shortDescription": {
        "text": "To be confirmed"
    }
})

_RULE_INDEX = dict((rule["id"], index) for index, rule in enumerate(_RULES))

_WORD = re.compile(r"\b(TBD|TBC)\b")

_DOCUMENT_SUFFIXES = (".md", ".rst")

# A suppression key is the UID of the item or document input, the attribute
# path for an item, the file path relative to the document input, and the line
# number in the document file.
_Key = tuple[str, Optional[str], Optional[str], Optional[int]]


def _key_order(key: _Key) -> tuple[str, str, str, int]:
    return (key[0], key[1] or "", key[2] or "", key[3] or 0)


def _attribute_values(value: Any, path: str) -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key in sorted(value):
            yield from _attribute_values(value[key], f"{path}/{key}")
    elif isinstance(value, list):
        for index, element in enumerate(value):
            yield from _attribute_values(element, f"{path}[{index}]")


class _Results:

    def __init__(self, suppressions: dict[_Key, str]) -> None:
        self.suppressions = suppressions
        self.used: set[_Key] = set()
        self.artifacts: list[dict[str, Any]] = []
        self.results: list[dict[str, Any]] = []

    def add_artifact(self, path: str, properties: dict[str, str]) -> int:
        """ Add the artifact and return its index. """
        index = len(self.artifacts)
        self.artifacts.append({
            "location": {
                "uri": Path(path).absolute().as_uri()
            },
            "properties": properties
        })
        return index

    def add(self, word: str, location: dict[str, Any], key: _Key) -> None:
        """ Add the result of an occurrence at the location. """
        result: dict[str, Any] = {
            "level": "note",
            "locations": [location],
            "message": {
                "text": f"{word} found"
            },
            "ruleId": word,
            "ruleIndex": _RULE_INDEX[word]
        }
        justification = self.suppressions.get(key, None)
        if justification is not None:
            self.used.add(key)
            result["suppressions"] = [{
                "justification": justification,
                "kind": "external"
            }]
        self.results.append(result)

    def scan_item(self, item: Item) -> None:
        """ Scan the string values of the item. """
        index = self.add_artifact(item.file, {"kind": "item", "uid": item.uid})
        artifact = self.artifacts[index]["location"]
        for attribute, value in _attribute_values(item.data, ""):
            for line_number, line in enumerate(value.split("\n"), start=1):
                for match in _WORD.finditer(line):
                    self.add(
                        match.group(1), {
                            "logicalLocations": [{
                                "fullyQualifiedName":
                                f"{item.uid}:{attribute}",
                                "kind": "member"
                            }],
                            "physicalLocation": {
                                "artifactLocation": {
                                    "index": index,
                                    "uri": artifact["uri"]
                                }
                            },
                            "properties": {
                                "attribute": attribute,
                                "column-in-value": match.start() + 1,
                                "line-in-value": line_number,
                                "text": line
                            }
                        }, (item.uid, attribute, None, None))

    def scan_document_file(self, uid: str, path: str,
                           relative_path: str) -> None:
        """ Scan the lines of the document file. """
        index = self.add_artifact(path, {
            "kind": "document",
            "path": relative_path,
            "uid": uid
        })
        artifact = self.artifacts[index]["location"]
        with open(path, "r", encoding="utf-8", errors="replace") as src:
            for line_number, line in enumerate(src, start=1):
                text = line.rstrip("\n")
                for match in _WORD.finditer(text):
                    self.add(
                        match.group(1), {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "index": index,
                                    "uri": artifact["uri"]
                                },
                                "region": {
                                    "endColumn": match.end() + 1,
                                    "snippet": {
                                        "text": text
                                    },
                                    "startColumn": match.start() + 1,
                                    "startLine": line_number
                                }
                            }
                        }, (uid, None, relative_path, line_number))


class QualityScanner(DirectoryState):
    """ Scans items and documents for TBD and TBC. """

    def run(self) -> None:
        results = _Results(
            dict(((entry["uid"], entry["attribute"], entry["path"],
                   entry["line"]), entry["justification"])
                 for entry in self["suppressions"]))
        for item in sorted(self.item.cache.values()):
            if item.uid != self.uid:
                results.scan_item(item)
        for _, document in self.input_links("document"):
            assert isinstance(document, DirectoryState)
            for path in document.files():
                if path.endswith(_DOCUMENT_SUFFIXES):
                    results.scan_document_file(
                        document.uid, path,
                        os.path.relpath(path, document.directory))
        for key in sorted(set(results.suppressions) - results.used,
                          key=_key_order):
            logging.warning(
                "%s: suppression without occurrence: uid '%s', attribute "
                "'%s', path '%s', line %s", self.uid, key[0], key[1], key[2],
                key[3])
        self.json_dump({
            "$schema":
            _SCHEMA,
            "version":
            "2.1.0",
            "runs": [{
                "artifacts": results.artifacts,
                "columnKind": "unicodeCodePoints",
                "results": results.results,
                "tool": {
                    "driver": {
                        "name": "QualityScanner",
                        "rules": list(_RULES),
                        "semanticVersion":
                        importlib.metadata.version("specmake")
                    }
                }
            }]
        })
        self.description.add(f"""Scan the items and the documents for TBD and
TBC and produce the SARIF file {self.description.path(self.file)}""")
