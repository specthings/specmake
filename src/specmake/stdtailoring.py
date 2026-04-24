# SPDX-License-Identifier: BSD-2-Clause
""" Provides an item value provider for standard tailoring. """

# Copyright (C) 2025, 2026 embedded brains GmbH & Co. KG
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

import os
from typing import Any

from specitems import (Item, ItemGetValueContext, ItemValueProvider,
                       TextContent, TextMapper)

from .sphinxbuilder import SphinxBuilder
from .pkgitems import BuildItem, BuildItemFactory, BuildItemMapper, export_data


def _add_compliance_matrix(content: TextContent, name: str,
                           clauses: list[Item]) -> None:
    table_name = f"Compliance matrix of {name}"
    options = [":widths: 13, 12, 13, 12, 13, 12, 13, 12", ":header-rows: 1"]
    with content.directive("list-table", table_name, options):
        content.add("""* - Clause
  - Status
  - Clause
  - Status
  - Clause
  - Status
  - Clause
  - Status""")
        for index, clause in enumerate(clauses):
            star = "*" if index % 4 == 0 else " "
            link = clause.child_link("statement-of-compliance")
            the_clause = f"{clause['section']}{clause['bullet']}"
            content.append(f"""{star} - {the_clause}
  - .. _CM{clause.ident}:

    :ref:`{link['supplier-status']} <{clause.ident}>`""")
        odd = len(clauses) % 4
        missing = 4 - odd if odd else 0
        content.append(missing * ["  - \u200b", "  - \u200b"])


def _add_topic(content: TextContent, builder: SphinxBuilder, clause: Item,
               topic: str, text: str | None) -> None:
    if text:
        with content.directive("topic", topic):
            content.add(builder.substitute(text, clause))


def _add_clause(content: TextContent, builder: SphinxBuilder, name: str,
                clause: Item) -> None:
    link = clause.child_link("statement-of-compliance")
    the_clause = f"{clause['section']}{clause['bullet']}"
    header = f"{clause['name']} ({the_clause})"
    with content.section(header, label=clause.ident):
        ident = f"{name[:12]}_{os.path.basename(clause.uid)}"
        _add_topic(content, builder, clause,
                   f"{name} - Clause {the_clause} - {ident}", clause["text"])
        _add_topic(content, builder, clause, "Aim", clause["aim"])
        if len(clause["notes"]) == 1:
            _add_topic(content, builder, clause, "Note", clause["notes"][0])
        else:
            for index, note in enumerate(clause["notes"]):
                _add_topic(content, builder, clause, f"Note {index + 1}", note)
        _add_topic(content, builder, clause, "Expected Output",
                   clause["expected-output"])
        content.add_definition_item(
            f"Tailoring Status: {link['supplier-status']}",
            builder.substitute(link.item["text"], link.item))
        content.add("For an overview of all clauses, see the "
                    f":ref:`tailoring table <CM{clause.ident}>`.")


def _ecss_order(item: Item) -> list:
    return [int(i) for i in item["section"].split(".")] + [item["bullet"]]


class StandardTailoringProvider(ItemValueProvider):
    """ Provides a statement of compliance and a standard tailoring. """

    # pylint: disable=too-few-public-methods

    def __init__(self, builder: SphinxBuilder) -> None:
        super().__init__(builder.mapper)
        self._builder = builder
        self._whoami = builder["document-key"]
        self._tailoring: dict[str, tuple[str, str]] = {}
        mapper = builder.mapper
        for name in [builder.item.type, "pkg/sphinx-section"]:
            mapper.add_get_value(f"{name}:/standard-tailoring",
                                 self._get_standard_tailoring)
        mapper.add_get_value("requirement/non-functional/ecss:/clause",
                             self._get_ecss_clause)
        mapper.add_get_value(
            "requirement/non-functional/ecss:/standard-and-clause",
            self._get_ecss_standard_and_clause)

    def _get_standard_tailoring(self, ctx: ItemGetValueContext) -> str:
        builder = self._builder
        with builder.section_level_scope(ctx):
            assert isinstance(self.mapper, TextMapper)
            content = self.mapper.create_content(
                section_level=builder.section_level)
            for std in builder.item.parents("standard-tailoring"):
                name = builder.substitute(std["name"], std)
                with content.section(f"Tailoring of {name}", label=std.ident):
                    clauses = list(
                        sorted(std.children("requirement-refinement"),
                               key=_ecss_order))
                    _add_compliance_matrix(content, name, clauses)
                    for clause in clauses:
                        _add_clause(content, builder, name, clause)
            return content.join()

    def _get_link(self, ctx: ItemGetValueContext, name: str) -> str:
        component = self._builder.component
        tailoring = self._tailoring.get(component.uid)
        if tailoring is None:
            document, path = component.get_document("ecss-tailoring")
            tailoring = (document["document-key"], path)
            self._tailoring[component.uid] = tailoring
        mapper = ctx.mapper
        assert isinstance(mapper, BuildItemMapper)
        if self._whoami == tailoring[0]:
            return mapper.format_reference(name, ctx.item.ident)
        return mapper.format_link(name,
                                  f"{tailoring[1]}#{ctx.item.ident.lower()}")

    def _get_ecss_standard_and_clause(self, ctx: ItemGetValueContext) -> str:
        item = ctx.item
        name = item.parent("requirement-refinement")["name"]
        name = f"{name} {item['section']}{item['bullet']}"
        return self._get_link(ctx, name)

    def _get_ecss_clause(self, ctx: ItemGetValueContext) -> str:
        item = ctx.item
        name = f"{item['section']}{item['bullet']}"
        return self._get_link(ctx, name)


def _export_data(item: Item, present: bool, built_later: bool) -> Any:
    data = export_data(item, present, built_later)
    for key in ("aim", "expected-output", "notes"):
        data[key] = None
    data["name"] = "Text removed due to license issues"
    data["text"] = "Text removed due to license issues."
    return data


class ECSSClause(BuildItem):
    """ Controls the ECSS data export. """

    @classmethod
    def prepare_factory(cls, factory: BuildItemFactory,
                        type_name: str) -> None:
        BuildItem.prepare_factory(factory, type_name)
        factory.add_export_data(type_name, _export_data)
