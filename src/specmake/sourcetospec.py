# SPDX-License-Identifier: BSD-2-Clause
""" Converts Doxygen XML content to interface specification files. """

# Copyright (C) 2024, 2025 embedded brains GmbH & Co. KG
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

import dataclasses
import os
import re
from typing import Any, Iterator
from xml.etree import ElementTree


@dataclasses.dataclass
class DoxygenContext:
    """ Represents the Doxygen context. """
    config: dict
    items_by_kind: dict[str, dict[str, "DoxygenItem"]] = dataclasses.field(
        default_factory=dict)
    items_by_name: dict[str, dict[str,
                                  list["DoxygenItem"]]] = dataclasses.field(
                                      default_factory=dict)
    items: dict[str, "DoxygenItem"] = dataclasses.field(default_factory=dict)
    compound_typedefs: dict[str, str] = dataclasses.field(default_factory=dict)


_Data = dict[str, Any]

_INVALID_NAME_CHARS = re.compile(r"[^a-zA-Z0-9]+")

_FUNCTION_POINTER = re.compile(r"([^(]+)\(\*\)\((.*)")


def _strip(text: str | None) -> str | None:
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    return text


def _decl(defs: dict[str, str], index: int) -> str:
    name = f"${{.:/params[{index}]/name}}"
    type_name = defs.get("type", None)
    if type_name is None:
        return name
    mobj = _FUNCTION_POINTER.match(type_name)
    if mobj is not None:
        type_name = mobj.group(1).strip()
        name = f"(*{name})({mobj.group(2)}"
    if type_name.endswith("*"):
        return f"{type_name}{name}"
    return f"{type_name} {name}"


