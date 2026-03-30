# SPDX-License-Identifier: BSD-2-Clause
""" Maintains an item cache directory state. """

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

import os
from typing import Optional

from specitems import Item, ItemCache, ItemCacheConfig, ItemTypeProvider
from specware import augment_with_test_case_links, augment_with_test_links

from .directorystate import DirectoryState
from .pkgitems import PackageBuildDirector


class ItemCacheDirectoryState(DirectoryState):
    """ Maintains an item cache directory state. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self._cache: ItemCache | None = None

    def load(self) -> str:
        self.cache()
        return super().load()

    def spec_paths(self, base: Optional[str] = None) -> list[str]:
        """ Return the specification item paths. """
        if base is None:
            source = self.input("source")
            assert isinstance(source, DirectoryState)
            base = source.directory
        return [os.path.join(base, path) for path in self["spec-paths"]]

    def cache(self) -> ItemCache:
        """ Return the item cache. """
        item_cache = self._cache
        if item_cache is None:
            cache_config = ItemCacheConfig(paths=self.spec_paths(),
                                           cache_directory=self.directory)
            type_provider = self.item.cache.type_provider
            item_cache = ItemCache(cache_config,
                                   type_provider=ItemTypeProvider(
                                       type_provider.data_by_uid,
                                       type_provider.root_type_uid,
                                       permissive_type_errors=True))
            augment_with_test_case_links(item_cache)
            augment_with_test_links(item_cache)
            self._cache = item_cache
        return item_cache
