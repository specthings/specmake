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

import logging
import os
import textwrap
from typing import Any, Iterator

from specitems import (Item, ItemGetValueContext, Link, TextContent,
                       TextMapper, get_citation_group_members, list_terms)

from .sphinxbuilder import SphinxBuilder, DocumentBuilderValueProvider
from .pkgitems import BuildItem, BuildItemFactory, export_data


def _clause_section(clause: Item) -> str:
    section = clause["section"]
    annex_section = clause.get("annex-section", None)
    if annex_section is None:
        return section
    return f"{section}<{annex_section}>"


def _clause_number(clause: Item) -> str:
    return f"{_clause_section(clause)}{clause['bullet']}"


def _add_compliance_matrix(content: TextContent, name: str,
                           clauses: list[Item]) -> None:
    if not clauses:
        return
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
            the_clause = _clause_number(clause)
            content.append(f"""{star} - {the_clause}
  - .. _CM{clause.ident}:

    :ref:`{link['supplier-status']} <{clause.ident}>`""")
        odd = len(clauses) % 4
        missing = 4 - odd if odd else 0
        content.append(missing * ["  - \u200b", "  - \u200b"])


_MEMBER_ROLE = "citation-group-member"

_TRACE_ROLE = "citation-group-user"

_KINDS = ("process", "assurance", "control", "method", "output")

_PLAN_KINDS = ("process", "assurance", "control")


def _key(link: Link) -> str | None:
    return link.data.get("citation-group-key")


def _group_name(link: Link) -> str:
    return _key(link) or link.uid


def _member_kind(member: Link) -> str:
    kind = member.data.get("kind")
    if kind not in _KINDS:
        raise ValueError(f"{member.item.uid}: the citation group member "
                         f"'{_group_name(member)}' needs a kind "
                         f"of {list_terms(_KINDS, 'or')}")
    return kind


def _trace_members(statement: Item) -> dict[str, list[Link]]:
    by_kind: dict[str, list[Link]] = {kind: [] for kind in _KINDS}
    for trace in statement.links_to_parents(_TRACE_ROLE):
        members = get_citation_group_members(trace.item, _key(trace))
        if not members:
            raise ValueError(f"{statement.uid}: the citation group "
                             f"'{_group_name(trace)}' is empty")
        for member in members:
            by_kind[_member_kind(member)].append(member)
    # A clause is the citation group of the sections which carry its content
    clause = statement.parent("statement-of-compliance")
    for member in get_citation_group_members(clause):
        if _member_kind(member) != "output":
            raise ValueError(f"{member.item.uid}: the citation group member "
                             f"'{clause.uid}' needs the kind output")
        by_kind["output"].append(member)
    return by_kind


def _check_statement(statement: Item, clause: Item, status: str,
                     by_kind: dict[str, list[Link]]) -> None:
    # The tailoring of a clause of an annex is always traced
    if not any(by_kind.values()) and "annex-section" not in clause.data:
        return
    uid = statement.uid
    if status != "Y" and not statement["text"].strip():
        raise ValueError(
            f"{uid}: a tailoring status of {status} needs a justification")
    if status in ("Y", "Ye") and not by_kind["output"]:
        raise ValueError(
            f"{uid}: a tailoring status of {status} needs an output")
    if by_kind["method"] and not any(by_kind[kind] for kind in _PLAN_KINDS):
        raise ValueError(f"{uid}: a method needs a process, an assurance, "
                         "or a control")
    if "cite-group" in statement["text"]:
        raise ValueError(f"{uid}: the text of a traced tailoring shall not "
                         "use a citation group")


def _add_trace(content: TextContent, builder: SphinxBuilder,
               by_kind: dict[str, list[Link]]) -> None:
    for kind in _KINDS:
        members = by_kind[kind]
        if members:
            content.add_definition_item(
                kind.capitalize(),
                list_terms([
                    builder.format_citation_group_member(link)
                    for link in members
                ]))


def _add_topic(content: TextContent, builder: SphinxBuilder, clause: Item,
               topic: str, text: str | None) -> None:
    if text:
        with content.directive("topic", topic):
            content.add(builder.substitute(text, clause))


