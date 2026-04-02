# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the directorystate module. """

# Copyright (C) 2020, 2026 embedded brains GmbH & Co. KG
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

from specitems import Item, EmptyItemCache, Link

import specmake
from specmake import (DirectoryState, RepositoryState, BuildItemFactory,
                      BuildItemTypeProvider, PackageBuildDirector,
                      PackageComponent)

from .util import get_and_clear_log


class _TestState(DirectoryState):

    def __init__(self, director, item):
        super().__init__(director, item)
        self.git_add_files = []
        self.commit_counter = 0

    def git_add(self, what):
        self.git_add_files = what

    def git_commit(self, _reason: str) -> None:
        self.commit_counter += 1


def _run_command(args, cwd, stdout):
    stdout.append("a412700fd90e6195c255aea2048ae2ef37244df5")
    return 0


@pytest.fixture
def _change_cwd():
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    yield
    os.chdir(cwd)


_DOC_RST_HASH = "Cm41zmS2o7TF6FBxnQxWxmPDVhufFst7pFkkQriQnEOwJWXS_zjEwKLVsgBT4L-v1iWzRUCilifIdY4uqkg5Gw=="
_T_YML_HASH = "_FTeBKV04q5fMTETF65lBzv6dNeHTMLT3dZmHF1BEAOLtmxvPdAJc_7-RDmGRiv3GU_uddvkFc005S0EeSx0PA=="
_INCLUDE_ALL = [{"include": "**/*", "exclude": []}]


