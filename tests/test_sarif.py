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

import pytest

from specmake.sarif import (Artifact, Finding, Position, check_identifier,
                            load, relative_path, source_file)

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
                         "Value stored to 'num' is never read", None, 0)
    assert clang.location == "cpukit/dev/iovprintf.c:117"
    assert clang.artifact.item is None and clang.artifact.document is None
    # A path outside of the base directories stays absolute
    cppcheck = [finding for finding in findings if finding.tool == "Cppcheck"]
    assert cppcheck[0].artifact.path == "/opt/rtems-qual-only/cpukit/a.c"
    assert cppcheck[0].location == "/opt/rtems-qual-only/cpukit/a.c:3"


def test_scanner_findings():
    findings = _load("quality-scanner/tbd-tbc-in-documentation-sources.sarif")
    item = findings[0]
    assert item.key == ("QualityScanner", "TBD", "/rtems/req/action",
                        "/rtems/req/action:/text", "TBD found", None, 0)
    assert item.location == "/rtems/req/action:/text"
    assert item.artifact.item == "/rtems/req/action"
    documents = [finding for finding in findings if finding.artifact.document]
    assert documents[0].artifact.path == "/pkg/source/doc-a: source/a.rst"
    assert documents[0].location.startswith("/pkg/source/doc-a: source/a.rst:")


def test_binary_findings():
    member, anonymous, top = _load("nopinion/nopinion.sarif")
    # A nested artifact names its parent
    assert member.key == ("nopinion", "TN-0009/back-to-back-store",
                          "LIBDIR/librtemscpu.a/m.o", "f",
                          "TN-0009 back-to-back-store", None, 0)
    assert member.location == "LIBDIR/librtemscpu.a(m.o) f"
    assert anonymous.logical_location is None
    assert anonymous.location == "LIBDIR/librtemscpu.a(n.o)"
    # A relative URI with a base ID without a URI starts with the base ID
    assert top.artifact.path == "LIBDIR/app.exe"
    assert top.location == "LIBDIR/app.exe g"


def test_base_ids(tmpdir):
    path = Path(tmpdir) / "bases.sarif"
    path.write_text(
        '{"runs":[{"tool":{"driver":{"name":"t"}},"originalUriBaseIds":{'
        '"A":{},"B":{},"ROOT":{"uri":"file:///opt/rtems/"}},"artifacts":['
        '{"location":{"uri":"lib.a","uriBaseId":"A"}},'
        '{"location":{"uri":"m.o"},"parentIndex":0},'
        '{"location":{"uri":"lib.a","uriBaseId":"B"}},'
        '{"location":{"uri":"m.o"},"parentIndex":2}],"results":['
        '{"ruleId":"r","message":{"text":"m"},"locations":[{'
        '"physicalLocation":{"artifactLocation":{"index":1}}}]},'
        '{"ruleId":"r","message":{"text":"m"},"locations":[{'
        '"physicalLocation":{"artifactLocation":{"index":3}}}]},'
        '{"ruleId":"r","message":{"text":"m"},"locations":[{'
        '"physicalLocation":{"artifactLocation":{"uri":"cpukit/a.c",'
        '"uriBaseId":"ROOT"}}}]},'
        '{"ruleId":"r","message":{"text":"m"},"locations":[{'
        '"physicalLocation":{"artifactLocation":{"uri":"/x/a.c",'
        '"uriBaseId":"A"}}}]}]}]}',
        encoding="utf-8")
    first, second, rooted, absolute = load([str(path)], ["/opt/rtems"])
    # Equal members of distinct bases are distinct findings
    assert first.artifact.path == "A/lib.a/m.o"
    assert second.artifact.path == "B/lib.a/m.o"
    assert first.identifier != second.identifier
    # A base ID with a URI resolves the relative URI
    assert rooted.artifact.path == "cpukit/a.c"
    # An absolute URI ignores the base ID
    assert absolute.artifact.path == "/x/a.c"


