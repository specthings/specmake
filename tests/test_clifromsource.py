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


def _nested_group_xml_files() -> list[str]:
    # nested-groups: a three-level @defgroup/@ingroup chain,
    # ComponentAPIGroup to ComponentAPISubGroup to
    # ComponentAPISubSubGroup, nested via @ingroup on the @defgroup
    # itself (not on any member), with gadget.h a direct member of the
    # innermost group via @file @ingroup.
    return [
        _get_path(f"source-to-spec/nested-groups/xml/{name}") for name in (
            "default_8dox.xml",
            "gadget_8h.xml",
            "group__ComponentAPIGroup.xml",
            "group__ComponentAPISubGroup.xml",
            "group__ComponentAPISubSubGroup.xml",
        )
    ]


def _write_config(tmp_path, config) -> str:
    config_file = tmp_path / "specware.yml"
    with open(config_file, "w", encoding="utf-8") as dst:
        yaml.safe_dump({"spec-from-source": config}, dst)
    return str(config_file)


def _propose(capsys, tmp_path, config, xml_files) -> str:
    """
    Run ``--propose-config`` through the command line interface and
    return what it printed.
    """
    clifromsource([
        "specfromsource", "--config-file",
        _write_config(tmp_path, config), "--propose-config", *xml_files
    ])
    return capsys.readouterr().out


def _generate(tmp_path, config, xml_files) -> None:
    """ Run a generation pass through the command line interface. """
    clifromsource([
        "specfromsource", "--config-file",
        _write_config(tmp_path, config), *xml_files
    ])


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


def test_nested_group_gets_interface_ingroup_link(tmp_path):
    spec_dir = tmp_path / "spec"
    config = {
        "data": {},
        "groups": {
            "ComponentAPIGroup": {
                "uid": "/if/group"
            },
            "ComponentAPISubGroup": {
                "uid": "/sub/if/group"
            },
            "ComponentAPISubSubGroup": {
                "uid": "/sub/sub/if/group"
            },
        },
        "enabled-groups": [
            "ComponentAPIGroup", "ComponentAPISubGroup",
            "ComponentAPISubSubGroup"
        ],
        "spec-directory":
        str(spec_dir),
    }
    _generate(tmp_path, config, _nested_group_xml_files())

    with open(spec_dir / "sub" / "if" / "group.yml", encoding="utf-8") as src:
        sub_group = yaml.safe_load(src)
    assert sub_group["links"] == [{
        "role": "interface-ingroup",
        "uid": "../../if/group"
    }]

    with open(spec_dir / "sub" / "sub" / "if" / "group.yml",
              encoding="utf-8") as src:
        sub_sub_group = yaml.safe_load(src)
    assert sub_sub_group["links"] == [{
        "role": "interface-ingroup",
        "uid": "../../if/group"
    }]

    # The innermost group's own content is generated exactly once, under
    # its own directory, not duplicated under either ancestor's, even
    # though it is also a "member" of its parent, which is in turn a
    # "member" of the root group.
    assert (spec_dir / "sub" / "sub" / "if" / "header-gadget.yml").is_file()
    assert (spec_dir / "sub" / "sub" / "if" / "gadget-init.yml").is_file()
    assert (spec_dir / "sub" / "sub" / "if" / "gadget-configure.yml").is_file()
    assert not (spec_dir / "sub" / "if" / "header-gadget.yml").exists()
    assert not (spec_dir / "if" / "header-gadget.yml").exists()


def test_generate_groups_reaches_files_via_member_ingroup_alone(tmp_path):
    # ingroup-only-member/widget.h has no @file @ingroup block at all: only
    # widget_set_size's own @ingroup associates it with WidgetAPI. Before
    # transitive discovery, this produced zero generated files, no error.
    spec_dir = tmp_path / "spec"
    config = {
        "data": {},
        "groups": {
            "WidgetAPI": {
                "uid": "/if/group"
            }
        },
        "enabled-groups": ["WidgetAPI"],
        "spec-directory": str(spec_dir),
    }
    _generate(tmp_path, config, [
        _get_path(
            "source-to-spec/ingroup-only-member/xml/group__WidgetAPI.xml"),
        _get_path("source-to-spec/ingroup-only-member/xml/widget_8h.xml"),
    ])
    assert (spec_dir / "if" / "header-widget.yml").is_file()
    assert (spec_dir / "if" / "widget-set-size.yml").is_file()


def _shared_header_xml_files() -> list[str]:
    # shared-header/shared.h carries two @file @ingroup blocks, so it is
    # a direct member of both AlphaAPI and BetaAPI.
    return [
        _get_path(f"source-to-spec/shared-header/xml/{name}")
        for name in ("group__AlphaAPI.xml", "group__BetaAPI.xml",
                     "shared_8h.xml")
    ]


def test_generate_groups_generates_a_shared_header_once(tmp_path, capsys):
    # A header reachable from two enabled groups used to be saved once
    # per owning group, rewriting the identical file and listing it
    # twice.
    spec_dir = tmp_path / "spec"
    config = {
        "data": {},
        "groups": {
            "AlphaAPI": {
                "uid": "/if/alpha"
            },
            "BetaAPI": {
                "uid": "/if/beta"
            }
        },
        "enabled-groups": ["AlphaAPI", "BetaAPI"],
        "spec-directory": str(spec_dir),
    }
    _generate(tmp_path, config, _shared_header_xml_files())
    output = capsys.readouterr().out
    assert output.count("/if/header-shared") == 1