def test_directorystate(caplog, tmpdir, monkeypatch, _change_cwd):
    item_cache = EmptyItemCache(type_provider=BuildItemTypeProvider({}))
    factory = BuildItemFactory()
    factory.add_constructor("pkg/directory-state/explicit", _TestState)
    factory.add_constructor("pkg/directory-state/patterns", _TestState)
    factory.add_constructor("pkg/directory-state/repository", RepositoryState)
    director = PackageBuildDirector(item_cache, "?", factory)
    base = "spec-glossary"

    data = {
        "SPDX-License-Identifier":
        "CC-BY-SA-4.0 OR BSD-2-Clause",
        "copyrights":
        ["Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG"],
        "copyrights-by-license": {},
        "directory":
        base,
        "directory-state-type":
        "explicit",
        "enabled-by":
        True,
        "files": [
            {
                "file": "doc.rst",
                "hash": None
            },
            {
                "file": "glossary/t.yml",
                "hash": None
            },
        ],
        "hash":
        None,
        "links": [],
        "pkg-type":
        "directory-state",
        "type":
        "pkg"
    }
    item = item_cache.add_item("/directory-state", data)
    item_file = os.path.join(tmpdir, "item.yml")
    item.file = str(item_file)
    dir_state = director["/directory-state"]
    assert dir_state.directory == base
    assert dir_state.digest() == "iRq64x4DHVvsuXXfE2wW6FWinS5utMjTGcDJkoMCfBY="
    assert not dir_state.is_present()
    assert dir_state.has_changed(Link(item, {"hash": "blub"}))
    overall_hash = dir_state.lazy_load()
    assert dir_state.is_present()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="
    assert dir_state.digest() == overall_hash
    dir_state.save()
    with open(item_file, "r") as src:
        assert f"""SPDX-License-Identifier: CC-BY-SA-4.0 OR BSD-2-Clause
copyrights:
- Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG
copyrights-by-license: {{}}
directory: {base}
directory-state-type: explicit
enabled-by: true
files:
- file: doc.rst
  hash: {_DOC_RST_HASH}
- file: glossary/t.yml
  hash: {_T_YML_HASH}
hash: SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag==
links: []
pkg-type: directory-state
type: pkg
""" == src.read()
    assert dir_state.file == "spec-glossary/doc.rst"
    assert dir_state.substitute("${.:/file}") == "spec-glossary/doc.rst"
    assert dir_state.substitute("${.:/file[0]}") == "spec-glossary/doc.rst"
    assert dir_state.substitute(
        "${.:/file[1]}") == "spec-glossary/glossary/t.yml"
    assert dir_state.substitute(
        "${.:/file-without-extension[1]}") == "spec-glossary/glossary/t"
    assert list(dir_state.files(".")) == ["./doc.rst", "./glossary/t.yml"]
    assert list(dir_state.files()) == [
        str(os.path.join(base, "doc.rst")),
        str(os.path.join(base, "glossary/t.yml"))
    ]
    assert list(dir_state.files_and_hashes(".")) == [
        ("./doc.rst", _DOC_RST_HASH), ("./glossary/t.yml", _T_YML_HASH)
    ]
    assert list(dir_state.files_and_hashes()) == [
        (str(os.path.join(base, "doc.rst")), _DOC_RST_HASH),
        (str(os.path.join(base, "glossary/t.yml")), _T_YML_HASH)
    ]

    dir_state.set_files(["doc.rst"])
    dir_state.add_files(["glossary/t.yml"])
    assert dir_state.digest() == "iRq64x4DHVvsuXXfE2wW6FWinS5utMjTGcDJkoMCfBY="
    overall_hash = dir_state.lazy_load()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="
    overall_hash = dir_state.lazy_load()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="
    assert dir_state.is_present()
    dir_state.invalidate()
    assert not dir_state.is_present()
    dir_state.load()
    assert dir_state.is_present()
    assert factory.export_data(dir_state.item, True, 0)["files"] == [{
        "file":
        "doc.rst",
        "hash":
        None
    }, {
        "file":
        "glossary/t.yml",
        "hash":
        None
    }]
    assert factory.export_data(dir_state.item, True,
                               len(dir_state.item.cache))["files"] == [{
                                   "file":
                                   "doc.rst",
                                   "hash":
                                   _DOC_RST_HASH
                               }, {
                                   "file":
                                   "glossary/t.yml",
                                   "hash":
                                   _T_YML_HASH
                               }]

    assert factory.export_data(dir_state.item, False,
                               len(dir_state.item.cache))["files"] == [{
                                   "file":
                                   "doc.rst",
                                   "hash":
                                   None
                               }, {
                                   "file":
                                   "glossary/t.yml",
                                   "hash":
                                   None
                               }]

    caplog.set_level(logging.DEBUG)
    data_2 = {
        "SPDX-License-Identifier":
        "CC-BY-SA-4.0 OR BSD-2-Clause",
        "copyrights":
        ["Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG"],
        "copyrights-by-license": {},
        "directory":
        base,
        "directory-state-type":
        "explicit",
        "enabled-by":
        True,
        "files": [],
        "links": [{
            "role": "directory-state-exclude",
            "uid": "directory-state"
        }, {
            "hash": None,
            "name": "associate",
            "role": "input",
            "uid": "directory-state"
        }],
        "pkg-type":
        "directory-state",
        "type":
        "pkg"
    }
    item_2 = item_cache.add_item("/directory-state-2", data_2)
    dir_state_2 = DirectoryState(director, item_2)
    dir_state_2.add_files(
        os.path.relpath(path, dir_state_2.directory) for path in dir_state)
    assert list(dir_state_2.files()) == []
    dir_state_2.set_files(
        os.path.relpath(path, dir_state_2.directory) for path in dir_state)
    assert list(dir_state_2.files()) == []
    dir_state_2.set_files([])
    assert list(dir_state_2.files()) == []
    assert dir_state_2.digest(
    ) == "_mhN0f3Vya1kxL2DnDRikyYBoMRKOLt5gtCMdVXFwO0="
    overall_hash = dir_state_2.load()
    assert overall_hash == "MC661WGYFYfEcrM30WKz76mmgBys6Yg7EEJKtn-khBVN8rqabUB40zYZ8LqJ_ruJAyuhd8oVTxYaNyyo8L9IoQ=="

    dir_state_2["patterns"] = _INCLUDE_ALL
    overall_hash = dir_state_2.load()
    assert overall_hash == "GA9knXEEVhdjswyhYGrY39UeEHB0FhMBF2jSpKFPi2ZTRORBOTfkqRvCYmBX02oTDR0Zfk09gEDvPsJnW_KekA=="
    assert dir_state_2.is_present()
    assert factory.export_data(
        dir_state_2.item, True, len(dir_state_2.item.cache)
    )["files"] == [{
        "file":
        "g.yml",
        "hash":
        "YBXb4OS3ytH7NyMOG4ZQhhQB2gRe6rPzzIf0c9hLK2khrv-AMf1auYc2ZpuEzCJw3sSG0Z2HzEUWcE4HBlzIAA=="
    }, {
        "file":
        "glossary.rst",
        "hash":
        "z4PhNX7vuL3xVChQ1m2AB9Yg5AULVxXcg_SpIdNs6c5H0NE8XYXysP-DGNKHfuwvY7kxvUdBeoGlODJ6-SfaPg=="
    }, {
        "file":
        "glossary/sub/g.yml",
        "hash":
        "fO5l2jF52e39z6wMoIqwLNZIN_MxRVxPMwonOzZZtnXWvJEyWJEVwShDogMa8_fLPoPmHQCdp1YreeV_1dZ9lw=="
    }, {
        "file":
        "glossary/sub/x.yml",
        "hash":
        "8o_9De_EgKasI9--3Mx3uR2yxH4bBPMz22PQ1S2vD5MavSwCVZ17FSO4VY-y7BO5NfpeUytQsiNme_4y_-iasg=="
    }, {
        "file":
        "glossary/u.yml",
        "hash":
        "Cum2wJ7aeuPJPQcKZNnZ4ZfHAfjbZJRnEuXM_0WjXKlyIMLzAJmZAhWiJFSP3iOxmJYxoGnjriDwN_tJhyfyEA=="
    }, {
        "file":
        "glossary/v.yml",
        "hash":
        "98PD0tJ7qCXJifE62mKALzHIBB6MyC93M7LWQMqCZii5x58CgtvlARcD0vT2roUP3i7Viw3AAqXbW1-e6DrnKg=="
    }]
    assert factory.export_data(dir_state_2.item, False, 0)["files"] == []

    item["patterns"] = [{
        "include": ["**/*"],
        "exclude": ["*/glossary.rst", "*/[guv].yml", "*/sub/*"]
    }]
    overall_hash = dir_state.load()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="

    item["patterns"] = [{
        "include": "**/doc.rst",
        "exclude": []
    }, {
        "include": "**/t.yml",
        "exclude": []
    }]
    overall_hash = dir_state.load()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="

    item["patterns"] = "**/doc.rst"
    overall_hash = dir_state.load()
    assert overall_hash == "XD9kB5A1Gz2zhJYzx5mh8Fm5EuRjqvFXyKe6bw7d0xBAx3fC2KFivARrnH-PXLZ0ezIo_eE2O8nglaQX-_pKmA=="

    item["patterns"] = ["**/doc.rst", "**/t.yml"]
    overall_hash = dir_state.load()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="

    item["patterns"] = {"include": "**/doc.rst", "exclude": []}
    overall_hash = dir_state.load()
    assert overall_hash == "XD9kB5A1Gz2zhJYzx5mh8Fm5EuRjqvFXyKe6bw7d0xBAx3fC2KFivARrnH-PXLZ0ezIo_eE2O8nglaQX-_pKmA=="

    item["patterns"] = [{"include": "**/doc.rst", "exclude": []}]
    overall_hash = dir_state.load()
    assert overall_hash == "XD9kB5A1Gz2zhJYzx5mh8Fm5EuRjqvFXyKe6bw7d0xBAx3fC2KFivARrnH-PXLZ0ezIo_eE2O8nglaQX-_pKmA=="

    item["patterns"] = [{"include": "**/foo", "exclude": []}]
    overall_hash = dir_state.load()
    assert overall_hash == "YtmDhTiLc9q20OthwE35dnsoPQz5gkQqajQQC2K3h5_yzY67hX35LlnhuR_kEx-_blEsjQlT1ijdP5YwUwb3bw=="

    caplog.set_level(logging.DEBUG)
    data_3 = {
        "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
        "copyrights":
        ["Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG"],
        "copyrights-by-license": {},
        "directory": str(tmpdir),
        "directory-state-type": "explicit",
        "enabled-by": True,
        "files": [],
        "links": [],
        "pkg-type": "directory-state",
        "type": "pkg"
    }
    item_3 = item_cache.add_item("/directory-state-3", data_3)
    item_3.type = "pkg/directory-state/patterns"
    item_3_file = os.path.join(tmpdir, "item-3.yml")
    item_3.file = str(item_3_file)
    dir_state_3 = director["/directory-state-3"]
    assert not dir_state_3.is_present()

    src_file = os.path.join(base, "doc.rst")
    dir_state_3.copy_file(src_file, "doc.rst")
    assert not dir_state_3.is_present()
    dst_file = os.path.join(tmpdir, "doc.rst")
    assert os.path.exists(dst_file)
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: copy '{src_file}' to '{dst_file}'" in log
    dir_state_3.load()
    assert dir_state_3.is_present()

    dir_state_3.remove_files()
    assert not os.path.exists(dst_file)
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: remove: {dst_file}" in log

    dir_state_3.remove_files()
    log = get_and_clear_log(caplog)
    assert f"DEBUG /directory-state-3: file not found: {dst_file}" in log

    dir_state_3["patterns"] = []
    dir_state_3.remove_files()
    del dir_state_3.item.data["patterns"]
    log = get_and_clear_log(caplog)
    assert f"WARNING /directory-state-3: file not found: {dst_file}" in log

    assert list(dir_state_3.files_and_hashes()) == [(str(dst_file),
                                                     _DOC_RST_HASH)]
    dir_state_3.invalidate()
    assert list(dir_state_3.files_and_hashes()) == [(str(dst_file), None)]

    dir_state_3["patterns"] = []
    dir_state_3.invalidate()
    del dir_state_3.item.data["patterns"]
    assert list(dir_state_3.files_and_hashes()) == []

    dir_state_3.copy_tree(base, "x")
    for path in [
            "doc.rst", "g.yml", "glossary.rst", "glossary/sub/g.yml",
            "glossary/sub/x.yml", "glossary/t.yml", "glossary/u.yml",
            "glossary/v.yml"
    ]:
        assert os.path.exists(os.path.join(tmpdir, "x", path))

    dir_state_3.clear()
    dir_state_3.add_tree(os.path.join("spec-glossary", "glossary", "sub"),
                         excludes=["/x.*"])
    assert list(dir_state_3.files()) == [f"{tmpdir}/g.yml"]
    assert not os.path.exists(os.path.join(tmpdir, "g.yml"))
    assert os.path.exists(os.path.join(tmpdir, "x", "glossary", "sub",
                                       "g.yml"))
    dir_state_3.move_tree(os.path.join(tmpdir, "x", "glossary", "sub"))
    assert list(dir_state_3.files()) == [f"{tmpdir}/g.yml", f"{tmpdir}/x.yml"]
    assert not os.path.exists(
        os.path.join(tmpdir, "x", "glossary", "sub", "g.yml"))
    assert os.path.exists(os.path.join(tmpdir, "g.yml"))

    assert not dir_state_3.is_present()
    link = Link(item_3, {"hash": None})
    dir_state_3.load()
    assert dir_state_3.is_present()
    assert dir_state_3.has_changed(link)
    dir_state_3.refresh_link(link)
    assert not dir_state_3.has_changed(link)

    dir_state_3.discard()
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: discard" in log

    dir_state_3.clear()
    dir_state_3.refresh()
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: refresh" in log

    dir_state_3.clear()
    dir_state_3.add_tarfile_members("test-files/archive.tar.xz", tmpdir, False)
    assert list(dir_state_3.files()) == [
        f"{tmpdir}/member-dir/dir-member.txt", f"{tmpdir}/member.txt"
    ]
    assert not os.path.exists(os.path.join(tmpdir, "member.txt"))
    dir_state_3.add_tarfile_members("test-files/archive.tar.xz", tmpdir, True)
    assert list(dir_state_3.files()) == [
        f"{tmpdir}/member-dir/dir-member.txt", f"{tmpdir}/member.txt"
    ]
    assert os.path.exists(os.path.join(tmpdir, "member.txt"))

    dir_state_3.clear()
    src_file = os.path.join(base, "doc.rst")
    dir_state_3.copy_files(base, ["doc.rst"], "uvw")
    dst_file = os.path.join(tmpdir, "uvw", "doc.rst")
    assert os.path.exists(dst_file)
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: copy '{src_file}' to '{dst_file}'" in log
    assert list(name for name in dir_state_3) == [dst_file]

    symlink = os.path.join(tmpdir, "symlink")
    os.symlink("foobar", symlink)
    dir_state_3.set_files(["symlink"])
    dir_state_3.load()
    assert list(dir_state_3.files_and_hashes()) == [(
        symlink,
        "ClAmHr0aOQ_tK_Mm8mc8FFWCpjQtUjIElz0CGTN_gWFqgGmwElh89WNfaSXxtWw2AjDBmyc1AO4BPgMGAb8kJQ=="
    )]

    get_and_clear_log(caplog)

    item["patterns"] = [{"include": "**/t.yml", "exclude": []}]
    dir_state.load()
    assert dir_state.is_present()
    dir_state_3.lazy_clone(dir_state)
    assert list(dir_state_3.files(".")) == ["./glossary/t.yml"]
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: copy" in log

    item["patterns"] = [{"include": "**/x.yml", "exclude": []}]
    dir_state.load()
    dir_state_3.lazy_clone(dir_state)
    assert list(dir_state_3.files(".")) == ["./glossary/sub/x.yml"]
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: remove" in log

    os.unlink(dir_state_3.file)
    item["patterns"] = [{"include": "**/t.yml", "exclude": []}]
    dir_state.load()
    dir_state_3.lazy_clone(dir_state)
    log = get_and_clear_log(caplog)
    assert f"WARNING /directory-state-3: file not found" in log

    dir_state_3.invalidate()
    dir_state_3.lazy_clone(dir_state)
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: copy" in log

    dir_state_3.lazy_clone(dir_state)
    assert list(dir_state_3.files(".")) == ["./glossary/t.yml"]
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: keep as is" in log

    assert dir_state_3.directory == tmpdir
    dir_state_3.set_files(["/a/b", "/a/c"])
    dir_state_3.compact()
    assert dir_state_3.directory == tmpdir
    dir_state_3.set_files(["a/b", "c/d"])
    dir_state_3.compact()
    assert dir_state_3.directory == tmpdir
    dir_state_3.set_files(["a/b", "a/c"])
    dir_state_3.compact()
    assert dir_state_3.directory == f"{tmpdir}/a"

    dir_state_3.set_files(["data.json"])
    assert not os.path.exists(dir_state_3.file)
    dir_state_3.json_dump({"foo": "bar"})
    assert os.path.exists(dir_state_3.file)
    assert dir_state_3.json_load() == {"foo": "bar"}

    # Test RepositoryState.lazy_verify()
    repo_item = item_cache.add_item(
        "/repo-state", {
            "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
            "branch": "b",
            "commit": "a412700fd90e6195c255aea2048ae2ef37244df5",
            "copyrights": ["Copyright (C) 2023 embedded brains GmbH & Co. KG"],
            "copyrights-by-license": {},
            "description": "d",
            "directory": "x",
            "directory-state-type": "repository",
            "enabled-by": True,
            "files": [],
            "hash": None,
            "links": [],
            "origin-branch": None,
            "origin-commit": None,
            "origin-commit-url": None,
            "origin-url": None,
            "patterns": [],
            "pkg-type": "directory-state",
            "type": "pkg"
        })
    repo_item.type = "pkg/directory-state/repository"
    repo_state = director["/repo-state"]
    monkeypatch.setattr(specmake.directorystate, "run_command", _run_command)
    assert director["/repo-state"].lazy_verify()
    monkeypatch.undo()


