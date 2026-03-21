# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the speccompare module. """

# Copyright (C) 2025 embedded brains GmbH & Co. KG
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

from specmake import DocumentBuilder

from .util import create_package


def test_speccompare(caplog, tmp_path):
    package = create_package(caplog,
                             tmp_path,
                             Path("speccompare/spec"),
                             workspace_dir="speccompare")
    director = package.director
    director.build_only("/pkg/registry")
    builder = director["/pkg/doc"]
    assert isinstance(builder, DocumentBuilder)

    assert builder.substitute(
        "${.:/input/spec-compare-registry/spec-change-log:-2:v0..v3}"
    ) == """.. _L3DoTheB:

Do the B
########

.. _L3DoTheBSpecNew:

spec:/new
*********

This change added the specification item.

.. _L3DoTheC:

Do the C
########

.. _L3DoTheCSpecNew:

spec:/new
*********

.. raw:: latex

    \\begin{footnotesize}

.. code-block:: diff
    :linenos:
    :lineno-start: 1

    @@ -10,5 +10,5 @@ rationale: null
     references: []
     requirement-type: non-functional
     text: |
    -  The bar shall be a buh.
    +  The bar shall be a ups.
     type: requirement

.. raw:: latex

    \\end{footnotesize}

.. _L3DoTheCSpecRoot:

spec:/root
**********

.. raw:: latex

    \\begin{footnotesize}

.. code-block:: diff
    :linenos:
    :lineno-start: 1

    @@ -20,7 +20,7 @@ text: |
       No changes.
       No changes.
       No changes.
    -  The foo shall be a bar.
    +  The foo shall be a buh.
       No changes.
       No changes.
       No changes.

.. raw:: latex

    \\end{footnotesize}

.. raw:: latex

    \\begin{footnotesize}

.. code-block:: diff
    :linenos:
    :lineno-start: 10

    @@ -33,5 +33,5 @@ text: |
       No changes.
       No changes.
       No changes.
    -  More stuff.
    +  Some more stuff.
     type: requirement

.. raw:: latex

    \\end{footnotesize}

.. _L3DoTheE:

Do the E
########

.. _L3DoTheESpecRemove:

spec:/remove
************

This change removed the specification item.

.. _L3DoTheG:

Do the G
########

.. _L3DoTheGSpecOther:

spec:/other
***********

This change added the specification item.

.. _L3DoTheH:

Do the H
########

.. _L3DoTheHSpecMove:

spec:/move
**********

This change removed the specification item.

.. _L3DoTheHSpecStrange:

spec:/strange
*************

This change removed the specification item.

.. _L3DoTheJ:

Do the J
########

.. _L3DoTheJSpecRoot:

spec:/root
**********

.. raw:: latex

    \\begin{footnotesize}

.. code-block:: diff
    :linenos:
    :lineno-start: 1

    @@ -34,4 +34,17 @@ text: |
       No changes.
       No changes.
       Some more stuff.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  Even more stuff.
     type: requirement

.. raw:: latex

    \\end{footnotesize}

.. _L3DoTheK:

Do the K
########

The do the K description.

.. _L3DoTheKSpecRoot:

spec:/root
**********

.. raw:: latex

    \\begin{footnotesize}

.. code-block:: diff
    :linenos:
    :lineno-start: 1

    @@ -34,17 +34,4 @@ text: |
       No changes.
       No changes.
       Some more stuff.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  Even more stuff.
     type: requirement

.. raw:: latex

    \\end{footnotesize}"""
    assert builder.substitute(
        "${.:/input/spec-compare-registry/spec-change-log:0:v1..v2}"
    ) == """.. _L2DoTheH:

Do the H
========

.. _L2DoTheHSpecMove:

spec:/move
----------

This change removed the specification item.

.. _L2DoTheHSpecStrange:

spec:/strange
-------------

This change removed the specification item."""

    with pytest.raises(ValueError):
        builder.substitute(
            "${.:/input/spec-compare-registry/spec-change-log:0:invalid}")

    with pytest.raises(ValueError):
        builder.substitute(
            "${.:/input/spec-compare-registry/spec-change-log:0:v1..invalid}")

    assert builder.substitute(
        "${.:/input/spec-compare-registry/spec-item-changes:0:/root}"
    ) == """The following changes are associated with Name v3.

.. topic:: Do the K

    The do the K description.

.. raw:: latex

    \\begin{footnotesize}

.. code-block:: diff
    :linenos:
    :lineno-start: 1

    @@ -34,17 +34,4 @@ text: |
       No changes.
       No changes.
       Some more stuff.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  No changes.
    -  Even more stuff.
     type: requirement

.. raw:: latex

    \\end{footnotesize}

.. topic:: Do the J

    No commit message.

.. raw:: latex

    \\begin{footnotesize}

.. code-block:: diff
    :linenos:
    :lineno-start: 1

    @@ -34,4 +34,17 @@ text: |
       No changes.
       No changes.
       Some more stuff.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  No changes.
    +  Even more stuff.
     type: requirement

.. raw:: latex

    \\end{footnotesize}

The following changes are associated with Name v1.

.. topic:: Do the C

    No commit message.

.. raw:: latex

    \\begin{footnotesize}

.. code-block:: diff
    :linenos:
    :lineno-start: 1

    @@ -20,7 +20,7 @@ text: |
       No changes.
       No changes.
       No changes.
    -  The foo shall be a bar.
    +  The foo shall be a buh.
       No changes.
       No changes.
       No changes.

.. raw:: latex

    \\end{footnotesize}

.. raw:: latex

    \\begin{footnotesize}

.. code-block:: diff
    :linenos:
    :lineno-start: 10

    @@ -33,5 +33,5 @@ text: |
       No changes.
       No changes.
       No changes.
    -  More stuff.
    +  Some more stuff.
     type: requirement

.. raw:: latex

    \\end{footnotesize}"""

    assert builder.substitute(
        "${.:/input/spec-compare-registry/spec-item-changes:0:/move}"
    ) == "The item was deleted in Name v2."

    assert builder.substitute(
        "${.:/input/spec-compare-registry/spec-item-changes:0:/new}"
    ) == "The item is new in Name v1."

    assert builder.substitute(
        "${.:/input/spec-compare-registry/spec-item-changes:0:/does-not-exist}"
    ) == "There are no changes since Name v0."

    assert builder.substitute(
        "${.:/input/spec-compare-registry/spec-changes-by-scope:0:requirements:v0}"
    ) == """.. raw:: latex

    \\begin{footnotesize}

.. table::
    :class: longtable
    :widths: 80,20

    +-------------------------+--------+
    | Items                   | Status |
    +=========================+========+
    | /move                   | New    |
    +-------------------------+--------+
    | /remove                 | New    |
    +-------------------------+--------+
    | :ref:`/root <SpecRoot>` | New    |
    +-------------------------+--------+
    | /strange                | New    |
    +-------------------------+--------+

.. raw:: latex

    \\end{footnotesize}"""

    assert builder.substitute(
        "${.:/input/spec-compare-registry/spec-changes-by-scope:0:requirements:v3}"
    ) == """.. raw:: latex

    \\begin{footnotesize}

.. table::
    :class: longtable
    :widths: 80,20

    +-------------------------+----------+
    | Items                   | Status   |
    +=========================+==========+
    | :ref:`/root <SpecRoot>` | Modified |
    +-------------------------+----------+

.. raw:: latex

    \\end{footnotesize}"""
