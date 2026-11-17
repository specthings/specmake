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

from specmake import DocumentBuilder, ECSSClause
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

.. topic:: ABCD-X-ST-01Y Rev. 42 - Clause 1.2.3.4y - ABCD-X-ST-01_clause-1

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
    +-----------------------------------+---------+------------------------------------------------------------------------------------------+"""
    assert builder.substitute("${/pkg/group:/cite-group}") == (
        "`Title, Group section <../doc-2/group.html#grouplabel>`__ "
        ":cite:`PkgDoc2`")
    group_member = _member_links(builder_2.item)[0]
    del group_member.data["kind"]
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

    # The text of a traced tailoring does not cite a group
    statement.data["text"] = "${/pkg/component:/cite-group:doc-output}"
    check("shall not use a citation group")
    statement.data["text"] = "Yes.\n"

    # A citation group item restricts the kinds of its members
    member.data["kind"] = "method"
    check("the member of citation group /pkg/group has the kind 'method', "
          "expected process or output")