def test_directorystate_glob():
    item_cache = EmptyItemCache(type_provider=BuildItemTypeProvider({}))
    factory = BuildItemFactory()
    factory.add_constructor("pkg/directory-state/explicit", DirectoryState)
    director = PackageBuildDirector(item_cache, "?", factory)
    base = os.path.abspath(os.path.dirname(__file__))
    data = {
        "SPDX-License-Identifier":
        "CC-BY-SA-4.0 OR BSD-2-Clause",
        "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
        "copyrights-by-license": {},
        "directory":
        base,
        "directory-state-type":
        "explicit",
        "enabled-by":
        True,
        "files": [
            {
                "file": "hello.py",
                "hash": None
            },
            {
                "file": "spec-glossary/doc.rst",
                "hash": None
            },
            {
                "file": "spec-glossary/glossary/t.yml",
                "hash": None
            },
        ],
        "hash":
        None,
        "links": [],
        "pkg-type":
        "directory-state",
        "type":
        "pkg"
    }
    item = item_cache.add_item("/directory-state", data)
    dir_state = director["/directory-state"]

    def _files(files):
        return [os.path.join(base, i) for i in files]

    assert dir_state.substitute(["${.:/glob:*}"]) == _files(
        ["hello.py", "spec-glossary/doc.rst", "spec-glossary/glossary/t.yml"])
    assert dir_state.substitute(["${.:/glob:*.rst}"
                                 ]) == _files(["spec-glossary/doc.rst"])
    assert dir_state.substitute(["${.:/glob:/spec-glossary/glossary/*.rst}"
                                 ]) == []
    assert dir_state.substitute(["${.:/glob:/spec-glossary/glossary/*.yml}"
                                 ]) == _files(["spec-glossary/glossary/t.yml"])
    assert dir_state.substitute(["${.:/glob-executables:*}"
                                 ]) == _files(["hello.py"])