@dataclasses.dataclass
class DoxygenItem:
    """ Represents a Doxygen item. """
    ctx: DoxygenContext
    kind: str
    doxygen_id: str
    name: str
    data: _Data = dataclasses.field(default_factory=lambda: {
        "brief": "",
        "description": ""
    })
    group_ids: list[str] = dataclasses.field(default_factory=list)
    file_ids: set[str] = dataclasses.field(default_factory=set)

    def __lt__(self, other: "DoxygenItem") -> bool:
        return self.doxygen_id < other.doxygen_id

    def __str__(self) -> str:
        fields = ", ".join(f"{field.name}={getattr(self, field.name)!r}"
                           for field in dataclasses.fields(self)
                           if field.name != "ctx")
        return f"{type(self).__name__}({fields})"

    @property
    def uid(self) -> str:
        """ Is the UID of the item. """
        group = self.group
        prefix = os.path.dirname(group.uid)
        name = self.name.lower()
        name = _INVALID_NAME_CHARS.sub("-", name)
        name = name.removeprefix(self.ctx.config["groups"].get(
            group.doxygen_id, {}).get("remove-prefix", ""))
        return os.path.join(prefix, name)

    def uid_relative_to(self, other: str) -> str:
        """ Get the UID of the item relative to the other UID. """
        return os.path.relpath(self.uid, os.path.dirname(other))

    @property
    def file(self) -> "DoxygenFile":
        """ Is the first file of the item. """
        try:
            return next(self.files)
        except StopIteration as err:
            raise ValueError(f"{self.name} has no file: {self}") from err

    @property
    def files(self) -> Iterator["DoxygenFile"]:
        """ Is the files of the item. """
        for file_id in self.file_ids:
            file = self.ctx.items[file_id]
            assert isinstance(file, DoxygenFile)
            yield file

    @property
    def group(self) -> "DoxygenGroup":
        """ Is the first group of the item. """
        try:
            return next(self.groups)
        except StopIteration as err:
            raise ValueError(f"{self.name} has no group: {self}") from err

    @property
    def groups(self) -> Iterator["DoxygenGroup"]:
        """ Is the group set of the item. """
        for group_id in self.group_ids:
            group = self.ctx.items[group_id]
            assert isinstance(group, DoxygenGroup)
            yield group

    @property
    def is_header(self) -> bool:
        """ Indicates if the item is a header file. """
        return False

    def _get_optional_text(self, key: str) -> str | None:
        return _strip(self.data.get(key, None))

    @property
    def brief(self) -> str | None:
        """ Is the brief description of the item. """
        return self._get_optional_text("brief")

    @property
    def description(self) -> str | None:
        """ Is the detailed description of the item. """
        return self._get_optional_text("description")

    @property
    def notes(self) -> str | None:
        """ Is the notes section of the item. """
        return self._get_optional_text("notes")

    def export(self) -> dict:
        """ Export the Doxygen item as specification item data. """
        links: list[dict] = []
        for file in self.files:
            if file.is_header:
                links.append({
                    "role": "interface-placement",
                    "uid": file.uid_relative_to(self.uid)
                })
        for group in self.groups:
            links.append({
                "role": "interface-ingroup",
                "uid": group.uid_relative_to(self.uid)
            })
        data = {
            "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
            "brief": self.brief,
            "copyrights": [],
            "description": self.description,
            "enabled-by": True,
            "index-entries": [],
            "links": links,
            "notes": self.notes,
            "type": "interface"
        }
        data.update(self.ctx.config["data"])
        return data

    def _get_initializer(self) -> str | None:
        body = self.data.get("initializer", None)
        if body is None:
            return None
        return body.replace("&gt;", ">").replace("&lt;", "<")

    def add_function_like_attributes(self, interface_type: str,
                                     data: dict[str, Any]) -> None:
        """ Add function-like attributes to the data. """
        data["name"] = self.name
        data["interface-type"] = interface_type
        params: list[dict] = []
        paramdefs: list[str] = []
        if len(self.data["param"]) == len(self.data["paramdefs"]):
            for index, (param, definition) in enumerate(
                    zip(self.data["param"], self.data["paramdefs"])):
                params.append({
                    "description": param["description"].strip(),
                    "dir": param["dir"],
                    "name": param["name"]
                })
                paramdefs.append(_decl(definition, index))
        else:
            for index, definition in enumerate(self.data["paramdefs"]):
                if definition["type"] == "void":
                    continue
                params.append({
                    "description": None,
                    "dir": None,
                    "name": definition["declname"]
                })
                paramdefs.append(_decl(definition, index))
        data["params"] = params
        type_name = self.data.get("type", None)
        data["definition"] = {
            "default": {
                "attributes": None,
                "body": self._get_initializer(),
                "params": paramdefs,
                "return": None if type_name == "void" else type_name
            },
            "variants": []
        }
        retval = self.data.get("retval", [])
        if "return" in self.data or retval:
            data["return"] = {
                "return":
                _strip(self.data.get("return", None)),
                "return-values": [{
                    "description": info["description"].strip(),
                    "value": info["name"]
                } for info in retval]
            }
        else:
            data["return"] = None

    def add_definition_kind(self, data: dict[str, Any]) -> None:
        """ Adds the definition kind attribute to the data. """
        if self.doxygen_id in self.ctx.compound_typedefs:
            if self.ctx.compound_typedefs[self.doxygen_id] is None:
                data["definition-kind"] = "typedef-only"
            else:
                data["definition-kind"] = f"typedef-and-{self.kind}"
        else:
            data["definition-kind"] = f"{self.kind}-only"


@dataclasses.dataclass
class DoxygenContainer(DoxygenItem):
    """ Represents a Doxygen container item. """
    member_ids: list[str] = dataclasses.field(default_factory=list)

    def members(self) -> Iterator[DoxygenItem]:
        """ Yields the members of the item. """
        for member_id in self.member_ids:
            yield self.ctx.items[member_id]


@dataclasses.dataclass
class DoxygenCompound(DoxygenContainer):
    """ Represents a Doxygen compound item. """

    def export(self) -> dict:
        data = super().export()
        data["name"] = self.name
        data["interface-type"] = self.kind
        self.add_definition_kind(data)
        definition: list[dict] = []
        for member in self.members():
            definition.append({
                "default": {
                    "brief":
                    member.brief,
                    "definition":
                    member.data["definition"].replace(
                        f"{self.name}::{member.name}", "${.:name}"),
                    "description":
                    member.description,
                    "kind":
                    "member",
                    "name":
                    member.name
                },
                "variants": []
            })
        data["definition"] = definition
        return data


