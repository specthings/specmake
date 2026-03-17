# SPDX-License-Identifier: BSD-2-Clause
""" Compare two specification sets. """

# Copyright (C) 2019, 2026 embedded brains GmbH & Co. KG
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
import tempfile
from typing import Any

from specitems import (Item, ItemCache, ItemCacheConfig, ItemGetValueContext,
                       ItemValueProvider, ItemSelection, TextContent,
                       TextMapper)
from specware import run_command, validate

from .directorystate import DirectoryState
from .sphinxbuilder import SphinxBuilder

_COMMIT = re.compile(r"commit ([0-9a-f]+)$")


@dataclasses.dataclass
class CompareSpecsConfig:
    # pylint: disable=too-many-instance-attributes
    """ Represents a specification comparison configuration. """
    repository: DirectoryState
    root_uid: str
    current_revision: str
    previous_revision: str
    ignored_commits: list[str]
    spec_paths: list[str]
    selection: ItemSelection
    enabled_set_actions: list[dict[str, Any]]
    label: str


class _LogParser:
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    def __init__(self, uids: set[str], ignored_commits: list[str],
                 spec_paths: list[str]):
        self._uids = uids
        self._ignored_commits = ignored_commits
        self._spec_paths = sorted(spec_paths, reverse=True)
        self._commits: list[list[str]] = []
        self._current_commit: dict[str, Any] = {}
        self._current_chunk: list[str] = []
        self._current_diff: dict[str, Any] = {}
        self.consume = self._expect_commit

    def _get_diff_uid(self, diff: dict, which: str) -> str | None:
        if diff[which] == "/dev/null":
            return None
        path = diff[which][2:]
        for prefix in self._spec_paths:
            uid = path.removeprefix(prefix)
            if path != uid and path.endswith(".yml"):
                return uid[:-4]
        raise ValueError

    def _finalize_diff(self):
        diff = self._current_diff
        self._current_diff = {}
        if diff:
            try:
                a_uid = self._get_diff_uid(diff, "a")
            except ValueError:
                return
            try:
                b_uid = self._get_diff_uid(diff, "b")
            except ValueError:
                return
            if b_uid is not None and b_uid not in self._uids:
                return
            diff["a-uid"] = a_uid
            diff["b-uid"] = b_uid
            self._current_commit["diffs"].append(diff)

    def _finalize(self):
        if self._current_chunk:
            self._current_diff["chunks"].append(self._current_chunk)
            self._current_chunk = []
        self._finalize_diff()
        commit = self._current_commit
        self._current_commit = {}
        if commit and commit["diffs"] and commit[
                "commit"] not in self._ignored_commits:
            self._commits.append(commit)

    def finalize(self):
        """ Finalizes the parsing and returns the commits. """
        self._finalize()
        return self._commits

    def _expect_commit(self, line: str) -> None:
        mobj = _COMMIT.match(line)
        assert mobj
        self._finalize()
        self._current_commit = {
            "diffs": [],
            "commit": mobj.group(1),
            "message": []
        }
        self.consume = self._expect_author

    def _expect_author(self, line: str) -> None:
        key = "Author: "
        assert line.startswith(key)
        self._current_commit["author"] = line[len(key):]
        self.consume = self._expect_date

    def _expect_date(self, line: str) -> None:
        key = "Date: "
        assert line.startswith(key)
        self._current_commit["date"] = line[len(key):]
        self.consume = self._expect_empty_line

    def _expect_empty_line(self, line: str) -> None:
        assert not line
        self.consume = self._message

    def _message(self, line: str) -> None:
        space = "    "
        if line.startswith(space):
            self._current_commit["message"].append(line[len(space):])
            return
        self.consume = self._diff_start
        self._diff_start(line)

    def _diff_start(self, line: str) -> None:
        self._finalize_diff()
        if line.startswith("---"):
            self._current_diff = {"a": line[4:], "chunks": []}
            self.consume = self._expect_diff_plus

    def _expect_diff_plus(self, line: str) -> None:
        assert line.startswith("+++")
        self._current_diff["b"] = line[4:]
        self.consume = self._expect_chunk_start

    def _expect_chunk_start(self, line: str) -> None:
        assert line.startswith("@@")
        self._current_chunk = [line]
        self.consume = self._chunk

    def _chunk(self, line: str) -> None:
        if line.startswith((" ", "-", "+")):
            self._current_chunk.append(line)
            return
        self._current_diff["chunks"].append(self._current_chunk)
        self._current_chunk = []
        if line.startswith("@@"):
            self.consume = self._expect_chunk_start
            self._expect_chunk_start(line)
            return
        if line.startswith("commit"):
            self.consume = self._expect_commit
            self._expect_commit(line)
            return
        if line.startswith("diff"):
            self.consume = self._diff_start
            self._diff_start(line)
            return


