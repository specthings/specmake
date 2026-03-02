# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the archiver module. """

# Copyright (C) 2023, 2026 embedded brains GmbH & Co. KG
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

import tarfile
from pathlib import Path

from specware import run_command

from .util import create_package, get_and_clear_log


def test_archiver(caplog, tmp_path):
    package = create_package(caplog, tmp_path, Path("spec-archiver"), [])
    director = package.director
    test_files = director["/pkg/test-files"]
    test_files.build()
    dir_state_a = director["/pkg/a"]
    dir_state_a.build()
    with open(tmp_path / "dir" / "subdir" / "d.txt", "w",
              encoding="utf-8") as dst:
        dst.write("d")
    dir_state_b = director["/pkg/b"]
    dir_state_b.load()
    dir_state_e = director["/pkg/e"]
    dir_state_e.load()
    export_spec_sample = tmp_path / "pkg" / "spec" / "pkg" / "archive-0.yml"
    assert not export_spec_sample.exists()
    director.build_package()
    archive_0 = director["/pkg/archive-0"]
    archive_1 = director["/pkg/archive-1"]
    assert export_spec_sample.is_file()
    log = get_and_clear_log(caplog)
    assert f"/pkg/archive-0: export specification to directory: {tmp_path}/pkg/spec" in log
    assert f"/pkg/archive-0: duplicates in directory states ['/pkg/a', '/pkg/b'] for file: {tmp_path}/dir/subdir/c.txt" in log
    assert f"/pkg/archive-0: duplicates in directory states ['/pkg/a', '/pkg/b'] for file: {tmp_path}/dir/subdir/d.txt" in log
    assert f"/pkg/archive-0: inconsistent file hashes {list(dir_state_a.files_and_hashes())[2][1]} (of /pkg/a) and {list(dir_state_b.files_and_hashes())[2][1]} (of /pkg/b) for file: {tmp_path}/dir/subdir/d.txt" in log
    with tarfile.open(archive_0.file, "r:*") as archive_0:
        assert archive_0.getnames() == [
            "dir/a.txt", "dir/e.txt", "dir/subdir/c.txt", "dir/subdir/d.txt",
            "pkg/spec/pkg/a.yml", "pkg/spec/pkg/archive-0.yml",
            "pkg/spec/pkg/archive-1.yml", "pkg/spec/pkg/b.yml",
            "pkg/spec/pkg/component.yml", "pkg/spec/pkg/e.yml",
            "pkg/spec/pkg/spec.yml", "pkg/spec/pkg/test-files.yml",
            "pkg/spec/pkg/verify-package.yml", "dir/b.txt"
        ]

    verify_package = director["/pkg/verify-package"]
    stdout = []
    status = run_command([verify_package.file, "--list-files-and-hashes"],
                         str(tmp_path), stdout)
    assert status == 0
    assert stdout == [
        "dir/a.txt\t7a296fab5364b34ce3e0476d55bf291bd41aa085e5ecf2a96883e593aa1836fed22f7242af48d54af18f55c8d1def13ec9314c926666a0ba63f7663500090565",
        "dir/b.txt\t3355aa4ae1b31404d9b5c262c863ec2ff0b63d6cbd3a0e506621d6d13846b925b0a922ee1408e14c1cdf69d7ab9a38c2d1118403ce50f71c32b1b33f72616677",
        "dir/e.txt\t61e9f9edbc37b2b5c2fc9633da2d8777916f0e4515a080374acedd14c935f2c6fb5a882c5459b7a06a03f0d057ce4f73f89def713a5824b8769a5917a3bdda93",
        "dir/subdir/c.txt\t663049a20dfea6b8da28b2eb90eddd10ccf28ef2519563310b9bde25b7268444014c48c4384ee5c5a54e7830e45fcd87df7910a7fda77b68c2efdd75f8de25e8",
        "dir/subdir/d.txt\t48fb10b15f3d44a09dc82d02b06581e0c0c69478c9fd2cf8f9093659019a1687baecdbb38c9e72b12169dc4148690f87467f9154f5931c5df665c6496cbfd5f5"
    ]
