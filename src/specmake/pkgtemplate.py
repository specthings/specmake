# SPDX-License-Identifier: BSD-2-Clause
""" Provides package build template items. """

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

import itertools
import logging
import os
import re
from typing import Any, NamedTuple

from specitems import (IS_ENABLED_OPS, Item, is_enabled_with_ops, items,
                       to_iterable)

from . import pkgitems


class _AttributeActionContext(NamedTuple):
    item: pkgitems.BuildItem
    action: dict
    action_value: Any
    value: Any
    name: str
    idx: int
    path: str


def _attribute_action_append(ctx: _AttributeActionContext) -> None:
    logging.info("%s: at %s append: %s", ctx.item.uid, ctx.path,
                 ctx.action_value)
    if ctx.idx >= 0:
        ctx.value[ctx.name][ctx.idx].append(ctx.action_value)
    else:
        ctx.value[ctx.name].append(ctx.action_value)


def _attribute_action_extend(ctx: _AttributeActionContext) -> None:
    logging.info("%s: at %s extend by: %s", ctx.item.uid, ctx.path,
                 ctx.action_value)
    if ctx.idx >= 0:
        ctx.value[ctx.name][ctx.idx] += ctx.action_value
    else:
        ctx.value[ctx.name] += ctx.action_value


def _attribute_action_insert(ctx: _AttributeActionContext,
                             adjustment: int) -> None:
    if ctx.idx >= 0:
        the_list = ctx.value[ctx.name][ctx.idx]
    else:
        the_list = ctx.value[ctx.name]
    for index, the_value in enumerate(the_list):
        if the_value[ctx.action["where-key"]] == ctx.action["where-value"]:
            index += adjustment
            logging.info(
                "%s: at %s insert at index "
                "%i where '%s' is '%s': %s", ctx.item.uid, ctx.path, index,
                ctx.action["where-key"], ctx.action["where-value"],
                ctx.action_value)
            the_list.insert(index, ctx.action_value)
            return
    logging.info("%s: at %s no matching insert position", ctx.item.uid,
                 ctx.path)


def _attribute_action_insert_after(ctx: _AttributeActionContext) -> None:
    _attribute_action_insert(ctx, 1)


def _attribute_action_insert_before(ctx: _AttributeActionContext) -> None:
    _attribute_action_insert(ctx, 0)


def _attribute_action_remove(ctx: _AttributeActionContext) -> None:
    msg = f"{ctx.item.uid}: at {ctx.action['path']} remove: "
    if ctx.idx >= 0:
        logging.info("%s%s", msg, ctx.value[ctx.name][ctx.idx])
        del ctx.value[ctx.name][ctx.idx]
    else:
        logging.info("%s%s", msg, ctx.value[ctx.name])
        del ctx.value[ctx.name]


def _remove_list_items(ctx: _AttributeActionContext,
                       the_list: list[str]) -> list[str]:
    new_list: list[str] = []
    pattern = re.compile(ctx.action["pattern"])
    for value in the_list:
        if pattern.search(value) is None:
            new_list.append(value)
        else:
            logging.info("%s: at %s remove: %s", ctx.item.uid, ctx.path, value)
    return new_list


def _attribute_action_remove_list_items(ctx: _AttributeActionContext) -> None:
    if ctx.idx >= 0:
        ctx.value[ctx.name][ctx.idx] = _remove_list_items(
            ctx, ctx.value[ctx.name][ctx.idx])
    else:
        ctx.value[ctx.name] = _remove_list_items(ctx, ctx.value[ctx.name])


def _attribute_action_set(ctx: _AttributeActionContext) -> None:
    logging.info("%s: at %s set to: %s", ctx.item.uid, ctx.path,
                 ctx.action_value)
    if ctx.idx >= 0:
        ctx.value[ctx.name][ctx.idx] = ctx.action_value
    else:
        ctx.value[ctx.name] = ctx.action_value


def _attribute_action_set_default(ctx: _AttributeActionContext) -> None:
    if ctx.name in ctx.value:
        logging.info("%s: at %s no need for a default value", ctx.item.uid,
                     ctx.path)
    else:
        _attribute_action_set(ctx)


def _attribute_action_substitute(ctx: _AttributeActionContext) -> None:
    if ctx.idx >= 0:
        new_value = ctx.item.substitute(ctx.value[ctx.name][ctx.idx])
        ctx.value[ctx.name][ctx.idx] = new_value
    else:
        new_value = ctx.item.substitute(ctx.value[ctx.name])
        ctx.value[ctx.name] = new_value
    logging.info("%s: at %s substitute to: %s", ctx.item.uid, ctx.path,
                 new_value)


