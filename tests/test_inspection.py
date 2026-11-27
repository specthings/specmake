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

import json
from pathlib import Path
import shutil

import pytest

from specitems import (CommonMarkContent, SphinxContent, data_digest,
                       hash_file_lines, load_data)

from specmake.cliupdateinspections import cliupdateinspections
from specmake.inspection import (State, _add_inspected_findings, _finding_term,
                                 baseline, item_digest, renew)

import specmake.inspection
import specmake.packagemanual

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
    assert report["strict"] is False
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
    gone = "CPC-2KHYYB Cppcheck variableScope cpukit/gone.c: The scope of the " \
        "variable 'z' can be reduced."
    assert states[(f"{pre}finding-ok",
                   "finding CPC-OVRINA Cppcheck variableScope "
                   "cpukit/a.c: The scope of the variable 'x' can be "
                   "reduced.")] == "not baselined"
    # A member which inspects the finding in another analysis does not
    # disposition the finding of the covered analysis.
    assert states[(f"{pre}finding-other-analysis",
                   "finding CPC-7VCNIL Cppcheck "
                   "variableScope cpukit/b.c: The scope of the variable 'y' "
                   "can be reduced.")] == "absent"
    assert not any(uid == f"{pre}finding-old" for uid, _ in states)
    assert states[(f"{pre}finding-absent", f"finding {gone}")] == "absent"
    undispositioned = sorted(
        (scope
         for (uid, scope), state in states.items() if uid == f"{pre}group"),
        key=lambda scope: scope.split(" ", 1)[1])
    # A member inspects the finding of a.c.  The member which inspects the
    # finding of b.c is superseded or inspects another analysis.
    assert undispositioned == [
        "CPC-GQY46Q Cppcheck checkersReport -: Active checkers: 160/592",
        "CPC-BYHUSI Cppcheck missingIncludeSystem cpukit/b.c: Include file: <stdio.h> "
        "not found.",
        "CPC-AW4UEL Cppcheck syntaxError /elsewhere/c.c: syntax error",
        "CPC-GZXWYB Cppcheck unusedFunction cpukit/dev ice.c: The function 'g' is "
        "never used.",
        "CPC-A3GPTL Cppcheck unusedFunction cpukit/driver#1.c: The "
        "function 'f' is never used.",
        "CPC-7VCNIL Cppcheck variableScope cpukit/b.c: The scope of the "
        "variable 'y' can be reduced."
    ]
    failing = sorted(
        {result["state"]
         for result in report["results"] if result["fails"]})
    assert failing == [
        "lost", "stale", "undispositioned", "unjudged", "unrelated",
        "untracked"
    ]
    # A member of a group which covers an analysis has to inspect a finding
    # of it.
    assert states[(f"{pre}finding-other-analysis", "findings")] == "unrelated"
    assert states[(f"{pre}file-fixed", "findings")] == "unrelated"
    assert (f"{pre}finding-ok", "findings") not in states
    # An inspection applies the methods which it and its groups link.  An
    # inspection without a method is not judged.
    details = {
        (result["uid"], result["scope"]): result["detail"]
        for result in report["results"]
    }
    assert details[(f"{pre}no-method", "judgement")] == \
        "no method is recorded"
    assert details[(f"{pre}unjudged", "judgement")] == \
        "no date, inspectors, verdict is recorded"
    assert (f"{pre}finding-ok", "judgement") not in states
    strict = sorted({
        result["state"]
        for result in report["results"] if result["fails-strict"]
    })
    assert strict == [
        "lost", "not baselined", "stale", "undispositioned", "unjudged",
        "unrelated", "untracked"
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


def test_inspection_finding_identity(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("spec-packagebuild"),
                             ["inspection", "paf-spamr"])
    check = package.director["/pkg/inspection/check"]
    check.build()
    report = check.json_load()
    states = _states(report)
    nopinion = "finding NOP-5U2JQX nopinion TN-0009/back-to-back-store " \
        "LIBDIR/librtemscpu.a/m.o f: TN-0009 back-to-back-store"
    assert states[("/pkg/spamr/inspection-nopinion",
                   nopinion)] == "not baselined"
    # The digest covers the identity of the finding and not its count
    digest = report["inspections"]["/pkg/spamr/inspection-nopinion"][0][
        "scopes"][0]["digest"]
    assert digest == data_digest({
        "finding": [
            "nopinion", "TN-0009/back-to-back-store",
            "LIBDIR/librtemscpu.a/m.o", "f", "TN-0009 back-to-back-store",
            None, 0
        ]
    })
    item = package.director.item_cache["/pkg/spamr/inspection-nopinion"]
    item.data["links"][0]["scopes"][0]["hash"] = digest
    check.build()
    assert _states(check.json_load())[("/pkg/spamr/inspection-nopinion",
                                       nopinion)] == "valid"
    # Each finding of a covered analysis needs an inspection
    scanner = sorted((scope for (uid, scope), state in states.items()
                      if uid == "/pkg/spamr/group-quality-scanner"),
                     key=lambda scope: scope.split(" ", 1)[1])
    assert scanner == [
        "QSC-52256U QualityScanner TBC /pkg/component /pkg/component:/name: TBC found",
        "QSC-3B57TE QualityScanner TBC /pkg/source/doc-a: source/a.rst: TBC found",
        "QSC-O5IZWM QualityScanner TBD /pkg/source/doc-a: source/a.rst: TBD found",
        "QSC-N6LNMA QualityScanner TBD /rtems/req/action /rtems/req/action:/text: "
        "TBD found"
    ]


def test_inspection_group(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("spec-packagebuild"),
                             ["inspection", "sphinx-builder"])
    package.director["/pkg/inspection/check"].build()
    doc = package.director["/pkg/deployment/doc"]
    text = doc.substitute("${.:/inspection-group:1:/pkg/inspection/group}")
    # The error box of the findings without an inspection begins the
    # section.
    assert text.startswith(""".. _PkgInspectionGroup:

Static analysis
---------------

.. error::

    These findings have no inspection:

    - :ref:`CPC-GQY46Q <SpamrFindingCPCGQY46Q>`
""")
    # The group text, the subject and the rationale are substituted in the
    # context of their item.
    assert "SpamrFindingCPC7VCNIL>`\n\nThe members of Static analysis " \
        "inspect the findings.\n" in text
    assert """Inspection /pkg/inspection/finding-ok
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Inspectors
    Erika Mustermann (New Company)

Date
    2026-11-24

Verdict
    not applicable

Method
    `The Title, Review <pkg/doc/method.html#methodreview>`__
    :cite:`PkgDeploymentDoc` and `The Title, Interview
    <pkg/doc/method.html#methodinterview>`__ :cite:`PkgDeploymentDoc`

Subject
    Inspection of the artefact of 2026-11-24.

Rationale
    The artefact of 2026-11-24 needs no change.
""" in text
    assert """Supersedes
    2026-11-24 (not-applicable)""" in text
    # An error box begins the section of an inspection which relates to no
    # finding of the analyses which its group covers.
    assert """Inspection /pkg/inspection/finding-other-analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. error::

    This inspection relates to no finding of the analyses which its group
    covers.
""" in text
    assert "Inspection /pkg/inspection/finding-ok\n" \
        "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\nInspectors" in text
    assert "Issues\n    `Issue issue 42 <https://www.foo.org/bar?id=42>`__ " \
        "(closed)" in text
    assert """Inspectors
    not recorded

Date
    not recorded""" in text
    assert "Judgement\n    unjudged\n" in text
    assert "file dir/gone.txt\n    /pkg/source/test-files: absent\n" in text
    # The section of an inspection has a label, which a disposition in the
    # SPAMR references.
    assert ".. _InspectionPkgInspectionFindingOk:\n\nInspection " \
        "/pkg/inspection/finding-ok\n" in text
    # A finding scope references the section of the finding in the SPAMR.
    # The definition list of the inspection relates the inspection to the
    # inspected finding with the state of the check unless it is valid.
    assert "Inspected findings\n    This inspection relates to " \
        ":ref:`CPC-OVRINA <SpamrFindingCPCOVRINA>` (not\n    baselined).\n" \
        in text
    # An absent finding has no section in the SPAMR, so the inspection names
    # it by its identifier without a reference.
    assert "This inspection relates to CPC-7VCNIL (absent).\n" in text
    # An error box lists the findings without an inspection by their
    # identifiers, each a reference to the section of the finding.
    assert "    - :ref:`CPC-GQY46Q <SpamrFindingCPCGQY46Q>`\n\n" \
        "    - :ref:`CPC-BYHUSI <SpamrFindingCPCBYHUSI>`\n" in text
    assert ".. table::" not in text
    # A round without scopes and without a judgement result has no table.
    text = doc.substitute(
        "${.:/inspection-group:1:/pkg/inspection/group-history}")
    assert "Subject\n    Review without scopes.\n" in text
    # The affiliation follows the date 2021-11-26 of the inspection.
    assert """Inspectors
    Erika Mustermann (Old Company), Reviewer A""" in text
    assert ".. table::" not in text
    text = doc.substitute(
        "${.:/inspection-group:1:/pkg/inspection/group-empty}")
    assert text == """.. _PkgInspectionGroupEmpty:

No inspections
--------------

The group has no members."""


def _summary(director) -> str:
    director["/pkg/inspection/check"].build()
    summary = director["/pkg/deployment/doc-package-summary"]
    # The repositories of the fixture package are not built.
    summary.item["list-repositories"] = False
    summary.build(force=True)
    with open(summary.file, "r", encoding="utf-8") as src:
        return src.read()


def test_package_summary(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("spec-packagebuild"),
                             ["inspection", "package-manual"])
    director = package.director
    text = _summary(director)
    report = director["/pkg/inspection/check"].json_load()
    failed = [result for result in report["results"] if result["fails"]]
    assert f"- {len(failed)} inspection scopes fail the check" in text
    assert "## Failed inspections" in text
    assert "/pkg/inspection/file-stale" in text
    assert "/pkg/inspection/not-baselined" not in text

    # The release gate also fails the scopes which are not baselined.
    director.item_cache["/pkg/inspection/check"]["strict"] = True
    text = _summary(director)
    report = director["/pkg/inspection/check"].json_load()
    assert report["strict"] is True
    failed = [result for result in report["results"] if result["fails-strict"]]
    assert f"- {len(failed)} inspection scopes fail the check" in text
    assert "/pkg/inspection/not-baselined" in text


def test_package_summary_passed():
    content = CommonMarkContent(0, context="BSD-2-Clause")
    specmake.packagemanual._add_status(content, [], [], [], False, [])
    assert str(content) == """<a id="Passed"></a>

# ✅ Passed

There are no unexpected test failures.  All coverage scopes meet their limits.  There are no stale gap items.  All inspection scopes pass the check.
"""


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
    data["links"].append({"role": "inspector", "uid": "/person/p0001"})
    report = _report("/i", [[({
        "anchor": "line",
        "file": "dir/gone.txt",
        "ranges": None,
        "scope": "file"
    }, None)]])
    new = renew(data, "/i", report)
    assert new["date"] is None
    assert new["verdict"] is None
    assert new["subject"] == "Inspection of the artefact."
    assert new["rationale"] is None
    assert "inspectors" not in new
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
        "role": "inspection-member",
        "uid": "group"
    }, {
        "role": "issue",
        "status": "closed",
        "uid": "../issue/issue"
    }]


