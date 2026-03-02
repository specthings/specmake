# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the pkgitems module related to the build ordering. """

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
# POSSIBILITY OF SUCH DAMAGE.

import logging
from pathlib import Path

from specitems import Item, Link

from specmake import BuildItem, PackageBuildDirector

from .util import create_package


class _TestItem(BuildItem):

    _order: list[str] = []

    def __init__(self, director: PackageBuildDirector, item: Item) -> None:
        super().__init__(director, item)
        _TestItem._order.append(f"C:{item.uid}")

    def has_changed(self, link: Link) -> bool:
        status = super().has_changed(link)
        if status:
            _TestItem._order.append(f"M:{self.uid}")
        else:
            _TestItem._order.append(f"U:{self.uid}")
        return status

    def is_present(self) -> bool:
        return self.item.view.get("present", True)

    def run(self) -> None:
        _TestItem._order.append(f"R:{self.uid}")
        self.item.view["present"] = True
        try:
            output = self.output("destination")
        except KeyError:
            pass
        else:
            output.item.view["present"] = True
            output.item["values"]["generation"] += 1

    @classmethod
    def pop_order(cls) -> list[str]:
        order = cls._order
        cls._order = []
        return order


def test_build_order(caplog, tmpdir):
    package = create_package(caplog, Path(tmpdir), Path("spec-build-order"))
    director = package.director
    director.factory.add_constructor("pkg/test", _TestItem)

    b = director["/b"].item
    c = director["/c"].item
    d = director["/d"].item
    e = director["/e"].item
    f = director["/f"].item
    g = director["/g"].item
    h = director["/h"].item
    i = director["/i"].item
    j = director["/j"].item
    k = director["/k"].item
    l = director["/l"].item
    assert _TestItem.pop_order() == [
        "C:/b",
        "C:/c",
        "C:/d",
        "C:/e",
        "C:/f",
        "C:/g",
        "C:/h",
        "C:/i",
        "C:/j",
        "C:/k",
        "C:/l",
    ]

    logging.critical("initial package build")
    director.clear()
    director.build_package()
    assert _TestItem.pop_order() == [
        "C:/l",
        "C:/k",
        "R:/l",
        "C:/e",
        "R:/e",
        "C:/g",
        "C:/h",
        "R:/g",
        "C:/f",
        "M:/g",
        "R:/f",
        "C:/j",
        "M:/k",
        "C:/i",
        "R:/j",
        "C:/d",
        "M:/e",
        "M:/f",
        "R:/d",
        "C:/c",
        "M:/d",
        "R:/c",
        "C:/b",
        "M:/d",
        "R:/b",
        "C:/a",
        "M:/b",
        "M:/c",
        "M:/h",
        "M:/i",
        "R:/a",
    ]

    logging.critical("second package build")
    director.clear()
    director.build_package()
    assert _TestItem.pop_order() == [
        "C:/l",
        "C:/k",
        "C:/e",
        "C:/g",
        "C:/h",
        "C:/f",
        "U:/g",
        "C:/j",
        "U:/k",
        "C:/i",
        "C:/d",
        "U:/e",
        "U:/f",
        "C:/c",
        "U:/d",
        "C:/b",
        "U:/d",
        "C:/a",
        "U:/b",
        "U:/c",
        "U:/h",
        "U:/i",
    ]

    logging.critical("package build with /d changed")
    director.clear()
    d["values"]["generation"] += 1
    director.build_package()
    assert _TestItem.pop_order() == [
        "C:/l",
        "C:/k",
        "C:/e",
        "C:/g",
        "C:/h",
        "C:/f",
        "U:/g",
        "C:/j",
        "U:/k",
        "C:/i",
        "C:/d",
        "U:/e",
        "U:/f",
        "C:/c",
        "M:/d",
        "R:/c",
        "C:/b",
        "M:/d",
        "R:/b",
        "C:/a",
        "M:/b",
        "M:/c",
        "U:/h",
        "U:/i",
        "R:/a",
    ]

    logging.critical("build only /a")
    director.clear()
    director.build_only(["/a"])
    assert _TestItem.pop_order() == [
        "C:/g",
        "C:/h",
        "C:/l",
        "C:/k",
        "C:/j",
        "U:/k",
        "C:/i",
        "C:/f",
        "U:/g",
        "C:/e",
        "C:/d",
        "U:/e",
        "U:/f",
        "C:/b",
        "U:/d",
        "C:/c",
        "U:/d",
        "C:/a",
        "U:/b",
        "U:/c",
        "U:/h",
        "U:/i",
    ]

    logging.critical("build only /a forced")
    director.clear()
    director.build_only(["/a"], force_patterns=["/a"])
    assert _TestItem.pop_order() == [
        "C:/g",
        "C:/h",
        "C:/l",
        "C:/k",
        "C:/j",
        "U:/k",
        "C:/i",
        "C:/f",
        "U:/g",
        "C:/e",
        "C:/d",
        "U:/e",
        "U:/f",
        "C:/b",
        "U:/d",
        "C:/c",
        "U:/d",
        "C:/a",
        "U:/b",
        "U:/c",
        "U:/h",
        "U:/i",
        "R:/a",
    ]

    logging.critical("build only /a with /d changed")
    director.clear()
    d["values"]["generation"] += 1
    director.build_only("/a")
    assert _TestItem.pop_order() == [
        "C:/g",
        "C:/h",
        "C:/l",
        "C:/k",
        "C:/j",
        "U:/k",
        "C:/i",
        "C:/f",
        "U:/g",
        "C:/e",
        "C:/d",
        "U:/e",
        "U:/f",
        "C:/b",
        "M:/d",
        "R:/b",
        "C:/c",
        "M:/d",
        "R:/c",
        "C:/a",
        "M:/b",
        "M:/c",
        "U:/h",
        "U:/i",
        "R:/a",
    ]

    logging.critical("build only /a with /c changed and /i not present")
    director.clear()
    c["values"]["generation"] += 1
    i.view["present"] = False
    director.build_only("/a")
    assert _TestItem.pop_order() == [
        "C:/g",
        "C:/h",
        "C:/l",
        "C:/k",
        "C:/j",
        "U:/k",
        "C:/i",
        "C:/f",
        "U:/g",
        "C:/e",
        "C:/d",
        "U:/e",
        "U:/f",
        "C:/b",
        "U:/d",
        "C:/c",
        "U:/d",
        "C:/a",
        "U:/b",
        "M:/c",
        "U:/h",
        "U:/i",
        "U:/k",
        "R:/j",
        "R:/a",
    ]

    logging.critical("build only /a with /k changed and /l not present")
    director.clear()
    k["values"]["generation"] += 1
    l.view["present"] = False
    director.build_only("/a")
    assert _TestItem.pop_order() == [
        "C:/g",
        "C:/h",
        "C:/l",
        "C:/k",
        "C:/j",
        "M:/k",
        "C:/i",
        "R:/j",
        "C:/f",
        "U:/g",
        "C:/e",
        "C:/d",
        "U:/e",
        "U:/f",
        "C:/b",
        "U:/d",
        "C:/c",
        "U:/d",
        "C:/a",
        "U:/b",
        "U:/c",
        "U:/h",
        "M:/i",
        "R:/a",
    ]

    logging.critical(
        "build only /a with /k changed and not present and /l not present")
    director.clear()
    k["values"]["generation"] += 1
    k.view["present"] = False
    l.view["present"] = False
    director.build_only("/a")
    assert _TestItem.pop_order() == [
        "C:/g",
        "C:/h",
        "C:/l",
        "C:/k",
        "C:/j",
        "M:/k",
        "C:/i",
        "R:/l",
        "R:/j",
        "C:/f",
        "U:/g",
        "C:/e",
        "C:/d",
        "U:/e",
        "U:/f",
        "C:/b",
        "U:/d",
        "C:/c",
        "U:/d",
        "C:/a",
        "U:/b",
        "U:/c",
        "U:/h",
        "M:/i",
        "R:/a",
    ]

    logging.critical("build only /a with all other items not present")
    director.clear()
    b.view["present"] = False
    c.view["present"] = False
    d.view["present"] = False
    e.view["present"] = False
    f.view["present"] = False
    g.view["present"] = False
    h.view["present"] = False
    i.view["present"] = False
    j.view["present"] = False
    k.view["present"] = False
    l.view["present"] = False
    director.build_only("/a")
    assert _TestItem.pop_order() == [
        "C:/g",
        "C:/h",
        "C:/l",
        "C:/k",
        "C:/j",
        "U:/k",
        "C:/i",
        "C:/f",
        "U:/g",
        "C:/e",
        "C:/d",
        "U:/e",
        "U:/f",
        "C:/b",
        "U:/d",
        "C:/c",
        "U:/d",
        "C:/a",
        "U:/b",
        "U:/c",
        "U:/h",
        "U:/i",
    ]

    logging.critical(
        "build only /a with all other items not present and /g changed")
    director.clear()
    g["values"]["generation"] += 1
    director.build_only("/a")
    assert _TestItem.pop_order() == [
        "C:/g",
        "C:/h",
        "C:/l",
        "C:/k",
        "C:/j",
        "U:/k",
        "C:/i",
        "C:/f",
        "M:/g",
        "R:/g",
        "R:/f",
        "C:/e",
        "C:/d",
        "U:/e",
        "M:/f",
        "R:/e",
        "R:/d",
        "C:/b",
        "M:/d",
        "R:/b",
        "C:/c",
        "M:/d",
        "R:/c",
        "C:/a",
        "M:/b",
        "M:/c",
        "M:/h",
        "U:/i",
        "U:/k",
        "R:/l",
        "R:/j",
        "R:/a",
    ]
