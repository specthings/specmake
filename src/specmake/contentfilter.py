# SPDX-License-Identifier: BSD-2-Clause
""" Provides the content rules of a repository filter. """

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

import copy
import json
import logging
import posixpath
import re
import subprocess
from typing import Any, Callable, Iterable

import yaml
from specitems import (ItemDumper, make_subprocess_environment,
                       yaml_round_trip)

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader  # type: ignore

Substitute = Callable[[Any], Any]

EditAttributes = Callable[[Any], None]

Files = dict[str, Callable[[], bytes]]

RunAttributeActions = Callable[[list[dict], Any], None]

_FLAGS = {
    "ASCII": re.ASCII,
    "DOTALL": re.DOTALL,
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "VERBOSE": re.VERBOSE,
}


def glob_to_regex(glob: str) -> re.Pattern:
    """
    Convert the path glob to a regular expression.

    The ``*`` and the ``?`` stay within one directory.  The ``**`` crosses
    directories.  A ``**/`` matches no directory too.
    """
    parts: list[str] = []
    index = 0
    while index < len(glob):
        if glob.startswith("**/", index):
            parts.append("(?:.*/)?")
            index += 3
        elif glob.startswith("**", index):
            parts.append(".*")
            index += 2
        elif glob[index] == "*":
            parts.append("[^/]*")
            index += 1
        elif glob[index] == "?":
            parts.append("[^/]")
            index += 1
        elif glob[index] == "[" and "]" in glob[index + 2:]:
            end = glob.index("]", index + 2)
            parts.append(glob[index:end + 1])
            index = end + 1
        else:
            parts.append(re.escape(glob[index]))
            index += 1
    return re.compile("".join(parts), re.DOTALL)


def _dump_item(data: Any) -> str:
    return yaml.dump(data,
                     Dumper=ItemDumper,
                     default_flow_style=False,
                     allow_unicode=True)


def _json_indent(text: str) -> int | None:
    lines = text.splitlines()
    if len(lines) < 2:
        return None
    return len(lines[1]) - len(lines[1].lstrip(" "))


def _dump_json(data: Any, indent: int | None, newline: bool) -> str:
    text = json.dumps(data, indent=indent, ensure_ascii=False)
    return f"{text}\n" if newline else text


def _edit_json(text: str, edit: EditAttributes, exact: bool) -> str:
    data = json.loads(text)
    indent = _json_indent(text)
    newline = text.endswith("\n")
    if exact and _dump_json(data, indent, newline) != text:
        raise ValueError("a dump of the unchanged data does not reproduce "
                         "the JSON text")
    edit(data)
    return _dump_json(data, indent, newline)


def _edit_yaml(text: str, edit: EditAttributes, exact: bool) -> str:
    data = yaml.load(text, Loader=SafeLoader)
    if _dump_item(data) == text:
        edit(data)
        return _dump_item(data)
    return yaml_round_trip(text, edit, exact)[0]


def _keep_invalid(path: str, err: Exception) -> None:
    logging.warning("%s: keep the content which is no valid data: %s", path,
                    str(err).splitlines()[0])


def edit_attributes(path: str, content: bytes, edit: EditAttributes,
                    exact: bool) -> bytes:
    """
    Edit the attributes of the YAML or JSON content of the file.

    A YAML text which equals the dump of a specification item gets that dump
    after the edit.  Any other YAML text goes through a round trip.  A JSON
    text keeps its indentation.  If exact is true, a text which a dump of the
    unchanged data does not reproduce raises a ValueError.  A content whose
    data the edit leaves unchanged stays as it is.  A content which is no valid
    YAML or JSON stays as it is and produces a warning.
    """
    text = content.decode("utf-8")
    try:
        if path.endswith(".json"):
            data = json.loads(text)
            edit_text = _edit_json
        elif path.endswith((".yml", ".yaml")):
            data = yaml.load(text, Loader=SafeLoader)
            edit_text = _edit_yaml
        else:
            raise ValueError("the file is no YAML or JSON file")
    except (json.JSONDecodeError, yaml.YAMLError) as err:
        _keep_invalid(path, err)
        return content
    edited = copy.deepcopy(data)
    edit(edited)
    if edited == data:
        return content
    return edit_text(text, edit, exact).encode("utf-8")


