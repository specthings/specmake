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

import base64
from dataclasses import dataclass
import hashlib
import json
import os
from typing import Any, Iterable, Iterator
import urllib.parse

#: The identity of a finding: the tool, the rule, the path of the artifact,
#: the logical location, the message, the text of the line and the ordinal of
#: the text in the artifact.
FindingKey = tuple[str, str, str, str | None, str, str | None, int]

_IDENTIFIER_PREFIXES = {
    "Cppcheck": "CPC",
    "QualityScanner": "QSC",
    "clang": "CSA",
    "nopinion": "NOP"
}


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
    location, if the result has one.  The text is the line of the file of the
    artifact with each run of white space replaced by one space, if a base
    directory contains the file.  The ordinal is the count of the preceding
    lines of the file with the same text.
    """

    location: str
    line: int | None = None
    text: str | None = None
    ordinal: int = 0


@dataclass(frozen=True)
class Finding:
    """
    This class represents one result of a SARIF log.

    The line of a finding is not part of its identity, since it moves when
    unrelated code moves.  The text of the line and its ordinal are part of
    it.  The ordinal tells apart two findings on lines with the same text.
    """

    tool: str
    rule: str
    artifact: Artifact
    logical_location: str | None
    message: str
    position: Position

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
                self.logical_location, self.message, self.position.text,
                self.position.ordinal)

    @property
    def identifier(self) -> str:
        """
        Is the identifier of the finding.  It is a prefix of the tool, a
        hyphen, and six base32 digits of the digest of the identity.
        """
        prefix = _IDENTIFIER_PREFIXES.get(self.tool, self.tool[:3].upper())
        digest = hashlib.sha256(json.dumps(self.key).encode("utf-8")).digest()
        return f"{prefix}-{base64.b32encode(digest).decode('ascii')[:6]}"


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


_BaseIds = dict[str, Any]


def _file_path(location: dict[str, Any], base_ids: _BaseIds,
               bases: list[str]) -> str:
    """
    Return the path of the file of the artifact location.

    A URI relative to a base ID with a URI is relative to that URI.  The path
    of a relative URI with another base ID starts with the base ID, so equal
    URIs of distinct bases have distinct paths.
    """
    uri = location["uri"]
    base_id = location.get("uriBaseId")
    if base_id is not None and not urllib.parse.urlparse(uri).scheme and \
            not uri.startswith("/"):
        base_uri = base_ids.get(base_id, {}).get("uri")
        if base_uri is None:
            return f"{base_id}/{urllib.parse.unquote(uri)}"
        uri = urllib.parse.urljoin(base_uri, uri)
    return relative_path(uri, bases)


def _artifact(artifacts: list[dict[str, Any]], index: int, base_ids: _BaseIds,
              bases: list[str]) -> Artifact:
    artifact = artifacts[index]
    properties = artifact.get("properties", {})
    if "uid" in properties:
        uid = properties["uid"]
        if properties["kind"] == "document":
            document = f"{uid}: {properties['path']}"
            return Artifact(document, document, None, document)
        return Artifact(uid, uid, uid, None)
    if "parentIndex" in artifact:
        parent = _artifact(artifacts, artifact["parentIndex"], base_ids, bases)
        name = urllib.parse.unquote(artifact["location"]["uri"])
        return Artifact(f"{parent.path}/{name}", f"{parent.display}({name})",
                        None, None)
    path = _file_path(artifact["location"], base_ids, bases)
    return Artifact(path, path, None, None)


def _location_artifact(result: dict[str, Any], artifacts: list[dict[str, Any]],
                       base_ids: _BaseIds,
                       bases: list[str]) -> tuple[Artifact, dict[str, Any]]:
    locations = result.get("locations") or [{}]
    physical = locations[0].get("physicalLocation", {})
    location = physical.get("artifactLocation", {})
    if "index" in location:
        return _artifact(artifacts, location["index"], base_ids,
                         bases), physical
    path = "-" if "uri" not in location else _file_path(
        location, base_ids, bases)
    return Artifact(path, path, None, None), physical


_Lines = dict[str, list[str] | None]


def source_file(artifact: Artifact, bases: list[str]) -> str | None:
    """
    Return the path of the file of a file artifact in the first base directory
    which contains it, or None if the artifact is no such file.
    """
    if artifact.item or artifact.document or artifact.path == "-":
        return None
    for base in [""] if os.path.isabs(artifact.path) else bases:
        path = os.path.join(base, artifact.path)
        if os.path.isfile(path):
            return path
    return None


def _source_lines(artifact: Artifact, bases: list[str],
                  sources: _Lines) -> list[str] | None:
    """
    Return the lines of the file of a file artifact with each run of white
    space replaced by one space, or None if it is no such file.
    """
    if artifact.path not in sources:
        path = source_file(artifact, bases)
        lines = None
        if path is not None:
            with open(path, "r", encoding="utf-8", errors="replace") as src:
                lines = [" ".join(line.split()) for line in src]
        sources[artifact.path] = lines
    return sources[artifact.path]


def _position(artifact: Artifact, location: str, line: int | None,
              bases: list[str], sources: _Lines) -> Position:
    lines = _source_lines(artifact, bases, sources)
    if lines is None or line is None or not 0 < line <= len(lines):
        return Position(location, line)
    text = lines[line - 1]
    return Position(location, line, text, lines[:line - 1].count(text))


def _finding(tool: str, result: dict[str, Any], run: dict[str, Any],
             bases: list[str], sources: _Lines) -> Finding:
    artifact, physical = _location_artifact(result, run.get("artifacts", []),
                                            run.get("originalUriBaseIds", {}),
                                            bases)
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
    return Finding(tool, result["ruleId"], artifact, qualified or name,
                   result["message"]["text"],
                   _position(artifact, location, line, bases, sources))


def load(paths: Iterable[str], bases: list[str]) -> Iterator[Finding]:
    """
    Yield the findings of the SARIF files in the order of the files, the runs
    and the results.

    The path of an artifact with a uid property is the UID of the item, or the
    UID and the path of a document.  The path of a nested artifact is the path
    of its parent followed by its own URI.  A file URI is relative to the
    first base directory which contains it.  The text of the line of a finding
    comes from the file in the first base directory which contains it.

    Args:
        paths: The paths of the SARIF files.
        bases: The base directories of file URIs.

    Raises:
        ValueError: Two findings with distinct identities have the same
            identifier.
    """
    sources: _Lines = {}
    keys: dict[str, FindingKey] = {}
    for path in paths:
        with open(path, "r", encoding="utf-8") as src:
            sarif = json.load(src)
        for run in sarif["runs"]:
            tool = run["tool"]["driver"]["name"]
            for result in run.get("results", []):
                finding = _finding(tool, result, run, bases, sources)
                check_identifier(keys, finding)
                yield finding


def check_identifier(keys: dict[str, FindingKey], finding: Finding) -> None:
    """
    Record the identity of the finding by its identifier.

    Raises:
        ValueError: The keys record another identity for the identifier.
    """
    key = keys.setdefault(finding.identifier, finding.key)
    if key != finding.key:
        raise ValueError(f"the findings {key} and {finding.key} have the "
                         f"same identifier {finding.identifier}")


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
