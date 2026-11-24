# SPDX-License-Identifier: BSD-2-Clause
""" Provides the check of the inspections. """

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
import collections
from dataclasses import dataclass
import enum
import hashlib
import json
import logging
import os
from typing import Any, Callable, Iterable, Iterator
import urllib.parse

from specitems import Item, Link, TextContent, data_digest, hash_file

from .directorystate import DirectoryState
from .pkgitems import BuildItemMapper

#: The item data keys which the digest of an item scope does not cover.  A
#: copyright year bump does not change an artefact, and the buildspace adds
#: the workspace hash.
ITEM_DIGEST_EXCLUDED_KEYS = ("SPDX-License-Identifier", "copyrights",
                             "workspace-hash")

_INSPECTION_TYPE = "pkg/inspection"
_GROUP_TYPE = "pkg/inspection-group"

#: Maps an inspected artefact to its directory state, or to None if the
#: artefact has no directory state.
StateOf = Callable[[Item], DirectoryState | None]

#: The identity of a finding: the tool, the rule, the file and the message.
_FindingKey = tuple[str, str, str, str]


class State(enum.Enum):
    """ This class represents the state of an inspected scope. """

    VALID = "valid"
    STALE = "stale"
    ABSENT = "absent"
    LOST = "lost"
    NOT_BASELINED = "not baselined"
    NOT_CHECKED = "not checked"
    UNDISPOSITIONED = "undispositioned"
    UNJUDGED = "unjudged"
    UNTRACKED = "untracked"

    def fails(self, strict: bool = False) -> bool:
        """
        Return true if the state fails the gate.

        Args:
            strict: If true, then the release gate applies.
        """
        return self in _FAILING_STATES or (strict
                                           and self in _STRICT_FAILING_STATES)


#: A stale scope is a judgement about content which changed.  A lost scope is
#: the evidence of a compliant or not applicable inspection which no longer
#: exists.  An undispositioned finding defeats the purpose of a group.  An
#: unjudged inspection records digests without a judgement.  An untracked
#: inspection found a defect which no issue tracks.  All of them fail.
#:
#: An absent scope is the inspected content of a non-compliant inspection, or
#: a finding, which no longer exists.  This is the outcome of a corrected
#: defect, so it does not fail.
_FAILING_STATES = frozenset([
    State.STALE, State.LOST, State.UNDISPOSITIONED, State.UNJUDGED,
    State.UNTRACKED
])

#: The release gate also fails a scope which is not baselined or not checked,
#: since such a scope covers nothing.
_STRICT_FAILING_STATES = frozenset([State.NOT_BASELINED, State.NOT_CHECKED])


@dataclass(frozen=True)
class Result:
    """ This class represents the check result of one inspected scope. """

    uid: str
    state: State
    scope: str
    detail: str

    def __str__(self) -> str:
        return f"{self.state.value.upper()} {self.uid} {self.scope}" \
            f": {self.detail}"


def item_digest(item: Item) -> str:
    """ Return the digest of the item which an item scope covers. """
    return data_digest({
        key: value
        for key, value in item.data.items()
        if key not in ITEM_DIGEST_EXCLUDED_KEYS
    })


_Ranges = list[tuple[int, int]]


def _ranges(scope: dict) -> _Ranges:
    return [(int(begin), int(last)) for begin, last in scope["ranges"]]


def _lines_digest(lines: list[bytes], ranges: _Ranges) -> str:
    # This is the digest of specitems.hash_file_lines().
    state = hashlib.sha512()
    for begin, last in ranges:
        state.update(b"\n".join(lines[begin - 1:last]))
    return base64.urlsafe_b64encode(state.digest()).decode("ascii")


def _find_ranges(lines: list[bytes], ranges: _Ranges,
                 digest: str) -> _Ranges | None:
    """
    Return the ranges shifted by the nearest offset which matches the digest.
    """
    first = min(begin for begin, _ in ranges)
    last = max(last for _, last in ranges)
    offsets = sorted(range(1 - first, len(lines) - last + 1), key=abs)
    for offset in offsets:
        moved = [(begin + offset, end + offset) for begin, end in ranges]
        if _lines_digest(lines, moved) == digest:
            return moved
    return None