def test_finding_without_location(tmpdir):
    path = Path(tmpdir) / "empty.sarif"
    path.write_text(
        '{"runs":[{"tool":{"driver":{"name":"t"}},"results":[{"ruleId":"r",'
        '"message":{"text":"m"}},{"ruleId":"s","message":{"text":"n"},'
        '"locations":[{"physicalLocation":{"artifactLocation":{}}}]}]}]}',
        encoding="utf-8")
    first, second = load([str(path)], [])
    assert first.artifact.path == "-" and first.location == "-"
    assert second.artifact.path == "-"


def test_relative_path():
    assert relative_path("file:///opt/rtems/a%20b.c", ["/opt/rtems"]) == \
        "a b.c"
    assert relative_path("/opt/x/a.c", ["/opt/rtems"]) == "/opt/x/a.c"


def _sarif(path: Path, source: Path, lines: list[int]) -> None:
    results = ",".join(
        '{"ruleId":"r","message":{"text":"m"},"locations":[{'
        f'"physicalLocation":{{"artifactLocation":{{"uri":"file://{source}"}},'
        f'"region":{{"startLine":{line}}}}}}}]}}' for line in lines)
    path.write_text(
        f'{{"runs":[{{"tool":{{"driver":{{"name":"clang"}}}},'
        f'"results":[{results}]}}]}}',
        encoding="utf-8")


def test_identity(tmpdir):
    base = Path(tmpdir) / "src"
    base.mkdir()
    source = base / "a.c"
    source.write_text("int x;\n  f(  x );\nint y;\nf(x);\n", encoding="utf-8")
    log = Path(tmpdir) / "a.sarif"
    _sarif(log, source, [2, 4, 9])
    first, second, outside = load([str(log)], ["/nil", str(base)])
    assert first.artifact.path == "a.c"
    # The text of a line has each run of white space replaced by one space
    assert first.position.text == "f( x );"
    assert second.position.text == "f(x);"
    assert first.position.ordinal == second.position.ordinal == 0
    assert first.identifier.startswith("CSA-")
    assert len(first.identifier) == 10
    # A line outside of the file has no text
    assert outside.position.text is None
    # The second line with the same text has the next ordinal
    source.write_text("f(x);\nf(x);\n", encoding="utf-8")
    _sarif(log, source, [1, 2])
    first, second = load([str(log)], [str(base)])
    assert first.position.text == second.position.text == "f(x);"
    assert (first.position.ordinal, second.position.ordinal) == (0, 1)
    assert first.identifier != second.identifier
    # A moved line keeps its identifier
    identifier = second.identifier
    source.write_text("int z;\nf(x);\n\nf(x);\n", encoding="utf-8")
    _sarif(log, source, [4])
    (moved, ) = load([str(log)], [str(base)])
    assert moved.line == 4 and moved.identifier == identifier
    # An unknown tool has the first three letters of its name as prefix
    assert Finding("abcd", "r", Artifact("-", "-", None, None), None, "m",
                   Position("-")).identifier.startswith("ABC-")


def test_source_file(tmpdir):
    base = Path(tmpdir)
    (base / "a.c").write_text("", encoding="utf-8")
    assert source_file(Artifact("a.c", "a.c", None, None),
                       [str(base)]) == str(base / "a.c")
    assert source_file(Artifact(str(base / "a.c"), "a.c", None, None),
                       []) == str(base / "a.c")
    assert source_file(Artifact("b.c", "b.c", None, None), [str(base)]) is None
    assert source_file(Artifact("/u", "/u", "/u", None), [str(base)]) is None


def test_identifier_collision(monkeypatch):
    # Two findings with distinct identities and the same identifier are an
    # error, since the report would merge them.
    monkeypatch.setattr(Finding, "identifier", property(lambda self: "X-1"))
    with pytest.raises(ValueError, match=" have the same identifier X-1$"):
        _load("cppcheck/cppcheck.sarif")
    first = Finding("t", "r", Artifact("a", "a", None, None), None, "m",
                    Position("a"))
    keys = {}
    check_identifier(keys, first)
    check_identifier(keys, first)
    assert keys == {"X-1": first.key}
