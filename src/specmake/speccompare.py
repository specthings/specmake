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
import itertools
import re
from typing import Any, Callable, Iterator

from specitems import (Item, ItemCache, ItemGetValueContext, ItemValueProvider,
                       ItemSelection, SphinxContent, TextContent, TextMapper,
                       get_reference, make_label)
from specware import (gather_benchmarks_and_test_suites, gather_related_items,
                      gather_test_cases, get_constraint_items,
                      get_interface_items, get_items_by_type_map,
                      get_items_by_types, get_requirement_items,
                      recursive_is_enabled, run_command)

from .directorystate import DirectoryState
from .itemcachestate import ItemCacheDirectoryState
from .sphinxbuilder import SphinxBuilder
from .pkgitems import BuildItem, PackageBuildDirector

_Commit = dict[str, Any]

_COMMIT = re.compile(r"commit ([0-9a-f]+)$")

_EMPTY_SCOPE_TO_UIDS: dict[str, frozenset[str]] = {
    "all": frozenset(),
    "interfaces": frozenset(),
    "requirements": frozenset(),
    "validations": frozenset(),
    "unit-and-integration-tests": frozenset(),
}


def _get_items(item_cache: ItemCache, selection: ItemSelection,
               enabled_set_actions: list[dict[str, Any]],
               root_uid: str) -> list[Item]:
    selection = ItemSelection(item_cache, selection.enabled_set,
                              recursive_is_enabled)
    for action in enabled_set_actions:
        selection.apply_action(action)
    with item_cache.selection(selection):
        return gather_related_items(item_cache[root_uid])


def _get_tests(item_cache: ItemCache, uids: list[str]) -> Iterator[str]:
    for uid in uids:
        test_suites: list[Item] = []
        gather_benchmarks_and_test_suites(item_cache[uid], test_suites)
        yield from (item.uid for item in test_suites)
        for test_suite in test_suites:
            test_cases: list[Item] = []
            gather_test_cases(test_suite, test_cases)
            yield from (item.uid for item in test_cases)


def _get_other_validations(
        items_by_type: dict[str, list[Item]]) -> Iterator[str]:
    yield from (item.uid
                for item in get_items_by_types(items_by_type, (
                    "validation/by-analysis", "validation/by-inspection",
                    "validation/by-review-of-design")))


@dataclasses.dataclass
class _SpecRevision:
    """ Represents a specification revision. """

    def __init__(self, state: ItemCacheDirectoryState,
                 selection: ItemSelection, data: dict,
                 previous_uids: dict[str, frozenset[str]]) -> None:
        item_cache = state.cache()
        items = _get_items(item_cache, selection, data["enabled-set-actions"],
                           data["root-uid"])
        items_by_type = get_items_by_type_map(items)
        self.previous_uids = previous_uids
        self.uids = {
            "all":
            frozenset(item.uid for item in items),
            "interfaces":
            frozenset(item.uid for item in get_interface_items(items_by_type)),
            "requirements":
            frozenset(item.uid for item in itertools.chain(
                get_constraint_items(items_by_type),
                get_requirement_items(items_by_type))),
            "validations":
            frozenset(
                itertools.chain(
                    _get_tests(item_cache, data["validation-test-suites"]),
                    _get_other_validations(items_by_type))),
            "unit-and-integration-tests":
            frozenset(
                _get_tests(item_cache,
                           data["unit-and-integration-test-suites"])),
        }
        self.key: str = data["revision-key"]
        self.label: str = data["label"]
        self.name: str = data["revision-name"]
        self.revision: str = state.input("source")["commit"]
        self.spec_paths = state.spec_paths("")


@dataclasses.dataclass
class _CompareSpecsConfig:
    """ Represents a specification comparison configuration. """
    repository: DirectoryState
    ignored_commits: list[str]
    previous: _SpecRevision
    current: _SpecRevision


def _get_git_log(config: _CompareSpecsConfig,
                 spec_paths: list[str]) -> list[str]:
    stdout: list[str] = []
    status = run_command([
        "git", "log", "--no-renames", "-p",
        f"{config.previous.revision}..{config.current.revision}", "--"
    ] + spec_paths, config.repository.directory, stdout)
    assert status == 0
    return stdout


class _LogParser:
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    def __init__(self, uids: frozenset[str], ignored_commits: list[str],
                 spec_paths: list[str]):
        self._uids = uids
        self._ignored_commits = ignored_commits
        self._spec_paths = sorted(spec_paths, reverse=True)
        self._commits: list[_Commit] = []
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

    def _finalize_diff(self) -> None:
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

    def _finalize(self) -> None:
        if self._current_chunk:
            self._current_diff["chunks"].append(self._current_chunk)
            self._current_chunk = []
        self._finalize_diff()
        commit = self._current_commit
        self._current_commit = {}
        if commit and commit["diffs"]:
            if commit["commit"] in self._ignored_commits:
                commit["diffs"] = []
            self._commits.append(commit)

    def finalize(self) -> list[_Commit]:
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


