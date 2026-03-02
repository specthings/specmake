# SPDX-License-Identifier: BSD-2-Clause
""" Builds a Doxyfile. """

# Copyright (C) 2024 embedded brains GmbH & Co. KG
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
from typing import Callable, Union

from specitems import is_enabled, Item, ItemGetValueContext

from .directorystate import DirectoryState
from .pkgitems import PackageBuildDirector
from .util import copy_and_substitute


def _yes_or_no(yes: bool) -> str:
    if yes:
        return "YES"
    return "NO"


def _add_element(_directory: str, element: str | list[str],
                 paths: list[str]) -> None:
    if isinstance(element, list):
        paths.extend(element)
    else:
        paths.append(element)


def _add_path(directory: str, element: str | list[str],
              paths: list[str]) -> None:
    if isinstance(element, list):
        paths.extend(
            os.path.normpath(os.path.join(directory, path))
            for path in element)
    else:
        paths.append(os.path.normpath(os.path.join(directory, element)))


class Doxyfile(DirectoryState):
    """ Maintains a Doxyfile. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        my_type = self.item.type
        self.mapper.add_get_value(f"{my_type}:/exclude-patterns",
                                  self._get_exclude_patterns)
        self.mapper.add_get_value(f"{my_type}:/include-path",
                                  self._get_include_path)
        self.mapper.add_get_value(f"{my_type}:/input", self._get_input)
        self.mapper.add_get_value(f"{my_type}:/generate-html",
                                  self._get_generate_html)
        self.mapper.add_get_value(f"{my_type}:/generate-latex",
                                  self._get_generate_latex)
        self.mapper.add_get_value(f"{my_type}:/output-directory",
                                  self._get_output_directory)
        self.mapper.add_get_value(f"{my_type}:/strip-from-path",
                                  self._get_strip_from_path)
        self.mapper.add_get_value(f"{my_type}:/tagfile", self._get_tagfile)

    def run(self) -> None:
        source = self.input("source")
        assert isinstance(source, DirectoryState)
        copy_and_substitute(source.file, self.file, self.mapper, self.uid)
        self.description.add(f"""Produce the Doxygen configuration file
{self.description.path(self.file)}""")

    def _get_elements(
            self, key: str,
            add: Callable[[str, Union[str, list[str]], list[str]],
                          None]) -> str:
        paths: list[str] = []
        for link, directory_state in self.input_links("doxygen"):
            assert isinstance(directory_state, DirectoryState)
            directory = directory_state.directory
            for optional_element in self.substitute(link[key], link.item):
                if not is_enabled(self.enabled_set,
                                  optional_element["enabled-by"]):
                    continue
                element = optional_element["path"]
                add(directory, element, paths)
        return " \\\n".join(paths)

    def _get_exclude_patterns(self, _ctx: ItemGetValueContext) -> str:
        return self._get_elements("exclude-patterns", _add_element)

    def _get_paths(self, key: str) -> str:
        return self._get_elements(key, _add_path)

    def _get_include_path(self, _ctx: ItemGetValueContext) -> str:
        return self._get_paths("include-path")

    def _get_input(self, _ctx: ItemGetValueContext) -> str:
        return self._get_paths("input")

    def _get_generate_html(self, _ctx: ItemGetValueContext) -> str:
        return _yes_or_no(self["generate-html"])

    def _get_generate_latex(self, _ctx: ItemGetValueContext) -> str:
        return _yes_or_no(self["generate-latex"])

    def _get_output_directory(self, _ctx: ItemGetValueContext) -> str:
        output = self.director[self.item.parent("output-directory").uid]
        assert isinstance(output, DirectoryState)
        return output.directory

    def _get_strip_from_path(self, _ctx: ItemGetValueContext) -> str:
        return self._get_paths("strip-from-path")

    def _get_tagfile(self, _ctx: ItemGetValueContext) -> str:
        tagfile = self.director[self.item.parent("doxygen-tagfile").uid]
        assert isinstance(tagfile, DirectoryState)
        return tagfile.file
