# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the stdtailoring module. """

# Copyright (C) 2025, 2026 embedded brains GmbH & Co. KG
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

from specitems import ContentContext

from specmake import DocumentBuilder, ECSSAnnex, ECSSClause
from specmake.rtems import get_substitution_errors

from .util import create_package


def test_stdtailoring(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("stdtailoring/spec"))
    director = package.director
    builder = director["/pkg/doc"]
    assert isinstance(builder, DocumentBuilder)
    builder_2 = director["/pkg/doc-2"]
    assert isinstance(builder_2, DocumentBuilder)

    # Check standard and clause references
    assert builder.substitute(
        "${/standard/clause-0:/clause}") == ":ref:`4.3.1.1x <StandardClause0>`"
    # The label drops the bullet, the target does not: a standard cites a
    # clause by its section, and the reference still points at the individual
    # requirement.
    assert builder.substitute("${/standard/clause-0:/clause-section}"
                              ) == ":ref:`4.3.1.1 <StandardClause0>`"
    assert builder.substitute(
        "${/standard/clause-0:/clause-long}"
    ) == ":ref:`4.3.1.1x (Clause 0 name) <StandardClause0>`"
    assert builder.substitute(
        "${/standard/clause-0:/standard-and-clause}"
    ) == ":ref:`ABCD-X-ST-01Y Rev. 42 - 4.3.1.1x <StandardClause0>`"
    assert builder.substitute(
        "${/standard/clause-0:/standard-and-clause-long}"
    ) == ":ref:`ABCD-X-ST-01Y Rev. 42 - 4.3.1.1x (Clause 0 name) <StandardClause0>`"

    # Check the references to a clause of an annex
    assert builder.substitute("${/standard/clause-2:/clause}"
                              ) == ":ref:`B.2.1\\<4.1>a <StandardClause2>`"
    assert builder.substitute("${/standard/clause-2:/clause-section}"
                              ) == ":ref:`B.2.1\\<4.1> <StandardClause2>`"
    assert builder.substitute(
        "${/standard/clause-2:/clause-long}"
    ) == ":ref:`B.2.1\\<4.1>a (Clause 2 name) <StandardClause2>`"
    assert builder.substitute(
        "${/standard/clause-2:/standard-and-clause}"
    ) == ":ref:`ABCD-X-ST-01Y Rev. 42 - B.2.1\\<4.1>a <StandardClause2>`"
    assert builder.substitute(
        "${/standard/clause-2:/standard-and-clause-long}") == (
            ":ref:`ABCD-X-ST-01Y Rev. 42 - B.2.1\\<4.1>a (Clause 2 name) "
            "<StandardClause2>`")

    # Check standard and clause links
    assert builder_2.substitute(
        "${/standard/clause-0:/clause}"
    ) == "`4.3.1.1x <../doc/path/to/ecss/tailoring#standardclause0>`__"
    assert builder_2.substitute(
        "${/standard/clause-0:/standard-and-clause}"
    ) == "`ABCD-X-ST-01Y Rev. 42 - 4.3.1.1x <../doc/path/to/ecss/tailoring#standardclause0>`__"
    with builder_2.component_scope(director["/pkg/component-2"]):
        assert builder_2.substitute(
            "${/standard/clause-0:/clause}"
        ) == "`4.3.1.1x <../doc/path/to/ecss/tailoring-2#standardclause0>`__"
        assert builder_2.substitute(
            "${/standard/clause-0:/standard-and-clause}"
        ) == "`ABCD-X-ST-01Y Rev. 42 - 4.3.1.1x <../doc/path/to/ecss/tailoring-2#standardclause0>`__"

    # Check standard and clause text without a standard tailoring resource
    with builder_2.component_scope(director["/pkg/component-3"]):
        caplog.clear()
        assert builder_2.substitute(
            "${/standard/clause-0:/clause}") == "4.3.1.1x"
        assert builder_2.substitute(
            "${/standard/clause-0:/clause-section}") == "4.3.1.1"
        assert builder_2.substitute(
            "${/standard/clause-0:/standard-and-clause}"
        ) == "ABCD-X-ST-01Y Rev. 42 - 4.3.1.1x"
        warnings = [
            record.getMessage() for record in caplog.records
            if record.levelname == "WARNING"
        ]
        assert warnings == [
            "/pkg/doc-2: there is no resource associated with resource key "
            "'ecss-tailoring', so the ECSS clause references have no link"
        ]

    # A citation takes no content of the clause, a clause name does.  The
    # document registers a mapped part once it has a content context.
    assert isinstance(builder.content_context, ContentContext)
    clause = director["/standard/clause-0"].item
    clause["SPDX-License-Identifier"] = "LicenseRef-X"
    for key in ("clause", "clause-section", "standard-and-clause"):
        builder.substitute(f"${{/standard/clause-0:/{key}}}")
    for key in ("clause-long", "standard-and-clause-long"):
        with pytest.raises(ValueError, match="permits neither"):
            builder.substitute(f"${{/standard/clause-0:/{key}}}")
    clause["SPDX-License-Identifier"] = "CC-BY-SA-4.0"

    # Check standard tailoring
    assert builder.substitute(
        "${.:/standard-tailoring}") == """.. _StandardStandard:

Tailoring of ABCD-X-ST-01Y Rev. 42
----------------------------------

.. list-table:: Compliance matrix of ABCD-X-ST-01Y Rev. 42
    :widths: 13, 12, 13, 12, 13, 12, 13, 12
    :header-rows: 1

    * - Clause
      - Status
      - Clause
      - Status
      - Clause
      - Status
      - Clause
      - Status
    * - 1.2.3.4y
      - .. _CMStandardClause1:

        :ref:`N <StandardClause1>`
      - 4.3.1.1x
      - .. _CMStandardClause0:

        :ref:`Y <StandardClause0>`
      - ​
      - ​
      - ​
      - ​

.. _StandardClause1:

Clause 1 name (1.2.3.4y)
^^^^^^^^^^^^^^^^^^^^^^^^

.. topic:: ABCD-X-ST-01Y Rev. 42 - Clause 1.2.3.4y - ABCD-X-ST-01_clause-1 - Permission

    The clause shall be 1.

.. topic:: Aim

    Aim.

.. topic:: Note

    Note.

.. topic:: Expected Output

    Expected output.

Tailoring Status: N
    No.

For an overview of all clauses, see the :ref:`tailoring table <CMStandardClause1>`.

.. _StandardClause0:

Clause 0 name (4.3.1.1x)
^^^^^^^^^^^^^^^^^^^^^^^^

.. topic:: ABCD-X-ST-01Y Rev. 42 - Clause 4.3.1.1x - ABCD-X-ST-01_clause-0

    The clause shall be 0.

.. topic:: Note 1

    Note 1

.. topic:: Note 2

    Note 2

Tailoring Status: Y
    Yes.

Process
    `Title, Process section <process.html#processlabel>`__ :cite:`PkgDoc` and
    `Title, Group section <../doc-2/group.html#grouplabel>`__ :cite:`PkgDoc2`

Output
    `Title, Output section <output.html#outputlabel>`__ :cite:`PkgDoc`

For an overview of all clauses, see the :ref:`tailoring table <CMStandardClause0>`."""

    # Check the clause traceability of a document
    caplog.clear()
    assert builder.substitute(
        "${.:/ecss-clause-traceability}") == """.. table::
    :class: longtable
    :widths: 30,10,60

    +---------------------------------------+---------+---------------------------------------------------------------+
    | Section                               | Role    | Clauses                                                       |
    +=======================================+=========+===============================================================+
    | :ref:`Process section <ProcessLabel>` | Process | :ref:`ABCD-X-ST-01Y Rev. 42 - 4.3.1.1x <StandardClause0>` (Y) |
    +---------------------------------------+---------+---------------------------------------------------------------+
    | :ref:`Output section <OutputLabel>`   | Output  | :ref:`ABCD-X-ST-01Y Rev. 42 - 4.3.1.1x <StandardClause0>` (Y) |
    +---------------------------------------+---------+---------------------------------------------------------------+"""
    assert ("the citation group member 'doc-unused' serves no tailoring"
            in caplog.text)
    assert "doc-method" not in caplog.text
    assert builder_2.substitute(
        "${.:/ecss-clause-traceability}") == """.. table::
    :class: longtable
    :widths: 30,10,60

    +-----------------------------------+---------+------------------------------------------------------------------------------------------+
    | Section                           | Role    | Clauses                                                                                  |
    +===================================+=========+==========================================================================================+
    | :ref:`Group section <GroupLabel>` | Process | `ABCD-X-ST-01Y Rev. 42 - 4.3.1.1x <../doc/path/to/ecss/tailoring#standardclause0>`__ (Y) |
    +-----------------------------------+---------+------------------------------------------------------------------------------------------+
    | :ref:`Row section <RowLabel>`     | Output  | `ABCD-Y-ST-02 - B.2.1<10>a <../doc/path/to/ecss/tailoring#standard2row1>`__ (Y)          |
    +-----------------------------------+---------+------------------------------------------------------------------------------------------+"""
    assert builder.substitute("${/pkg/group:/cite-group}") == (
        "`Title, Group section <../doc-2/group.html#grouplabel>`__ "
        ":cite:`PkgDoc2`")
    for member in _member_links(builder_2.item):
        del member.data["kind"]
    assert builder_2.substitute("${.:/ecss-clause-traceability}") == (
        "No section of this document serves a tailoring decision.")

    clause = director["/standard/clause-0"]
    assert isinstance(clause, ECSSClause)
    assert director.factory.export_data(clause.item, True, 0) == {
        "SPDX-License-Identifier": "CC-BY-SA-4.0",
        "aim": None,
        "bullet": "x",
        "copyrights": [
            "Copyright (C) 2025 embedded brains GmbH & Co. KG",
        ],
        "ecss-type": "requirement",
        "enabled-by": True,
        "expected-output": None,
        "links": [
            {
                "role": "requirement-refinement",
                "uid": "standard",
            },
        ],
        "name": "Text removed due to license issues",
        "non-functional-type": "ecss",
        "notes": None,
        "rationale": None,
        "references": [],
        "requirement-type": "non-functional",
        "section": "4.3.1.1",
        "text": "Text removed due to license issues.",
        "type": "requirement",
    }

    annex = director["/standard/annex-b"]
    assert isinstance(annex, ECSSAnnex)
    assert director.factory.export_data(annex.item, True, 0) == {
        "SPDX-License-Identifier": "CC-BY-SA-4.0",
        "annex": "B",
        "copyrights": [
            "Copyright (C) 2026 embedded brains GmbH & Co. KG",
        ],
        "enabled-by": True,
        "links": [
            {
                "role": "requirement-refinement",
                "uid": "standard",
            },
        ],
        "name": "Text removed due to license issues",
        "non-functional-type": "ecss-annex",
        "rationale": None,
        "references": [],
        "requirement-type": "non-functional",
        "text": "The ${/glossary/ecss:/term} standard ABCD-X-ST-01Y Rev. 42 "
        "shall contain the\nannex B.\n",
        "type": "requirement",
    }


