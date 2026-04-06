# SPDX-License-Identifier: BSD-2-Clause
""" Document specification items. """

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

from specitems import (EmptyItemCache, Item, ItemCache, ItemGetValueContext,
                       ItemTypeProvider, ItemValueProvider, SpecDocumentConfig,
                       SpecTypeProvider, TextMapper,
                       add_specification_documentation, create_config,
                       unpack_args)
from specware import SpecWareTypeProvider

from .pkgitems import BuildItemTypeProvider
from .sphinxbuilder import SphinxBuilder

_SPEC_TYPES = {
    "specitems": SpecTypeProvider,
    "specmake": BuildItemTypeProvider,
    "specware": SpecWareTypeProvider,
}


class _SpecDocItemCache(EmptyItemCache):

    def __init__(self, item_cache: ItemCache,
                 type_provider: ItemTypeProvider) -> None:
        super().__init__(type_provider=type_provider)
        self._item_cache = item_cache

    def __missing__(self, uid: str) -> Item:
        return self._item_cache[uid]


class SpecDocProvider(ItemValueProvider):
    """ Documents specification items. """

    # pylint: disable=too-few-public-methods

    def __init__(self, builder: SphinxBuilder) -> None:
        super().__init__(builder.mapper)
        self._builder = builder
        self.mapper.add_get_value(f"{builder.item.type}:/specdoc",
                                  self._get_specdoc)

    def _get_specdoc(self, ctx: ItemGetValueContext) -> str:
        builder = self._builder
        with builder.section_level_scope(ctx) as optional_args:
            args, kwargs = unpack_args(optional_args, self.mapper.substitute)
            config = create_config(kwargs, SpecDocumentConfig)
            assert isinstance(self.mapper, TextMapper)
            content = self.mapper.create_content(
                section_level=builder.section_level)
            type_provider = _SPEC_TYPES[args[0]]({})
            item_cache = _SpecDocItemCache(self._builder.item.cache,
                                           type_provider=type_provider)
            add_specification_documentation(content, config, item_cache,
                                            self.mapper)
            return content.join()
