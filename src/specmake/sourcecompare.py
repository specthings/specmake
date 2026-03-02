# SPDX-License-Identifier: BSD-2-Clause
""" Compares two source trees. """

# Copyright (C) 2019, 2025 embedded brains GmbH & Co. KG
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
import difflib
import os
import re
from typing import NamedTuple, Union

import specitems

from .directorystate import DirectoryState
from .sphinxbuilder import SphinxBuilder

_COMMENT = re.compile(r"\s*(\*|\/\*|\s*$)")

_WARNING_NO_REVIEW = """.. topic:: WARNING

    This change has no associated review.
"""


@dataclasses.dataclass
class CompareSourcesConfig:
    """ Represents a source comparison configuration. """
    current: DirectoryState
    previous: DirectoryState
    reviews: dict[str, dict[str, str]]
    file_to_review: dict[str, Union[str, list[str]]]
    renamed: dict[str, str]
    label: str


class _Context:
    # pylint: disable=too-many-instance-attributes

    def __init__(self, content: specitems.TextContent,
                 file_to_review: dict[str, Union[str, list[str]]]):
        self.content = content
        self.file_to_review = file_to_review
        self.new_files: set[str] = set()
        self.removed_files: set[str] = set()
        self.other: dict[str, list[list[str]]] = {}
        self.inline: dict[str, list[list[str]]] = {}
        self.comments: dict[str, list[list[str]]] = {}
        self.no_changes: set[str] = set()
        self.review_to_new_files: dict[str, list[str]] = {}
        self.review_to_removed_files: dict[str, list[str]] = {}
        self.review_to_other_files: dict[str, list[str]] = {}
        self.label: str = ""

    def make_label(self, key: str) -> str:
        """ Make a label derived from the key. """
        return specitems.make_label(f"{self.label} {key}")

    def add_review_ref(self, name: str) -> None:
        """
        Add the review reference associated with the name to the content.
        """
        maybe_key = self.file_to_review.get(name, None)
        if maybe_key is None:
            self.content.add(_WARNING_NO_REVIEW)
        elif isinstance(maybe_key, str):
            self.content.add(f"See :ref:`{self.make_label(maybe_key)}`.")
        else:
            self.content.add_list(
                [f":ref:`{self.make_label(key)}`" for key in maybe_key],
                "See the following reviews:")

    def add_diffs(self, diffs: dict[str, list[list[str]]],
                  ref_review: bool) -> None:
        """
        Add the file differences to the content.

        Optionally adds review references.
        """
        for name, chunks in sorted(diffs.items()):
            if ref_review:
                label = self.make_label(name)
            else:
                label = None
            with self.content.section(name, label=label):
                if ref_review:
                    self.add_review_ref(name)
                for chunk in chunks:
                    for begin in range(0, len(chunk), 100):
                        with self.content.directive("code-block", "diff"):
                            self.content.add(chunk[begin:begin + 100])

    def add_files(self, files: set[str], section: str) -> None:
        """ Add the section with files to the content. """
        with self.content.section(section):
            for name in sorted(files):
                with self.content.section(name, label=self.make_label(name)):
                    self.add_review_ref(name)

    def add_related_files(self, key: str, review_to_files: dict[str,
                                                                list[str]],
                          action: str) -> None:
        """
        Add the files related to the review associated with the key to the
        content.
        """
        files = review_to_files.get(key, None)
        if files is None:
            return
        if len(files) == 1:
            self.content.add(f"This review is related to the {action} "
                             f"file :ref:`{self.make_label(files[0])}`.")
        else:
            self.content.add_list(
                (f":ref:`{self.make_label(name)}`" for name in sorted(files)),
                f"This review is related to the following {action} files:")

    def add_to_other_or_inline(self, name: str, chunk: list[str]) -> None:
        """ Add the chunk to the other or inline set. """
        minus = 0
        plus = 0
        inline_minus = 0
        inline_plus = 0
        for line in chunk:
            i = line[0]
            minus += int(i == "-")
            plus += int(i == "+")
            inline_minus += int(i == "-" and "RTEMS_INLINE_ROUTINE" in line)
            inline_plus += int(i == "+" and "static inline" in line)
        if minus == inline_minus and plus == inline_plus:
            self.inline.setdefault(name, []).append(chunk)
        else:
            self.other.setdefault(name, []).append(chunk)


def _get_chunks(prefix_current: str, prefix_previous: str, name_current: str,
                name_previous: str) -> list[list[str]]:
    chunks: list[list[str]] = []
    path = os.path.join(prefix_current, name_current)
    path_previous = os.path.join(prefix_previous, name_previous)
    with open(path,
              encoding="utf-8") as src, open(path_previous,
                                             encoding="utf-8") as src_previous:
        chunk: list[str] = []
        for line in difflib.unified_diff(src_previous.readlines(),
                                         src.readlines(), path_previous, path):
            line = line.rstrip("\r\n")
            if line.startswith("@@"):
                chunks.append(chunk)
                chunk = []
            chunk.append(line)
        if chunk:
            chunks.append(chunk)
    return chunks[1:]


