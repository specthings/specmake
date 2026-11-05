# SPDX-License-Identifier: BSD-2-Clause
""" Tests of the spec-tree substitution of the specdocbuilder module. """

# Copyright (C) 2026 embedded brains GmbH & Co. KG
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

from pathlib import Path

import pytest

from .util import create_package

_LICENSE = {
    "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
    "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"]
}


def _requirement(parents: list[str], rationale: str | None = "Why.") -> dict:
    return _LICENSE | {
        "enabled-by":
        True,
        "links": [{
            "role": "requirement-refinement",
            "uid": parent
        } for parent in parents],
        "non-functional-type":
        "design",
        "rationale":
        rationale,
        "references": [],
        "requirement-type":
        "non-functional",
        "text":
        "It shall be.",
        "type":
        "requirement"
    }


def _validation(target: str, method: str) -> dict:
    return _LICENSE | {
        "enabled-by": True,
        "links": [{
            "role": "validation",
            "uid": target
        }],
        "method": method,
        "references": [],
        "text": f"It is validated {method}.",
        "type": "validation"
    }


_ITEMS = {
    "/tree/alpha": _requirement(["/req/root"]),
    "/tree/beta": _requirement(["/tree/alpha"]),
    "/tree/gamma": _requirement(["/tree/alpha"], None),
    "/tree/delta": _requirement(["/tree/beta"]),
    "/tree/val/beta": _validation("/tree/beta", "by-inspection"),
    "/tree/val/delta": _validation("/tree/delta", "by-analysis"),
    "/tree/val/gamma": _validation("/tree/gamma", "by-review-of-design"),
    "/tree/chain-0": _requirement(["/req/root"]),
    "/tree/odd": _requirement(["/req/root"]),
    "/tree/odd-child": _requirement(["/tree/odd"]),
}
for _index in range(1, 9):
    _ITEMS[f"/tree/chain-{_index}"] = _requirement(
        [f"/tree/chain-{_index - 1}"])
_TYPES = {
    "/tree/val/beta": "validation/by-inspection",
    "/tree/val/delta": "validation/by-analysis",
    "/tree/val/gamma": "validation/by-review-of-design",
    "/tree/odd-child": "requirement/non-functional/unknown",
}


def _document(caplog, tmp_path):
    package = create_package(caplog, tmp_path, Path("spec-packagebuild"),
                             ["spec-tree"])
    cache = package.item.cache
    cache.add_items(_ITEMS)
    for uid in _ITEMS:
        cache[uid].type = _TYPES.get(uid, "requirement/non-functional/design")
    return package.director["/pkg/deployment/doc-spec"]


def _sections(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("spec:/")]


def test_spec_tree(caplog, tmp_path):
    doc = _document(caplog, tmp_path)
    spec = doc.input("spec")
    spec.run()
    assert "without test" in spec.description.join()
    text = doc.substitute("${.:/spec-tree:0:/tree/alpha}")
    assert _sections(text) == [
        "spec:/tree/alpha", "spec:/tree/beta", "spec:/tree/delta",
        "spec:/tree/val/delta", "spec:/tree/val/beta", "spec:/tree/gamma",
        "spec:/tree/val/gamma"
    ]
    assert "spec:/tree/alpha\n================\n" in text
    assert "spec:/tree/beta\n---------------\n" in text
    assert "spec:/tree/val/delta\n\"\"\"\"" in text
    assert "spec:/tree/val/beta\n^^^^" in text
    assert ".. _SpecTreeAlpha:" in text
    assert "design requirement\n    ``spec:/\u200breq/\u200broot``." in text
    assert ("refines the design requirement\n"
            "    :ref:`spec:/\u200btree/\u200balpha <SpecTreeAlpha>`.") in text
    assert "It is validated by-inspection." in text
    assert "It is validated by-review-of-design." in text
    assert text.count("Rationale") == 3
    assert "Changes" not in text


def test_spec_tree_levels(caplog, tmp_path):
    doc = _document(caplog, tmp_path)
    text = doc.substitute("${.:/spec-tree:0:/tree/chain-0}")
    headings = [
        line[0] for line in text.splitlines()[1:]
        if line and line == len(line) * line[0] and line[0] in "=-~^\"'"
    ]
    assert len(headings) == 9
    assert len(set(headings[5:])) == 1


def test_spec_tree_errors(caplog, tmp_path):
    doc = _document(caplog, tmp_path)
    with pytest.raises(ValueError, match="requirement/non-functional/unknown"):
        doc.substitute("${.:/spec-tree:0:/tree/odd}")
    with pytest.raises(ValueError, match="/tree/nil"):
        doc.substitute("${.:/spec-tree:0:/tree/nil}")
