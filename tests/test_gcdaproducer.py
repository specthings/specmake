# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the gcdaproducer module. """

# Copyright (C) 2023, 2025 embedded brains GmbH & Co. KG
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

from pathlib import Path

import specmake

from .util import create_package, get_and_clear_log


def _gcov_tool(command, check, cwd, input):
    assert command == ["foo", "merge-stream"]
    assert check
    assert input == b"gcfnB04R\x00\x00\x00\x95/opt"
    (Path(cwd) / "file.gcda").touch()


def test_gcdaproducer(caplog, tmpdir, monkeypatch):
    tmp_dir = Path(tmpdir)
    package = create_package(caplog, tmp_dir, Path("spec-packagebuild"),
                             ["gcda-producer"])
    monkeypatch.setattr(specmake.gcdaproducer, "subprocess_run", _gcov_tool)
    director = package.director
    director.build_package()
    test_log_coverage = director["/pkg/test-logs/coverage"]
    test_log_coverage.load()
    log = get_and_clear_log(caplog)
    assert f"/pkg/build/gcda: copy *.gcno files from '{tmp_dir}/pkg/build/bsp' to '{tmp_dir}/pkg/build/gcda'" in log
    assert f"/pkg/build/gcda: remove unexpected *.gcda file in build directory: '{tmp_dir}/pkg/build/bsp/f.gcda'" in log
    assert f"/pkg/build/gcda: process: ts-unit-no-clock-0.exe" in log
    assert f"/pkg/build/gcda: move *.gcda files from '{tmp_dir}/pkg/build/bsp' to '{tmp_dir}/pkg/build/gcda'" in log
    assert f"/pkg/build/gcda: create symbolic link from '{tmp_dir}/pkg/build/gcda-symbolic-link-name' to 'gcda-symbolic-link-target'" in log