def _scope_name(scope: dict) -> str:
    kind = scope["scope"]
    if kind == "file":
        if scope["ranges"] is None:
            return f"file {scope['file']}"
        ranges = ",".join(f"{begin}:{last}" for begin, last in _ranges(scope))
        return f"file {scope['file']} lines {ranges}"
    if kind == "finding":
        return f"finding {scope['tool']} {scope['rule']} {scope['file']}: " \
            f"{scope['message']}"
    return "item"


def _finding_key(scope: dict) -> _FindingKey:
    return (str(scope["tool"]), str(scope["rule"]), str(scope["file"]),
            str(scope["message"]))


def _relative_path(uri: str, bases: list[str]) -> str:
    if uri.startswith("file://"):
        uri = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(uri)
    for base in bases:
        if path.startswith(f"{base}/"):
            return os.path.relpath(path, base)
    return path


def _result_file(result: dict, artifacts: list[dict], bases: list[str]) -> str:
    locations = result.get("locations") or [{}]
    location = locations[0].get("physicalLocation",
                                {}).get("artifactLocation", {})
    if "index" in location:
        artifact = artifacts[location["index"]]
        properties = artifact.get("properties", {})
        if "uid" in properties:
            if properties["kind"] == "document":
                return f"{properties['uid']}: {properties['path']}"
            return properties["uid"]
        location = artifact.get("location", location)
    uri = location.get("uri")
    return "-" if uri is None else _relative_path(uri, bases)


def load_findings(paths: Iterable[str],
                  bases: list[str]) -> collections.Counter[_FindingKey]:
    """
    Load the findings of the SARIF files.

    The line of a finding is not part of its identity, since it moves when
    unrelated code moves.  Findings with the same identity are counted.

    Args:
        paths: The paths of the SARIF files.
        bases: The source directories which the file paths are relative to.
    """
    findings: collections.Counter[_FindingKey] = collections.Counter()
    for path in paths:
        with open(path, "r", encoding="utf-8") as src:
            sarif = json.load(src)
        for run in sarif["runs"]:
            tool = run["tool"]["driver"]["name"]
            artifacts = run.get("artifacts", [])
            for result in run.get("results", []):
                findings[(tool, result["ruleId"],
                          _result_file(result, artifacts,
                                       bases), result["message"]["text"])] += 1
    return findings


class _Context:
    """ Provides the content of the inspected artefacts. """

    def __init__(self, state_of: StateOf, bases: list[str]) -> None:
        self._state_of = state_of
        self._bases = bases
        self._findings: dict[str, collections.Counter[_FindingKey]] = {}

    def directory(self, target: Item) -> str | None:
        """
        Return the directory of the target, or None if it is not present.
        """
        state = self._state_of(target)
        if state is None or not os.path.isdir(state.directory):
            return None
        return state.directory

    def findings(self, target: Item,
                 user: Item) -> collections.Counter[_FindingKey]:
        """
        Return the findings of the SARIF files of the target.

        Raises:
            ValueError: The target is no directory state with SARIF files.
        """
        if target.uid not in self._findings:
            state = self._state_of(target)
            paths = [] if state is None else [
                path for path in state.files() if path.endswith(".sarif")
            ]
            if not paths:
                raise ValueError(f"{user.uid}: the analysis {target.uid} is "
                                 "no directory state with SARIF files")
            self._findings[target.uid] = load_findings(paths, self._bases)
        return self._findings[target.uid]

    def locate(self, scope: dict, target: Item,
               user: Item) -> tuple[str | None, _Ranges | None]:
        """
        Return the digest of the inspected content, or None if it is absent,
        and the line ranges which the content covers in the file.
        """
        kind = scope["scope"]
        if kind == "item":
            return item_digest(target), None
        if kind == "finding":
            return self._finding_digest(scope, target, user), None
        return self._file_digest(scope, target)

    def _finding_digest(self, scope: dict, target: Item,
                        user: Item) -> str | None:
        key = _finding_key(scope)
        count = self.findings(target, user)[key]
        if count == 0:
            return None
        return data_digest({"count": count, "finding": list(key)})

    def _file_digest(self, scope: dict,
                     target: Item) -> tuple[str | None, _Ranges | None]:
        directory = self.directory(target)
        if directory is None:
            return None, None
        path = os.path.join(directory, scope["file"])
        if not os.path.isfile(path):
            return None, None
        if scope["ranges"] is None:
            return hash_file(path), None
        with open(path, "rb") as src:
            lines = src.read().splitlines()
        ranges = _ranges(scope)
        digest = _lines_digest(lines, ranges)
        expected = scope["hash"]
        if scope["anchor"] == "line" or expected in (None, digest):
            return digest, ranges
        moved = _find_ranges(lines, ranges, expected)
        if moved is None:
            return digest, ranges
        return expected, moved