def _get_commits(config: _CompareSpecsConfig) -> list[_Commit]:
    uids_current = config.current.uids["all"]
    uids_previous = config.previous.uids["all"]
    all_uids = uids_current.union(uids_previous)
    spec_paths = sorted(
        set(
            itertools.chain(config.current.spec_paths,
                            config.previous.spec_paths)))
    parser = _LogParser(all_uids, config.ignored_commits, spec_paths)
    for line in _get_git_log(config, spec_paths):
        parser.consume(line.rstrip("\n"))
    return parser.finalize()


def _add_change_log(content: TextContent, config: _CompareSpecsConfig) -> None:
    with content.label_scope(config.current.label):
        for commit in reversed(_get_commits(config)):
            with content.section(commit["message"][0]):
                content.add(commit["message"][2:])
                if not commit["diffs"]:
                    with content.directive("note"):
                        content.add("The modifications of this change are "
                                    "not listed in the document.")
                    continue
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


def _ref(uid: str, present: frozenset[str]) -> str:
    if uid in present:
        return get_reference(make_label(f"Spec{uid}"), uid)
    return uid


class CompareSpecsRegistry(BuildItem):
    """ Provides a registry for specification comparisons. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self._revisions: list[_SpecRevision] = []
        self._key_to_revision: dict[str, _SpecRevision] = {}
        self._item_history: dict[str, dict] = {}

    def _initialize_item_history(self) -> None:
        repository = self.input("repository")
        assert isinstance(repository, DirectoryState)
        previous = self._revisions[0]
        for current in self._revisions[1:]:
            uid_to_commit_list: dict[str, list[dict[str, dict]]] = {}
            config = _CompareSpecsConfig(
                repository=repository,
                ignored_commits=self["ignored-commits"],
                previous=previous,
                current=current)
            for commit in reversed(_get_commits(config)):
                uid_to_commit: dict[str, dict] = {}
                for diff in commit["diffs"]:
                    a_uid = diff["a-uid"]
                    b_uid = diff["b-uid"]
                    if b_uid is None:
                        uid = a_uid
                    else:
                        uid = b_uid
                    uid_to_commit.setdefault(uid, {
                        "message": commit["message"],
                        "diffs": []
                    })["diffs"].append(diff)
                for uid, item_commit in uid_to_commit.items():
                    uid_to_commit_list.setdefault(uid, []).append(item_commit)
            for uid, commit_list in uid_to_commit_list.items():
                history = self._item_history.setdefault(
                    uid, {
                        "changes": [],
                        "revisions": []
                    })
                history["changes"].append({
                    "commits": commit_list,
                    "key": current.key,
                    "name": current.name,
                    "revision": current,
                    "previous-revision": previous
                })
                history["revisions"].append(current.key)
            previous = current

    def _initialize_revisions(self) -> None:
        if self._revisions:
            return
        selection = self.item.cache.active_selection
        previous_uids = _EMPTY_SCOPE_TO_UIDS
        for link, state in self.input_links("spec-compare-revision"):
            assert isinstance(state, ItemCacheDirectoryState)
            data = self.substitute(link.data)
            revision = _SpecRevision(state, selection, data, previous_uids)
            self._revisions.append(revision)
            self._key_to_revision[revision.key] = revision
            previous_uids = revision.uids
        self._initialize_item_history()

    def _get_revision(self, key: str) -> _SpecRevision:
        try:
            return self._key_to_revision[key]
        except KeyError as err:
            available = [revision.key for revision in self._revisions]
            raise ValueError("there is no revision associated with the "
                             f"key '{key}', available {available}") from err

    def add_change_log(self, content: TextContent, previous_key: str,
                       current_key: str) -> None:
        """
        Add a list of changes from the specification associated with the
        previous key to the specification associated with the current key.
        """
        self._initialize_revisions()
        repository = self.input("repository")
        assert isinstance(repository, DirectoryState)
        previous = self._get_revision(previous_key)
        current = self._get_revision(current_key)
        config = _CompareSpecsConfig(repository=repository,
                                     ignored_commits=self["ignored-commits"],
                                     previous=previous,
                                     current=current)
        _add_change_log(content, config)

    def add_change_log_by_args(self, content: TextContent, args: str) -> None:
        """ Add a list of changes specified by args. """
        previous_key, _, current_key = args.partition("..")
        self.add_change_log(content, previous_key, current_key)

    def add_item_changes(self, content: TextContent, uid: str) -> None:
        """ Get the item history by UID. """
        self._initialize_revisions()
        history = self._item_history.get(uid)
        if history is None:
            content.add(
                f"There are no changes since {self._revisions[0].name}.")
            return
        for change in reversed(history["changes"]):
            name = change["name"]
            in_current = uid in change["revision"].uids["all"]
            in_previous = uid in change["previous-revision"].uids["all"]
            if not in_previous and in_current:
                content.add(f"The item is new in {name}.")
                continue
            if in_previous and not in_current:
                content.add(f"The item was deleted in {name}.")
                continue
            content.add(f"The following changes are associated with {name}.")
            for commit in reversed(change["commits"]):
                message = commit["message"]
                with content.directive("topic", message[0]):
                    if len(message) >= 2:
                        content.append(message[2:])
                    else:
                        content.append("No commit message.")
                for diff in commit["diffs"]:
                    line_number_start = 1
                    for chunk in diff["chunks"]:
                        content.add_code_block(
                            chunk,
                            language="diff",
                            line_number_start=line_number_start)
                        line_number_start += len(chunk)

    def add_changes_by_scope(self, content: TextContent, scope: str,
                             revision_key: str) -> None:
        """
        Add the changes of items within the scope from the revision associated
        with the key compared to the previous revision.
        """
        # pylint: disable=too-many-locals
        self._initialize_revisions()
        current = self._get_revision(revision_key)
        current_scope = current.uids[scope]
        current_other = current.uids["all"].difference(current_scope)
        previous_scope = current.previous_uids[scope]
        previous_other = current.previous_uids["all"].difference(
            previous_scope)
        maybe_deleted = previous_scope.difference(current_scope)
        moved_out = maybe_deleted.intersection(current_other)
        deleted = maybe_deleted.difference(moved_out)
        maybe_new = current_scope.difference(previous_scope)
        moved_in = maybe_new.intersection(previous_other)
        new = maybe_new.difference(moved_in)
        modified = sorted(uid
                          for uid in current_scope.intersection(previous_scope)
                          if current.key in self._item_history.get(
                              uid, {}).get("revisions", tuple()))
        present = self._revisions[-1].uids[scope]
        rows = [("Items", "Status")]
        rows.extend((_ref(uid, present), "Deleted") for uid in sorted(deleted))
        rows.extend(
            (_ref(uid, present), "Moved out") for uid in sorted(moved_out))
        rows.extend(
            (_ref(uid, present), "Moved in") for uid in sorted(moved_in))
        rows.extend((_ref(uid, present), "New") for uid in sorted(new))
        rows.extend((_ref(uid, present), "Modified") for uid in modified)
        assert isinstance(content, SphinxContent)
        content.add_grid_table(rows, widths=[80, 20], font_size=-2)

    def add_changes_by_scope_by_args(self, content: TextContent,
                                     args: str) -> None:
        """ Add the changes specified by args. """
        scope, _, revision_key = args.partition(":")
        self.add_changes_by_scope(content, scope, revision_key)


class CompareSpecsProvider(ItemValueProvider):
    """ Provides a specification comparison. """

    # pylint: disable=too-few-public-methods

    def __init__(self, builder: SphinxBuilder) -> None:
        super().__init__(builder.mapper)
        self._builder = builder
        self.mapper.add_get_value("pkg/spec-compare-registry:/spec-change-log",
                                  self._get_spec_change_log)
        self.mapper.add_get_value(
            "pkg/spec-compare-registry:/spec-item-changes",
            self._get_spec_item_changes)
        self.mapper.add_get_value(
            "pkg/spec-compare-registry:/spec-changes-by-scope",
            self._get_spec_changes_by_scope)

    def _get_spec_things(
            self, ctx: ItemGetValueContext,
            what: Callable[[CompareSpecsRegistry, TextContent, str],
                           None]) -> str:
        builder = self._builder
        director = builder.director
        with builder.section_level_scope(ctx) as args:
            assert isinstance(self.mapper, TextMapper)
            content = self.mapper.create_content(
                section_level=builder.section_level)
            registry = director[ctx.item.uid]
            assert isinstance(registry, CompareSpecsRegistry)
            assert args
            what(registry, content, args)
            return "\n".join(content)

    def _get_spec_change_log(self, ctx: ItemGetValueContext) -> str:
        return self._get_spec_things(
            ctx, CompareSpecsRegistry.add_change_log_by_args)

    def _get_spec_item_changes(self, ctx: ItemGetValueContext) -> str:
        return self._get_spec_things(ctx,
                                     CompareSpecsRegistry.add_item_changes)

    def _get_spec_changes_by_scope(self, ctx: ItemGetValueContext) -> str:
        return self._get_spec_things(
            ctx, CompareSpecsRegistry.add_changes_by_scope_by_args)