@dataclasses.dataclass
class DoxygenDefine(DoxygenItem):
    """ Represents a Doxygen define item. """

    def export(self) -> dict:
        data = super().export()
        if self.data.get("param", []):
            self.add_function_like_attributes("macro", data)
        else:
            data["name"] = self.name
            data["interface-type"] = "define"
            data["definition"] = {
                "default": self._get_initializer(),
                "variants": []
            }
        return data


@dataclasses.dataclass
class DoxygenDir(DoxygenItem):
    """ Represents a Doxygen directory item. """


@dataclasses.dataclass
class DoxygenEnum(DoxygenContainer):
    """ Represents a Doxygen enumeration item. """

    def export(self) -> dict:
        data = super().export()
        data["name"] = self.name
        data["interface-type"] = "enum"
        self.add_definition_kind(data)
        for member in self.members():
            data["links"].append({
                "role": "interface-enumerator",
                "uid": member.uid_relative_to(self.uid)
            })
        return data


@dataclasses.dataclass
class DoxygenEnumValue(DoxygenItem):
    """ Represents a Doxygen enumerator item. """

    def export(self) -> dict:
        data = super().export()
        data["name"] = self.name
        data["interface-type"] = "enumerator"
        data["links"] = []
        return data


@dataclasses.dataclass
class DoxygenFile(DoxygenContainer):
    """ Represents a Doxygen file item. """

    @property
    def uid(self) -> str:
        the_uid = super().uid
        if not self.is_header:
            return the_uid
        basename = os.path.basename(the_uid)[:-2]
        if basename:
            basename = f"header-{basename}"
        else:
            basename = "header"
        return os.path.join(os.path.dirname(the_uid), basename)

    @property
    def is_header(self) -> bool:
        return self.name.endswith(".h")


@dataclasses.dataclass
class DoxygenFunction(DoxygenItem):
    """ Represents a Doxygen function item. """

    def export(self) -> dict:
        data = super().export()
        self.add_function_like_attributes("function", data)
        return data


@dataclasses.dataclass
class DoxygenGroup(DoxygenContainer):
    """ Represents a Doxygen group item. """

    @property
    def uid(self) -> str:
        return self.ctx.config["groups"].get(self.doxygen_id,
                                             {}).get("uid",
                                                     f"/{self.name.lower()}")


@dataclasses.dataclass
class DoxygenStruct(DoxygenCompound):
    """ Represents a Doxygen structure item. """


@dataclasses.dataclass
class DoxygenTypedef(DoxygenItem):
    """ Represents a Doxygen typedef item. """


@dataclasses.dataclass
class DoxygenUnion(DoxygenCompound):
    """ Represents a Doxygen union item. """


@dataclasses.dataclass
class DoxygenVariable(DoxygenItem):
    """ Represents a Doxygen variable item. """


_ITEM_TYPES = {
    "define": DoxygenDefine,
    "dir": DoxygenDir,
    "enum": DoxygenEnum,
    "enumvalue": DoxygenEnumValue,
    "file": DoxygenFile,
    "function": DoxygenFunction,
    "group": DoxygenGroup,
    "struct": DoxygenStruct,
    "typedef": DoxygenTypedef,
    "union": DoxygenUnion,
    "variable": DoxygenVariable
}


@dataclasses.dataclass
class _Scope:
    item: DoxygenItem
    data: Any
    key: str


def _tag_attribute(elem: ElementTree.Element, scope: _Scope,
                   attribute: str) -> _Scope:
    text = elem.text
    scope.data[attribute] = text if text is not None else ""
    return _Scope(scope.item, scope.data, attribute)


