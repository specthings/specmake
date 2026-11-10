# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the repository filter. """

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

import copy
import logging
import os
import subprocess

import pytest

from specware import run_command

import specmake
from specmake.pkgworkspace import (_filter_items, _ItemFilter,
                                   _prepare_content_filter)
from specmake.repositoryfilter import RepositoryFilter

from .test_workspace import (_create_buildspace,
                             _create_buildspace_from_workspace,
                             _create_workspace)

_BASELINE = "40abab3c7aca7f38d06f339d784fa08178588f47"

_SPEC = [
    "spec-pkg-wk/repo/archive", "spec-pkg-wk/repo/default",
    "spec-pkg-wk/repo/filter"
]


def _git(directory, *args):
    stdout = []
    status = run_command([
        "git", "-c", "user.name=A", "-c", "user.email=a@b", "-c",
        "commit.gpgsign=false", *args
    ], directory, stdout)
    assert status == 0
    return "\n".join(stdout).strip()


def _commit(directory, message, files, removed=()):
    for path, content in files.items():
        file_path = os.path.join(directory, path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as dst:
            dst.write(content)
        _git(directory, "add", path)
    for path in removed:
        _git(directory, "rm", "--quiet", path)
    _git(directory, "commit", "--no-verify", "--quiet", "-m", message)
    return _git(directory, "rev-parse", "HEAD")


def _add_history(source):
    _commit(source, "Add internal file", {".eb/config.yml": "internal\n"})
    _commit(source, "Add code", {"code.c": "code\n", "private/a.txt": "a\n"})
    _commit(source, "Add shared file", {
        "private/shared.txt": "real\n",
        "private/public.txt": "public\n"
    })
    _commit(source, "Change shared file", {"private/shared.txt": "real 2\n"})
    return _commit(source, "Change private file", {"private/a.txt": "b\n"})


def _files(directory):
    return sorted(_git(directory, "ls-files").splitlines())


def _all_paths(directory):
    return set(
        _git(directory, "log", "--all", "--format=",
             "--name-only").splitlines()) - {""}


def test_repository_filter_keep():
    repository_filter = RepositoryFilter("/f", _BASELINE, {
        "a/": False,
        "a/b/": True,
        "a/b/c": False,
        "a/x": True
    })
    assert repository_filter.keep("x")
    assert not repository_filter.keep("a/y")
    assert repository_filter.keep("a/x")
    assert repository_filter.keep("a/b/y")
    assert not repository_filter.keep("a/b/c")
    assert repository_filter.keep("a/b/c/d")
    assert repository_filter.keep("a/b/cd")
    repository_filter = RepositoryFilter("/f", _BASELINE, {
        "": False,
        "a/b": False
    })
    assert repository_filter.keep("x")
    assert repository_filter.keep("a/b/c")
    assert not repository_filter.keep("a/b")
    digest = repository_filter.digest()
    repository_filter.content_rules.append({"rule": "replace"})
    assert repository_filter.digest() != digest


def test_repository_filter_history(caplog, tmpdir):
    caplog.set_level(logging.WARNING)
    buildspace, workspace = _create_buildspace(tmpdir, _SPEC)
    assert ("/repo: the rules drop 1 paths of the baseline "
            f"{_BASELINE}, they stay unchanged up to the first filtered "
            "commit which changes them: README.md") in caplog.text
    repo = buildspace.director["/repo"]
    assert repo["commit"] == _BASELINE
    assert repo.lazy_verify()

    source = os.path.join(tmpdir, "source", "repo")
    head = _add_history(source)
    wk_repo = workspace.director["/repo"]
    wk_repo.item["commit"] = head
    buildspace = _create_buildspace_from_workspace(tmpdir, workspace)
    repo = buildspace.director["/repo"]
    commit = repo["commit"]
    assert commit != head
    assert repo.lazy_verify()
    directory = repo.directory
    assert _git(directory, "log", "--format=%s") == "\n".join(
        ("Add shared file", "Add code", "Initial import"))
    assert _files(directory) == [
        "README.md", "code.c", "private/public.txt", "private/shared.txt"
    ]
    with open(os.path.join(directory, "private", "shared.txt"),
              encoding="utf-8") as src:
        assert src.read() == "empty\n"
    assert not _all_paths(directory) & {".eb/config.yml", "private/a.txt"}
    assert _git(directory, "remote", "get-url",
                "origin") == wk_repo["directory"]

    # The same commit and filter give the same result
    buildspace = _create_buildspace_from_workspace(tmpdir, workspace)
    assert buildspace.director["/repo"]["commit"] == commit

    # A change of the enabled rules filters the repository again
    rules = workspace.cache["/filter"]["path-rules"]
    rules[1]["enabled-by"] = True
    buildspace = _create_buildspace_from_workspace(tmpdir, workspace)
    repo = buildspace.director["/repo"]
    assert repo["commit"] != commit
    assert "code.c" not in _files(repo.directory)
    rules[1]["enabled-by"] = False

    # The clone depth applies to the filtered history
    wk_repo.item["clone-depth"] = 1
    wk_repo.item["origin-branch"] = None
    buildspace = _create_buildspace_from_workspace(tmpdir, workspace)
    repo = buildspace.director["/repo"]
    assert repo["commit"] == commit
    assert repo.lazy_verify()
    assert _git(repo.directory, "rev-parse",
                "--is-shallow-repository") == "true"


def _drop_and_keep(workspace):
    rule = workspace.cache["/filter"]["path-rules"][1]
    rule["enabled-by"] = True
    rule["keep"] = [".eb/"]


def _bad_baseline(workspace):
    workspace.cache["/filter"]["baseline"] = "a" * 40
    workspace.director["/repo"].item["origin-commit"] = None


def _bad_origin_commit(workspace):
    source = os.path.join(workspace.director.package["deployment-directory"],
                          "source", "repo")
    workspace.director["/repo"].item["origin-commit"] = _add_history(source)


@pytest.mark.parametrize("modify, match", [
    (_drop_and_keep, "'.eb/' is in an enabled drop and keep list"),
    (_bad_baseline, "is no ancestor of commit"),
    (_bad_origin_commit, "is no ancestor of the baseline"),
])
def test_repository_filter_errors(tmpdir, modify, match):
    workspace = _create_workspace(tmpdir, _SPEC)
    _create_buildspace_from_workspace(tmpdir, workspace)
    modify(workspace)
    with pytest.raises(ValueError, match=match):
        _create_buildspace_from_workspace(tmpdir, workspace)


def _add_filter(workspace, baseline):
    data = copy.deepcopy(workspace.cache["/filter"].data)
    data["baseline"] = baseline
    data["links"][0]["uid"] = "/repo"
    data["path-rules"] = [{"drop": ["code.c"], "enabled-by": True, "keep": []}]
    workspace.cache.add_item("/filter-2", data)


def test_repository_filter_two_items(tmpdir):
    workspace = _create_workspace(tmpdir, _SPEC)
    _create_buildspace_from_workspace(tmpdir, workspace)
    source = os.path.join(tmpdir, "source", "repo")
    workspace.director["/repo"].item["commit"] = _add_history(source)
    _add_filter(workspace, _BASELINE)
    buildspace = _create_buildspace_from_workspace(tmpdir, workspace)
    assert _files(buildspace.director["/repo"].directory) == [
        "README.md", "private/public.txt", "private/shared.txt"
    ]


def test_repository_filter_two_baselines(tmpdir):
    workspace = _create_workspace(tmpdir, _SPEC)
    _create_buildspace_from_workspace(tmpdir, workspace)
    _add_filter(workspace, "a" * 40)
    with pytest.raises(ValueError,
                       match="/filter-2: the baseline a+ differs from the "
                       f"baseline {_BASELINE} of the other repository "
                       "filters of /repo"):
        _create_buildspace_from_workspace(tmpdir, workspace)


def test_repository_filter_non_utf8_names(tmpdir):
    workspace = _create_workspace(tmpdir, _SPEC)
    _create_buildspace_from_workspace(tmpdir, workspace)
    source = os.path.join(tmpdir, "source", "repo")
    blob = subprocess.run(["git", "hash-object", "-w", "--stdin"],
                          cwd=source,
                          input=b"x\n",
                          check=True,
                          capture_output=True).stdout.strip()
    index_info = b"".join(b"100644 " + blob + b"\t" + name + b"\0"
                          for name in (b"private/\xff.txt", b"\xfe.txt"))
    subprocess.run(["git", "update-index", "-z", "--index-info"],
                   cwd=source,
                   input=index_info,
                   check=True)
    _commit(source, "Add names", {})
    subprocess.run([b"git", b"rm", b"--cached", b"--quiet", b"\xfe.txt"],
                   cwd=source,
                   check=True)
    workspace.director["/repo"].item["commit"] = _commit(
        source, "Remove name", {})
    buildspace = _create_buildspace_from_workspace(tmpdir, workspace)
    names = subprocess.run(
        ["git", "log", "-z", "--format=", "--name-only", "HEAD"],
        cwd=buildspace.director["/repo"].directory,
        check=True,
        capture_output=True).stdout.split(b"\0")
    assert b"\xfe.txt" in names
    assert b"private/\xff.txt" not in names


def test_repository_filter_warning_limit(caplog, tmpdir):
    caplog.set_level(logging.WARNING)
    directory = str(tmpdir)
    _git(directory, "init", "--quiet")
    paths = [f"d/{index:02}" for index in range(11)]
    baseline = _commit(directory, "Add files", {path: "x\n" for path in paths})
    repository_filter = RepositoryFilter("/f", baseline, {})
    repository_filter.run(directory, baseline)
    assert "/f: the rules drop" not in caplog.text
    repository_filter.path_rules["d/"] = False
    repository_filter.run(directory, baseline)
    listed = ", ".join(paths[:10])
    assert (f"/f: the rules drop 11 paths of the baseline "
            f"{baseline}, they stay unchanged up to the first filtered "
            f"commit which changes them: {listed}, ...") in caplog.text


def test_repository_filter_warning_content_rules(caplog, tmpdir):
    caplog.set_level(logging.WARNING)
    directory = str(tmpdir)
    _git(directory, "init", "--quiet")
    baseline = _commit(
        directory, "Add files", {
            "a.txt": "x\n",
            "b.txt": "x\n",
            "c.c": "x\n",
            "spec/d.yml": "enabled-by: false\nlinks: []\n"
        })
    repository_filter = RepositoryFilter("/f", baseline, {"b.txt": False})
    for index, rule in enumerate([{
            "rule": "replace",
            "files": ["*.txt"],
            "content": "y\n"
    }, {
            "rule": "replace",
            "files": ["*.h"],
            "content": "y\n"
    }, {
            "rule": "item-closure",
            "spec-directories": ["spec/"]
    }]):
        repository_filter.content_filter.add_rule("/i", index, rule, None,
                                                  None)
    repository_filter.run(directory, baseline)
    assert (f"/f: the rules drop 2 paths of the baseline {baseline}, they "
            "stay unchanged up to the first filtered commit which changes "
            "them: b.txt, spec/d.yml") in caplog.text
    assert ("/f: the content rule 0 of kind 'replace' of /i selects 1 files "
            f"of the baseline {baseline}, they stay unchanged up to the first "
            "filtered commit which changes them") in caplog.text
    assert "content rule 1 " not in caplog.text
    assert "content rule 2 " not in caplog.text


def test_repository_filter_fetch_error(tmpdir, monkeypatch):

    def _run_command(args, cwd=None, stdout=None, status=None):
        if "fetch" in args and "--no-tags" in args:
            return 1
        return run_command(args, cwd, stdout, status)

    monkeypatch.setattr(specmake.pkgworkspace, "run_command", _run_command)
    with pytest.raises(IOError, match="cannot fetch commit"):
        _create_buildspace(tmpdir, _SPEC)


_EMPTY_TERM = """SPDX-License-Identifier: CC-BY-SA-4.0
copyrights: []
enabled-by: true
glossary-type: term
links: []
term: empty
text: Empty.
type: glossary
"""

_ITEMS = os.path.join(os.path.dirname(__file__), "spec-pkg-wk", "repo",
                      "items")

_REPLACE_RULE = {
    "rule": "replace",
    "enabled-by": True,
    "files": ["replaced.yml"],
    "content": _EMPTY_TERM
}


def _create_items_workspace(tmpdir, spec=()):
    workspace = _create_workspace(tmpdir,
                                  [*_SPEC, "spec-pkg-wk/repo/items", *spec])
    workspace.cache["/filter"]["content-rules"] = [_REPLACE_RULE]
    workspace.cache["/repo"]["directory"] = f"file://{_ITEMS}"
    return workspace


def test_repository_filter_items(tmpdir):
    workspace = _create_items_workspace(tmpdir)
    cache = workspace.cache
    file = cache["/replaced"].file
    assert _filter_items(workspace) == ["/private/dropped"]
    assert "/kept" in cache
    assert "/private/dropped" not in cache
    assert "/filter" in cache
    replaced = cache["/replaced"]
    assert replaced["term"] == "empty"
    assert replaced.file == file
    assert not replaced["links"]
    assert cache["/linker"].parent("glossary-member") is replaced
    assert replaced.child("glossary-member") is cache["/linker"]
    assert not _filter_items(workspace)


def test_repository_filter_items_disabled(tmpdir, monkeypatch):
    workspace = _create_items_workspace(tmpdir)
    monkeypatch.setattr(type(workspace.cache["/repo"]), "enabled",
                        property(lambda _item: False))
    assert not _filter_items(workspace)
    assert "/private/dropped" in workspace.cache
    assert workspace.cache["/replaced"]["term"] == "replaced"


def test_repository_filter_items_nested(tmpdir):
    workspace = _create_items_workspace(tmpdir, ["spec-pkg-wk/repo/fetch"])
    workspace.cache["/repo-2"]["directory"] = os.path.join(_ITEMS, "private")
    assert not _filter_items(workspace)
    assert "/private/dropped" in workspace.cache
    assert workspace.cache["/replaced"]["term"] == "empty"


def test_repository_filter_items_export(tmpdir, monkeypatch):
    workspace = _create_workspace(tmpdir, _SPEC)
    filtered = []
    monkeypatch.setattr(specmake.pkgworkspace, "_filter_items",
                        filtered.append)
    _create_buildspace_from_workspace(tmpdir, workspace)
    assert filtered == [workspace]


_CONTENT_RULES = [{
    "rule": "regex",
    "enabled-by": True,
    "files": ["**/*.txt"],
    "pattern": "secret",
    "replacement": "public",
    "flags": [],
    "count": 0
}, {
    "rule": "regex",
    "enabled-by": False,
    "files": ["**"],
    "pattern": ".*",
    "replacement": "",
    "flags": [],
    "count": 0
}, {
    "rule": "enabled-by",
    "enabled-by": True,
    "files": ["spec/**/*.yml"],
    "symbols": {
        "x": False
    }
}, {
    "rule": "item-closure",
    "enabled-by": True,
    "spec-directories": ["spec/"]
}]

_ITEM_A = """enabled-by: true
links:
- role: r
  uid: b
"""


def _add_content_history(source):
    os.symlink("notes.txt", os.path.join(source, "link.txt"))
    _git(source, "add", "link.txt")
    _commit(
        source, "Add items", {
            "notes.txt": "secret\n",
            "spec/a.yml": _ITEM_A,
            "spec/b.yml": "enabled-by: x\nlinks: []\n"
        })
    _commit(source, "Change notes", {"notes.txt": "secret 2\n"})
    return _commit(source, "Revert notes", {"notes.txt": "secret\n"})


def _show(directory, path):
    return _git(directory, "show", f"HEAD:{path}")


def test_repository_filter_content_rules(tmpdir):
    workspace = _create_workspace(tmpdir, _SPEC)
    buildspace = _create_buildspace_from_workspace(tmpdir, workspace)
    commit = buildspace.director["/repo"]["commit"]
    source = os.path.join(tmpdir, "source", "repo")
    workspace.director["/repo"].item["commit"] = _add_content_history(source)
    buildspace = _create_buildspace_from_workspace(tmpdir, workspace)
    path_commit = buildspace.director["/repo"]["commit"]
    workspace.cache["/filter"]["content-rules"] = _CONTENT_RULES
    buildspace = _create_buildspace_from_workspace(tmpdir, workspace)
    repo = buildspace.director["/repo"]
    assert repo["commit"] not in (commit, path_commit)
    directory = repo.directory
    assert "spec/b.yml" not in _all_paths(directory)
    assert _show(directory, "spec/a.yml") == "enabled-by: true\nlinks: []"
    assert _show(directory, "notes.txt") == "public"
    assert _git(directory, "show", "HEAD~1:notes.txt") == "public 2"
    assert _show(directory, "link.txt") == "notes.txt"


def test_repository_filter_content_rules_error(tmpdir):
    workspace = _create_workspace(tmpdir, _SPEC)
    _create_buildspace_from_workspace(tmpdir, workspace)
    source = os.path.join(tmpdir, "source", "repo")
    workspace.director["/repo"].item["commit"] = _commit(
        source, "Add items", {
            "spec/a.yml": _ITEM_A,
            "spec/b.yml": "enabled-by: true\nlinks: []\n"
        })
    workspace.cache["/filter"]["content-rules"] = _CONTENT_RULES
    workspace.cache["/filter"]["path-rules"].append({
        "drop": ["spec/b.yml"],
        "enabled-by": True,
        "keep": []
    })
    with pytest.raises(ValueError,
                       match="the item /a links to the removed item /b"):
        _create_buildspace_from_workspace(tmpdir, workspace)


@pytest.mark.parametrize("file, text", [("kept.yml", "The changed term.\n"),
                                        ("linker.yml", "The kept term.\n")])
def test_repository_filter_items_content_rules(tmpdir, file, text):
    workspace = _create_items_workspace(tmpdir)
    workspace.cache["/filter"]["content-rules"] = [
        _REPLACE_RULE, {
            "rule": "regex",
            "enabled-by": True,
            "files": [file],
            "pattern": "The (kept|linker) term",
            "replacement": "The changed term",
            "flags": [],
            "count": 0
        }, {
            "rule":
            "structure",
            "enabled-by":
            True,
            "files": ["linker.yml"],
            "accept-format-changes":
            False,
            "attribute-actions": [{
                "action": "remove",
                "enabled-by": True,
                "path": "/links[attr(uid)='replaced']"
            }, {
                "action": "set",
                "enabled-by": True,
                "path": "/enabled-by",
                "value": False
            }]
        }, {
            "rule": "item-closure",
            "enabled-by": True,
            "spec-directories": [""]
        }
    ]
    cache = workspace.cache
    assert sorted(_filter_items(workspace)) == ["/linker", "/private/dropped"]
    assert cache["/kept"]["text"] == text
    assert cache["/replaced"]["term"] == "empty"


def test_repository_filter_prepare_directory(tmpdir):
    directory = str(tmpdir)
    for path in (".git/a.yml", "a.yml", "b/c.yml"):
        os.makedirs(os.path.dirname(os.path.join(directory, path)),
                    exist_ok=True)
        with open(os.path.join(directory, path), "w", encoding="utf-8") as dst:
            dst.write("enabled-by: false\nlinks: []\n")
    repository_filter = RepositoryFilter("/f", _BASELINE, {})
    repository_filter.content_filter.add_rule("/f", 0, {
        "rule": "item-closure",
        "enabled-by": True,
        "spec-directories": [""]
    }, None, None)
    _prepare_content_filter(
        _ItemFilter(os.path.join(directory, ""), repository_filter))
    assert repository_filter.content_filter.dropped_paths == {
        "a.yml", "b/c.yml"
    }
