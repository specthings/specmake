# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the sreldbuilder module. """

# Copyright (C) 2023, 2025 embedded brains GmbH & Co. KG
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

from .util import create_package


def test_sreldbuilder(caplog, tmpdir):
    tmp_dir = Path(tmpdir)
    package = create_package(caplog, tmp_dir, Path("spec-packagebuild"),
                             ["ddf-sreld"])
    director = package.director
    director["/pkg/source/doc-ddf-sreld"].load()
    director.build_package()
    ddf_sreld_build = Path(director["/pkg/build/doc-ddf-sreld"].directory)
    ddf_sreld_index = ddf_sreld_build / "source" / "index.rst"
    with open(ddf_sreld_index, "r", encoding="utf-8") as src:
        assert src.read() == f""".. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2023 embedded brains GmbH & Co. KG

Description 2.

.. _NewlyOpenIssues:

Newly open issues
-----------------

At the time when the package of this version was produced, the following newly open issues with respect to the previous package version were present.

.. raw:: latex

    \\begin{{footnotesize}}

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+---------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                                 |
    +==============+===============================================+=========================================================+
    | RTEMS Ticket | `2548 <https://devel.rtems.org/ticket/2548>`_ | Problematic integer conversion in rtems_clock_get_tod() |
    +--------------+-----------------------------------------------+---------------------------------------------------------+

.. raw:: latex

    \\end{{footnotesize}}

.. _AlreadyOpenIssues:

Already open issues
-------------------

At the time when the package of this version was produced, the following open issues which were newly or already open in the previous package version were present.

.. raw:: latex

    \\begin{{footnotesize}}

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+------------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                                    |
    +==============+===============================================+============================================================+
    | RTEMS Ticket | `2365 <https://devel.rtems.org/ticket/2365>`_ | Task pre-emption disable is broken due to pseudo ISR tasks |
    +--------------+-----------------------------------------------+------------------------------------------------------------+

.. raw:: latex

    \\end{{footnotesize}}

.. _ClosedIssues:

Closed issues
-------------

For this package version, the following issues which were newly or already open in the previous package version were closed.

.. raw:: latex

    \\begin{{footnotesize}}

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                              |
    +==============+===============================================+======================================================+
    | RTEMS Ticket | `2189 <https://devel.rtems.org/ticket/2189>`_ | Insufficient documentation for rtems_clock_get_tod() |
    +--------------+-----------------------------------------------+------------------------------------------------------+

.. raw:: latex

    \\end{{footnotesize}}
"""
