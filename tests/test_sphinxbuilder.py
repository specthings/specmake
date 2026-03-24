# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the sphinxbuilder module. """

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

import logging
import os
from pathlib import Path

import pytest
from specitems import ItemGetValueContext

import specmake
from specmake import PackageComponent

from .util import create_package


def _set_enabled_set(item: PackageComponent, enabled_set: list[str]) -> None:
    logging.critical("%s: set enabled set: %s", item.uid, enabled_set)
    item["enabled-set"] = enabled_set
    item.selection.reset(enabled_set)
    for link in item.item.links_to_children("input"):
        child = item.director[link.item.uid]
        if isinstance(child, PackageComponent):
            _set_enabled_set(child, enabled_set)


def _run_command(args, cwd=None, stdout=None):
    logging.info("run command: %s", " ".join(args))
    if args == ["python3", "-msphinx", "-M", "clean", "source", "build"]:
        return 0
    if args == ["python3", "-msphinx", "-M", "latexpdf", "source", "build"]:
        os.makedirs(os.path.join(cwd, "build/latex"))
        open(os.path.join(cwd, "build/latex/document.pdf"), "w+").close()
        return 0
    if args == ["python3", "-msphinx", "-M", "html", "source", "build"]:
        os.makedirs(os.path.join(cwd, "build/html"))
        open(os.path.join(cwd, "build/html/index.html"), "w+").close()
        return 0
    return 1