class _Sources(NamedTuple):
    prefix: str
    files: set[str]


def _review_to_files(
        files: set[str],
        file_to_review: dict[str, Union[str,
                                        list[str]]]) -> dict[str, list[str]]:
    review_to_files: dict[str, list[str]] = {}
    for name in files:
        maybe_key = file_to_review.get(name, None)
        if maybe_key is None:
            continue
        if isinstance(maybe_key, str):
            review_to_files.setdefault(maybe_key, []).append(name)
        else:
            for key in maybe_key:
                review_to_files.setdefault(key, []).append(name)
    return review_to_files


def _add_comparison(content: specitems.TextContent,
                    config: CompareSourcesConfig, current: _Sources,
                    previous: _Sources) -> None:
    ctx = _Context(content, config.file_to_review)
    for name_current in current.files:
        name_previous = config.renamed.get(name_current, name_current)
        if name_previous not in previous.files:
            ctx.new_files.add(name_current)
            continue
        previous.files.remove(name_previous)
        chunks = _get_chunks(current.prefix, previous.prefix, name_current,
                             name_previous)
        if not chunks:
            ctx.no_changes.add(name_current)
            continue
        for chunk in chunks:
            for line in chunk:
                if line.startswith(("-", "+")):
                    if _COMMENT.match(line[1:]) is None:
                        ctx.add_to_other_or_inline(name_current, chunk)
                        break
            else:
                ctx.comments.setdefault(name_current, []).append(chunk)
    ctx.removed_files = previous.files
    ctx.review_to_new_files = _review_to_files(ctx.new_files,
                                               ctx.file_to_review)
    ctx.review_to_removed_files = _review_to_files(ctx.removed_files,
                                                   ctx.file_to_review)
    ctx.review_to_other_files = _review_to_files(set(ctx.other.keys()),
                                                 ctx.file_to_review)
    with ctx.content.label_scope(config.label):
        ctx.label = ctx.content.get_label()
        with ctx.content.section("Reviews"):
            for key, review in config.reviews.items():
                with ctx.content.section(review["subject"],
                                         label=ctx.make_label(key)):
                    ctx.content.add(review["text"])
                    ctx.add_related_files(key, ctx.review_to_new_files, "new")
                    ctx.add_related_files(key, ctx.review_to_removed_files,
                                          "removed")
                    ctx.add_related_files(key, ctx.review_to_other_files,
                                          "changed")
        ctx.add_files(ctx.new_files, "New files")
        ctx.add_files(previous.files, "Removed files")
        with ctx.content.section("Files with unspecific changes"):
            ctx.add_diffs(ctx.other, True)
        with ctx.content.section("Files with RTEMS_INLINE_ROUTINE changes"):
            ctx.content.add(f"See :ref:`{ctx.make_label('inline')}`.")
            ctx.add_diffs(ctx.inline, False)
        with ctx.content.section("Files with changes inside of comments"):
            ctx.add_diffs(ctx.comments, False)
        with ctx.content.section("Unchanged files"):
            ctx.content.add_list(sorted(ctx.no_changes))


def compare_sources(content: specitems.TextContent,
                    config: CompareSourcesConfig) -> None:
    """ Compare two source trees according to the configuration. """
    sources_current = _Sources(config.current.directory,
                               set(config.current.files(base="")))
    sources_previous = _Sources(config.previous.directory,
                                set(config.previous.files(base="")))
    _add_comparison(content, config, sources_current, sources_previous)


class CompareSourcesProvider(specitems.ItemValueProvider):
    """ Provides a source comparison. """

    # pylint: disable=too-few-public-methods

    def __init__(self, builder: SphinxBuilder) -> None:
        super().__init__(builder.mapper)
        self._builder = builder
        self.mapper.add_get_value(f"{builder.item.type}:/compare-sources",
                                  self._get_compare_sources)

    def _get_compare_sources(self, ctx: specitems.ItemGetValueContext) -> str:
        builder = self._builder
        with builder.section_level_scope(ctx) as key:
            assert key
            current_link, current_sources = builder.input_link_by_key(
                "source-compare-current", "source-compare-key", key)
            assert isinstance(current_sources, DirectoryState)
            _, previous_sources = builder.input_link_by_key(
                "source-compare-previous", "source-compare-key", key)
            assert isinstance(previous_sources, DirectoryState)
            config = CompareSourcesConfig(
                current=current_sources,
                previous=previous_sources,
                reviews=current_link["reviews"],
                file_to_review=current_link["file-to-review"],
                renamed=current_link["renamed"],
                label=current_link["label"])
            assert isinstance(self.mapper, specitems.TextMapper)
            content = self.mapper.create_content(
                section_level=builder.section_level)
            compare_sources(content, config)
            return content.join()
