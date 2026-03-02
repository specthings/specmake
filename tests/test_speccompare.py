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
import specitems

from specmake import (DocumentBuilder, DirectoryState, CompareSpecsConfig,
                      compare_specs)

from .util import create_package


def test_sourcecompare(caplog, tmpdir):
    package = create_package(caplog,
                             Path(tmpdir),
                             Path("speccompare/spec"),
                             workspace_dir="speccompare")
    director = package.director
    repo = director["/pkg/repo"]
    assert isinstance(repo, DirectoryState)
    config = CompareSpecsConfig(
        repository=repo,
        root_uid="/root",
        current_revision="fe7782fc29caf331d9cf4d61592f5769d124318d",
        previous_revision="eb06e17a1a44e22dc3b44dbd857da379cab2f51f",
        ignored_commits=["9a2e490f8c74e720b9d827030e0c3f89bc75052c"],
        spec_paths=["spec", "other"],
        selection=repo.component.selection,
        enabled_set_actions=[{
            "action": "add",
            "enabled-by": False,
            "value": []
        }],
        label="L")
    content = specitems.SphinxContent()
    compare_specs(content, config)
    assert str(content) == """.. _LDoTheB:

Do the B
########

.. _LDoTheBSpecNew:

spec:/new
*********

This change added the specification item.

.. _LDoTheC:

Do the C
########

.. _LDoTheCSpecNew:

spec:/new
*********

.. code-block:: diff

    @@ -10,5 +10,5 @@ rationale: null
     references: []
     requirement-type: non-functional
     text: |
    -  The bar shall be a buh.
    +  The bar shall be a ups.
     type: requirement

.. _LDoTheCSpecRoot:

spec:/root
**********

.. code-block:: diff

    @@ -20,7 +20,7 @@ text: |
       No changes.
       No changes.
       No changes.
    -  The foo shall be a bar.
    +  The foo shall be a buh.
       No changes.
       No changes.
       No changes.

.. code-block:: diff

    @@ -33,5 +33,5 @@ text: |
       No changes.
       No changes.
       No changes.
    -  More stuff.
    +  Some more stuff.
     type: requirement

.. _LDoTheE:

Do the E
########

.. _LDoTheESpecRemove:

spec:/remove
************

This change removed the specification item.

.. _LDoTheG:

Do the G
########

.. _LDoTheGSpecOther:

spec:/other
***********

This change added the specification item.

.. _LDoTheH:

Do the H
########

.. _LDoTheHSpecMove:

spec:/move
**********

This change removed the specification item.

.. _LDoTheHSpecStrange:

spec:/strange
*************

This change removed the specification item.

.. _LDoTheJ:

Do the J
########

.. _LDoTheJSpecRoot:

spec:/root
**********

.. code-block:: diff

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

.. _LDoTheK:

Do the K
########

.. _LDoTheKSpecRoot:

spec:/root
**********

.. code-block:: diff

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
"""
    builder = director["/pkg/doc"]
    assert isinstance(builder, DocumentBuilder)
    assert builder.substitute(
        "${.:/compare-specs:0:the-spec-compare-key}") == """.. _LDoTheH:

Do the H
========

.. _LDoTheHSpecMove:

spec:/move
----------

This change removed the specification item.

.. _LDoTheHSpecStrange:

spec:/strange
-------------

This change removed the specification item."""
    with pytest.raises(ValueError):
        builder.substitute("${.:/compare-specs:0:invalid}")
