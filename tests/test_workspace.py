# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the workspace and buildspace. """

# Copyright (C) 2025, 2026 embedded brains GmbH & Co. KG
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
import pytest

from specware import util

from specmake import (BuildItem, BuildspaceConfig, DirectoryState,
                      PackageComponent, WorkspaceConfig,
                      create_build_item_factory, create_workspace,
                      create_workspace_item_factory, export_to_buildspace)
from specmake.pkgworkspace import _WorkspaceItem


def _git_commit(directory, what):
    stdout = []
    status = util.run_command(["git", "rev-parse", what], directory, stdout)
    assert status == 0
    return stdout[0].strip()


def _create_workspace(tmp_dir, spec_dir):
    test_dir = os.path.dirname(__file__)
    if isinstance(spec_dir, str):
        spec_dir = [spec_dir]
    spec_dir.append("spec-pkg-wk/component")
    workspace_config = WorkspaceConfig(
        spec_directories=[os.path.join(test_dir, name) for name in spec_dir],
        workspace_directory=os.path.join(test_dir, "workspace"),
        cache_directory=os.path.join(tmp_dir, "cache-workspace"),
        factory=create_workspace_item_factory())
    workspace = create_workspace(workspace_config)
    workspace.director.package.item["deployment-directory"] = str(tmp_dir)
    return workspace


def _create_buildspace_from_workspace(tmp_dir, workspace):
    buildspace_config = BuildspaceConfig(
        spec_directory=os.path.join(tmp_dir, "spec"),
        cache_directory=os.path.join(tmp_dir, "cache-buildspace"),
        verify_specification_format=True,
        factory=create_build_item_factory())
    return export_to_buildspace(workspace, buildspace_config)


def _create_buildspace(tmp_dir, spec_dir):
    workspace = _create_workspace(tmp_dir, spec_dir)
    buildspace = _create_buildspace_from_workspace(tmp_dir, workspace)
    return buildspace, workspace


def test_workspace_not_implemented():
    with pytest.raises(NotImplementedError):
        _WorkspaceItem.get_buildspace_data(0)


def test_workspace_dir_patterns(tmp_path):
    buildspace, _ = _create_buildspace(str(tmp_path),
                                       "spec-pkg-wk/dir/patterns")
    buildspace.director["/dir"]["directory-state-type"] == "explicit"
    assert (tmp_path / "rc1" / "c1" / "c1").is_file()
    assert (tmp_path / "rcn" / "rcn" / "cn").is_file()
    assert (tmp_path / "c" / "a").is_file()
    assert (tmp_path / "rs" / "s").is_file()
    assert (tmp_path / "e" / "re").is_file()
    assert (tmp_path / "n").is_file()
    with open(tmp_path / "t.txt", "r", encoding="utf-8") as file:
        assert file.read() == f"{tmp_path}\n"


def test_workspace_file_single(tmpdir):
    buildspace, _ = _create_buildspace(tmpdir, "spec-pkg-wk/file/single")
    buildspace.director["/file"]["directory-state-type"] == "explicit"
    with open(os.path.join(tmpdir, "file", "c.txt"), "rb") as file:
        assert file.read() == b"b\n"


def test_workspace_file_list(tmpdir):
    buildspace, _ = _create_buildspace(tmpdir, "spec-pkg-wk/file/list")
    buildspace.director["/file"]["directory-state-type"] == "explicit"
    with open(os.path.join(tmpdir, "file", "c.txt"), "rb") as file:
        assert file.read() == b"b\n"


def test_workspace_file_no_file(tmpdir):
    with pytest.raises(ValueError, match="file: no source file available"):
        _create_buildspace(tmpdir, "spec-pkg-wk/file/no-file")


def test_workspace_repo_default(tmpdir):
    buildspace, workspace = _create_buildspace(
        tmpdir, ["spec-pkg-wk/repo/archive", "spec-pkg-wk/repo/default"])
    wk_repo = workspace.director["/repo"]
    assert wk_repo.substitute(
        "${.:/git-commit}") == "40abab3c7aca7f38d06f339d784fa08178588f47"
    assert wk_repo.substitute(
        "${.:/git-commit:main}") == "40abab3c7aca7f38d06f339d784fa08178588f47"
    assert wk_repo.substitute(
        "${.:/git-commit-head}") == "40abab3c7aca7f38d06f339d784fa08178588f47"
    repo = buildspace.director["/repo"]
    assert repo["commit"] == "40abab3c7aca7f38d06f339d784fa08178588f47"
    assert repo.lazy_verify()


def test_workspace_repo_clone_depth(tmpdir):
    buildspace, _ = _create_buildspace(
        tmpdir, ["spec-pkg-wk/repo/archive", "spec-pkg-wk/repo/clone-depth"])
    repo = buildspace.director["/repo"]
    assert repo["commit"] == "40abab3c7aca7f38d06f339d784fa08178588f47"
    assert repo.lazy_verify()


def test_workspace_repo_origin_url(tmpdir):
    buildspace, _ = _create_buildspace(
        tmpdir, ["spec-pkg-wk/repo/archive", "spec-pkg-wk/repo/origin-url"])
    repo = buildspace.director["/repo"]
    assert repo["commit"] == "40abab3c7aca7f38d06f339d784fa08178588f47"
    assert repo.lazy_verify()
    stdout: list[str] = []
    status = util.run_command(["git", "remote", "-v"], repo.directory, stdout)
    assert status == 0
    assert "https://foobar.org" in "".join(stdout)


