# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the indexer of the archiver module. """

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

import os
import tarfile
from pathlib import Path

import pytest

import specmake.archiver

from .util import create_package


class _Link:
    """ Stands in for a specification item link. """

    def __init__(self, values: dict):
        self._values = values
        self.item = None

    def __getitem__(self, key: str):
        return self._values[key]


class _Member:
    """ Stands in for a Sphinx document directory state. """

    def __init__(self, directory: str, values: dict, title: str | None = None):
        self.directory = directory
        self.uid = "/pkg/stub"
        self.item = {"document-title": title}
        self._values = values
        self._title = title

    def get(self, key: str, default=None):
        return self._values.get(key, default)

    def substitute(self, _data):
        return self._title


def _create_index(caplog, tmp_path):
    package = create_package(caplog,
                             tmp_path,
                             Path("spec-indexer"), [],
                             workspace_dir="index-files")
    director = package.director
    director["/pkg/test-files"].build()
    director.build_package()
    return director["/pkg/index"]


def test_indexer(caplog, tmp_path):
    index = _create_index(caplog, tmp_path)
    with open(Path(index.directory) / "index.html", encoding="utf-8") as src:
        content = src.read()
    assert "<title>pkg</title>" in content
    assert content.index("Section One") < content.index("Section Two")
    assert content.index("Document E") < content.index("Document A")
    assert '<a class="index-target" href="../index/doc-a.pdf"' \
        ' aria-label="Document A (PDF)">PDF</a>' in content
    assert '<a class="index-target" href="../dir/e.txt"' \
        ' aria-label="Document E (TXT)">TXT</a>' in content
    assert '<a class="index-target" href="../dir/subdir/c.txt"' \
        ' aria-label="Document C (TXT)">TXT</a>' in content
    assert "Disabled Document" not in content
    assert "Section Three" not in content
    assert "Section Six" not in content
    assert content.count('<section class="index-group index-level-2"') == 1
    assert '<section class="index-group index-level-3"' in content
    assert '<section class="index-group index-level-4"' in content
    assert content.index("Section Two") < content.index("Section Five")
    assert content.index("Document A") < content.index("Section Two")
    assert (Path(index.directory) / "style.css").is_file()
    plain = Path(index.directory) / "plain" / "index.html"
    assert "Plain pkg" in plain.read_text(encoding="utf-8")
    assert not (Path(index.directory) / "plain" / "doc.tar.xz").exists()
    assert not (Path(index.directory) / "doc.tar.xz").exists()
    archive_state = index.director["/pkg/index-archive"]
    with tarfile.open(Path(archive_state.directory) / "doc.tar.xz",
                      "r:*") as archive:
        assert sorted(archive.getnames()) == [
            "dir/e.txt", "dir/subdir/c.txt", "index/doc-a.pdf",
            "pkg/index.html", "pkg/style.css"
        ]


def test_indexer_derived_entry(caplog, tmp_path):
    index = _create_index(caplog, tmp_path)
    member = _Member(os.path.join(index.directory, os.pardir, "index"), {
        "document-key": "blub",
        "output-html": ".",
        "output-pdf": "doc-a.pdf"
    }, "Package The Title [v1]")
    link = _Link({"title": None, "path": None, "sort-key": 3})
    entry = index._entry(link, member)
    assert entry == (3, "Package The Title [v1]", "blub",
                     [("HTML", os.path.join(os.pardir, "index", "index.html")),
                      ("PDF", os.path.join(os.pardir, "index", "doc-a.pdf"))])
    node = specmake.archiver._IndexNode(0, "Section")
    node.entries.append(entry)
    assert '<span class="index-key">blub</span>' in node.render(2)


def test_indexer_entry_errors(caplog, tmp_path):
    index = _create_index(caplog, tmp_path)
    member = _Member(index.directory, {})
    with pytest.raises(ValueError, match="index member has no title"):
        index._entry(_Link({
            "title": None,
            "path": None,
            "sort-key": 0
        }), member)
    with pytest.raises(ValueError, match="index member has no link target"):
        index._entry(_Link({
            "title": "T",
            "path": None,
            "sort-key": 0
        }), member)
    with pytest.raises(ValueError, match="no such link target"):
        index._entry(_Link({
            "title": "T",
            "path": "gone.pdf",
            "sort-key": 0
        }), member)
    link = next(index._groups())[0]
    link["title"] = None
    with pytest.raises(ValueError, match="index group has no title"):
        index._get_index_body(None)


def test_indexer_without_archive_output(caplog, tmp_path):
    index = _create_index(caplog, tmp_path)
    plain = index.director["/pkg/index-plain"]
    plain.item["archive-file"] = "doc.tar.xz"
    with pytest.raises(ValueError, match="no archive output"):
        plain.run()
