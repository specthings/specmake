# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the stdtailoring module. """

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

from specmake import DocumentBuilder

from .util import create_package


def test_stdtailoring(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("stdtailoring/spec"))
    director = package.director
    builder = director["/pkg/doc"]
    assert isinstance(builder, DocumentBuilder)
    assert builder.substitute(
        "${/standard/clause-0:/clause}") == ":ref:`4.3.1.1x <StandardClause0>`"
    assert builder.substitute(
        "${/standard/clause-0:/standard-and-clause}"
    ) == ":ref:`ABCD-X-ST-01Y Rev. 42 4.3.1.1x <StandardClause0>`"
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

For an overview of all clauses, see the :ref:`tailoring table <CMStandardClause0>`."""