def _check_scope(item: Item, scope: dict, target: Item,
                 context: _Context) -> Result:
    name = _scope_name(scope)
    if scope["scope"] == "file" and context.directory(target) is None:
        return Result(item.uid, State.NOT_CHECKED, name,
                      f"the directory of {target.uid} is not present")
    expected = scope["hash"]
    if expected is None:
        return Result(item.uid, State.NOT_BASELINED, name,
                      "no digest is recorded")
    actual, ranges = context.locate(scope, target, item)
    if actual is None:
        if scope["scope"] == "finding" or item["verdict"] == "non-compliant":
            return Result(item.uid, State.ABSENT, name,
                          "the inspected content no longer exists")
        return Result(item.uid, State.LOST, name,
                      "the evidence of the judgement no longer exists")
    if actual != expected:
        return Result(item.uid, State.STALE, name,
                      f"expected {expected} but got {actual}")
    detail = "the digest matches"
    if ranges is not None and ranges != _ranges(scope):
        moved = ",".join(f"{begin}:{last}" for begin, last in ranges)
        detail = f"{detail} at lines {moved}"
    return Result(item.uid, State.VALID, name, detail)


def is_superseded(item: Item) -> bool:
    """
    Return true if a newer inspection supersedes the item.

    The newer round declares the link, so the superseded round sees it as an
    incoming link.
    """
    return any(item.links_to_children("inspection-supersedes"))


def _check_judgement(item: Item) -> Iterator[Result]:
    missing = [
        key for key in ("date", "inspectors", "method", "verdict")
        if not item[key]
    ]
    if missing:
        yield Result(item.uid, State.UNJUDGED, "judgement",
                     f"no {', '.join(missing)} is recorded")
    if item["verdict"] == "non-compliant" and not any(
            item.links_to_parents("issue")):
        yield Result(item.uid, State.UNTRACKED, "judgement",
                     "no issue tracks the non-compliance")


def _inspected_finding_keys(group: Item) -> set[tuple[str, _FindingKey]]:
    keys = set()
    for member in group.links_to_children("inspection-member"):
        inspection = member.item
        if is_superseded(inspection):
            continue
        for link in inspection.links_to_parents("inspected"):
            for scope in link["scopes"]:
                if scope["scope"] == "finding":
                    keys.add((link.item.uid, _finding_key(scope)))
    return keys


def _check_group(group: Item, context: _Context) -> Iterator[Result]:
    inspected = _inspected_finding_keys(group)
    for link in group.links_to_parents("inspection-covered-analysis"):
        for key in sorted(context.findings(link.item, group)):
            if (link.item.uid, key) not in inspected:
                tool, rule, file, message = key
                yield Result(
                    group.uid, State.UNDISPOSITIONED,
                    f"{tool} {rule} {file}: {message}",
                    f"no member inspects this finding of {link.item.uid}")


def _items_of_type(items: Iterable[Item], item_type: str) -> list[Item]:
    return sorted((item for item in items if item.type == item_type),
                  key=lambda item: item.uid)


def check(items: Iterable[Item], state_of: StateOf,
          bases: list[str]) -> list[Result]:
    """
    Check every inspection and every inspection group of the items.

    A superseded inspection is historical evidence.  It keeps the digests
    which it was baselined with, so the check skips it.
    """
    items = list(items)
    context = _Context(state_of, bases)
    results: list[Result] = []
    for item in _items_of_type(items, _INSPECTION_TYPE):
        if is_superseded(item):
            continue
        results.extend(_check_judgement(item))
        for link in item.links_to_parents("inspected"):
            for scope in link["scopes"]:
                results.append(_check_scope(item, scope, link.item, context))
    for group in _items_of_type(items, _GROUP_TYPE):
        results.extend(_check_group(group, context))
    return results


def _scope_identity(scope: dict) -> dict:
    return {key: value for key, value in scope.items() if key != "hash"}