def _validate(_item: Item, validated: bool) -> bool:
    return validated


def _get_uids_current(config: CompareSpecsConfig) -> set[str]:
    return set(item.uid for item in validate(
        config.repository.item.cache[config.root_uid], _validate))


def _get_uids_previous(config: CompareSpecsConfig) -> set[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache_config = ItemCacheConfig(paths=[
            os.path.join(config.repository.directory, path)
            for path in config.spec_paths
        ],
                                       cache_directory=tmp_dir)
        item_cache = ItemCache(cache_config)
        selection = config.selection.clone(item_cache)
        for action in config.enabled_set_actions:
            selection.apply_action(action)
        item_cache.set_selection(selection)
        uids: set[str] = set()
        for item in item_cache.values():
            if not item.enabled or item.type == "spec":
                continue
            uids.add(item.uid)
        return uids


def _get_commits(config: CompareSpecsConfig) -> list[str]:
    stdout: list[str] = []
    status = run_command([
        "git", "log", "--no-renames", "-p",
        f"{config.previous_revision}..{config.current_revision}"
    ] + config.spec_paths, config.repository.directory, stdout)
    assert status == 0
    return stdout


def compare_specs(content: TextContent, config: CompareSpecsConfig) -> None:
    """ Compare two specifications according to the configuration. """
    uids_current = _get_uids_current(config)
    uids_previous = _get_uids_previous(config)
    all_uids = uids_current.union(uids_previous)
    parser = _LogParser(all_uids, config.ignored_commits, config.spec_paths)
    for line in _get_commits(config):
        parser.consume(line.rstrip("\n"))
    with content.label_scope(config.label):
        for commit in reversed(parser.finalize()):
            with content.section(commit["message"][0]):
                content.add(commit["message"][2:])
                for diff in commit["diffs"]:
                    a_uid = diff["a-uid"]
                    b_uid = diff["b-uid"]
                    if a_uid is None:
                        with content.section(f"spec:{b_uid}"):
                            content.add(
                                "This change added the specification item.")
                        continue
                    if b_uid is None:
                        with content.section(f"spec:{a_uid}"):
                            content.add(
                                "This change removed the specification item.")
                        continue
                    with content.section(f"spec:{b_uid}"):
                        line_number_start = 1
                        for chunk in diff["chunks"]:
                            content.add_code_block(
                                chunk,
                                language="diff",
                                line_number_start=line_number_start)
                            line_number_start += len(chunk)


class CompareSpecsProvider(ItemValueProvider):
    """ Provides a specification comparison. """

    # pylint: disable=too-few-public-methods

    def __init__(self, builder: SphinxBuilder) -> None:
        super().__init__(builder.mapper)
        self._builder = builder
        self.mapper.add_get_value(f"{builder.item.type}:/compare-specs",
                                  self._get_compare_specs)

    def _get_compare_specs(self, ctx: ItemGetValueContext) -> str:
        builder = self._builder
        with builder.section_level_scope(ctx) as key:
            assert key
            link, repo = builder.input_link_by_key("spec-compare",
                                                   "spec-compare-key", key)
            assert isinstance(repo, DirectoryState)
            data = builder.substitute(link.data)
            config = CompareSpecsConfig(
                repository=repo,
                root_uid=data["root-uid"],
                current_revision=data["current-revision"],
                previous_revision=data["previous-revision"],
                ignored_commits=data["ignored-commits"],
                spec_paths=data["spec-paths"],
                selection=builder.director.item_cache.active_selection,
                enabled_set_actions=data["enabled-set-actions"],
                label=data["label"])
            assert isinstance(self.mapper, TextMapper)
            content = self.mapper.create_content(
                section_level=builder.section_level)
            compare_specs(content, config)
            return "\n".join(content)
