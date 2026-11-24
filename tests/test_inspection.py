# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the inspection module. """

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

from pathlib import Path

import pytest

from specitems import hash_file_lines, load_data

from specmake.inspection import (State, baseline, item_digest, load_findings,
                                 renew)

import specmake.inspection

from .util import create_package, get_and_clear_log

_A_TXT = "eilvq1Nks0zj4EdtVb8pG9QaoIXl7PKpaIPlk6oYNv7SL3JCr0jVSvGPVcjR3vE-" \
    "yTFMkmZmoLpj92Y1AAkFZQ=="

_INSPECTIONS = Path(__file__).parent / "spec-packagebuild" / "pkg" / \
    "inspection"


def _build(caplog, tmp_dir: Path):
    package = create_package(caplog, tmp_dir, Path("spec-packagebuild"),
                             ["inspection"])
    check = package.director["/pkg/inspection/check"]
    check.build()
    return package.director, check.json_load()


def _states(report: dict) -> dict[tuple[str, str], str]:
    return {
        (result["uid"], result["scope"]): result["state"]
        for result in report["results"]
    }


def test_inspection_check(caplog, tmpdir):
    director, report = _build(caplog, Path(tmpdir))
    states = _states(report)
    pre = "/pkg/inspection/"
    assert states[(f"{pre}file-ok", "file dir/a.txt")] == "valid"
    assert states[(f"{pre}file-ok",
                   "file dir/e.txt lines 1:1")] == "not baselined"
    assert states[(f"{pre}file-stale", "file dir/a.txt")] == "stale"
    chapter = "file quality-scanner/doc/chapter.rst lines 3:4"
    # The content anchored lines moved to the begin of the file.
    assert states[(f"{pre}file-moved", chapter)] == "valid"
    assert states[(f"{pre}file-shifted", chapter)] == "stale"
    assert states[(f"{pre}file-changed", chapter)] == "stale"
    assert states[(f"{pre}file-lost", "file dir/gone.txt")] == "lost"
    assert states[(f"{pre}file-fixed", "file dir/gone.txt")] == "absent"
    assert (f"{pre}file-fixed", "judgement") not in states
    assert states[(f"{pre}not-baselined", "file dir/a.txt")] == \
        "not baselined"
    assert states[(f"{pre}unjudged", "judgement")] == "unjudged"
    assert states[(f"{pre}non-compliant", "judgement")] == "untracked"
    assert states[(f"{pre}new-round", "file dir/a.txt")] == "valid"
    assert not any(uid == f"{pre}old-round" for uid, _ in states)
    assert states[(f"{pre}item-scope", "item")] == "not baselined"
    gone = "Cppcheck variableScope cpukit/gone.c: The scope of the " \
        "variable 'z' can be reduced."
    assert states[(f"{pre}finding-ok", "finding Cppcheck variableScope "
                   "cpukit/a.c: The scope of the variable 'x' can be "
                   "reduced.")] == "not baselined"
    # A member which inspects the finding in another analysis does not
    # disposition the finding of the covered analysis.
    assert states[(f"{pre}finding-other-analysis", "finding Cppcheck "
                   "variableScope cpukit/b.c: The scope of the variable 'y' "
                   "can be reduced.")] == "absent"
    assert not any(uid == f"{pre}finding-old" for uid, _ in states)
    assert states[(f"{pre}finding-absent", f"finding {gone}")] == "absent"
    undispositioned = sorted(scope for (uid, scope), state in states.items()
                             if uid == f"{pre}group")
    # A member inspects the finding of a.c.  The member which inspects the
    # finding of b.c is superseded or inspects another analysis.
    assert undispositioned == [
        "Cppcheck checkersReport -: Active checkers: 160/592",
        "Cppcheck missingIncludeSystem cpukit/b.c: Include file: <stdio.h> "
        "not found.", "Cppcheck syntaxError /elsewhere/c.c: syntax error",
        "Cppcheck unusedFunction cpukit/dev ice.c: The function 'g' is "
        "never used.", "Cppcheck unusedFunction cpukit/driver#1.c: The "
        "function 'f' is never used.",
        "Cppcheck variableScope cpukit/b.c: The scope of the variable 'y' "
        "can be reduced."
    ]
    failing = sorted(
        {result["state"]
         for result in report["results"] if result["fails"]})
    assert failing == [
        "lost", "stale", "undispositioned", "unjudged", "untracked"
    ]
    strict = sorted({
        result["state"]
        for result in report["results"] if result["fails-strict"]
    })
    assert strict == [
        "lost", "not baselined", "stale", "undispositioned", "unjudged",
        "untracked"
    ]

    details = {
        (result["uid"], result["scope"]): result["detail"]
        for result in report["results"]
    }
    assert details[(f"{pre}file-moved", chapter)] == \
        "the digest matches at lines 1:2"
    moved = report["inspections"][f"{pre}file-moved"][0]["scopes"][0]
    assert moved["ranges"] == [[1, 2]]
    shifted = report["inspections"][f"{pre}file-shifted"][0]["scopes"][0]
    assert shifted["ranges"] == [[3, 4]]
    assert shifted["digest"] != moved["digest"]
    log = get_and_clear_log(caplog)
    assert "WARNING /pkg/inspection/check: STALE /pkg/inspection/file-stale " \
        "file dir/a.txt: expected " in log

    # The report carries the current digests in the order of the item.
    digests = report["inspections"][f"{pre}file-ok"]
    assert digests[0]["uid"] == "/pkg/source/test-files"
    assert digests[0]["scopes"][0]["digest"] == _A_TXT
    assert digests[0]["scopes"][0]["scope"] == {
        "anchor": "line",
        "file": "dir/a.txt",
        "ranges": None,
        "scope": "file"
    }
    assert digests[1]["scopes"][0]["digest"] is not None
    item = director.item_cache["/req/usage-constraints"]
    assert report["inspections"][f"{pre}item-scope"][0]["scopes"][0][
        "digest"] == item_digest(item)
    assert report["inspections"][f"{pre}file-lost"][0]["scopes"][0][
        "digest"] is None

    # A target without a directory leaves its file scopes not checked.
    item = director.item_cache[f"{pre}file-ok"]
    item.data["links"][0]["uid"] = "/pkg/component"
    director.item_cache.reinitialize_links()
    check = director["/pkg/inspection/check"]
    check.build()
    states = _states(check.json_load())
    assert states[(f"{pre}file-ok", "file dir/a.txt")] == "not checked"


