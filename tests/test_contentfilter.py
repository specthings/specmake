# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the contentfilter module. """

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

import logging
import sys

import pytest

from specmake.contentfilter import (ContentFilter, ContentRule,
                                    edit_attributes, glob_to_regex,
                                    simplify_enabled_by)


@pytest.mark.parametrize("glob, path, match", [
    ("**/*.h", "a.h", True),
    ("**/*.h", "x/y/a.h", True),
    ("**/*.h", "a.c", False),
    ("*.c", "a.c", True),
    ("*.c", "x/a.c", False),
    ("a/**", "a/b/c", True),
    ("a/**", "b/c", False),
    ("?.c", "a.c", True),
    ("?.c", "/.c", False),
    ("*.[ch]", "a.h", True),
    ("*.[ch]", "a.s", False),
    ("a[", "a[", True),
    ("a.b", "axb", False),
])
def test_glob_to_regex(glob, path, match):
    assert (glob_to_regex(glob).fullmatch(path) is not None) == match


def _set_b(data):
    data["b"] = 2


def _no_change(data):
    data["a"] = data["a"]


_ITEM = b"""a: 1
links: []
"""

_YAML = b"""# comment
a: 1   # one
"""

_YAML_WRAPPED = b"""a: x
  y
"""


def test_edit_attributes():
    assert edit_attributes("a.json", b'{\n  "a": 1\n}\n', _set_b,
                           True) == b'{\n  "a": 1,\n  "b": 2\n}\n'
    assert edit_attributes("a.json", b'{"a": 1}', _set_b,
                           True) == b'{"a": 1, "b": 2}'
    with pytest.raises(ValueError, match="does not reproduce the JSON"):
        edit_attributes("a.json", b'{"a":1}', _set_b, True)
    assert edit_attributes("a.json", b'{"a":1}', _set_b,
                           False) == b'{"a": 1, "b": 2}'
    assert edit_attributes("a.yml", _ITEM, _set_b,
                           True) == b"a: 1\nb: 2\nlinks: []\n"
    assert edit_attributes("a.yaml", _YAML, _set_b,
                           True) == b"# comment\na: 1   # one\nb: 2\n"
    with pytest.raises(ValueError, match="does not reproduce the YAML"):
        edit_attributes("a.yaml", _YAML_WRAPPED, _set_b, True)
    assert edit_attributes("a.yaml", _YAML_WRAPPED, _set_b,
                           False) == b"a: x y\nb: 2\n"
    with pytest.raises(ValueError, match="no YAML or JSON file"):
        edit_attributes("a.txt", b"", _set_b, True)
    assert edit_attributes("a.yaml", _YAML_WRAPPED, _no_change,
                           True) == _YAML_WRAPPED
    assert edit_attributes("a.json", b'{"a":1}', _no_change,
                           True) == b'{"a":1}'


def test_edit_attributes_invalid(caplog):
    caplog.set_level(logging.WARNING)
    assert edit_attributes("a.yml", b"a: b\nc\n", _set_b, True) == b"a: b\nc\n"
    assert "a.yml: keep the content which is no valid data: " in caplog.text
    assert edit_attributes("a.json", b"{", _set_b, True) == b"{"
    assert "a.json: keep the content which is no valid data: " in caplog.text


@pytest.mark.parametrize("enabled_by, simplified", [
    (True, True),
    ("a", True),
    ("b", False),
    ("c", "c"),
    (["a", "c"], True),
    (["b", "c"], ["c"]),
    (["b"], False),
    ([], False),
    ({
        "and": ["a", "c"]
    }, {
        "and": ["c"]
    }),
    ({
        "and": ["b", "c"]
    }, False),
    ({
        "and": ["a"]
    }, True),
    ({
        "or": ["b", "c"]
    }, {
        "or": ["c"]
    }),
    ({
        "or": ["a", "c"]
    }, True),
    ({
        "not": "a"
    }, False),
    ({
        "not": "c"
    }, {
        "not": "c"
    }),
    ({
        "not": ["b", "c"]
    }, {
        "not": ["c"]
    }),
    ({
        "has-sibling": "a"
    }, {
        "has-sibling": "a"
    }),
    ({
        "and": "a"
    }, {
        "and": "a"
    }),
    ({
        "and": [],
        "or": []
    }, {
        "and": [],
        "or": []
    }),
])
def test_simplify_enabled_by(enabled_by, simplified):
    assert simplify_enabled_by(enabled_by, {
        "a": True,
        "b": False
    }) == simplified