def test_directorystate_load_before_use():
    item_cache = EmptyItemCache(type_provider=BuildItemTypeProvider({}))
    factory = BuildItemFactory()
    factory.add_constructor("pkg/directory-state/explicit", DirectoryState)
    director = PackageBuildDirector(item_cache, "?", factory)
    base = os.path.abspath(os.path.dirname(__file__))
    data = {
        "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
        "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
        "copyrights-by-license": {},
        "directory": base,
        "directory-state-type": "explicit",
        "enabled-by": True,
        "files": [{
            "file": "hello.py",
            "hash": None
        }],
        "hash": None,
        "links": [],
        "pkg-type": "directory-state",
        "type": "pkg"
    }
    item = item_cache.add_item("/directory-state", data)
    dir_state = director["/directory-state"]
    assert [digest for name, digest in dir_state.files_and_hashes()] == [None]

    data["directory-state-load-before-use"] = True
    del director["/directory-state"]
    dir_state_2 = director["/directory-state"]
    assert [digest for name, digest in dir_state_2.files_and_hashes()] == [
        "9hgOv9b7ff8c3NpW5g62EUUY0UZ-Dnqv0tO36wFs94XHmAOkDLbdYPSc18FBdSanbrNFroBspMQoyp1tyH0cug=="
    ]