def test_workspace_repo_fetch(tmpdir):
    buildspace, workspace = _create_buildspace(tmpdir, [
        "spec-pkg-wk/repo/archive", "spec-pkg-wk/repo/default",
        "spec-pkg-wk/repo/fetch"
    ])
    archive = buildspace.director["/archive"]
    repo = buildspace.director["/repo"]
    assert repo["commit"] == "40abab3c7aca7f38d06f339d784fa08178588f47"
    assert repo.lazy_verify()
    status = util.run_command(["git", "commit", "--amend", "-m", "message"],
                              archive.directory)
    assert status == 0
    wk_repo_2 = workspace.director["/repo-2"]
    commit = _git_commit(archive.directory, "HEAD")
    wk_repo_2.item["commit"] = commit
    buildspace_2 = _create_buildspace_from_workspace(tmpdir, workspace)
    repo_2 = buildspace_2.director["/repo-2"]
    assert _git_commit(repo_2.directory, "other") == commit
    assert _git_commit(repo_2.directory, "post-clone") == commit


def test_workspace_test_log(tmpdir):
    buildspace, _ = _create_buildspace(tmpdir, "spec-pkg-wk/test-log")
    buildspace.director["/file"]["directory-state-type"] == "test-log"
    with open(os.path.join(tmpdir, "file", "c.txt"), "rb") as file:
        assert file.read() == b"b\n"


def test_workspace_component(tmpdir):
    test_dir = os.path.dirname(__file__)
    workspace_config = WorkspaceConfig(
        spec_directories=[
            os.path.join(test_dir, name)
            for name in ("spec-pkg", "spec-pkg-component")
        ],
        workspace_directory=os.path.join(test_dir, "workspace"),
        cache_directory=os.path.join(tmpdir, "cache"))
    workspace = create_workspace(workspace_config)

    package = workspace.director.package
    assert isinstance(package, PackageComponent)
    assert package.item["a"] == "a"
    assert package.item["b"] == "tb"
    assert package.item["c"] == "a/${.:/b}"
    assert package["c"] == "a/tb"
    assert package.item["d"] == ["d", "td"]
    assert package.item["e"] == {"e0": 0, "e1": 1}
    assert package.item["list"] == [{
        "k": 6
    }, {
        "k": 1
    }, {
        "k": 5
    }, 2, [{
        "k": 8
    }, {
        "k": 3
    }, {
        "k": 4
    }, {
        "k": 7
    }]]
    assert package.item["list-2"] == [{"b": 2}]
    assert package.item["list-3"] == ["y"]
    assert package.item["list-4"] == [["Y"]]
    assert package.item["list-5"] == ["a"]
    assert sorted(package.selection.enabled_set) == [
        "pkg.arch.furch", "pkg.bsp-family.furch.lurch",
        "pkg.bsp-family.furch.lurch-2", "pkg.bsp.furch.blur",
        "pkg.bsp.furch.blur-2", "pkg.feature.blue", "pkg.feature.green",
        "pkg.feature.red"
    ]

    work_bsp = workspace.director["/pkg/arch/bsp/cfg/component"]
    assert work_bsp.item["has-sibling-0"] == "has-sibling-0"
    assert work_bsp.item["has-sibling-1"] == "has-sibling-1"
    assert work_bsp.item["has-sibling-2"] == "has-sibling-2"
    assert work_bsp.item["has-sibling-3"] == "has-sibling-3"
    assert work_bsp.item["has-sibling-4"] == "has-sibling-4"

    work_item_a = workspace.director["/pkg/template-item-a"]
    assert isinstance(work_item_a, BuildItem)

    work_item_b = workspace.director["/pkg/template-item-b"]
    assert isinstance(work_item_b, BuildItem)

    buildspace_config = BuildspaceConfig(
        spec_directory=os.path.join(tmpdir, "build", "spec"),
        cache_directory=os.path.join(tmpdir, "build", "cache"),
        use_git=True,
        verify_specification_format=True)

    assert not os.path.exists(
        os.path.join(buildspace_config.spec_directory,
                     "pkg/template-item-a.json"))

    deployment_directory = str(tmpdir)
    status = util.run_command(["git", "init"], deployment_directory)
    assert status == 0
    package.item["deployment-directory"] = deployment_directory

    buildspace = export_to_buildspace(workspace, buildspace_config)

    build_item_a = buildspace.director["/pkg/template-item-a"]
    assert isinstance(build_item_a, DirectoryState)
    assert build_item_a.directory == "."
    assert os.path.exists(
        os.path.join(buildspace_config.spec_directory,
                     "pkg/template-item-a.json"))

    assert work_item_a["directory"] == "."
    work_item_a["directory"] = "foobar"

    buildspace_2 = export_to_buildspace(workspace, buildspace_config)

    build_item_a_2 = buildspace_2.director["/pkg/template-item-a"]
    assert isinstance(build_item_a_2, DirectoryState)
    assert build_item_a_2.directory == "foobar"

    assert build_item_a.directory == "."
    build_item_a.item.load()
    assert build_item_a.directory == "foobar"

    assert "/pkg/source/delete-me" in buildspace_2.cache
    workspace.director.remove("/pkg/source/delete-me")
    buildspace_3 = export_to_buildspace(workspace, buildspace_config)
    assert "/pkg/source/delete-me" not in buildspace_3.cache