def _spec(tmp_path: Path) -> Path:
    spec = tmp_path / "spec"
    (spec / "pkg" / "inspection").mkdir(parents=True)
    shutil.copy(_INSPECTIONS / "file-ok.yml", spec / "pkg" / "inspection")
    return spec


def _run(tmp_path: Path, *args: str) -> None:
    cliupdateinspections([
        "specupdateinspections", "--spec-directory",
        str(tmp_path / "spec"), "--cache-directory",
        str(tmp_path / "cache"), *args
    ])


def test_cliupdateinspections(caplog, tmpdir):
    tmp_path = Path(tmpdir)
    _, report = _build(caplog, tmp_path / "build")
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps(report), encoding="utf-8")
    spec = _spec(tmp_path)
    item_file = spec / "pkg" / "inspection" / "file-ok.yml"
    uid = "/pkg/inspection/file-ok"
    _run(tmp_path, uid, str(report_file))
    data = load_data(str(item_file))
    assert data["links"][0]["scopes"][0]["hash"] == _A_TXT
    assert data["links"][1]["scopes"][0]["hash"] is not None
    before = item_file.read_text(encoding="utf-8")
    _run(tmp_path, uid, str(report_file))
    assert item_file.read_text(encoding="utf-8") == before
    output = tmp_path / "new.yml"
    _run(tmp_path, "--renew", "--output", str(output), uid, str(report_file))
    assert load_data(str(output))["links"][0] == {
        "role": "inspection-supersedes",
        "uid": uid
    }