def test_content_rule_not_implemented():
    with pytest.raises(NotImplementedError):
        ContentRule({}).apply("a", b"")


def _substitute(value):
    return value


def _run_attribute_actions(actions, data):
    for action in actions:
        data[action["path"]] = action["value"]


def _filter(*rules):
    content_filter = ContentFilter()
    for index, rule in enumerate(rules):
        content_filter.add_rule("/f", index, {
            "enabled-by": True,
            **rule
        }, _substitute, _run_attribute_actions)
    return content_filter


def test_content_filter_empty():
    content_filter = ContentFilter()
    assert not content_filter
    assert not content_filter.matches("a")
    assert content_filter.apply("a", b"x") == b"x"
    assert not content_filter.dropped_paths


def test_content_filter_regex():
    content_filter = _filter(
        {
            "rule": "regex",
            "files": ["*.txt"],
            "pattern": "^x",
            "replacement": "y",
            "flags": ["MULTILINE", "IGNORECASE"],
            "count": 0
        }, {
            "rule": "regex",
            "files": ["**"],
            "pattern": "y",
            "replacement": "z",
            "flags": [],
            "count": 1
        })
    assert content_filter
    assert content_filter.matches("a.c")
    assert content_filter.apply("a.txt", b"x\nX\n\xff") == b"z\ny\n\xff"
    assert content_filter.apply("a.c", b"y\ny\n") == b"z\ny\n"


def test_content_filter_structure():
    content_filter = _filter({
        "rule": "structure",
        "files": ["*.yml"],
        "accept-format-changes": False,
        "attribute-actions": [{
            "path": "b",
            "value": 2
        }]
    })
    assert content_filter.apply("a.yml", _ITEM) == b"a: 1\nb: 2\nlinks: []\n"
    with pytest.raises(ValueError,
                       match=r"/f: the content rule 0 of kind 'structure' "
                       r"cannot filter 'a.yml': a dump of the unchanged"):
        content_filter.apply("a.yml", _YAML_WRAPPED)


def test_content_filter_enabled_by():
    content_filter = _filter({
        "rule": "enabled-by",
        "files": ["*.yml"],
        "symbols": {
            "a": False
        }
    })
    assert content_filter.apply(
        "a.yml", b"enabled-by: a\nx:\n- enabled-by:\n  - a\n  - b\n"
    ) == b"enabled-by: false\nx:\n- enabled-by:\n  - b\n"


def _item(enabled_by, *links):
    text = f"enabled-by: {enabled_by}\nlinks:"
    if not links:
        return f"{text} []\n".encode("utf-8")
    for uid in links:
        text += f"\n- role: r\n  uid: {uid}"
    return f"{text}\n".encode("utf-8")


def _closure_filter():
    return _filter(
        {
            "rule": "replace",
            "files": ["spec/g.yml"],
            "content": "enabled-by: false\nlinks: []\n"
        }, {
            "rule": "enabled-by",
            "files": ["spec/**/*.yml"],
            "symbols": {
                "x": False
            }
        }, {
            "rule": "item-closure",
            "spec-directories": ["spec/"]
        })


def _readers(files):
    return {
        path: (lambda content=content: content)
        for path, content in files.items()
    }


