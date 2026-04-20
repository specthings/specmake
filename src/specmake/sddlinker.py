# SPDX-License-Identifier: BSD-2-Clause
""" Links SDD elements to other documents. """

# Copyright (C) 2022 embedded brains GmbH & Co. KG
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

import itertools

from specitems import Item
from specware import CContent

from .directorystate import DirectoryState
from .linkhub import LinkHub, SpecMapper
from .pkgitems import PackageBuildDirector


def _add_variant(content: CContent, variant: dict) -> None:
    with content.doxygen_block():
        content.add(variant["doxygen"])
        for group in variant.get("groups", []):
            content.add(f"@ingroup {group[group.find('/') + 1:]}")
        links = [
            f"[{item.spec}]({item.view['default-document-path']})"
            for item in sorted(variant["items"])
        ]
        line = "This design element is related to"
        content_2 = CContent()
        if len(links) > 1:
            line = f"{line}:"
            content_2.add_list(links, line)
        else:
            content_2.add(f"{line} {links[0]}.")
        content.add_paragraph("Traceability", content_2)


class SDDLinker(DirectoryState):
    """ Links SDD elements to other documents. """

    def __init__(self, director: PackageBuildDirector, item: Item) -> None:
        super().__init__(director, item, SpecMapper("sdd", self, item))

    def run(self):
        content = CContent()
        link_hub = self.input("link-hub")
        assert isinstance(link_hub, LinkHub)
        for _, info in sorted(link_hub.name_info.items()):
            if not isinstance(info, dict):
                continue
            for variant in itertools.chain([info], info.get("variants", [])):
                _add_variant(content, variant)
        content.write(self.file)

        self.description.add(f"""Produce the header file
{self.description.path(self.file)} with links from software design elements to
the specification documents.""")