def test_inspection_check_no_analysis(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("spec-packagebuild"),
                             ["inspection", "inspection-error"])
    with pytest.raises(ValueError,
                       match="^/pkg/inspection/finding-no-analysis: the "
                       "analysis /pkg/spamr/rtems is no directory "
                       "state with SARIF files$"):
        package.director["/pkg/inspection/check"].build()


def test_load_findings():
    spamr = Path(__file__).parent / "test-files" / "pkg" / "build" / "src" / \
        "spamr"
    paths = [
        str(spamr / "clang-analyzer" / "2026-10-13-100000-1-1" /
            "report-a.sarif"),
        str(spamr / "quality-scanner" /
            "tbd-tbc-in-documentation-sources.sarif")
    ]
    findings = load_findings(paths, ["/opt/rtems"])
    assert findings[("clang", "deadcode.DeadStores", "cpukit/dev/iovprintf.c",
                     "Value stored to 'num' is never read")] == 1
    assert findings[("QualityScanner", "TBD", "/rtems/req/action",
                     "TBD found")] == 1
    assert findings[("QualityScanner", "TBD",
                     "/pkg/source/doc-a: source/a.rst", "TBD found")] == 1
    # Findings with the same identity are counted.
    findings = load_findings(paths + paths[:1], ["/opt/rtems"])
    assert findings[("clang", "deadcode.DeadStores", "cpukit/dev/iovprintf.c",
                     "Value stored to 'num' is never read")] == 2


