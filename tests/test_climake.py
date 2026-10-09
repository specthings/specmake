# SPDX-License-Identifier: BSD-2-Clause
""" Tests the command to make items of a package. """

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

import pytest

import specmake.climake
from specmake.climake import climake


class _Director:

    def __init__(self):
        self.package = {"deployment-directory": "deployment"}
        self.git_directory = None
        self.builds = []

    def build_package(self, only, force, skip):
        self.builds.append((only, force, skip))


class _Buildspace:

    def __init__(self):
        self.director = _Director()


@pytest.mark.parametrize("use_git", [False, True])
def test_package(tmp_path, monkeypatch, use_git):
    calls = []
    buildspace = _Buildspace()

    def _load_buildspace(config, package_uid, enabled_set):
        calls.append((config, package_uid, enabled_set))
        return buildspace

    monkeypatch.setattr(specmake.climake, "load_buildspace", _load_buildspace)
    argv = [
        "specmake", "--package", "--cache-directory",
        str(tmp_path / "cache"), "--enabled-set", " a , b ,, ", "--only", "o",
        "--force", "f", "--skip", "s", "--spec-directory",
        str(tmp_path / "spec")
    ]
    if use_git:
        argv.insert(1, "--use-git")
    climake(argv)
    config, package_uid, enabled_set = calls[0]
    assert config.spec_directory == str(tmp_path / "spec")
    assert config.cache_directory == str(tmp_path / "cache")
    assert not config.verify_specification_format
    assert package_uid == "/pkg/component"
    assert enabled_set == ["a", "b"]
    assert buildspace.director.builds == [(["o"], ["f"], ["s"])]
    if use_git:
        assert buildspace.director.git_directory == "deployment"
    else:
        assert buildspace.director.git_directory is None


@pytest.mark.parametrize(
    "arguments", [["/x"], ["--spec-directory", "a", "--spec-directory", "b"]])
def test_package_invalid(arguments):
    with pytest.raises(ValueError):
        climake(["specmake", "--package"] + arguments)