def _simplify_list(items: list, symbols: dict[str, bool],
                   absorbing: bool) -> list | bool:
    neutral = not absorbing
    simplified: list = []
    for item in items:
        item = simplify_enabled_by(item, symbols)
        if item is absorbing:
            return absorbing
        if item is not neutral:
            simplified.append(item)
    return simplified if simplified else neutral


def simplify_enabled_by(enabled_by: Any, symbols: dict[str, bool]) -> Any:
    """
    Assign the symbols in the enabled-by expression and simplify it.

    A constant ``and``, ``or`` or ``not`` operation becomes ``true`` or
    ``false``.  Each other operation keeps its operands which are not
    constant.
    """
    if isinstance(enabled_by, str):
        return symbols.get(enabled_by, enabled_by)
    if isinstance(enabled_by, list):
        return _simplify_list(enabled_by, symbols, True)
    if isinstance(enabled_by, dict) and len(enabled_by) == 1:
        key, value = next(iter(enabled_by.items()))
        if key == "not":
            value = simplify_enabled_by(value, symbols)
            return (not value) if isinstance(value, bool) else {"not": value}
        if key in ("and", "or") and isinstance(value, list):
            value = _simplify_list(value, symbols, key == "or")
            return value if isinstance(value, bool) else {key: value}
    return enabled_by