def _tag_item(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    item = scope.item.ctx.items[_doxygen_id(elem)]
    if item.kind == "variable" and isinstance(scope.item, DoxygenCompound):
        scope.item.member_ids.append(item.doxygen_id)
    elif item.kind == "enumvalue":
        enum = scope.item
        assert isinstance(enum, DoxygenEnum)
        enum.member_ids.append(item.doxygen_id)

    # Doxygen places the description into multiple files.  Lets hope they are
    # all the same.
    item.data["brief"] = ""
    item.data["description"] = ""
    item.data["param"] = []
    item.data["paramdefs"] = []

    return _Scope(item, item.data, "")


def _tag_add_text(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    text = elem.text
    if text is not None:
        scope.data[scope.key] = f"{scope.data[scope.key]} {text} "
    return scope


def _tag_brief(_elem: ElementTree.Element, scope: _Scope) -> _Scope:
    return _Scope(scope.item, scope.data, "brief")


def _tag_description(_elem: ElementTree.Element, scope: _Scope) -> _Scope:
    return _Scope(scope.item, scope.data, "description")


def _tag_param(_elem: ElementTree.Element, scope: _Scope) -> _Scope:
    paramdef: dict[str, str] = {}
    scope.item.data["paramdefs"].append(paramdef)
    return _Scope(scope.item, paramdef, "")


def _tag_parameteritem(_elem: ElementTree.Element, scope: _Scope) -> _Scope:
    param = {"description": ""}
    scope.item.data[scope.key].append(param)
    return _Scope(scope.item, param, "description")


def _tag_parameterlist(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    kind = elem.attrib["kind"]
    scope.item.data[kind] = []
    return _Scope(scope.item, scope.data, kind)


def _tag_parametername(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    scope.data["name"] = elem.text
    try:
        direction = elem.attrib["direction"]
    except KeyError:
        direction = None
    scope.data["dir"] = direction
    return scope


def _tag_ref(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    text = elem.text
    assert text is not None
    tail = elem.tail
    if tail is not None:
        text += tail
    scope.data[scope.key] += text
    return scope


def _tag_type(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    return _tag_attribute(elem, scope, "type")


def _tag_definition(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    return _tag_attribute(elem, scope, "definition")


def _tag_argsstring(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    return _tag_attribute(elem, scope, "argsstring")


def _tag_initializer(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    return _tag_attribute(elem, scope, "initializer")


def _tag_declname(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    return _tag_attribute(elem, scope, "declname")


def _tag_simplesect(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    return _tag_attribute(elem, scope, elem.attrib["kind"])


def _tag_title(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    return _tag_attribute(elem, scope, "title")


def _tag_sectiondef(elem: ElementTree.Element, scope: _Scope) -> _Scope:
    kind = elem.attrib["kind"]
    more = {"description": ""}
    scope.data[f"section-{kind}"] = more
    return _Scope(scope.item, more, "description")


def _tag_listitem(_elem: ElementTree.Element, scope: _Scope) -> _Scope:
    scope.data[scope.key] = f"{scope.data[scope.key]}\n\n* "
    return scope


_TAG_HANDLER = {
    "argsstring": _tag_argsstring,
    "briefdescription": _tag_brief,
    "compounddef": _tag_item,
    "declname": _tag_declname,
    "definition": _tag_definition,
    "description": _tag_description,
    "detaileddescription": _tag_description,
    "enumvalue": _tag_item,
    "initializer": _tag_initializer,
    "listitem": _tag_listitem,
    "memberdef": _tag_item,
    "para": _tag_add_text,
    "param": _tag_param,
    "parameterdescription": _tag_description,
    "parameteritem": _tag_parameteritem,
    "parameterlist": _tag_parameterlist,
    "parametername": _tag_parametername,
    "ref": _tag_ref,
    "sectiondef": _tag_sectiondef,
    "simplesect": _tag_simplesect,
    "title": _tag_title,
    "type": _tag_type,
}


def _doxygen_id(elem: ElementTree.Element) -> str:
    try:
        return elem.attrib["id"]
    except KeyError:
        return elem.attrib["refid"]


def _relationships(elem: ElementTree.Element, item: DoxygenItem) -> None:
    assert isinstance(item, DoxygenContainer)
    for member_kind in ("enumvalue", "innerfile", "innerclass", "member",
                        "memberdef"):
        for member in elem.findall(f".//{member_kind}"):
            item.member_ids.append(_doxygen_id(member))


_RELATIONSHIP_HANDLER = {"file": _relationships, "group": _relationships}

_TAG_IS_KIND = {"enumvalue"}


def _get_kind_name(elem: ElementTree.Element) -> tuple[str, str]:
    try:
        kind = elem.attrib["kind"]
    except KeyError:
        if elem.tag not in _TAG_IS_KIND:
            raise
        kind = elem.tag
    name_tag = elem.find("name")
    if name_tag is None:
        name_tag = elem.find("compoundname")
    assert name_tag is not None
    name = name_tag.text
    assert name is not None
    return kind, name


_IGNORE = ("programlisting", "preformatted")


def _fill_items(elem: ElementTree.Element, scope: _Scope) -> None:
    if elem.tag in _IGNORE:
        return
    handler = _TAG_HANDLER.get(elem.tag, None)
    if handler is not None:
        scope = handler(elem, scope)
    for child in elem.findall("*"):
        _fill_items(child, scope)


_COMPOUND_TYPEDEF = re.compile(
    r"typedef\s+(enum|struct|union)(\s+[a-zA-Z0-9_]+)?")


def _learn_compound_typedefs(ctx: DoxygenContext,
                             elem: ElementTree.Element) -> None:
    text = " ".join(elem.itertext()).strip()
    mobj = _COMPOUND_TYPEDEF.match(text)
    if mobj:
        ctx.compound_typedefs[elem.attrib["refid"]] = mobj.group(2)


def _gather_doxygen_id_to_item_mappings(ctx: DoxygenContext,
                                        xml_files: list[str]):
    for xml_file in xml_files:
        tree = ElementTree.parse(xml_file)
        for elem in tree.iter():
            if elem.tag == "codeline" and elem.attrib.get(
                    "refkind", None) in ("compound", "member"):
                _learn_compound_typedefs(ctx, elem)
                continue
            try:
                doxygen_id = elem.attrib["id"]
            except KeyError:
                continue
            try:
                kind, name = _get_kind_name(elem)
            except KeyError:
                continue
            item = ctx.items.setdefault(
                doxygen_id, _ITEM_TYPES[kind](ctx, kind, doxygen_id, name))
            ctx.items_by_kind.setdefault(kind, {}).setdefault(doxygen_id, item)
            ctx.items_by_name.setdefault(kind, {}).setdefault(name,
                                                              []).append(item)
            handler = _RELATIONSHIP_HANDLER.get(kind, None)
            if handler is not None:
                handler(elem, item)


def _add_group_associations(ctx: DoxygenContext):
    for group in ctx.items_by_kind["group"].values():
        assert isinstance(group, DoxygenGroup)
        group_id = group.doxygen_id
        for member_id in group.member_ids:
            ctx.items[member_id].group_ids.append(group_id)


def _add_file_associations(ctx: DoxygenContext):
    for file in ctx.items_by_kind["file"].values():
        assert isinstance(file, DoxygenFile)
        for member_id in file.member_ids:
            ctx.items[member_id].file_ids.add(file.doxygen_id)


def _add_group_through_file_associations(ctx: DoxygenContext):
    for kind, items in ctx.items_by_kind.items():
        if kind in ("dir", "group"):
            continue
        for item in items.values():
            if not item.group_ids:
                try:
                    file_item = ctx.items[item.file.doxygen_id]
                    assert isinstance(file_item, DoxygenFile)
                except ValueError:
                    pass
                else:
                    try:
                        item.group_ids.append(file_item.group_ids[0])
                    except IndexError:
                        pass


def doxygen_xml_to_spec(config: dict, xml_files: list[str]) -> DoxygenContext:
    """ Convert Doxygen XML files to specification item data.  """
    ctx = DoxygenContext(config)

    # In the first pass get the Doxygen identifier to item mappings and vice
    # versa.  Associate items with groups.
    _gather_doxygen_id_to_item_mappings(ctx, xml_files)
    _add_group_associations(ctx)
    _add_file_associations(ctx)
    _add_group_through_file_associations(ctx)

    # In the second pass fill the items
    for xml_file in xml_files:
        tree = ElementTree.parse(xml_file)
        _fill_items(tree.getroot(),
                    _Scope(DoxygenItem(ctx, "root", "", ""), {}, ""))

    return ctx