def test_state_fails():
    assert State.STALE.fails()
    assert not State.NOT_CHECKED.fails()
    assert State.NOT_CHECKED.fails(strict=True)
    assert not State.ABSENT.fails(strict=True)
    assert not State.VALID.fails(strict=True)


def test_lines_digest():
    # The content search computes the digest of specitems.hash_file_lines()
    # on lines in memory.  Both have to agree.
    path = Path(__file__).parent / "test-files" / "quality-scanner" / "doc" / \
        "chapter.rst"
    lines = path.read_bytes().splitlines()
    for ranges in ([(1, 2)], [(1, 1), (3, 6)], [(6, 6)], [(5, 9)]):
        # pylint: disable=protected-access
        assert specmake.inspection._lines_digest(lines, ranges) == \
            hash_file_lines(str(path), ranges)


def _report(uid: str, digests: list[list[tuple[dict, str | None]]]) -> dict:
    return {
        "inspections": {
            uid: [{
                "uid":
                "/t",
                "scopes": [{
                    "scope": scope,
                    "digest": digest
                } for scope, digest in link]
            } for link in digests]
        },
        "results": []
    }


def test_baseline_moved_ranges():
    data = load_data(str(_INSPECTIONS / "file-moved.yml"))
    scope = dict(data["links"][0]["scopes"][0])
    digest = scope.pop("hash")
    report = _report("/i", [[(scope, digest)]])
    report["inspections"]["/i"][0]["scopes"][0]["ranges"] = [[1, 2]]
    assert baseline(data, "/i", report) == 1
    assert data["links"][0]["scopes"][0]["ranges"] == [[1, 2]]
    assert data["links"][0]["scopes"][0]["hash"] == digest
    new = renew(load_data(str(_INSPECTIONS / "file-moved.yml")), "/i", report)
    assert new["links"][1]["scopes"][0]["ranges"] == [[1, 2]]


def _data() -> dict:
    return load_data(str(_INSPECTIONS / "file-ok.yml"))


def test_baseline():
    data = _data()
    report = _report("/i", [[({
        "anchor": "line",
        "file": "dir/a.txt",
        "ranges": None,
        "scope": "file"
    }, "x")],
                            [({
                                "anchor": "line",
                                "file": "dir/e.txt",
                                "ranges": [[1, 1]],
                                "scope": "file"
                            }, "y")]])
    assert baseline(data, "/i", report) == 1
    # A recorded digest stays.
    assert data["links"][0]["scopes"][0]["hash"] == _A_TXT
    assert data["links"][1]["scopes"][0]["hash"] == "y"
    assert baseline(data, "/i", report) == 0
    data["links"][1]["scopes"][0]["hash"] = None
    report["inspections"]["/i"][1]["scopes"][0]["digest"] = None
    assert baseline(data, "/i", report) == 0
    with pytest.raises(ValueError, match="the report has no inspection /j"):
        baseline(data, "/j", report)
    data["links"][1]["scopes"][0]["file"] = "dir/b.txt"
    with pytest.raises(ValueError,
                       match="the scopes of /i changed since the build"):
        baseline(data, "/i", report)


def test_renew():
    data = load_data(str(_INSPECTIONS / "file-fixed.yml"))
    report = _report("/i", [[({
        "anchor": "line",
        "file": "dir/gone.txt",
        "ranges": None,
        "scope": "file"
    }, None)]])
    new = renew(data, "/i", report)
    assert new["date"] is None
    assert new["verdict"] is None
    assert new["method"] is None
    assert new["findings"] is None
    assert new["inspectors"] == []
    assert new["pkg-type"] == "inspection"
    assert new["links"] == [{
        "role": "inspection-supersedes",
        "uid": "/i"
    }, {
        "role":
        "inspected",
        "uid":
        "../source/test-files",
        "scopes": [{
            "anchor": "line",
            "file": "dir/gone.txt",
            "hash": None,
            "ranges": None,
            "scope": "file"
        }]
    }, {
        "role": "issue",
        "status": "closed",
        "uid": "../issue/issue"
    }]