def _add_clause(content: TextContent, builder: SphinxBuilder, name: str,
                clause: Item) -> None:
    link = clause.child_link("statement-of-compliance")
    status = link["supplier-status"]
    by_kind = _trace_members(link.item)
    _check_statement(link.item, clause, status, by_kind)
    the_clause = _clause_number(clause)
    header = f"{clause['name']} ({the_clause})"
    with content.section(header, label=clause.ident):
        ident = f"{name[:12]}_{os.path.basename(clause.uid)}"
        topic = f"{name} - Clause {the_clause} - {ident}"
        ecss_type = clause.get("ecss-type", "requirement")
        if ecss_type != "requirement":
            topic = f"{topic} - {ecss_type.capitalize()}"
        _add_topic(content, builder, clause, topic, clause["text"])
        _add_topic(content, builder, clause, "Aim", clause["aim"])
        if len(clause["notes"]) == 1:
            _add_topic(content, builder, clause, "Note", clause["notes"][0])
        else:
            for index, note in enumerate(clause["notes"]):
                _add_topic(content, builder, clause, f"Note {index + 1}", note)
        _add_topic(content, builder, clause, "Expected Output",
                   clause["expected-output"])
        content.add_definition_item(
            f"Tailoring Status: {status}",
            builder.substitute(link.item["text"], link.item))
        _add_trace(content, builder, by_kind)
        content.add("For an overview of all clauses, see the "
                    f":ref:`tailoring table <CM{clause.ident}>`.")


_TAILORING_KEY = "ecss-tailoring"


def _served_clauses(member: Link) -> Iterator[tuple[Item, str]]:
    group = member.item
    if group.type == "requirement/non-functional/ecss":
        for link in group.links_to_children("statement-of-compliance"):
            yield group, link["supplier-status"]
        return
    for trace in group.links_to_children(_TRACE_ROLE):
        if (trace.item.type != "statement-of-compliance"
                or _key(trace) != _key(member)):
            continue
        link = trace.item.parent_link("statement-of-compliance")
        yield link.item, link["supplier-status"]


def _standard(item: Item) -> Item:
    # The clause of an annex refines the annex, which refines the standard.
    parent = item.parent("requirement-refinement")
    if parent.type == "requirement/non-functional/ecss-annex":
        return parent.parent("requirement-refinement")
    return parent


def _section_order(section: str) -> tuple[tuple[int, int, str], ...]:
    # The section number of an annex starts with the letter of the annex.
    return tuple((0, int(part), "") if part.isdigit() else (1, 0, part)
                 for part in section.split("."))


def _ecss_order(item: Item) -> tuple:
    return (_section_order(item["section"]),
            _section_order(item.get("annex-section", "0")), item["bullet"])


def _is_tailored(item: Item) -> bool:
    return any(item.links_to_children("statement-of-compliance"))


def _add_statements(content: TextContent, builder: SphinxBuilder,
                    item: Item) -> bool:
    # A tailoring of a standard or an annex covers each of its clauses
    # which has no tailoring of its own.
    covered = False
    for link in item.links_to_children("statement-of-compliance"):
        covered = True
        content.add_definition_item(
            f"Tailoring Status: {link['supplier-status']}",
            builder.substitute(link.item["text"], link.item))
    return covered


def _ecss_children(item: Item, type_name: str) -> list[Item]:
    return [
        child for child in item.children("requirement-refinement")
        if child.type == type_name
    ]


def _tailored_clauses(item: Item, covered: bool) -> list[Item]:
    clauses = sorted(_ecss_children(item, "requirement/non-functional/ecss"),
                     key=_ecss_order)
    if covered:
        return [clause for clause in clauses if _is_tailored(clause)]
    for clause in clauses:
        if not _is_tailored(clause):
            raise ValueError(f"{clause.uid}: the clause has no tailoring")
    return clauses


def _add_clauses(content: TextContent, builder: SphinxBuilder, name: str,
                 matrix_name: str, item: Item) -> None:
    covered = _add_statements(content, builder, item)
    clauses = _tailored_clauses(item, covered)
    _add_compliance_matrix(content, matrix_name, clauses)
    for clause in clauses:
        _add_clause(content, builder, name, clause)


def _add_annexes(content: TextContent, builder: SphinxBuilder, name: str,
                 std: Item) -> None:
    annexes = [
        annex for annex in sorted(_ecss_children(
            std, "requirement/non-functional/ecss-annex"),
                                  key=lambda annex: annex["annex"])
        if _is_tailored(annex) or any(
            _is_tailored(clause) for clause in _ecss_children(
                annex, "requirement/non-functional/ecss"))
    ]
    if not annexes:
        return
    with content.section(f"Annexes of {name}", label=f"{std.ident}Annexes"):
        for annex in annexes:
            letter = annex["annex"]
            with content.section(f"{annex['name']} (Annex {letter})",
                                 label=annex.ident):
                _add_clauses(content, builder, name, f"{name} Annex {letter}",
                             annex)