def test_stdtailoring_substitution_errors(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("stdtailoring/spec"))
    clause = package.item.cache["/standard/clause-1"]

    # The notes of a clause are plain strings and a clause reference needs
    # the context of a document
    clause.data["text"] = ("See ${/standard/clause-0:/clause} and "
                           "${/standard/clause-0:/clause-section}.")
    assert get_substitution_errors(clause) == []

    # The text of a clause has the MyST format
    clause.data["text"] = "See ${/standard/clause-0:/nix}."
    assert [uid for uid, _ in get_substitution_errors(clause)
            ] == ["/standard/clause-1"]


def test_stdtailoring_annexes(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("stdtailoring/spec"))
    builder = package.director["/pkg/doc-2"]

    # A tailoring of a standard or an annex covers each of its clauses which
    # has no tailoring of its own.  An annex without a tailoring is missing.
    assert builder.substitute(
        "${.:/standard-tailoring}") == '''.. _Standard2Standard:

Tailoring of ABCD-Y-ST-02
-------------------------

Tailoring Status: N/A
    The body clauses apply where another standard calls on them.

.. list-table:: Compliance matrix of ABCD-Y-ST-02
    :widths: 13, 12, 13, 12, 13, 12, 13, 12
    :header-rows: 1

    * - Clause
      - Status
      - Clause
      - Status
      - Clause
      - Status
      - Clause
      - Status
    * - 5.2.1a
      - .. _CMStandard2Clause1:

        :ref:`Y <Standard2Clause1>`
      - ​
      - ​
      - ​
      - ​
      - ​
      - ​

.. _Standard2Clause1:

Body 1 (5.2.1a)
^^^^^^^^^^^^^^^

.. topic:: ABCD-Y-ST-02 - Clause 5.2.1a - ABCD-Y-ST-02_clause-1

    The clause clause-1 shall exist.

Tailoring Status: Y
    Yes.

For an overview of all clauses, see the :ref:`tailoring table <CMStandard2Clause1>`.

.. _Standard2StandardAnnexes:

Annexes of ABCD-Y-ST-02
^^^^^^^^^^^^^^^^^^^^^^^

.. _Standard2AnnexA:

Annex A name (Annex A)
""""""""""""""""""""""

Tailoring Status: N/A
    The package does not deliver the document.

.. _Standard2AnnexB:

Annex B name (Annex B)
""""""""""""""""""""""

.. list-table:: Compliance matrix of ABCD-Y-ST-02 Annex B
    :widths: 13, 12, 13, 12, 13, 12, 13, 12
    :header-rows: 1

    * - Clause
      - Status
      - Clause
      - Status
      - Clause
      - Status
      - Clause
      - Status
    * - B.2.1<2.1>b
      - .. _CMStandard2Row2:

        :ref:`N <Standard2Row2>`
      - B.2.1<10>a
      - .. _CMStandard2Row1:

        :ref:`Y <Standard2Row1>`
      - ​
      - ​
      - ​
      - ​

.. _Standard2Row2:

Row 2 (B.2.1<2.1>b)
"""""""""""""""""""

.. topic:: ABCD-Y-ST-02 - Clause B.2.1<2.1>b - ABCD-Y-ST-02_row-2

    The clause row-2 shall exist.

Tailoring Status: N
    No.

For an overview of all clauses, see the :ref:`tailoring table <CMStandard2Row2>`.

.. _Standard2Row1:

Row 1 (B.2.1<10>a)
""""""""""""""""""

.. topic:: ABCD-Y-ST-02 - Clause B.2.1<10>a - ABCD-Y-ST-02_row-1

    The clause row-1 shall exist.

Tailoring Status: Y
    Yes.

Output
    `Title, Row section <row.html#rowlabel>`__ :cite:`PkgDoc2`

For an overview of all clauses, see the :ref:`tailoring table <CMStandard2Row1>`.'''

    def check(match):
        with pytest.raises(ValueError, match=match):
            builder.substitute("${.:/standard-tailoring}")

    # A section which carries the content of a clause is an output
    member = _member_links(builder.item)[1]
    member.data["kind"] = "process"
    check("/pkg/doc-2: the citation group member '/standard-2/row-1' needs "
          "the kind output")
    member.data["kind"] = "output"

    # The tailoring of a clause of an annex is traced even without a member
    statement = package.item.cache["/standard-2/tailoring-row-2"]
    statement.data["text"] = " "
    check("/standard-2/tailoring-row-2: a tailoring status of N needs a "
          "justification")
    statement.data["text"] = "No.\n"

    # A clause needs a tailoring if its standard or annex has none
    row = package.item.cache["/standard-2/row-2"]
    row.child_link("statement-of-compliance").data["role"] = "nix"
    check("/standard-2/row-2: the clause has no tailoring")