def test_directorystate_input_file_list():
    item_cache = EmptyItemCache(type_provider=BuildItemTypeProvider({}))
    factory = BuildItemFactory()
    factory.add_constructor("pkg/component/generic", PackageComponent)
    factory.add_constructor("pkg/directory-state/explicit", DirectoryState)
    director = PackageBuildDirector(item_cache, "?", factory)
    base = os.path.abspath(os.path.dirname(__file__))
    item_cache.add_item(
        "/component", {
            "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
            "base": base,
            "component-type": "generic",
            "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
            "enabled-by": True,
            "enabled-set": [],
            "links": [],
            "pkg-type": "component",
            "type": "pkg",
        })
    item_cache.add_item(
        "/directory-state", {
            "SPDX-License-Identifier":
            "CC-BY-SA-4.0 OR BSD-2-Clause",
            "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
            "copyrights-by-license": {},
            "directory":
            base,
            "directory-state-type":
            "explicit",
            "directory-state-load-before-use":
            True,
            "enabled-by":
            True,
            "files": [{
                "file": "hello.py",
                "hash": None
            }],
            "hash":
            None,
            "links": [{
                "role": "input",
                "hash": None,
                "name": "component",
                "uid": "/component"
            }],
            "pkg-type":
            "directory-state",
            "type":
            "pkg",
        })
    item_cache.add_item(
        "/directory-state-2", {
            "SPDX-License-Identifier":
            "CC-BY-SA-4.0 OR BSD-2-Clause",
            "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
            "copyrights-by-license": {},
            "directory":
            base,
            "directory-state-type":
            "explicit",
            "enabled-by":
            True,
            "files": [],
            "hash":
            None,
            "links": [{
                "role": "input",
                "hash": None,
                "name": "component",
                "uid": "/component"
            }, {
                "role": "input",
                "hash": None,
                "name": "source",
                "uid": "/directory-state"
            }],
            "pkg-type":
            "directory-state",
            "type":
            "pkg",
        })
    item_cache.add_item(
        "/directory-state-3", {
            "SPDX-License-Identifier":
            "CC-BY-SA-4.0 OR BSD-2-Clause",
            "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
            "copyrights-by-license": {},
            "directory":
            base,
            "directory-state-type":
            "explicit",
            "enabled-by":
            True,
            "files": [],
            "hash":
            None,
            "links": [{
                "role": "input",
                "hash": None,
                "name": "component",
                "uid": "/component"
            }, {
                "role": "input",
                "hash": None,
                "name": "source",
                "uid": "/directory-state-2"
            }],
            "pkg-type":
            "directory-state",
            "type":
            "pkg",
        })
    dir_state_3 = director["/directory-state-3"]

    assert dir_state_3.substitute(
        "${.:/input-file-list:relpath=%(.:/component/base),foobar}") == ""

    assert dir_state_3.substitute(
        "${.:/input-file-list:relpath=%(.:/component/base),component}") == ""

    assert dir_state_3.substitute(
        "${.:/input-file-list:relpath=%(.:/component/base),source}") == ""

    assert dir_state_3.substitute(
        "${.:/input-file-list:relpath=%(.:/component/base),source,source}"
    ) == "- :file:`hello.​py`"

    assert dir_state_3.substitute(
        "${.:/input-file-list-with-hashes:relpath=%(.:/component/base),source,source}"
    ) == """- :file:`hello.​py` with an SHA512 digest of
  f​6​1​8​0​e​b​f​d​6​f​b​7​d​f​f​1​c​d​c​d​a​5​6​e​6​0​e​b​6​1​1​4​5​1​8​d​1​4​6​7​e​0​e​7​a​a​f​d​2​d​3​b​7​e​b​0​1​6​c​f​7​8​5​c​7​9​8​0​3​a​4​0​c​b​6​d​d​6​0​f​4​9​c​d​7​c​1​4​1​7​5​2​6​a​7​6​e​b​3​4​5​a​e​8​0​6​c​a​4​c​4​2​8​c​a​9​d​6​d​c​8​7​d​1​c​b​a"""
