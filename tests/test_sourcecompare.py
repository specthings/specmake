# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the sourcecompare module. """

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

import pytest
from pathlib import Path

import specitems

from specmake import (DocumentBuilder, DirectoryState, CompareSourcesConfig,
                      compare_sources)

from .util import create_package


def test_sourcecompare(caplog, tmpdir):
    package = create_package(caplog,
                             Path(tmpdir),
                             Path("sourcecompare/spec"),
                             workspace_dir="sourcecompare")
    director = package.director
    current = director["/pkg/current"]
    assert isinstance(current, DirectoryState)
    previous = director["/pkg/previous"]
    assert isinstance(previous, DirectoryState)

    config = CompareSourcesConfig(current=current,
                                  previous=current,
                                  reviews={},
                                  file_to_review={},
                                  renamed={},
                                  label="Label")
    content = specitems.SphinxContent()
    compare_sources(content, config)

.. _LabelFilesWithRTEMSINLINEROUTINEChanges:

Files with RTEMS_INLINE_ROUTINE changes
#######################################

See :ref:`LabelInline`.
    assert str(content) == """.. _LabelUnchangedFiles:

Unchanged files
###############

- changed-no-review.txt

- new.txt

- renamed-to.txt
"""

    config_2 = CompareSourcesConfig(current=current,
                                    previous=previous,
                                    reviews={
                                        "a": {
                                            "subject": "SA",
                                            "text": "TA"
                                        },
                                        "b": {
                                            "subject": "SB",
                                            "text": "TB"
                                        }
                                    },
                                    file_to_review={
                                        "removed-one-review.txt": "a",
                                        "removed-two-reviews.txt": ["a", "b"]
                                    },
                                    renamed={"renamed-from": "renamed-to"},
                                    label="Label")
    content_2 = specitems.SphinxContent()
    compare_sources(content_2, config_2)
    assert str(content_2) == """.. _LabelReviews:

Reviews
#######

.. _LabelA:

SA
**

TA

This review is related to the following removed files:

- :ref:`LabelRemovedOneReviewTxt`

- :ref:`LabelRemovedTwoReviewsTxt`

.. _LabelB:

SB
**

TB

This review is related to the removed file :ref:`LabelRemovedTwoReviewsTxt`.

.. _LabelNewFiles:

New files
#########

.. _LabelNewTxt:

new.txt
*******

.. topic:: WARNING

    This change has no associated review.

.. _LabelRenamedToTxt:

renamed-to.txt
**************

.. topic:: WARNING

    This change has no associated review.

.. _LabelRemovedFiles:

Removed files
#############

.. _LabelRemovedNoReviewTxt:

removed-no-review.txt
*********************

.. topic:: WARNING

    This change has no associated review.

.. _LabelRemovedOneReviewTxt:

removed-one-review.txt
**********************

See :ref:`LabelA`.

.. _LabelRemovedTwoReviewsTxt:

removed-two-reviews.txt
***********************

See the following reviews:

- :ref:`LabelA`

- :ref:`LabelB`

.. _LabelRenamedFromTxt:

renamed-from.txt
****************

.. topic:: WARNING

    This change has no associated review.

.. _LabelFilesWithUnspecificChanges:

Files with unspecific changes
#############################

.. _LabelChangedNoReviewTxt:

changed-no-review.txt
*********************

.. topic:: WARNING

    This change has no associated review.

.. code-block:: diff

    @@ -1,4 +1,4 @@
    -Previous
    +Current
     No changes
     No changes
     No changes

.. _LabelFilesWithRTEMSINLINEROUTINEChanges:

Files with RTEMS_INLINE_ROUTINE changes
#######################################

See :ref:`LabelInline`.

.. _LabelFilesWithRTEMSINLINEROUTINEChangesChangedNoReviewTxt:

changed-no-review.txt
*********************

.. code-block:: diff

    @@ -11,7 +11,7 @@
     No changes
     No changes
     No changes
    -static RTEMS_INLINE_ROUTINE void f(void) {};
    +static inline void f(void) {};
     No changes
     No changes
     No changes

.. _LabelFilesWithChangesInsideOfComments:

Files with changes inside of comments
#####################################

.. _LabelFilesWithChangesInsideOfCommentsChangedNoReviewTxt:

changed-no-review.txt
*********************

.. code-block:: diff

    @@ -24,7 +24,7 @@
     No changes
     No changes
     No changes
    -/* Previous */
    +/* Current */
     No changes
     No changes
     No changes
"""
    builder = director["/pkg/doc"]
    assert isinstance(builder, DocumentBuilder)
    assert builder.substitute("${.:/compare-sources:0:the-source-compare-key}"
                              ) == """.. _LabelReviews:

Reviews
=======

.. _LabelA:

SA
--

TA

This review is related to the following removed files:

- :ref:`LabelRemovedOneReviewTxt`

- :ref:`LabelRemovedTwoReviewsTxt`

.. _LabelB:

SB
--

TB

This review is related to the removed file :ref:`LabelRemovedTwoReviewsTxt`.

.. _LabelNewFiles:

New files
=========

.. _LabelNewTxt:

new.txt
-------

.. topic:: WARNING

    This change has no associated review.

.. _LabelRenamedToTxt:

renamed-to.txt
--------------

.. topic:: WARNING

    This change has no associated review.

.. _LabelRemovedFiles:

Removed files
=============

.. _LabelRemovedNoReviewTxt:

removed-no-review.txt
---------------------

.. topic:: WARNING

    This change has no associated review.

.. _LabelRemovedOneReviewTxt:

removed-one-review.txt
----------------------

See :ref:`LabelA`.

.. _LabelRemovedTwoReviewsTxt:

removed-two-reviews.txt
-----------------------

See the following reviews:

- :ref:`LabelA`

- :ref:`LabelB`

.. _LabelRenamedFromTxt:

renamed-from.txt
----------------

.. topic:: WARNING

    This change has no associated review.

.. _LabelFilesWithUnspecificChanges:

Files with unspecific changes
=============================

.. _LabelChangedNoReviewTxt:

changed-no-review.txt
---------------------

.. topic:: WARNING

    This change has no associated review.

.. code-block:: diff

    @@ -1,4 +1,4 @@
    -Previous
    +Current
     No changes
     No changes
     No changes

.. _LabelFilesWithRTEMSINLINEROUTINEChanges:

Files with RTEMS_INLINE_ROUTINE changes
=======================================

See :ref:`LabelInline`.

.. _LabelFilesWithRTEMSINLINEROUTINEChangesChangedNoReviewTxt:

changed-no-review.txt
---------------------

.. code-block:: diff

    @@ -11,7 +11,7 @@
     No changes
     No changes
     No changes
    -static RTEMS_INLINE_ROUTINE void f(void) {};
    +static inline void f(void) {};
     No changes
     No changes
     No changes

.. _LabelFilesWithChangesInsideOfComments:

Files with changes inside of comments
=====================================

.. _LabelFilesWithChangesInsideOfCommentsChangedNoReviewTxt:

changed-no-review.txt
---------------------

.. code-block:: diff

    @@ -24,7 +24,7 @@
     No changes
     No changes
     No changes
    -/* Previous */
    +/* Current */
     No changes
     No changes
     No changes"""
    with pytest.raises(ValueError):
        builder.substitute("${.:/compare-sources:0:invalid}")
