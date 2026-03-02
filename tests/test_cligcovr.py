# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the cligcovr module. """

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

from pathlib import Path
import base64

import pytest

from specmake.cligcovr import cligcovr


def _write_gcov_output_with_info(path):
    """Write a test output file with valid base64 GCOV info."""
    info = base64.b64encode(b"12345678").decode("ascii")
    with open(path, "w", encoding="latin-1") as f:
        f.write(f"""Output
*** BEGIN OF GCOV INFO BASE64 ***
{info}
*** END OF GCOV INFO BASE64 ***
""")


def _write_gcov_output_no_info(path):
    """Write a test output file without GCOV info."""
    with open(path, "w", encoding="latin-1") as f:
        f.write("Output only\n")


@pytest.fixture
def fake_run(tmp_path):
    """
    Monkeypatch subprocess.run so cligcovr works without real gcov binaries.
    Simulates gcov-tool merge-stream, gcovr output, and gcov.
    """
    created_files = []

    def fake_run_func(cmd, *args, **kwargs):
        # Simulate gcov-tool merge-stream
        if isinstance(cmd, list) and "merge-stream" in cmd:
            return
        # Simulate gcovr creating outputs
        if isinstance(cmd, list) and "gcovr" in cmd:
            # Find destination directory
            cwd = kwargs.get("cwd", ".")
            for arg in cmd:
                if arg.endswith("summary.json"):
                    summary_path = Path(cwd) / arg
                    summary_path.write_text('{"dummy": true}')
                    created_files.append(summary_path)
                if arg.endswith("index.html"):
                    html_path = Path(cwd) / arg
                    html_path.write_text('HTML dummy')
                    created_files.append(html_path)
            return
        # Simulate gcov (usually just for the executable path, do nothing)
        return

    return fake_run_func, created_files


def test_remove_gcda_and_coverage_run(tmp_path, monkeypatch, fake_run):
    fake_run_func, created_files = fake_run

    # monkeypatch subprocess.run in cligcovr's namespace.
    monkeypatch.setattr("subprocess.run", fake_run_func)

    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "dummy.gcda").write_bytes(b"gcda-content")
    dest_dir = tmp_path / "coverage"
    dest_dir.mkdir()
    output_file = tmp_path / "output.txt"
    _write_gcov_output_with_info(output_file)

    argv = [
        "prog", "-o",
        str(build_dir), "-d",
        str(dest_dir), "-w",
        str(tmp_path), "-r", "gcovr", "-g", "gcov", "-t", "gcov-tool",
        str(output_file)
    ]
    cligcovr(argv)
    assert not (build_dir / "dummy.gcda").exists()
    assert (dest_dir / "index.html").exists()
    assert (dest_dir / "summary.json").exists()


def test_run_with_verbose_and_multiple_outputs(tmp_path, monkeypatch, capsys,
                                               fake_run):
    fake_run_func, created_files = fake_run
    monkeypatch.setattr("subprocess.run", fake_run_func)

    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "file.gcda").write_bytes(b"foo")
    dest_dir = tmp_path / "coverage"
    dest_dir.mkdir()
    output1 = tmp_path / "out1.txt"
    output2 = tmp_path / "out2.txt"
    _write_gcov_output_with_info(output1)
    _write_gcov_output_no_info(output2)

    argv = [
        "prog", "-o",
        str(build_dir), "-d",
        str(dest_dir), "-w",
        str(tmp_path), "-r", "gcovr", "-g", "gcov", "-t", "gcov-tool", "-v",
        str(output1),
        str(output2)
    ]
    cligcovr(argv)
    out = capsys.readouterr().out
    assert "remove:" in out
    assert "run in" in out
    assert "gcov-tool merge-stream" in out
    assert "gcovr" in out
    assert (dest_dir / "index.html").exists()
    assert (dest_dir / "summary.json").exists()


def test_run_with_no_gcda_and_no_coverage_dir(tmp_path, monkeypatch, fake_run):
    fake_run_func, created_files = fake_run
    monkeypatch.setattr("subprocess.run", fake_run_func)

    build_dir = tmp_path / "build"
    build_dir.mkdir()
    output = tmp_path / "output.txt"
    _write_gcov_output_no_info(output)

    argv = [
        "prog", "-o",
        str(build_dir), "-d",
        str(tmp_path / "coverage"), "-w",
        str(tmp_path), "-r", "gcovr", "-g", "gcov", "-t", "gcov-tool",
        str(output)
    ]
    cligcovr(argv)
    assert (tmp_path / "coverage" / "index.html").exists()
    assert (tmp_path / "coverage" / "summary.json").exists()


def test_destination_dir_absent(tmp_path, monkeypatch, fake_run):
    fake_run_func, created_files = fake_run
    monkeypatch.setattr("subprocess.run", fake_run_func)

    build_dir = tmp_path / "build"
    build_dir.mkdir()
    output = tmp_path / "output.txt"
    _write_gcov_output_no_info(output)

    argv = [
        "prog", "-o",
        str(build_dir), "-d",
        str(tmp_path / "coverage"), "-w",
        str(tmp_path), "-r", "gcovr", "-g", "gcov", "-t", "gcov-tool",
        str(output)
    ]
    cligcovr(argv)
    assert (tmp_path / "coverage" / "index.html").exists()
    assert (tmp_path / "coverage" / "summary.json").exists()


def test_bad_output_file_format(tmp_path, monkeypatch, fake_run):
    fake_run_func, created_files = fake_run
    monkeypatch.setattr("subprocess.run", fake_run_func)

    build_dir = tmp_path / "build"
    build_dir.mkdir()
    output = tmp_path / "output.txt"
    with open(output, "w") as f:
        f.write("This is nonsense")  # Totally non-matching format

    argv = [
        "prog", "-o",
        str(build_dir), "-d",
        str(tmp_path / "coverage"), "-w",
        str(tmp_path), "-r", "gcovr", "-g", "gcov", "-t", "gcov-tool",
        str(output)
    ]
    cligcovr(argv)
    assert (tmp_path / "coverage" / "index.html").exists()
    assert (tmp_path / "coverage" / "summary.json").exists()


def test_custom_paths_and_absent_dirs(tmp_path, monkeypatch, fake_run):
    fake_run_func, created_files = fake_run
    monkeypatch.setattr("subprocess.run", fake_run_func)

    build_dir = tmp_path / "obj"
    build_dir.mkdir()
    output = tmp_path / "out.txt"
    _write_gcov_output_no_info(output)

    argv = [
        "prog", "-o",
        str(build_dir), "-d",
        str(tmp_path / "covr"), "-w",
        str(tmp_path), "-r", "gcovr", "-g", "gcov", "-t", "gcov-tool",
        str(output)
    ]
    cligcovr(argv)
    assert (tmp_path / "covr" / "index.html").exists()
    assert (tmp_path / "covr" / "summary.json").exists()


def test_gcov_tool_not_run_if_no_info(tmp_path, monkeypatch, fake_run):
    fake_run_func, created_files = fake_run
    monkeypatch.setattr("subprocess.run", fake_run_func)

    build_dir = tmp_path / "build"
    build_dir.mkdir()
    output = tmp_path / "output.txt"
    _write_gcov_output_no_info(output)

    argv = [
        "prog", "-o",
        str(build_dir), "-d",
        str(tmp_path / "coverage"), "-w",
        str(tmp_path), "-r", "gcovr", "-g", "gcov", "-t", "gcov-tool",
        str(output)
    ]
    cligcovr(argv)
    assert (tmp_path / "coverage" / "index.html").exists()
    assert (tmp_path / "coverage" / "summary.json").exists()
