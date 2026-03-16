# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the linkhub module. """

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

from specmake.linkhub import (_name_info_key_default, _link_default,
                              _ref_default, get_kind, SpecMapper)

from .util import create_package, get_and_clear_log


def test_linkhub(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("spec-packagebuild"),
                             ["djf-svs", "link-hub"])
    item_cache = package.item.cache
    director = package.director
    director.build_package()

    with pytest.raises(ValueError, match="no name information"):
        _name_info_key_default(package.item)

    with pytest.raises(ValueError, match="no link"):
        _link_default(package.item, "unused")

    with pytest.raises(ValueError, match="no reference"):
        _ref_default(package.item)

    link_hub = director["/pkg/steps/link-hub"]
    assert link_hub.get_sdd_link(
        "function", "blub"
    ) == f"`blub() <{tmpdir}/pkg/doc-ddf-sdd/html/group__Blub.html#ga754ccc677acbd87ede8b3c082bb9ff6b>`__"
    assert link_hub.get_file_sdd_link(
        "a.c") == f"`a.c <{tmpdir}/pkg/doc-ddf-sdd/html/a_8c.html>`__"
    assert link_hub.get_function_sdd_link(
        "blub"
    ) == f"`blub() <{tmpdir}/pkg/doc-ddf-sdd/html/group__Blub.html#ga754ccc677acbd87ede8b3c082bb9ff6b>`__"

    mapper = SpecMapper("icd", link_hub, link_hub.item)
    assert mapper.substitute(
        "${.:/sdd-define:DISABLED}"
    ) == f"`DISABLED <{tmpdir}/pkg/doc-ddf-sdd/html/group__Blub.html#gabd5c8ab57c190a6522ccdbf0ed7577da>`__"
    assert mapper.substitute(
        "${.:/sdd-enum:the_enum}"
    ) == f"`the_enum <{tmpdir}/pkg/doc-ddf-sdd/html/group__Blub.html#ga582a1afc79f3b607104a52d7aa268624>`__"
    assert mapper.substitute(
        "${.:/sdd-enumerator:ENUMERATOR}"
    ) == f"`ENUMERATOR <{tmpdir}/pkg/doc-ddf-sdd/html/group__Blub.html#gga582a1afc79f3b607104a52d7aa268624a183cf8edbca25c5db49f6fda4224f87a>`__"
    assert mapper.substitute(
        "${.:/sdd-file:a.c}"
    ) == f"`a.c <{tmpdir}/pkg/doc-ddf-sdd/html/a_8c.html>`__"
    assert mapper.substitute(
        "${.:/sdd-function:blub}"
    ) == f"`blub() <{tmpdir}/pkg/doc-ddf-sdd/html/group__Blub.html#ga754ccc677acbd87ede8b3c082bb9ff6b>`__"
    assert mapper.substitute(
        "${.:/sdd-group:GroupA}"
    ) == f"`A <{tmpdir}/pkg/doc-ddf-sdd/html/group__GroupA.html>`__"
    assert mapper.substitute(
        "${.:/sdd:GroupA}"
    ) == f"`A <{tmpdir}/pkg/doc-ddf-sdd/html/group__GroupA.html>`__"
    with pytest.raises(ValueError):
        mapper.substitute("${.:/sdd:DoesNotExist}")
    assert mapper.substitute(
        "${.:/sdd-object:obj}"
    ) == f"`obj <{tmpdir}/pkg/doc-ddf-sdd/html/group__Blub.html#gafc83d933ee990064a19b6b66ccad1800>`__"
    assert mapper.substitute(
        "${.:/sdd-type:Union}"
    ) == f"`Union <{tmpdir}/pkg/doc-ddf-sdd/html/unionUnion.html>`__"

    assert mapper.substitute(
        "${/rtems/if/func:/spec}") == ":ref:`blub() <SpecRtemsIfFunc>`"
    assert mapper.substitute(
        "${/rtems/if/define-disabled:/spec}") == "``DISABLED``"

    assert mapper.make_reference(
        link_hub.item
    ) == ":ref:`spec:/​pkg/​steps/​link-hub <SpecPkgStepsLinkHub>`"
    assert mapper.make_reference(link_hub.item,
                                 "name") == ":ref:`name <SpecPkgStepsLinkHub>`"

    assert mapper.get_link(item_cache["/rtems/if/func"],
                           "icd") == ":ref:`blub() <SpecRtemsIfFunc>`"
    assert mapper.get_link(
        item_cache["/req/root"], "foobar"
    ) == f"`spec:/​req/​root <{tmpdir}/pkg/doc-ts-srs/html/requirements.html#specreqroot>`__"
    assert mapper.get_link(item_cache["/req/disabled"],
                           "foobar") == "spec:/​req/​disabled"
    assert mapper.get_link(item_cache["/rtems/if/forward-decl-disabled"],
                           "foobar") == "``StructOnly``"
    assert mapper.get_link(item_cache["/rtems/if/func-disabled"],
                           "foobar") == "``disabled()``"
    assert mapper.get_link(item_cache["/rtems/if/header-disabled"],
                           "foobar") == "``<blub.h>``"

    assert get_kind(item_cache["/rtems/if/func"]) == "directive"


def test_linkhub_no_test_to_req(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("spec-packagebuild"),
                             ["djf-svs", "link-hub"])
    item_cache = package.item.cache
    item_cache.remove_item("/build/test-suite")
    with pytest.raises(
            ValueError,
            match="no test-case to test-suite to requirement-refinement"):
        package.director.build_package()


def test_linkhub_files_without_group(caplog, tmpdir):
    package = create_package(
        caplog, Path(tmpdir), Path("spec-packagebuild"),
        ["djf-svs", "link-hub", "link-hub-files-without-group"])
    with pytest.raises(ValueError, match="files without group"):
        package.director.build_package()


def test_linkhub_groups_without_items(caplog, tmpdir):
    package = create_package(
        caplog, Path(tmpdir), Path("spec-packagebuild"),
        ["djf-svs", "link-hub", "link-hub-groups-without-items"])
    with pytest.raises(ValueError, match="groups without items"):
        package.director.build_package()


def test_linkhub_no_file(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("spec-packagebuild"),
                             ["djf-svs", "link-hub", "link-hub-no-file"])
    with pytest.raises(ValueError, match="not associated with a file"):
        package.director.build_package()


def test_linkhub_no_tagfile(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("spec-packagebuild"),
                             ["djf-svs", "link-hub", "link-hub-no-tagfile"])
    package.director.build_package()
    link_hub = package.director["/pkg/steps/link-hub"]
    mapper = SpecMapper("icd", link_hub, link_hub.item)
    assert mapper.get_link(
        package.item.cache["/rtems/if/func"], "icd"
    ) == "`spec:/​rtems/​if/​func <https://embedded-brains.de/qdp-support>`__"


def test_linkhub_no_tagfile_qual(caplog, tmpdir):
    package = create_package(
        caplog, Path(tmpdir), Path("spec-packagebuild"),
        ["djf-svs", "link-hub", "link-hub-no-tagfile", "RTEMS_QUAL"])
    with pytest.raises(ValueError, match="there is no associated tagfile"):
        package.director.build_package()
