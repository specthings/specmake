# SPDX-License-Identifier: BSD-2-Clause
""" Provides the findings of SARIF logs. """

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

from dataclasses import dataclass
import json
import os
from typing import Any, Iterable, Iterator
import urllib.parse

#: The identity of a finding: the tool, the rule, the path of the artifact,
#: the logical location and the message.
FindingKey = tuple[str, str, str, str | None, str]


@dataclass(frozen=True)
class Artifact:
    """
    This class represents the artifact of a finding.

    The path is the identity of the artifact.  The display is the name of the
    artifact in a report.  The item is the UID of an item artifact.  The
    document is the UID and the path of a document artifact.
    """

    path: str
    display: str
    item: str | None
    document: str | None


@dataclass(frozen=True)
class Position:
    """
    This class represents the position of a finding in its artifact.

    The location is the fully qualified name of the logical location, or the
    display of the artifact followed by the line or the name of the logical
    location.  The line is the start line of the region of the physical
    location, if the result has one.
    """

    location: str
    line: int | None = None


@dataclass(frozen=True)
class Finding:
    """
    This class represents one result of a SARIF log.

    The line of a finding is not part of its identity, since it moves when
    unrelated code moves.
    """

    tool: str
    rule: str
    artifact: Artifact
    logical_location: str | None
    message: str
    position: Position
    suppression: str | None

    @property
    def location(self) -> str:
        """ Is the location of the finding. """
        return self.position.location

    @property
    def line(self) -> int | None:
        """ Is the line of the finding. """
        return self.position.line

    @property
    def key(self) -> FindingKey:
        """ Is the identity of the finding. """
        return (self.tool, self.rule, self.artifact.path,
                self.logical_location, self.message)


def relative_path(uri: str, bases: list[str]) -> str:
    """
    Return the path of the URI relative to the first base directory which
    contains it, or the path itself.
    """
    if uri.startswith("file://"):
        uri = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(uri)
    for base in bases:
        if path.startswith(f"{base}/"):
            return os.path.relpath(path, base)
    return path


def _artifact(artifacts: list[dict[str, Any]], index: int,
              bases: list[str]) -> Artifact:
    artifact = artifacts[index]
    properties = artifact.get("properties", {})
    if "uid" in properties:
        uid = properties["uid"]
        if properties["kind"] == "document":
            document = f"{uid}: {properties['path']}"
            return Artifact(document, document, None, document)
        return Artifact(uid, uid, uid, None)
    uri = artifact["location"]["uri"]
    if "parentIndex" in artifact:
        parent = _artifact(artifacts, artifact["parentIndex"], bases)
        name = urllib.parse.unquote(uri)
        return Artifact(f"{parent.path}/{name}", f"{parent.display}({name})",
                        None, None)
    path = relative_path(uri, bases)
    return Artifact(path, path, None, None)


def _location_artifact(result: dict[str, Any], artifacts: list[dict[str, Any]],
                       bases: list[str]) -> tuple[Artifact, dict[str, Any]]:
    locations = result.get("locations") or [{}]
    physical = locations[0].get("physicalLocation", {})
    location = physical.get("artifactLocation", {})
    if "index" in location:
        return _artifact(artifacts, location["index"], bases), physical
    uri = location.get("uri")
    path = "-" if uri is None else relative_path(uri, bases)
    return Artifact(path, path, None, None), physical


def _finding(tool: str, result: dict[str, Any],
             artifacts: list[dict[str, Any]], bases: list[str]) -> Finding:
    artifact, physical = _location_artifact(result, artifacts, bases)
    logical_locations = (result.get("locations")
                         or [{}])[0].get("logicalLocations") or [{}]
    qualified = logical_locations[0].get("fullyQualifiedName")
    name = logical_locations[0].get("name")
    line = physical.get("region", {}).get("startLine")
    if qualified is not None:
        location = qualified
    elif line is not None:
        location = f"{artifact.display}:{line}"
    elif name is not None:
        location = f"{artifact.display} {name}"
    else:
        location = artifact.display
    suppressions = result.get("suppressions") or []
    suppression = suppressions[0].get("justification",
                                      "") if suppressions else None
    return Finding(tool, result["ruleId"], artifact,
                   qualified or name, result["message"]["text"],
                   Position(location, line), suppression)


def load(paths: Iterable[str], bases: list[str]) -> Iterator[Finding]:
    """
    Yield the findings of the SARIF files in the order of the files, the runs
    and the results.

    The path of an artifact with a uid property is the UID of the item, or the
    UID and the path of a document.  The path of a nested artifact is the path
    of its parent followed by its own URI.  A file URI is relative to the
    first base directory which contains it.

    Args:
        paths: The paths of the SARIF files.
        bases: The base directories of file URIs.
    """
    for path in paths:
        with open(path, "r", encoding="utf-8") as src:
            sarif = json.load(src)
        for run in sarif["runs"]:
            tool = run["tool"]["driver"]["name"]
            artifacts = run.get("artifacts", [])
            for result in run.get("results", []):
                yield _finding(tool, result, artifacts, bases)


def documents(paths: Iterable[str]) -> list[str]:
    """
    Return the sorted UIDs of the artifacts of the kind document of the SARIF
    files.
    """
    uids: set[str] = set()
    for path in paths:
        with open(path, "r", encoding="utf-8") as src:
            sarif = json.load(src)
        for run in sarif["runs"]:
            for artifact in run.get("artifacts", []):
                properties = artifact.get("properties", {})
                if properties.get("kind") == "document":
                    uids.add(properties["uid"])
    return sorted(uids)
