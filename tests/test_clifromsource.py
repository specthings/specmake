# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the clifromsource module. """

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

import yaml

from specmake.clifromsource import clifromsource

# bad_f is declared in bad_8c.c, which belongs to no Doxygen group. With
# no default-group-name configured, nothing associates it with a group
# unless an item-to-group entry does.
_BAD_F = "bad_8c_1a8cc687906d3e4964fc993ca1bf18472e"


def _minimal_config(**overrides) -> dict:
    config = {
        "data": {},
        "groups": {},
        "spec-directory": "spec",
    }
    config.update(overrides)
    return config


def _get_path(path: str) -> str:
    test_dir = Path(__file__).parent
    return str(test_dir / path)


def _widget_api_xml_files() -> list[str]:
    # null-item-to-group/widget.h: every declaration (including the file
    # itself, via @file @ingroup) carries an explicit @ingroup, so nothing
    # needs an item-to-group entry. This is what used to make
    # --propose-config print a bare "item-to-group:" (parsed as YAML null)
    # instead of {}.
    return [
        _get_path(f"source-to-spec/null-item-to-group/xml/{name}")
        for name in ("group__WidgetAPI.xml", "widget_8h.xml")
    ]


def _foo_group_xml_files() -> list[str]:
    return [
        _get_path(f"source-to-spec/xml/{name}") for name in (
            "bad_8c.xml",
            "default_8h.xml",
            "foobar_8h.xml",
            "group__DefaultGroup.xml",
            "group__FooGroup.xml",
            "header_8h.xml",
            "source_8c.xml",
            "structgs__0.xml",
            "structgt__0.xml",
            "structs__0.xml",
            "structt__0.xml",
            "uniongu__0.xml",
            "uniongu__1.xml",
            "unionu__0.xml",
            "unionu__1.xml",
        )
    ]


def _propose(capsys, tmp_path, config, xml_files) -> str:
    """
    Run ``--propose-config`` through the command line interface and
    return what it printed.
    """
    config_file = tmp_path / "specware.yml"
    with open(config_file, "w", encoding="utf-8") as dst:
        yaml.safe_dump({"spec-from-source": config}, dst)
    clifromsource([
        "specfromsource", "--config-file",
        str(config_file), "--propose-config", *xml_files
    ])
    return capsys.readouterr().out


def _proposed_item_to_group(output: str) -> dict:
    """
    Parse the proposal's ``item-to-group`` back out of the printed text.

    Parsing rather than matching on the text is what makes this a
    round-trip check: the proposal is meant to be pasted straight back
    into a configuration file, so it has to survive being read as YAML.
    """
    return yaml.safe_load(output)["spec-from-source"]["item-to-group"]


def test_propose_config_prints_an_empty_map_when_nothing_to_list(
        tmp_path, capsys):
    output = _propose(capsys, tmp_path, _minimal_config(),
                      _widget_api_xml_files())
    assert _proposed_item_to_group(output) == {}


def test_propose_config_lists_resolved_item_to_group_entries(tmp_path, capsys):
    config = _minimal_config(groups={"FooGroup": {
        "uid": "/if/group"
    }},
                             **{"item-to-group": {
                                 _BAD_F: "FooGroup"
                             }})
    output = _propose(capsys, tmp_path, config, _foo_group_xml_files())
    assert _proposed_item_to_group(output)[_BAD_F] == "FooGroup"
    assert f"{_BAD_F}: FooGroup # function/bad_f" in output


def test_propose_config_emits_a_null_group_as_yaml_null(tmp_path, capsys):
    # A bare "item-to-group:" attribute parses as YAML null. An entry
    # whose value stays null must be printed as null rather than as the
    # string "None", or pasting the proposal back in changes its meaning.
    config = _minimal_config(groups={"FooGroup": {
        "uid": "/if/group"
    }},
                             **{"item-to-group": {
                                 _BAD_F: None
                             }})
    output = _propose(capsys, tmp_path, config, _foo_group_xml_files())
    assert _proposed_item_to_group(output)[_BAD_F] is None