_ATTRIBUTE_ACTIONS = {
    "append": _attribute_action_append,
    "extend": _attribute_action_extend,
    "insert-after": _attribute_action_insert_after,
    "insert-before": _attribute_action_insert_before,
    "remove": _attribute_action_remove,
    "remove-list-items": _attribute_action_remove_list_items,
    "set": _attribute_action_set,
    "set-default": _attribute_action_set_default,
    "substitute": _attribute_action_substitute,
}


def _get_name_and_index(key: str) -> tuple[str, int]:
    parts = key.split("[")
    try:
        return parts[0], int(parts[1].split("]")[0])
    except IndexError:
        return parts[0], -1


def _attribute_action(item: pkgitems.BuildItem, action: dict,
                      data: Any) -> None:
    for path in to_iterable(action["path"]):
        path_list = path.strip("/").split("/")
        value = data
        for key in path_list[:-1]:
            name, index = _get_name_and_index(key)
            if index >= 0:
                value = value[name][index]
            else:
                value = value[name]
        name, index = _get_name_and_index(path_list[-1])
        _ATTRIBUTE_ACTIONS[action["action"]](_AttributeActionContext(
            item, action, item.substitute(action.get("value", None)), value,
            name, index, path))


def _enabled_by_has_type(item: Item, enabled_by: dict, who: str) -> bool:
    value = enabled_by[f"{who}-type"]
    if value is None:
        return True
    if isinstance(value, str):
        return item.type == value
    return item.type in value


class _Template(pkgitems.BuildItem):

    def run_attribute_actions(self, component: pkgitems.PackageComponent,
                              data: Any) -> None:
        """ Run the attribute actions on the data. """

        def _has_sibling(_enabled_set: list[str], enabled_by: Any,
                         _ops: dict) -> bool:
            for parent in component.item.parents(enabled_by["parent-role"]):
                if _enabled_by_has_type(parent, enabled_by, "parent"):
                    for child in parent.children(enabled_by["sibling-role"]):
                        if child == component.item:
                            continue
                        if _enabled_by_has_type(child, enabled_by, "sibling"):
                            return True
            return False

        ops = IS_ENABLED_OPS | {"has-sibling": _has_sibling}
        for action in self.item["attribute-actions"]:
            if not is_enabled_with_ops(component.selection.enabled_set,
                                       action["enabled-by"], ops):
                continue
            _attribute_action(component, action, data)

    def add_item(self, component: pkgitems.PackageComponent, data: dict,
                 new_uids) -> None:
        """ Add an item with the data along the component. """
        uid = f"{os.path.dirname(component.uid)}/{os.path.basename(self.uid)}"
        logging.info("%s: expand template to: %s", self.uid, uid)
        data = component.substitute(data)
        self.run_attribute_actions(component, data)
        component.item.cache.add_item(uid, data, initialize_links=False)
        new_uids.append(uid)

    def expand_template(self, component: pkgitems.PackageComponent,
                        new_uids: list[str]) -> None:
        """ Expand the template for the component. """
        for item in itertools.chain(
                self.item.parents("use-package-template"),
                self.item.children("add-package-template")):
            template_item = self.director[item.uid]
            template_item.expand_template(component, new_uids)


class ComponentTemplate(_Template):
    """ Provides a template for components. """

    def expand_template(self, component: pkgitems.PackageComponent,
                        new_uids: list[str]) -> None:
        self.run_attribute_actions(component, component.item.data)
        super().expand_template(component, new_uids)


class FileItemTemplate(_Template):
    """
    Provides a template for items where the attributes are provided by a file
    referenced by the template item.
    """

    def expand_template(self, component: pkgitems.PackageComponent,
                        new_uids: list[str]) -> None:
        path = component.substitute(self.item["file"])
        data = items.load_data(path)
        self.add_item(component, data, new_uids)
        super().expand_template(component, new_uids)


class InlineItemTemplate(_Template):
    """
    Provides a template for items where the attributes are provided by the
    template item.
    """

    def expand_template(self, component: pkgitems.PackageComponent,
                        new_uids: list[str]) -> None:
        data = self.item["attributes"]
        data["SPDX-License-Identifier"] = self.item["SPDX-License-Identifier"]
        data["copyrights"] = self.item["copyrights"]
        self.add_item(component, data, new_uids)
        super().expand_template(component, new_uids)
