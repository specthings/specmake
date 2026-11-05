# SPDX-License-Identifier: BSD-2-Clause
""" Provides the validated items related to a specification root. """

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

from typing import Callable, Iterable

from specitems import Item
from specware import (get_items_by_type_map, get_item_types_by_prefix,
                      get_items_by_types, get_interface_items,
                      get_interface_and_requirement_items,
                      get_requirement_items, validate)

from .pkgitems import BuildItem, PackageBuildDirector


class SpecItemCacheBase(BuildItem):
    """ Provides the items related to the root of a specification. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self.item_cache = self.item.cache
        self.related_items: set[Item] = set()
        self.related_items_by_type: dict[str, list[Item]] = {}

    def get_spec_root(self) -> Item:
        """ Get the root of the specification. """
        return self.item_cache[self["spec-root-uid"]]

    def validate_tree(self, validator: Callable[[Item, bool], bool]) -> None:
        """
        Validate the specification from its root with the validator.

        The validation sets the views of the related items.
        """
        self.related_items = validate(self.get_spec_root(), validator)
        self.related_items_by_type = get_items_by_type_map(self.related_items)

    def get_related_items_by_type(self,
                                  types: str | Iterable[str]) -> list[Item]:
        """ Get related items by a list of types. """
        return get_items_by_types(self.related_items_by_type, types)

    def get_related_types_by_prefix(
        self,
        prefix: str | tuple[str, ...],
        exclude: tuple[str, ...] = tuple()
    ) -> list[str]:
        """
        Get the types of the related items having one of the type prefixes.
        """
        return get_item_types_by_prefix(self.related_items_by_type, prefix,
                                        exclude)

    def get_related_interfaces(self) -> list[Item]:
        """ Get the related interfaces. """
        return get_interface_items(self.related_items_by_type)

    def get_related_requirements(self) -> list[Item]:
        """ Get the related requirements. """
        return get_requirement_items(self.related_items_by_type)

    def get_related_interfaces_and_requirements(self) -> list[Item]:
        """ Get the related interfaces and requirements. """
        return get_interface_and_requirement_items(self.related_items_by_type)


def _validate_without_test_results(_item: Item, validated: bool) -> bool:
    return validated


class SpecItemCache(SpecItemCacheBase):
    """ Validates the specification without test results. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self.validate_tree(_validate_without_test_results)

    def run(self) -> None:
        self.description.add("""Validate the specification items without test
results.""")
