# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the sarif module. """

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

from specmake.sarif import Finding, load, relative_path

_SPAMR = Path(__file__).parent / "test-files" / "pkg" / "build" / "src" / \
    "spamr"


def _load(*names: str) -> list[Finding]:
    return list(load([str(_SPAMR / name) for name in names], ["/opt/rtems"]))


def test_source_findings():
    findings = _load("clang-analyzer/2026-10-13-100000-1-1/report-a.sarif",
                     "cppcheck/cppcheck.sarif")
    clang = findings[0]
    assert clang.key == ("clang", "deadcode.DeadStores",
                         "cpukit/dev/iovprintf.c", None,
                         "Value stored to 'num' is never read")
    assert clang.location == "cpukit/dev/iovprintf.c:117"
    assert clang.suppression is None
    assert clang.artifact.item is None and clang.artifact.document is None
    # A path outside of the base directories stays absolute
    cppcheck = [finding for finding in findings if finding.tool == "Cppcheck"]
    assert cppcheck[0].artifact.path == "/opt/rtems-qual-only/cpukit/a.c"
    assert cppcheck[0].location == "/opt/rtems-qual-only/cpukit/a.c:3"


def test_scanner_findings():
    findings = _load("quality-scanner/tbd-tbc-in-documentation-sources.sarif")
    item = findings[0]
    assert item.key == ("QualityScanner", "TBD", "/rtems/req/action",
                        "/rtems/req/action:/text", "TBD found")
    assert item.location == "/rtems/req/action:/text"
    assert item.artifact.item == "/rtems/req/action"
    documents = [finding for finding in findings if finding.artifact.document]
    assert documents[0].artifact.path == "/pkg/source/doc-a: source/a.rst"
    assert documents[0].location.startswith("/pkg/source/doc-a: source/a.rst:")
    suppressed = [finding for finding in findings if finding.suppression]
    assert suppressed[0].suppression == \
        "The glossary term *TBC* names the marker."


def test_binary_findings():
    member, anonymous, top = _load("nopinion/nopinion.sarif")
    # A nested artifact names its parent
    assert member.key == ("nopinion", "TN-0009/back-to-back-store",
                          "librtemscpu.a/m.o", "f",
                          "TN-0009 back-to-back-store")
    assert member.location == "librtemscpu.a(m.o) f"
    assert anonymous.logical_location is None
    assert anonymous.location == "librtemscpu.a(n.o)"
    # A relative URI with a base id stays relative
    assert top.artifact.path == "app.exe"
    assert top.location == "app.exe g"


def test_finding_without_location(tmpdir):
    path = Path(tmpdir) / "empty.sarif"
    path.write_text(
        '{"runs":[{"tool":{"driver":{"name":"t"}},"results":[{"ruleId":"r",'
        '"message":{"text":"m"}},{"ruleId":"s","message":{"text":"n"},'
        '"locations":[{"physicalLocation":{"artifactLocation":{}}}],'
        '"suppressions":[{"kind":"inSource"}]}]}]}',
        encoding="utf-8")
    first, second = load([str(path)], [])
    assert first.artifact.path == "-" and first.location == "-"
    assert second.artifact.path == "-"
    # A suppression without a justification has an empty justification
    assert second.suppression == ""


def test_relative_path():
    assert relative_path("file:///opt/rtems/a%20b.c", ["/opt/rtems"]) == \
        "a b.c"
    assert relative_path("/opt/x/a.c", ["/opt/rtems"]) == "/opt/x/a.c"