def test_sphinxbuilder(caplog, tmpdir, monkeypatch):
    monkeypatch.setattr(specmake.sphinxbuilder, "run_command", _run_command)
    tmp_dir = Path(tmpdir)
    package = create_package(caplog, tmp_dir, Path("spec-packagebuild"),
                             ["sphinx-builder"])
    director = package.director
    doc = director["/pkg/deployment/doc"]
    doc.substitute("${.:/document-author}") == "embedded brains GmbH & Co. KG"
    doc.substitute("${.:/document-year}") == "2020"
    doc.substitute(
        "${.:/document-copyright}") == "2020 embedded brains GmbH & Co. KG"
    doc.item["document-copyrights"].append("Copyright (C) 2023 John Doe")
    doc.substitute("${.:/document-author}"
                   ) == "embedded brains GmbH & Co. KG and contributors"
    doc.substitute("${.:/document-copyright}"
                   ) == "2020 embedded brains GmbH & Co. KG and contributors"
    doc.item["document-copyrights"].pop()
    assert doc.substitute(
        "${.:/document-title-page-title}") == "The \\break \\break Title"
    doc_title = doc.item["document-title"]
    doc.item["document-title"] = "012345678901234/678901234/6789"
    assert doc.substitute(
        "${.:/document-title-page-title}"
    ) == "012345678901234 \\break \\break /678901234/6789"
    doc.item["document-title"] = doc_title
    doc_src = director["/pkg/source/doc"]
    doc_src.load()
    doc_build = Path(director["/pkg/build/doc"].directory)
    assert not (doc_build / "source" / "copy.rst").exists()
    with pytest.raises(ValueError):
        doc.substitute("${.:/subprocess:args=error}}")
    director.build_package()
    assert (doc_build / "source" / "copy.rst").is_file()
    doc_result = doc_build / "source" / "copy-and-substitute.rst"
    with open(doc_result, "r", encoding="utf-8") as src:
        assert src.read() == f""".. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2023 embedded brains GmbH & Co. KG

footer
2020 embedded brains GmbH \\& Co. KG
footer right
geometry
header left
sphinxsetup
The Title
The Title
2
The \\break \\break Title
:term:`Term`
:term:`Terms <Term>`
text
`spec:/​rtems/​if/​func <https://embedded-brains.de/qdp-support>`__
text
``DISABLED``
text
`spec:/​pkg/​deployment/​doc <https://embedded-brains.de/qdp-support>`__
.. _SectionHeader:

Section content: sub-arch

.. _PkgSourceDocSubsection:

Subsection Header
^^^^^^^^^^^^^^^^^

Subsection content: sparc


Push component content: sub-arch

.. _subsection 2 Header:

subsection 2 Header
^^^^^^^^^^^^^^^^^^^

Subsection content: sub-arch

subsection 2 Header
text
:ref:`SectionHeader`
text
:ref:`PkgSourceDocSubsection`
text
  Element content: sparc
- Element 2 Header

  Element 2 content: sparc

- Element 3 Header

  Element 3 content: sub-arch
text
:cite:`PkgDeploymentDoc`
text
*The Title* :cite:`PkgDeploymentDoc`
text
@manual{{PkgDeploymentDoc,
  author = {{{{Bar, Foo and Doe, John and Long Name, This is a}}}},
  organization = {{{{Bár Organization, Short, Some Organization}}}},
  title = {{{{The Title}}}},
  url = {{{tmp_dir}/pkg/doc/doc.pdf}},
  year = {{2020}},
}}
text
"""
    doc_index = doc_build / "source" / "index.rst"
    with open(doc_index, "r", encoding="utf-8") as src:
        assert src.read() == """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2023 embedded brains GmbH & Co. KG

.. begin subcomponent list depth 0

.. end subcomponent list depth 0

.. begin subcomponent list depth 1
sub and sub-b
.. end subcomponent list depth 1

2020 embedded brains GmbH & Co. KG

embedded brains GmbH & Co. KG

| © 2023 Alice
| © 2020, 2025 embedded brains GmbH & Co. KG

| © 2023 Bob
| © 2023 embedded brains GmbH & Co. KG

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

The Title
*********

.. topic:: Release: 2, Date: 2020-10-26, Status: Draft

    * 2020 embedded brains GmbH & Co. KG

    * e

.. topic:: Release: 1, Date: 1970-01-01, Status: Replaced

    Initial release.

.. _Release2Date20201026StatusDraft:

Release: 2, Date: 2020-10-26, Status: Draft
-------------------------------------------

* 2020 embedded brains GmbH & Co. KG

* e

.. _Release1Date19700101StatusReplaced:

Release: 1, Date: 1970-01-01, Status: Replaced
----------------------------------------------

Initial release.

.. table::
    :class: longtable
    :widths: 16 26 30 28

    +--------------+---------------------+-------------------+-----------+
    | Action       | Name                | Organization      | Signature |
    +==============+=====================+===================+===========+
    | Written by   | John Doe            | Some Organization |           |
    +              +---------------------+-------------------+-----------+
    |              | Foo Bar             | Bár Organization  |           |
    +--------------+---------------------+-------------------+-----------+
    | Super Action | This is a Long Name | Short             |           |
    +--------------+---------------------+-------------------+-----------+

.. toctree::
    :maxdepth: 4
    :numbered:

    copy-and-substitute
    glossary
"""
    doc_glossary = doc_build / "source" / "glossary.rst"
    with open(doc_glossary, "r", encoding="utf-8") as src:
        assert src.read() == """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2023 Alice
.. Copyright (C) 2020 embedded brains GmbH & Co. KG

.. _TermsDefinitionsAndAbbreviatedTerms:

Terms, definitions and abbreviated terms
########################################

.. glossary::

    Term
        This is the term.
"""
    doc_deployment = director["/pkg/deployment/doc"]
    assert doc_deployment["copyrights-by-license"] == {
        "BSD-2-Clause": [
            "Copyright (C) 2023 Bob",
            "Copyright (C) 2023 embedded brains GmbH & Co. KG"
        ]
    }

    _set_enabled_set(package, ["sphinx-builder-2"])
    doc_2 = director["/pkg/deployment/doc-2"]
    doc_2.substitute("${.:/document-bsd-2-clause-copyrights}") == "\n"

    assert doc_2.section_level == 2
    with doc_2.section_level_scope(
            ItemGetValueContext(doc_2.item, "", "", None, None, {})) as args:
        assert doc_2.section_level == 3
        assert args == None
        with doc_2.section_level_scope(
                ItemGetValueContext(doc_2.item, "", "-1", None, None,
                                    {})) as args:
            assert doc_2.section_level == 2
            assert args == None
        assert doc_2.section_level == 3
    with doc_2.section_level_scope(
            ItemGetValueContext(doc_2.item, "", "2:mo:re", None, None,
                                {})) as args:
        assert doc_2.section_level == 4
        assert args == "mo:re"
    assert doc_2.section_level == 2

    doc_2.item["document-components"].append({
        "action": "foobar",
        "add-to-index": False,
        "value": 123
    })
    action_run = 0

    def action(_source_dir, _build_dir, component):
        nonlocal action_run
        action_run += 1
        assert component["value"] == 123

    doc_2.add_component_action("foobar", action)
    director.build_package()
    assert action_run == 1

    # Test make SphinxBuilder
    subcomponent = director["/pkg/sub/component"]
    _set_enabled_set(package, ["make"])
    director.build_package()
    doc_make_build = Path(director["/pkg/build/doc-make"].directory)
    doc_make_result = doc_make_build / "source" / "make.rst"
    with open(doc_make_result, "r", encoding="utf-8") as src:
        assert src.read() == f""".. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2024 embedded brains GmbH & Co. KG

bar
{tmp_dir}/pkg/build/src/doc
{tmp_dir}/pkg/build/doc-make
sparc/gr712rc/smp/4
"""
