# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the runtests module. """

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

import io
import sys

from specmake.runtests import _run_executable, _StreamReader


def _read(data, limit):
    reader = _StreamReader(io.BytesIO(data), limit)
    reader.start()
    reader.join()
    return reader


def test_stream_reader_without_limit():
    reader = _read(b"\xe4bc", None)
    assert reader.size == 3
    assert reader.get_text() == "äbc"


def test_stream_reader_with_limit():
    # The stream is read in blocks of 65536 bytes.  The second block is
    # discarded completely.
    reader = _read(b"a" * 100000, 4096)
    assert reader.size == 100000
    assert reader.get_text() == "a" * 4096


def test_run_executable_with_large_standard_error():
    stdout, stderr, stderr_size, error = _run_executable([
        sys.executable, "-c", "import sys; sys.stdout.write('out');"
        " sys.stderr.write('e' * 100000)"
    ], 60.0)
    assert stdout == "out"
    assert stderr == "e" * 4096
    assert stderr_size == 100000
    assert error is None