class StandardTailoringProvider(DocumentBuilderValueProvider):
    """ Provides a statement of compliance and a standard tailoring. """

    def __init__(self, builder: SphinxBuilder) -> None:
        super().__init__(builder)
        self._warned_no_tailoring = False
        mapper = builder.mapper
        for name in [builder.item.type, "pkg/sphinx-section"]:
            mapper.add_get_value(f"{name}:/standard-tailoring",
                                 self._get_standard_tailoring)
        mapper.add_get_value(f"{builder.item.type}:/ecss-clause-traceability",
                             self._get_clause_traceability)
        mapper.add_get_value("requirement/non-functional/ecss:/clause",
                             self._get_ecss_clause,
                             reference=True)
        mapper.add_get_value("requirement/non-functional/ecss:/clause-long",
                             self._get_ecss_clause_long)
        mapper.add_get_value("requirement/non-functional/ecss:/clause-section",
                             self._get_ecss_clause_section,
                             reference=True)
        mapper.add_get_value(
            "requirement/non-functional/ecss:/standard-and-clause",
            self._get_ecss_standard_and_clause,
            reference=True)
        mapper.add_get_value(
            "requirement/non-functional/ecss:/standard-and-clause-long",
            self._get_ecss_standard_and_clause_long)

    def _get_standard_tailoring(self, ctx: ItemGetValueContext) -> str:
        builder = self.builder
        with builder.section_content(ctx) as (content, _):
            assert isinstance(self.mapper, TextMapper)
            for std in builder.item.parents("standard-tailoring"):
                name = builder.substitute(std["name"], std)
                with content.section(f"Tailoring of {name}", label=std.ident):
                    _add_clauses(content, builder, name, name, std)
                    _add_annexes(content, builder, name, std)
            return content.join()

    def _get_clause_traceability(self, ctx: ItemGetValueContext) -> str:
        builder = self.builder
        mapper = builder.mapper
        rows = [["Section", "Role", "Clauses"]]
        for member in ctx.item.links_to_parents(_MEMBER_ROLE):
            if "kind" not in member.data:
                continue
            kind = _member_kind(member)
            clauses: list[tuple[tuple, str]] = []
            for clause, status in _served_clauses(member):
                name = builder.substitute(
                    f"${{{clause.uid}:/standard-and-clause}}")
                clauses.append((_ecss_order(clause), f"{name} ({status})"))
            if not clauses:
                if kind != "method":
                    logging.warning(
                        "%s: the citation group member '%s' serves no "
                        "tailoring", ctx.item.uid, _group_name(member))
                continue
            section = mapper.format_reference(member["name"], member["label"])
            rows.append([
                section,
                kind.capitalize(),
                list_terms([text for _, text in sorted(clauses)])
            ])
        content = mapper.create_content()
        if len(rows) == 1:
            content.add("No section of this document serves a tailoring "
                        "decision.")
        else:
            content.add_grid_table(rows, [30, 10, 60])
        return content.join()

    def _get_clause_reference(self, ctx: ItemGetValueContext,
                              name: str) -> str:
        # A build without the standard tailoring renders the clause as text.
        try:
            self.builder.get_resource(_TAILORING_KEY)
        except KeyError:
            if not self._warned_no_tailoring:
                self._warned_no_tailoring = True
                logging.warning(
                    "%s: there is no resource associated with resource key "
                    "'%s', so the ECSS clause references have no link",
                    self.builder.item.uid, _TAILORING_KEY)
            return name
        return self.get_reference(ctx, _TAILORING_KEY, name, ctx.item.ident)

    def _get_ecss_clause(self, ctx: ItemGetValueContext) -> str:
        return self._get_clause_reference(ctx, _clause_number(ctx.item))

    def _get_ecss_clause_long(self, ctx: ItemGetValueContext) -> str:
        item = ctx.item
        name = f"{_clause_number(item)} ({item['name']})"
        return self._get_clause_reference(ctx, name)

    def _get_ecss_clause_section(self, ctx: ItemGetValueContext) -> str:
        return self._get_clause_reference(ctx, _clause_section(ctx.item))

    def _get_ecss_standard_and_clause(self, ctx: ItemGetValueContext) -> str:
        item = ctx.item
        name = f"{_standard(item)['name']} - {_clause_number(item)}"
        return self._get_clause_reference(ctx, name)

    def _get_ecss_standard_and_clause_long(self,
                                           ctx: ItemGetValueContext) -> str:
        item = ctx.item
        name = (f"{_standard(item)['name']} - {_clause_number(item)} "
                f"({item['name']})")
        return self._get_clause_reference(ctx, name)


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


def _export_annex_data(item: Item, present: bool, built_later: bool) -> Any:
    data = export_data(item, present, built_later)
    name = item.parent("requirement-refinement")["name"]
    text = (f"The ${{/glossary/ecss:/term}} standard {name} shall contain "
            f"the annex {item['annex']}.")
    data["name"] = "Text removed due to license issues"
    data["text"] = "\n".join(textwrap.wrap(text, 77)) + "\n"
    return data


class ECSSAnnex(BuildItem):
    """ Controls the ECSS annex data export. """

    @classmethod
    def prepare_factory(cls, factory: BuildItemFactory,
                        type_name: str) -> None:
        BuildItem.prepare_factory(factory, type_name)
        factory.add_export_data(type_name, _export_annex_data)