def _trace_links(item):
    return list(item.links_to_parents("citation-group-user"))


def _member_links(item):
    return list(item.links_to_parents("citation-group-member"))


def test_stdtailoring_trace_errors(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("stdtailoring/spec"))
    builder = package.director["/pkg/doc"]
    statement = package.item.cache["/standard/tailoring-0"]
    soc = statement.parent_link("statement-of-compliance")
    process, output, _ = _trace_links(statement)

    def check(match):
        with pytest.raises(ValueError, match=match):
            builder.substitute("${.:/standard-tailoring}")

    # A traced tailoring needs an output
    output.data["citation-group-key"] = "doc-process"
    check("a tailoring status of Y needs an output")

    # A method needs a process, an assurance, or a control
    member = _member_links(package.item.cache["/pkg/doc-2"])[0]
    member.data["kind"] = "output"
    process.data["citation-group-key"] = "doc-method"
    output.data["citation-group-key"] = "doc-output"
    check("a method needs a process, an assurance, or a control")
    process.data["citation-group-key"] = "doc-process"
    member.data["kind"] = "process"

    # A member of a traced citation group needs a kind
    output.data["citation-group-key"] = "doc-no-kind"
    check("'doc-no-kind' needs a kind of process, assurance, control, "
          "method, or output")

    # A traced citation group shall not be empty
    output.data["citation-group-key"] = "doc-none"
    check("the citation group 'doc-none' is empty")
    output.data["citation-group-key"] = "doc-output"

    # A status other than Y needs a justification
    soc.data["supplier-status"] = "Ye"
    statement.data["text"] = " "
    check("a tailoring status of Ye needs a justification")
    soc.data["supplier-status"] = "Y"

    # The text of a traced tailoring may cite a group
    statement.data["text"] = "See ${/pkg/component:/cite-group:doc-output}.\n"
    cited = builder.substitute("${/pkg/component:/cite-group:doc-output}")
    assert f"See {cited}." in builder.substitute("${.:/standard-tailoring}")
    statement.data["text"] = "Yes.\n"

    # A citation group item restricts the kinds of its members
    member.data["kind"] = "method"
    check("the member of citation group /pkg/group has the kind 'method', "
          "expected process or output")
