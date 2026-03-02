# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the doxyfile module. """

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

from .util import create_package


def test_doxyfile(caplog, tmpdir):
    tmp_dir = Path(tmpdir)
    package = create_package(caplog, tmp_dir, Path("spec-packagebuild"),
                             ["doxyfile"])
    director = package.director
    director.build_package()
    doxyfile = Path(director["/pkg/deployment/doxyfile"].file)
    with open(doxyfile, "r", encoding="utf-8") as src:
        assert src.read() == f"""*/exclude/a/* \\
*/exclude/b/*
---
{tmp_dir}/include/path/0 \\
{tmp_dir}/include/path/1
---
{tmp_dir}/input/path/0
---
YES
---
NO
---
{tmp_dir}/pkg/build
---
{tmp_dir}/strip/from/path
---
{tmp_dir}/pkg/build/Doxyfile
"""
