# SPDX-License-Identifier: BSD-2-Clause
""" Produces a directory state which is subset of a repository. """

# Copyright (C) 2021 EDISOFT
# Copyright (C) 2020, 2025 embedded brains GmbH & Co. KG
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
import tempfile

from specitems import ItemCache, ItemCacheConfig, is_enabled
from specware import gather_build_files

from .directorystate import DirectoryState


class RepositorySubset(DirectoryState):
    """
    Creates a directory containing only the specified subset of the
    repository.
    """

    def gather_files(self) -> list[str]:
        """ Gather the files of the repository subset. """
        logging.info("%s: gather repository subset", self.uid)
        enabled_set = list(self.enabled_set)
        for enable_enabled_by in self["enabled-set-extension"]:
            if is_enabled(enabled_set, enable_enabled_by["enabled-by"]):
                enabled_set.append(enable_enabled_by["enable"])
        build_spec_directories = self["build-spec-directories"]
        if build_spec_directories:
            with tempfile.TemporaryDirectory() as tmp_dir:
                cache_config = ItemCacheConfig(
                    paths=[
                        os.path.join(self.directory, directory)
                        for directory in build_spec_directories
                    ],
                    resolve_proxies=False,
                    cache_directory=tmp_dir,
                )
                item_cache = ItemCache(cache_config)
                logging.info("items %s %s", cache_config,
                             list(item_cache.keys()))
        else:
            item_cache = self.item.cache
        config = {
            "arch": self["arch"],
            "bsp": self["bsp"],
            "enabled-set": enabled_set,
            "base-directory-map": self["base-directory-map"],
            "build-uids": self["build-uids"]
        }
        files = gather_build_files(config, item_cache,
                                   self["include-test-header"])
        files.extend(self["extra-files"])
        return files

    def run(self):
        source = self.input("source")
        assert isinstance(source, DirectoryState)

        self.discard()
        self.clear()

        logging.info("%s: copy gathered files", self.uid)
        self.copy_files(source.directory, self.gather_files())

        self.description.add(f"""Produce a repository subset in directory
{self.description.path(self.directory)}""")