def _assign_enabled_by(data: Any, symbols: dict[str, bool]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "enabled-by":
                data[key] = simplify_enabled_by(value, symbols)
            else:
                _assign_enabled_by(value, symbols)
    elif isinstance(data, list):
        for value in data:
            _assign_enabled_by(value, symbols)


class ContentRule:
    """ Represents a content rule of a repository filter. """

    def __init__(self, rule: dict) -> None:
        self.rule = rule
        self._files = [glob_to_regex(glob) for glob in rule.get("files", [])]

    def matches(self, path: str) -> bool:
        """ Return true, if the rule applies to the path. """
        return any(pattern.fullmatch(path) for pattern in self._files)

    def apply(self, path: str, content: bytes) -> bytes:
        """ Return the content of the file after the rule. """
        raise NotImplementedError


class _ReplaceRule(ContentRule):

    def apply(self, path: str, content: bytes) -> bytes:
        return self.rule["content"].encode("utf-8")


class _RegexRule(ContentRule):

    def __init__(self, rule: dict) -> None:
        super().__init__(rule)
        flags = 0
        for flag in rule["flags"]:
            flags |= _FLAGS[flag]
        self._pattern = re.compile(rule["pattern"], flags)

    def apply(self, path: str, content: bytes) -> bytes:
        text = content.decode("utf-8", "surrogateescape")
        text = self._pattern.sub(self.rule["replacement"],
                                 text,
                                 count=self.rule["count"])
        return text.encode("utf-8", "surrogateescape")


class _StructureRule(ContentRule):

    def __init__(self, rule: dict,
                 run_attribute_actions: RunAttributeActions) -> None:
        super().__init__(rule)
        self._run_attribute_actions = run_attribute_actions

    def apply(self, path: str, content: bytes) -> bytes:
        return edit_attributes(
            path, content, lambda data: self._run_attribute_actions(
                self.rule["attribute-actions"], data),
            not self.rule["accept-format-changes"])


class _EnabledByRule(ContentRule):

    def apply(self, path: str, content: bytes) -> bytes:
        return edit_attributes(
            path, content,
            lambda data: _assign_enabled_by(data, self.rule["symbols"]), True)


def _item_uid(directory: str, path: str) -> str | None:
    if path.startswith(directory) and path.endswith(".yml"):
        return f"/{path[len(directory):-4]}"
    return None


def _abs_uid(uid: str, link_uid: str) -> str:
    if link_uid == ".":
        return uid
    return posixpath.normpath(posixpath.join(posixpath.dirname(uid), link_uid))


class _ItemClosureRule(ContentRule):

    def __init__(self, rule: dict) -> None:
        super().__init__(rule)
        self.dropped_paths: set[str] = set()
        self._dropped: set[str] = set()

    def _item_uid(self, path: str) -> str | None:
        for directory in self.rule["spec-directories"]:
            uid = _item_uid(directory, path)
            if uid is not None:
                return uid
        return None

    def matches(self, path: str) -> bool:
        return self._item_uid(path) is not None

    def prepare(self, items: dict[str, dict], removed: Iterable[str]) -> None:
        """
        Prepare the rule with the data of the items of the tip by path.  Raise
        a ValueError for a link of a kept item to an item whose path is in the
        removed paths of the tip.  A link to an item outside the specification
        directories of the rule refers to another repository.
        """
        removed_uids = {
            uid
            for uid in map(self._item_uid, removed) if uid is not None
        }
        kept: dict[str, dict] = {}
        for path, data in items.items():
            uid = self._item_uid(path)
            assert uid is not None
            if data.get("enabled-by", True) is False:
                self._dropped.add(uid)
                self.dropped_paths.add(path)
            else:
                kept[uid] = data
        for uid, data in sorted(kept.items()):
            for link in data.get("links", []):
                link_uid = _abs_uid(uid, link["uid"])
                if link_uid in removed_uids:
                    raise ValueError(f"the item {uid} links to the removed "
                                     f"item {link_uid}")

    def reset(self) -> None:
        """ Drop no item. """
        self.dropped_paths.clear()
        self._dropped.clear()

    def _remove_links(self, uid: str, data: dict) -> None:
        data["links"][:] = [
            link for link in data["links"]
            if _abs_uid(uid, link["uid"]) not in self._dropped
        ]

    def apply(self, path: str, content: bytes) -> bytes:
        uid = self._item_uid(path)
        assert uid is not None
        try:
            data = yaml.load(content, Loader=SafeLoader)
        except yaml.YAMLError as err:
            _keep_invalid(path, err)
            return content
        if not isinstance(data, dict) or not any(
                _abs_uid(uid, link["uid"]) in self._dropped
                for link in data.get("links", [])):
            return content
        return edit_attributes(path, content,
                               lambda data: self._remove_links(uid, data),
                               True)


class _CppRule(ContentRule):

    def apply(self, path: str, content: bytes) -> bytes:
        command = ["unifdef"]
        for name, value in self.rule["defined"].items():
            command.append(f"-D{name}" if value is
                           None else f"-D{name}={value}")
        command.extend(f"-U{name}" for name in self.rule["undefined"])
        result = subprocess.run(command,
                                input=content,
                                capture_output=True,
                                check=False)
        if result.returncode not in (0, 1):
            stderr = result.stderr.decode("utf-8", "replace").strip()
            raise ValueError(f"unifdef failed: {stderr}")
        return result.stdout


class _SubprocessRule(ContentRule):

    def __init__(self, rule: dict, substitute: Substitute, uid: str) -> None:
        super().__init__(rule)
        self._action = substitute(rule["subprocess"])
        self._env = make_subprocess_environment(uid, self._action["env"])

    def apply(self, path: str, content: bytes) -> bytes:
        action = self._action
        result = subprocess.run([*action["command"], path],
                                input=content,
                                capture_output=True,
                                cwd=action["working-directory"],
                                env=self._env,
                                check=False)
        expected = action["expected-return-code"]
        if expected is not None and result.returncode != expected:
            stderr = result.stderr.decode("utf-8", "replace").strip()
            raise ValueError(f"the subprocess ended with the status "
                             f"{result.returncode}: {stderr}")
        return result.stdout


class _PythonRule(ContentRule):

    def __init__(self, rule: dict, uid: str, index: int) -> None:
        super().__init__(rule)
        namespace: dict[str, Any] = {}
        code = compile(rule["code"], f"{uid}:content-rules[{index}]", "exec")
        exec(code, namespace)  # pylint: disable=exec-used
        self._filter_content = namespace["filter_content"]

    def apply(self, path: str, content: bytes) -> bytes:
        result = self._filter_content(path, content)
        if not isinstance(result, bytes):
            raise TypeError("filter_content() returned no bytes")
        return result


class ContentFilter:
    """
    Applies the content rules of the repository filter items in their order.
    """

    def __init__(self) -> None:
        self._rules: list[tuple[str, int, ContentRule]] = []
        self._closures: list[_ItemClosureRule] = []

    def __bool__(self) -> bool:
        return bool(self._rules)

    def add_rule(self, uid: str, index: int, rule: dict,
                 substitute: Substitute,
                 run_attribute_actions: RunAttributeActions) -> None:
        """ Add the content rule of the item at the index. """
        kind = rule["rule"]
        content_rule: ContentRule
        if kind == "replace":
            content_rule = _ReplaceRule(rule)
        elif kind == "regex":
            content_rule = _RegexRule(rule)
        elif kind == "structure":
            content_rule = _StructureRule(rule, run_attribute_actions)
        elif kind == "enabled-by":
            content_rule = _EnabledByRule(rule)
        elif kind == "item-closure":
            content_rule = _ItemClosureRule(rule)
            self._closures.append(content_rule)
        elif kind == "cpp":
            content_rule = _CppRule(rule)
        elif kind == "subprocess":
            content_rule = _SubprocessRule(rule, substitute, uid)
        else:
            assert kind == "python"
            content_rule = _PythonRule(rule, uid, index)
        self._rules.append((uid, index, content_rule))

    def count_selected(self,
                       paths: list[str]) -> list[tuple[str, int, str, int]]:
        """
        Return the item UID, the index, the kind and the count of selected
        paths of each content rule which selects at least one of the paths.
        """
        counts: list[tuple[str, int, str, int]] = []
        for uid, index, rule in self._rules:
            count = sum(1 for path in paths if rule.matches(path))
            if count:
                counts.append((uid, index, rule.rule["rule"], count))
        return counts

    def matches(self, path: str) -> bool:
        """ Return true, if a content rule applies to the path. """
        return any(rule.matches(path) for _, _, rule in self._rules)

    @property
    def dropped_paths(self) -> set[str]:
        """ Is the set of paths of the items which an item closure drops. """
        paths: set[str] = set()
        for closure in self._closures:
            paths.update(closure.dropped_paths)
        return paths

    def _apply(self, path: str, content: bytes,
               stop: ContentRule | None) -> bytes:
        for uid, index, rule in self._rules:
            if rule is stop:
                break
            if rule.matches(path):
                try:
                    content = rule.apply(path, content)
                except Exception as err:
                    raise ValueError(
                        f"{uid}: the content rule {index} of kind "
                        f"'{rule.rule['rule']}' cannot filter '{path}': "
                        f"{err}") from err
        return content

    def apply(self, path: str, content: bytes) -> bytes:
        """ Return the content of the file after the content rules. """
        return self._apply(path, content, None)

    def reset(self) -> None:
        """ Make the item closures drop no item. """
        for closure in self._closures:
            closure.reset()

    def prepare(self, files: Files, removed: Iterable[str] = ()) -> None:
        """
        Prepare the item closures with the files of the tip.  The files map
        each path to the reader of its content.  Each closure sees the items
        after the rules before it.  The removed paths are the paths of the tip
        which the path rules drop.
        """
        removed = list(removed)
        for closure in self._closures:
            items: dict[str, dict] = {}
            for path, read in sorted(files.items()):
                if closure.matches(path):
                    content = self._apply(path, read(), closure)
                    data = yaml.load(content, Loader=SafeLoader)
                    if isinstance(data, dict):
                        items[path] = data
            logging.info("prepare the item closure with %d items", len(items))
            closure.prepare(items, removed)
