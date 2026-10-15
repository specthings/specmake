# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the spamrbuilder module. """

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

import pytest

from specmake import SpamrBuilder

from .util import build_document


def test_spamrbuilder(caplog, tmpdir):
    package, text = build_document(caplog, tmpdir, "doc-paf-spamr",
                                   ["aggregate-test-results", "paf-spamr"])
    spamr_builder = package.director["/pkg/deployment/doc-paf-spamr"]
    assert isinstance(spamr_builder, SpamrBuilder)
    assert text.replace("\u200b",
                        "") == r""".. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2026 embedded brains GmbH & Co. KG

.. table::
    :class: longtable
    :widths: 34,36,15,15

    +-+-+-+-+
    | Metric | Value | Threshold | Result |
    +=+=+=+=+
    | Requirement implementation coverage | 3 of 23 requirements | 1 | **NOK** |
    +-+-+-+-+
    | Requirement completeness | 1 of 23 requirements | 0 | **NOK** |
    +-+-+-+-+
    | V&V coverage | 0 of 2 functions | 1 | **NOK** |
    +-+-+-+-+
    | Requirement clarity | 0.08 | 0 | OK |
    +-+-+-+-+
    | Documentation suitability | Y or NA only | 1 | OK |
    +-+-+-+-+
    | Cyclomatic complexity (VG) | 1 of 5 functions | 10 | **NOK** |
    +-+-+-+-+
    | Nesting level | 1 of 5 functions | 5 | **NOK** |
    +-+-+-+-+
    | Lines of code (LOC) | 1 of 2 files | 500 | **NOK** |
    +-+-+-+-+
    | Comment frequency | 2 of 5 functions | 30 % | **NOK** |
    +-+-+-+-+
    | Requirement testability | 34.8 % (8 of 23 requirements) | 80 % | **NOK** |
    +-+-+-+-+
    | SPR/NCR status | 6 open issues | n.a. | n.a. |
    +-+-+-+-+
    | Safety activities adequacy | Y or NA only | 1 | OK |
    +-+-+-+-+
    | User documentation clarity | 0.02 | 0 | **NOK** |
    +-+-+-+-+
    | User documentation completeness | 1 document file, 2 items | 0 | **NOK** |
    +-+-+-+-+
    | User manual suitability | Y or NA only | 1 | OK |
    +-+-+-+-+
    | Milestone tracking | \- | n.a. | n.a. |
    +-+-+-+-+
    | RID/action status | 1 open action | n.a. | n.a. |
    +-+-+-+-+

The package has 23 related requirements. 3 of them have an associated
validation.

The following requirements have no validation:

- /req/glossary

- /req/perf-runtime

- /req/perf-runtime-environment

- /req/perf-runtime-environment-dirty-cache

- /req/perf-runtime-environment-full-cache

- /req/perf-runtime-environment-hot-cache

- /req/perf-runtime-environment-load

- /req/root

- /rtems/req/action

- /rtems/req/action-2

- /rtems/req/define-not-defined

- /rtems/req/func

- /rtems/req/group

- /rtems/req/group-no-identifier

- /rtems/req/perf

- /rtems/req/perf-no-results

- /rtems/target-a

- /testsuites/unit

- /testsuites/validation

- /testsuites/validation-refinement

The quality scanner found an open TBD or TBC in 1 of 23 related requirements.

- /rtems/req/action

Section :ref:`AnnexTBDTBCFindings` lists each finding and each suppression of
the quality scanner.

Test cases cover 0 of 2 functions.

The package has 23 related requirements. 8 of them are verified by test.

.. table::
    :class: longtable
    :widths: 60,20,20

    +-+-+-+
    | Issue database | Open | Closed |
    +=+=+=+
    | Issue | 3 | 1 |
    +-+-+-+
    | RTEMS Ticket | 3 | 0 |
    +-+-+-+

The following RIDs are open:

- `Issue issue 44 <https://www.foo.org/bar?id=44>`_

The actions are the issues with the label MAI in the issue databases.

- Actions issued: 1

- Actions closed: 0

- Actions open: 1

The RIDs are the issues with the label RID in the issue databases.

- RIDs issued: 2

- RIDs closed: 1

- RIDs open: 1

The pre-qualified source code has 671 lines of code and preprocessor
directives.

.. table::
    :class: longtable
    :widths: 40,20,20,20

    +-+-+-+-+
    | Metric | Threshold | Exceeded | Total |
    +=+=+=+=+
    | Cyclomatic complexity (VG) | 10 | 1 | 5 functions |
    +-+-+-+-+
    | Nesting level | 5 | 1 | 5 functions |
    +-+-+-+-+
    | Lines of code (LOC) | 500 | 1 | 2 files |
    +-+-+-+-+
    | Comment frequency | 30 % | 2 | 5 functions |
    +-+-+-+-+

Section :ref:`AnnexCodeMetrics` lists each function and file which exceeds a
threshold. The file
:file:`build/src/spamr/metrixplusplus/metrixplusplus.csv` of the package
contains the values of all regions.

The quality scanner found an open TBD or TBC in 1 document file and in 2 items.
Section :ref:`AnnexTBDTBCFindings` lists each finding and each suppression.

The quality scanner scanned these documents:

- /pkg/source/doc-a

- /pkg/source/doc-b

The tool reported 3 findings. Section :ref:`AnnexCppcheckFindings` lists each
finding.

.. table::
    :class: longtable
    :widths: 80,20

    +-+-+
    | Rule | Findings |
    +=+=+
    | ``syntaxError`` | 1 |
    +-+-+
    | ``variableScope`` | 2 |
    +-+-+

The tool reported 1 finding. Section :ref:`AnnexClangFindings` lists each
finding.

.. table::
    :class: longtable
    :widths: 80,20

    +-+-+
    | Rule | Findings |
    +=+=+
    | ``deadcode.DeadStores`` | 1 |
    +-+-+

.. raw:: latex

    \begin{footnotesize}

.. table::
    :class: longtable
    :widths: 24,38,38

    +-+-+-+
    | Rule | Location | Message |
    +=+=+=+
    | variableScope | cpukit/a.c:3 | The scope of the variable 'x' can be reduced. |
    +-+-+-+
    | syntaxError | /elsewhere/c.c:7 | syntax error |
    +-+-+-+
    | variableScope | cpukit/b.c:9 | The scope of the variable 'y' can be reduced. |
    +-+-+-+

.. raw:: latex

    \end{footnotesize}

.. raw:: latex

    \begin{footnotesize}

.. table::
    :class: longtable
    :widths: 24,38,38

    +-+-+-+
    | Rule | Location | Message |
    +=+=+=+
    | deadcode.DeadStores | cpukit/dev/iovprintf.c:117 | Value stored to 'num' is never read |
    +-+-+-+

.. raw:: latex

    \end{footnotesize}

.. raw:: latex

    \begin{footnotesize}

.. table::
    :class: longtable
    :widths: 15,85

    +-+-+
    | Marker | Location |
    +=+=+
    | TBD | /rtems/req/action:/text |
    +-+-+
    | TBC | /pkg/component:/name |
    +-+-+
    | TBD | /pkg/source/doc-a: source/a.rst:5 |
    +-+-+

.. raw:: latex

    \end{footnotesize}

.. raw:: latex

    \begin{footnotesize}

.. table::
    :class: longtable
    :widths: 15,40,45

    +-+-+-+
    | Marker | Location | Reason |
    +=+=+=+
    | TBC | /pkg/source/doc-a: source/a.rst:9 | The glossary term \*TBC\* names the marker. |
    +-+-+-+

.. raw:: latex

    \end{footnotesize}

:file:`cpukit/a.c`

.. table::
    :class: longtable
    :widths: 44,14,14,14,14

    +-+-+-+-+-+
    | Function | Line | VG | Nesting | Comments |
    +=+=+=+=+=+
    | complex | 10 | **12** | 2 | 4 % |
    +-+-+-+-+-+
    | deep | 50 | 3 | **6** | **50 %** |
    +-+-+-+-+-+

:file:`cpukit/b.c`

.. table::
    :class: longtable
    :widths: 44,14,14,14,14

    +-+-+-+-+-+
    | Function | Line | VG | Nesting | Comments |
    +=+=+=+=+=+
    | chatty | 10 | 1 | 1 | **50 %** |
    +-+-+-+-+-+

.. table::
    :class: longtable
    :widths: 80,20

    +-+-+
    | File | Lines of code |
    +=+=+
    | :file:`cpukit/a.c` | 651 |
    +-+-+"""

    # Check the content without findings and thresholds
    tools = ("clang-analyzer", "cppcheck", "quality-scanner")
    spamr_builder.__dict__["_findings"] = dict((tool, []) for tool in tools)
    thresholds = dict((key, None) for key in spamr_builder._thresholds)
    spamr_builder.__dict__["_thresholds"] = thresholds
    mapper = spamr_builder.mapper
    for name, text in (
        ("annex-cppcheck-findings", "The tool reported no finding."),
        ("annex-clang-analyzer-findings", "The tool reported no finding."),
        ("annex-quality-scanner-findings",
         "The quality scanner found no open TBD or TBC."),
        ("annex-quality-scanner-suppressions",
         "No finding of the quality scanner is suppressed."),
        ("annex-functions", "No function exceeds a threshold."),
        ("annex-files", "No file exceeds the threshold."),
    ):
        assert mapper.substitute(f"${{.:/{name}}}") == text
    spamr_builder.__dict__["_issues"] = []
    assert mapper.substitute("${.:/sprs-and-ncrws}") == "No RID is open."
    spamr_builder.__dict__["_requirements"] = []
    assert mapper.substitute(
        "${.:/requirement-implementation-and-vv-coverage}"
    ) == """The package has 0 related requirements. 0 of them have an associated
validation."""
    assert mapper.substitute("${.:/requirements-completeness}") == \
        "The quality scanner found an open TBD or TBC in 0 of 0 related " \
        "requirements.\n\nSection :ref:`AnnexTBDTBCFindings` lists each " \
        "finding and each suppression of\nthe quality scanner."
    assert mapper.substitute("${.:/cppcheck-results}") == """The tool \
reported 0 findings. Section :ref:`AnnexCppcheckFindings` lists each
finding."""
    assert "suppressed" not in mapper.substitute(
        "${.:/user-documentation-completeness}")
    assert mapper.substitute("${.:/metrics-overview}").count("n.a.") == 34

    # Check that a metric with a threshold needs a verdict
    thresholds["requirement-clarity"] = 0
    del spamr_builder.item.data["metric-verdicts"]["requirement-clarity"]
    with pytest.raises(ValueError):
        mapper.substitute("${.:/metrics-overview}")
