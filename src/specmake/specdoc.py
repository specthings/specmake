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
                       ItemTypeProvider, SpecDocumentConfig, SpecTypeProvider,
                       TextMapper, add_specification_documentation,
                       create_config, make_label, unpack_args)
from specware import SpecWareTypeProvider

from .pkgitems import BuildItemTypeProvider
from .sphinxbuilder import SphinxBuilder, DocumentBuilderValueProvider

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


class SpecDocProvider(DocumentBuilderValueProvider):
    """ Documents specification items. """

    def __init__(self, builder: SphinxBuilder) -> None:
        super().__init__(builder)
        self.mapper.add_get_value(f"{builder.item.type}:/specdoc",
                                  self._get_specdoc)
        self.mapper.add_get_value("spec:/spec-name", self._get_spec_name)

    def _get_specdoc(self, ctx: ItemGetValueContext) -> str:
        builder = self.builder
        with builder.section_content(ctx) as (content, optional_args):
            args, kwargs = unpack_args(optional_args, self.mapper.substitute)
            config = create_config(kwargs, SpecDocumentConfig)
            assert isinstance(self.mapper, TextMapper)
            type_provider = _SPEC_TYPES[args[0]]({})
            item_cache = _SpecDocItemCache(self.builder.item.cache,
                                           type_provider=type_provider)
            with self.mapper.scope(item_cache["/spec/root"]):
                add_specification_documentation(content, config, self.mapper)
            return content.join()

    def _get_spec_name(self, ctx: ItemGetValueContext) -> str:
        name = ctx.item["spec-name"]
        label = f"SpecType{make_label(name)}"
        return self.get_reference(ctx, "spec-types", name, label)