def test_cliupdateinspections_errors(tmpdir):
    tmp_path = Path(tmpdir)
    _spec(tmp_path)
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps({"inspections": {}}), encoding="utf-8")
    uid = "/pkg/inspection/file-ok"
    with pytest.raises(SystemExit, match="--renew needs an --output file"):
        _run(tmp_path, "--renew", uid, str(report_file))
    with pytest.raises(SystemExit, match="there is no item /nope"):
        _run(tmp_path, "/nope", str(report_file))
    with pytest.raises(SystemExit,
                       match=f"{uid}: the report has no inspection {uid}"):
        _run(tmp_path, uid, str(report_file))


def test_inspected_findings():
    content = SphinxContent(context="CC-BY-SA-4.0")
    _add_inspected_findings(content, [])
    assert not list(content)
    _add_inspected_findings(content, ["A", "B"])
    assert "\n".join(content) == """Inspected findings
    This inspection relates to the following findings:

    - A

    - B"""


def test_finding_term():
    content = SphinxContent(context="CC-BY-SA-4.0")
    # A reported finding references its section in the SPAMR.
    assert _finding_term(content, "CPC-A", "valid") == \
        ":ref:`CPC-A <SpamrFindingCPCA>`"
    assert _finding_term(content, "CPC-A", "stale") == \
        ":ref:`CPC-A <SpamrFindingCPCA>` (stale)"
    # The SPAMR has no section of a finding which no analysis reports.
    assert _finding_term(content, "CPC-A", "absent") == "CPC-A (absent)"
    assert _finding_term(content, "CPC-A", "lost") == "CPC-A (lost)"