def _current(scope: dict, digest: str | None, ranges: _Ranges | None) -> dict:
    current: dict[str, Any] = {
        "scope": _scope_identity(scope),
        "digest": digest
    }
    if ranges is not None:
        current["ranges"] = [list(line_range) for line_range in ranges]
    return current


def current_digests(items: Iterable[Item], state_of: StateOf,
                    bases: list[str]) -> dict[str, list[dict]]:
    """
    Return the current digests of the scopes of every current inspection.

    The value of an inspection lists its inspected links in the order of the
    item.  Each link lists its scopes without their recorded digest, the
    current digest of their content, and for line ranges the lines which the
    content covers.
    """
    context = _Context(state_of, bases)
    digests: dict[str, list[dict]] = {}
    for item in _items_of_type(items, _INSPECTION_TYPE):
        if is_superseded(item):
            continue
        digests[item.uid] = [{
            "uid":
            link.item.uid,
            "scopes": [
                _current(scope, *context.locate(scope, link.item, item))
                for scope in link["scopes"]
            ]
        } for link in item.links_to_parents("inspected")]
    return digests


def _inspected_links(data: dict) -> list[dict]:
    return [link for link in data["links"] if link["role"] == "inspected"]


def _report_links(data: dict, uid: str, report: dict) -> list[dict]:
    try:
        links = report["inspections"][uid]
    except KeyError as err:
        raise ValueError(f"the report has no inspection {uid}") from err
    recorded = [[_scope_identity(scope) for scope in link["scopes"]]
                for link in _inspected_links(data)]
    reported = [[scope["scope"] for scope in link["scopes"]] for link in links]
    if recorded != reported:
        raise ValueError(f"the scopes of {uid} changed since the build of "
                         "the report")
    return links


def baseline(data: dict, uid: str, report: dict) -> int:
    """
    Record the digests of the report in the scopes which have none.

    A scope with a digest keeps it, so a judgement stays bound to the content
    which the inspectors saw.  The lines of a content anchored scope whose
    content moved follow the content.

    Args:
        data: The data of the inspection item in the workspace.
        uid: The UID of the inspection item.
        report: The report of an inspection check.

    Returns:
        The count of the changed scopes.
    """
    count = 0
    for link, reported in zip(_inspected_links(data),
                              _report_links(data, uid, report)):
        for scope, current in zip(link["scopes"], reported["scopes"]):
            if scope["hash"] is None:
                if current["digest"] is not None:
                    scope["hash"] = current["digest"]
                    count += 1
            elif scope["hash"] == current["digest"] and current.get(
                    "ranges", scope["ranges"]) != scope["ranges"]:
                scope["ranges"] = current["ranges"]
                count += 1
    return count


def renew(data: dict, uid: str, report: dict) -> dict:
    """
    Return the data of a new inspection round which supersedes the item.

    The digests come from the report.  The judgement of the inspectors stays
    unset, so the new round fails the check until a person records it.

    Args:
        data: The data of the inspection item in the workspace.
        uid: The UID of the inspection item.
        report: The report of an inspection check.
    """
    links: list[dict] = [{"role": "inspection-supersedes", "uid": uid}]
    for link, reported in zip(_inspected_links(data),
                              _report_links(data, uid, report)):
        scopes = []
        for scope, current in zip(link["scopes"], reported["scopes"]):
            fresh = dict(scope)
            fresh["hash"] = current["digest"]
            if "ranges" in current:
                fresh["ranges"] = current["ranges"]
            scopes.append(fresh)
        links.append({
            "role": "inspected",
            "uid": link["uid"],
            "scopes": scopes
        })
    for link in data["links"]:
        if link["role"] not in ("inspected", "inspection-supersedes"):
            links.append(dict(link))
    return {
        "SPDX-License-Identifier": data["SPDX-License-Identifier"],
        "copyrights": data["copyrights"],
        "date": None,
        "enabled-by": data["enabled-by"],
        "findings": None,
        "inspectors": [],
        "links": links,
        "method": None,
        "pkg-type": "inspection",
        "type": "pkg",
        "verdict": None,
    }