def test_content_filter_item_closure():
    content_filter = _closure_filter()
    files = {
        "spec/a.yml": _item("true", "b", "/c/d", "."),
        "spec/b.yml": _item("x"),
        "spec/c/d.yml": _item("true", "../a"),
        "spec/e.yml": _item("true"),
        "spec/f.yml": b"- x\n",
        "spec/g.yml": b"replaced",
        "spec/h.txt": b"",
        "other.yml": b"",
    }
    content_filter.prepare(_readers(files))
    assert content_filter.dropped_paths == {"spec/b.yml", "spec/g.yml"}
    assert not content_filter.matches("other.yml")
    assert not content_filter.matches("spec/h.txt")
    assert content_filter.apply("spec/a.yml", files["spec/a.yml"]) == _item(
        "true", "/c/d", ".")
    assert content_filter.apply("spec/c/d.yml",
                                files["spec/c/d.yml"]) == _item(
                                    "true", "../a")
    assert content_filter.apply("spec/f.yml", b"- x\n") == b"- x\n"
    assert content_filter.apply("spec/i.yml", b"a: b\nc\n") == b"a: b\nc\n"
    content_filter.reset()
    assert not content_filter.dropped_paths


def test_content_filter_item_closure_removed_link():
    content_filter = _closure_filter()
    files = {"spec/a.yml": _item("true", "b", "/other/c")}
    content_filter.prepare(_readers(files), ["other.txt"])
    assert not content_filter.dropped_paths
    with pytest.raises(ValueError,
                       match="the item /a links to the removed item /b"):
        content_filter.prepare(_readers(files), ["spec/b.yml"])


_CODE = b"""#ifdef A
a
#endif
#if B == 2
b
#endif
#ifdef C
c
#endif
#ifdef D
d
#endif
"""


def test_content_filter_cpp():
    content_filter = _filter({
        "rule": "cpp",
        "files": ["*.c"],
        "defined": {
            "A": None,
            "B": "2"
        },
        "undefined": ["C"]
    })
    assert content_filter.apply("a.c", _CODE) == b"a\nb\n#ifdef D\nd\n#endif\n"
    assert content_filter.apply("a.c", b"x\n") == b"x\n"
    with pytest.raises(ValueError, match="unifdef failed: .*"):
        content_filter.apply("a.c", b"#ifdef A\n")


_SCRIPT = ("import os, sys; "
           "sys.stdout.write(sys.stdin.read().upper() + sys.argv[1] + "
           "os.environ['X']); sys.exit(int(os.environ['STATUS']))")


def _subprocess_filter(tmpdir, status, expected):
    return _filter({
        "rule": "subprocess",
        "files": ["*.txt"],
        "subprocess": {
            "command": [sys.executable, "-c", _SCRIPT],
            "env": [{
                "action": "set",
                "name": "X",
                "value": "!"
            }, {
                "action": "set",
                "name": "STATUS",
                "value": status
            }],
            "expected-return-code":
            expected,
            "working-directory":
            str(tmpdir)
        }
    })


def test_content_filter_subprocess(tmpdir):
    assert _subprocess_filter(tmpdir, "0", None).apply("a.txt",
                                                       b"x") == b"Xa.txt!"
    assert _subprocess_filter(tmpdir, "3", 3).apply("a.txt",
                                                    b"x") == b"Xa.txt!"
    assert _subprocess_filter(tmpdir, "1", None).apply("a.txt",
                                                       b"x") == b"Xa.txt!"
    with pytest.raises(ValueError,
                       match="the subprocess ended with the status 1"):
        _subprocess_filter(tmpdir, "1", 0).apply("a.txt", b"x")


def test_content_filter_python():
    content_filter = _filter({
        "rule":
        "python",
        "files": ["*.txt"],
        "code":
        "def filter_content(path, content):\n"
        "    if path == 'b.txt':\n"
        "        return 'x'\n"
        "    return content + path.encode()\n"
    })
    assert content_filter.apply("a.txt", b"x") == b"xa.txt"
    with pytest.raises(ValueError, match="filter_content\\(\\) returned no"):
        content_filter.apply("b.txt", b"x")
