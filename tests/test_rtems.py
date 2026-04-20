# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the rtems module. """

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

import pytest

from specmake import RTEMSItemCache

from tests import util


def test_rtems_item_cache(caplog, tmpdir):
    package = util.create_package(caplog, Path(tmpdir),
                                  Path("spec-packagebuild"),
                                  ["aggregate-test-results"])
    director = package.director

    # Check RTEMSPackageComponent build description
    component = director["/pkg/component"]
    component.run()
    assert str(
        component.description) == """Provide settings for the RTEMS-specific
component.
"""

    # Check RTEMS item cache services
    director.build_package()
    rtems_item_cache = director["/pkg/steps/rtems-item-cache"]
    assert isinstance(rtems_item_cache, RTEMSItemCache)
    related_items = rtems_item_cache.get_related_items_by_type("test-case")
    assert [item.uid for item in related_items] == [
        "/rtems/val/test-case", "/rtems/val/test-case-fail",
        "/rtems/val/test-case-pass", "/rtems/val/test-case-run",
        "/rtems/val/test-case-unit", "/rtems/val/test-case-xfail"
    ]
    related_items = rtems_item_cache.get_related_items_by_type(["test-case"])
    assert [item.uid for item in related_items] == [
        "/rtems/val/test-case", "/rtems/val/test-case-fail",
        "/rtems/val/test-case-pass", "/rtems/val/test-case-run",
        "/rtems/val/test-case-unit", "/rtems/val/test-case-xfail"
    ]
    related_types = rtems_item_cache.get_related_types_by_prefix("requirement")
    assert related_types == [
        "requirement/functional/action", "requirement/functional/function",
        "requirement/functional/interface-define-not-defined",
        "requirement/non-functional/design",
        "requirement/non-functional/design-group",
        "requirement/non-functional/design-target",
        "requirement/non-functional/interface-requirement",
        "requirement/non-functional/performance",
        "requirement/non-functional/performance-runtime",
        "requirement/non-functional/performance-runtime-environment",
        "requirement/non-functional/quality"
    ]
    related_items = rtems_item_cache.get_related_interfaces()
    assert [item.uid for item in related_items] == [
        "/c/if/uint32_t", "/req/api", "/rtems/if/acfg-integer",
        "/rtems/if/define-duplicate", "/rtems/if/define-not-defined",
        "/rtems/if/define-real", "/rtems/if/define-second-duplicate",
        "/rtems/if/domain", "/rtems/if/enum-real", "/rtems/if/enumerator",
        "/rtems/if/enumerator-2", "/rtems/if/forward-decl", "/rtems/if/func",
        "/rtems/if/group", "/rtems/if/group-2", "/rtems/if/group-a",
        "/rtems/if/group-acfg", "/rtems/if/group-b", "/rtems/if/header",
        "/rtems/if/header-2", "/rtems/if/obj", "/rtems/if/reg-block",
        "/rtems/if/reg-block-2", "/rtems/if/struct", "/rtems/if/struct-both",
        "/rtems/if/struct-only", "/rtems/if/typedef", "/rtems/if/union",
        "/rtems/if/union-both", "/rtems/if/union-only",
        "/rtems/if/unspec-define", "/rtems/if/unspec-enum",
        "/rtems/if/unspec-enumerator", "/rtems/if/unspec-function",
        "/rtems/if/unspec-group", "/rtems/if/unspec-header",
        "/rtems/if/unspec-macro", "/rtems/if/unspec-object",
        "/rtems/if/unspec-struct", "/rtems/if/unspec-typedef",
        "/rtems/if/unspec-union"
    ]
    related_items = rtems_item_cache.get_related_requirements()
    assert [item.uid for item in related_items] == [
        "/glossary/group", "/req/glossary", "/req/perf-runtime",
        "/req/perf-runtime-environment",
        "/req/perf-runtime-environment-dirty-cache",
        "/req/perf-runtime-environment-full-cache",
        "/req/perf-runtime-environment-hot-cache",
        "/req/perf-runtime-environment-load", "/req/root",
        "/req/usage-constraints", "/rtems/req/action", "/rtems/req/action-2",
        "/rtems/req/define-not-defined", "/rtems/req/func", "/rtems/req/group",
        "/rtems/req/group-no-identifier", "/rtems/req/mem-basic",
        "/rtems/req/perf", "/rtems/req/perf-no-results", "/rtems/target-a",
        "/testsuites/unit", "/testsuites/validation",
        "/testsuites/validation-refinement"
    ]
    related_items = rtems_item_cache.get_related_interfaces_and_requirements()
    assert [item.uid for item in related_items] == [
        "/c/if/uint32_t", "/glossary/group", "/req/api", "/req/glossary",
        "/req/perf-runtime", "/req/perf-runtime-environment",
        "/req/perf-runtime-environment-dirty-cache",
        "/req/perf-runtime-environment-full-cache",
        "/req/perf-runtime-environment-hot-cache",
        "/req/perf-runtime-environment-load", "/req/root",
        "/req/usage-constraints", "/rtems/if/acfg-integer",
        "/rtems/if/define-duplicate", "/rtems/if/define-not-defined",
        "/rtems/if/define-real", "/rtems/if/define-second-duplicate",
        "/rtems/if/domain", "/rtems/if/enum-real", "/rtems/if/enumerator",
        "/rtems/if/enumerator-2", "/rtems/if/forward-decl", "/rtems/if/func",
        "/rtems/if/group", "/rtems/if/group-2", "/rtems/if/group-a",
        "/rtems/if/group-acfg", "/rtems/if/group-b", "/rtems/if/header",
        "/rtems/if/header-2", "/rtems/if/obj", "/rtems/if/reg-block",
        "/rtems/if/reg-block-2", "/rtems/if/struct", "/rtems/if/struct-both",
        "/rtems/if/struct-only", "/rtems/if/typedef", "/rtems/if/union",
        "/rtems/if/union-both", "/rtems/if/union-only",
        "/rtems/if/unspec-define", "/rtems/if/unspec-enum",
        "/rtems/if/unspec-enumerator", "/rtems/if/unspec-function",
        "/rtems/if/unspec-group", "/rtems/if/unspec-header",
        "/rtems/if/unspec-macro", "/rtems/if/unspec-object",
        "/rtems/if/unspec-struct", "/rtems/if/unspec-typedef",
        "/rtems/if/unspec-union", "/rtems/req/action", "/rtems/req/action-2",
        "/rtems/req/define-not-defined", "/rtems/req/func", "/rtems/req/group",
        "/rtems/req/group-no-identifier", "/rtems/req/mem-basic",
        "/rtems/req/perf", "/rtems/req/perf-no-results", "/rtems/target-a",
        "/testsuites/unit", "/testsuites/validation",
        "/testsuites/validation-refinement"
    ]
    assert rtems_item_cache.substitute(
        "${/pkg/issue/issue:/name}"
    ) == "`Issue issue 42 <https://www.foo.org/bar?id=42>`__"

    # Check RTEMS item cache workspace digest handling
    digest = rtems_item_cache._hash
    del director["/pkg/steps/rtems-item-cache"]
    rtems_item_cache = director["/pkg/steps/rtems-item-cache"]
    assert rtems_item_cache._hash == digest
    rtems_item_cache.item.cache["/req/root"].data[
        "workspace-digest"] = "foobar"
    del director["/pkg/steps/rtems-item-cache"]
    rtems_item_cache = director["/pkg/steps/rtems-item-cache"]
    assert rtems_item_cache._hash != digest


def test_rtems_item_cache_errors(caplog, tmpdir):
    package = util.create_package(
        caplog, Path(tmpdir), Path("spec-packagebuild"),
        ["aggregate-test-results", "rtems-item-cache-errors"])
    director = package.director
    match = (r"duplicate defines specified by "
             r"/rtems/if/define-third-duplicate and /rtems/if/define-real")
    with pytest.raises(ValueError, match=match):
        director["/pkg/steps/rtems-item-cache"]
    package.item.cache.remove_item("/rtems/if/define-third-duplicate")
    match = (r"items /rtems/if/enum-real and /rtems/if/enum-duplicate "
             r"specify the same interface group: the_enum")
    with pytest.raises(ValueError, match=match):
        director["/pkg/steps/rtems-item-cache"]