class InspectionCheck(DirectoryState):
    """
    Checks the inspections of the package.

    The check is a function of the inspections and of the content which they
    inspect.  It costs one digest per scope, so it runs in every build.
    """

    def is_build_necessary(self) -> bool:
        return True

    def _state_of(self, target: Item) -> DirectoryState | None:
        build_item = self.director[target.uid]
        if isinstance(build_item, DirectoryState):
            return build_item
        return None

    def run(self) -> None:
        items = [item for item in self.item.cache.values() if item.enabled]
        bases = []
        for state in self.inputs("source"):
            assert isinstance(state, DirectoryState)
            bases.append(state.directory)
        results = check(items, self._state_of, bases)
        for result in results:
            if result.state.fails():
                logging.warning("%s: %s", self.uid, result)
        report: dict[str, Any] = {
            "inspections":
            current_digests(items, self._state_of, bases),
            "results": [{
                "detail": result.detail,
                "fails": result.state.fails(),
                "fails-strict": result.state.fails(strict=True),
                "scope": result.scope,
                "state": result.state.value,
                "uid": result.uid
            } for result in results]
        }
        self.json_dump(report)
        self.description.add(
            "Check the digests and the judgements of the inspections and "
            f"produce the report {self.description.path(self.file)}.")


def _person(person: dict) -> str:
    return f"{person['first-name']} {person['last-name']} " \
        f"({person['organization']})"


def _issue(mapper: BuildItemMapper, link: Link) -> str:
    issue = link.item
    database = issue.parent("issue-member")
    url = mapper.substitute(database["url"], issue)
    identifier = mapper.substitute(database["format-identifier"], issue)
    name = f"{database['name']} {identifier}"
    return f"{mapper.format_link(name, url)} ({link['status']})"


def _optional(value: str | None) -> str:
    return "not recorded" if value is None else value.strip()


def _history(item: Item) -> list[str]:
    rounds: list[str] = []
    while True:
        superseded = [
            link.item
            for link in item.links_to_parents("inspection-supersedes")
        ]
        if not superseded:
            return rounds
        item = superseded[0]
        rounds.append(f"{_optional(item['date'])} "
                      f"({_optional(item['verdict'])})")


def _add_inspection(content: TextContent, mapper: BuildItemMapper, item: Item,
                    states: dict[tuple[str, str], dict]) -> None:
    with content.section(f"Inspection {item.uid}"):
        inspectors = ", ".join(
            _person(person) for person in item["inspectors"])
        content.add_definition_item("Inspectors", inspectors or "not recorded")
        content.add_definition_item("Date", _optional(item["date"]))
        content.add_definition_item(
            "Verdict",
            _optional(item["verdict"]).replace("-", " "))
        content.add_definition_item("Method", _optional(item["method"]))
        content.add_definition_item("Findings", _optional(item["findings"]))
        issues = [
            _issue(mapper, link) for link in item.links_to_parents("issue")
        ]
        if issues:
            content.add_definition_item("Issues", ", ".join(issues))
        history = _history(item)
        if history:
            content.add_definition_item("Supersedes", ", ".join(history))
        rows = [("Scope", "Artefact", "State")]
        judgement = states.get((item.uid, "judgement"))
        if judgement is not None:
            rows.append(("judgement", "", judgement["state"]))
        for link in item.links_to_parents("inspected"):
            for scope in link["scopes"]:
                name = _scope_name(scope)
                rows.append((content.escape(name), link.item.uid,
                             states[(item.uid, name)]["state"]))
        content.add_simple_table(rows)


def render_group(content: TextContent, mapper: BuildItemMapper, group: Item,
                 report: dict) -> None:
    """
    Render the inspection group with the states of the check report.

    The label of the section of the group follows from the UID of the group,
    so that a citation group member link to the section survives a change of
    the group name.

    Args:
        content: The content which receives the inspection group.
        mapper: The mapper of the document.
        group: The inspection group item.
        report: The report of the inspection check.
    """
    states = {
        (result["uid"], result["scope"]): result
        for result in report["results"]
    }
    with content.section(group["name"], label_tail=group.ident):
        content.add(group["text"])
        members = sorted(
            (link.item for link in group.links_to_children("inspection-member")
             if not is_superseded(link.item)),
            key=lambda item: item.uid)
        for member in members:
            _add_inspection(content, mapper, member, states)
        undispositioned = [
            result for result in report["results"]
            if result["uid"] == group.uid
        ]
        if undispositioned:
            content.add("These findings have no inspection:")
            content.add_simple_table([("Finding", "Detail")] +
                                     [(content.escape(result["scope"]),
                                       result["detail"])
                                      for result in undispositioned])
