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

import json
import os
import re
from pathlib import Path

import yaml

import pytest

from specmake import DoxygenContext
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


def _generate(tmp_path, config, xml_files, prune: bool = False) -> None:
    """ Run a generation pass through the command line interface. """
    argv = ["specfromsource", "--config-file", _write_config(tmp_path, config)]
    if prune:
        argv.append("--prune")
    clifromsource(argv + list(xml_files))


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


def _valid_config() -> dict:
    return {
        "data": {},
        "spec-directory": "spec",
        "groups": {},
        "item-to-group": None,
        "type-map": {},
        "default-group-name": "DefaultGroup",
        "enabled-groups": [],
    }


def test_doxygen_context_accepts_a_valid_config():
    # DoxygenContext validates on construction, so a caller that never
    # goes through the command line interface gets the same named error
    # rather than a crash deep in resolution.
    DoxygenContext(_valid_config(), require_enabled_groups=True)
    DoxygenContext(_valid_config(), require_enabled_groups=False)


@pytest.mark.parametrize("missing_attribute",
                         ["data", "spec-directory", "groups"])
def test_doxygen_context_reports_missing_required_attribute(missing_attribute):
    config = _valid_config()
    del config[missing_attribute]
    with pytest.raises(
            ValueError,
            match=f"missing required attribute {missing_attribute!r}"):
        DoxygenContext(config, require_enabled_groups=True)


@pytest.mark.parametrize("attribute,bad_value", [
    ("data", []),
    ("spec-directory", 123),
    ("groups", []),
    ("item-to-group", []),
    ("type-map", []),
    ("default-group-name", []),
    ("enabled-groups", "FooGroup"),
])
def test_doxygen_context_reports_wrong_type(attribute, bad_value):
    config = _valid_config()
    config[attribute] = bad_value
    with pytest.raises(ValueError, match=f"attribute {attribute!r} must be a"):
        DoxygenContext(config, require_enabled_groups=True)


def test_doxygen_context_reports_every_problem_at_once():
    with pytest.raises(ValueError) as excinfo:
        DoxygenContext({}, require_enabled_groups=True)
    message = str(excinfo.value)
    for attribute in ("data", "spec-directory", "groups", "enabled-groups"):
        assert attribute in message, (
            f"{attribute!r} missing from aggregated error")


def test_doxygen_context_does_not_require_enabled_groups_to_propose():
    DoxygenContext({"data": {}, "spec-directory": "spec", "groups": {}})


def test_doxygen_context_still_checks_enabled_groups_type_when_optional():
    config = {
        "data": {},
        "spec-directory": "spec",
        "groups": {},
        "enabled-groups": "FooGroup",
    }
    with pytest.raises(ValueError,
                       match="attribute 'enabled-groups' must be a"):
        DoxygenContext(config)


# Elements, not just the containers holding them. Each of these values
# reaches code that assumes a string, so an unchecked element would
# surface as a TypeError far from the configuration that caused it.
@pytest.mark.parametrize("attribute,bad_value,expected", [
    ("enabled-groups", [{
        "FooGroup": True
    }], "entry 0 must be a string"),
    ("enabled-groups", ["FooGroup", 7], "entry 1 must be a string"),
    ("groups", {
        "FooGroup": []
    }, "entry 'FooGroup' must be a dict"),
    ("groups", {
        7: {}
    }, "non-string key 7"),
    ("item-to-group", {
        "id_0": []
    }, "must be a string or null"),
    ("item-to-group", {
        7: "FooGroup"
    }, "non-string key 7"),
    ("type-map", {
        "a": 7
    }, "value for 'a' must be a string"),
    ("type-map", {
        7: "a"
    }, "non-string key 7"),
])
def test_doxygen_context_reports_bad_elements(attribute, bad_value, expected):
    config = _valid_config()
    config[attribute] = bad_value
    with pytest.raises(ValueError, match=re.escape(expected)):
        DoxygenContext(config, require_enabled_groups=True)


def test_doxygen_context_accepts_a_null_item_to_group_value():
    # A null value is how a user pins an item to no group at all and
    # leaves it to inference, so it has to stay valid.
    config = _valid_config()
    config["item-to-group"] = {"id_0": None}
    DoxygenContext(config, require_enabled_groups=True)


def test_clifromsource_reports_an_invalid_config(tmp_path):
    with pytest.raises(ValueError, match="invalid 'spec-from-source'"):
        _generate(tmp_path, {"groups": {}}, _foo_group_xml_files())


def test_generate_writes_the_enabled_group_contents(tmp_path):
    spec_dir = tmp_path / "spec"
    config = {
        "data": {},
        "groups": {
            "FooGroup": {
                "uid": "/if/group",
                "remove-prefix": "foobar-"
            }
        },
        "enabled-groups": ["FooGroup"],
        "spec-directory": str(spec_dir),
    }
    _generate(tmp_path, config, _foo_group_xml_files())

    # A function (gf_0) and an enum with enumerators (ge_0/GE_0_A) both
    # live in FooGroup, exercising the header member loop and its
    # enum-enumerator recursion in one real run. header.h's e_0 also has
    # a "typedef enum e_0 e_0" alias with the same target uid as the enum
    # itself; the typedef skip keeps that alias from ever being saved, so
    # e-0.yml ends up holding the enum's own content.
    assert (spec_dir / "if" / "group.yml").is_file()
    assert (spec_dir / "if" / "gf-0.yml").is_file()
    assert (spec_dir / "if" / "ge-0.yml").is_file()
    assert (spec_dir / "if" / "ge-0-a.yml").is_file()


def test_generate_skips_disabled_groups(tmp_path):
    spec_dir = tmp_path / "spec"
    config = {
        "data": {},
        "groups": {},
        "enabled-groups": [],
        "spec-directory": str(spec_dir),
    }
    _generate(tmp_path, config, _foo_group_xml_files())
    assert not list(spec_dir.rglob("*.yml"))


def test_propose_config_output_is_usable_verbatim(tmp_path, capsys):
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
    output = _propose(capsys, tmp_path, config, _widget_api_xml_files())
    proposed = yaml.safe_load(output)["spec-from-source"]
    assert proposed["item-to-group"] == {}

    # Copy the proposal verbatim into a fresh run, exactly as a user
    # would, and it has to generate.
    proposed["spec-directory"] = str(spec_dir)
    _generate(tmp_path, proposed, _widget_api_xml_files())
    assert (spec_dir / "if" / "group.yml").is_file()
    assert (spec_dir / "if" / "widget-set-size.yml").is_file()


def test_generate_groups_generates_typedefs(tmp_path):
    spec_dir = tmp_path / "spec"
    config = {
        "data": {},
        "groups": {
            "TypesAPI": {
                "uid": "/if/group"
            }
        },
        "enabled-groups": ["TypesAPI"],
        "spec-directory": str(spec_dir),
    }
    _generate(tmp_path, config, [
        _get_path("source-to-spec/typedef-generation/xml/group__TypesAPI.xml"),
        _get_path("source-to-spec/typedef-generation/xml/types_8h.xml"),
    ])

    # Genuine standalone typedefs are generated.
    assert (spec_dir / "if" / "widget-size-t.yml").is_file()
    assert (spec_dir / "if" / "widget-handle.yml").is_file()

    # tagged_enum has both an enum item and a same-named typedef alias
    # (`typedef enum tagged_enum { ... } tagged_enum;`); the typedef alias
    # must not overwrite the enum's own generated content.
    with open(spec_dir / "if" / "tagged-enum.yml", encoding="utf-8") as src:
        tagged_enum = yaml.safe_load(src)
    assert tagged_enum["interface-type"] == "enum"


def test_generate_groups_typedef_alias_check_is_scoped_by_group(tmp_path):
    # networking.h's "status" struct and storage.h's "status" typedef are
    # unrelated declarations that only coincidentally share a name, each in
    # its own group and directory: the genuine storage.h typedef must
    # still be generated, not mistaken for an alias of the unrelated
    # struct.
    spec_dir = tmp_path / "spec"
    config = {
        "data": {},
        "groups": {
            "NetworkingAPI": {
                "uid": "/net/if/group"
            },
            "StorageAPI": {
                "uid": "/storage/if/group"
            },
        },
        "enabled-groups": ["NetworkingAPI", "StorageAPI"],
        "spec-directory": str(spec_dir),
    }
    _generate(tmp_path, config, [
        _get_path(f"source-to-spec/typedef-name-collision/xml/{name}")
        for name in (
            "group__NetworkingAPI.xml",
            "group__StorageAPI.xml",
            "networking_8h.xml",
            "storage_8h.xml",
            "structstatus.xml",
        )
    ])

    with open(spec_dir / "storage" / "if" / "status.yml",
              encoding="utf-8") as src:
        storage_status = yaml.safe_load(src)
    assert storage_status["interface-type"] == "typedef"

    with open(spec_dir / "net" / "if" / "status.yml", encoding="utf-8") as src:
        networking_status = yaml.safe_load(src)
    assert networking_status["interface-type"] == "struct"


def _manifest_path(spec_dir) -> Path:
    return spec_dir / ".specfromsource-manifest.json"


def _read_manifest(spec_dir) -> dict:
    with open(_manifest_path(spec_dir), encoding="utf-8") as src:
        return json.load(src)


def _write_manifest(spec_dir, manifest: dict) -> None:
    spec_dir.mkdir(parents=True, exist_ok=True)
    with open(_manifest_path(spec_dir), "w", encoding="utf-8") as dst:
        json.dump(manifest, dst)


def _foo_group_config(spec_dir) -> dict:
    return {
        "data": {},
        "groups": {
            "FooGroup": {
                "uid": "/if/group",
                "remove-prefix": "foobar-"
            }
        },
        "enabled-groups": ["FooGroup"],
        "spec-directory": str(spec_dir),
    }


def test_prune_manifest_records_every_generated_uid_with_its_group(tmp_path):
    # The manifest is how one run's generated set survives to the next,
    # so it is also where that set is observable from outside.
    spec_dir = tmp_path / "spec"
    _generate(tmp_path,
              _foo_group_config(spec_dir),
              _foo_group_xml_files(),
              prune=True)
    manifest = _read_manifest(spec_dir)
    assert manifest["/if/group"] == ["FooGroup"]
    assert manifest["/if/gf-0"] == ["FooGroup"]
    assert {owner
            for owners in manifest.values()
            for owner in owners} == {"FooGroup"}


def test_prune_removes_stale_items_tracked_in_manifest(tmp_path):
    spec_dir = tmp_path / "spec"
    _write_manifest(spec_dir, {
        "/if/gone": ["FooGroup"],
        "/if/group": ["FooGroup"]
    })
    (spec_dir / "if").mkdir(parents=True, exist_ok=True)
    (spec_dir / "if" / "gone.yml").write_text("stale: true\n")

    # This run regenerates /if/group, but nothing produces /if/gone.
    _generate(tmp_path,
              _foo_group_config(spec_dir),
              _foo_group_xml_files(),
              prune=True)

    assert not (spec_dir / "if" / "gone.yml").exists()
    assert (spec_dir / "if" / "group.yml").is_file()
    assert "/if/gone" not in _read_manifest(spec_dir)


def test_prune_does_not_touch_groups_outside_this_run(tmp_path):
    spec_dir = tmp_path / "spec"
    _write_manifest(spec_dir, {"/other/item": ["OtherGroup"]})
    (spec_dir / "other").mkdir(parents=True, exist_ok=True)
    (spec_dir / "other" / "item.yml").write_text("x: 1\n")

    # This run only processes FooGroup. OtherGroup is left alone even
    # though none of its manifest entries were regenerated.
    _generate(tmp_path,
              _foo_group_config(spec_dir),
              _foo_group_xml_files(),
              prune=True)

    assert (spec_dir / "other" / "item.yml").is_file()
    manifest = _read_manifest(spec_dir)
    assert manifest["/other/item"] == ["OtherGroup"]
    # This run's own entries are recorded alongside it, which is what
    # distinguishes "pruning ran and spared OtherGroup" from "pruning
    # never ran at all".
    assert manifest["/if/group"] == ["FooGroup"]


def test_prune_never_touches_files_outside_the_manifest(tmp_path):
    spec_dir = tmp_path / "spec"
    (spec_dir / "if").mkdir(parents=True, exist_ok=True)
    (spec_dir / "if" / "hand-authored.yml").write_text("x: 1\n")
    # No manifest yet: hand-authored.yml was never tool-generated.
    _generate(tmp_path,
              _foo_group_config(spec_dir),
              _foo_group_xml_files(),
              prune=True)
    assert (spec_dir / "if" / "hand-authored.yml").is_file()
    # A manifest exists only because pruning ran, so this cannot pass by
    # pruning having been skipped.
    assert "/if/group" in _read_manifest(spec_dir)


def test_prune_tolerates_a_manifest_entry_already_missing_from_disk(tmp_path):
    # A manifest entry whose file was already removed by other means,
    # for example by hand, must not raise. It is simply dropped from the
    # manifest.
    spec_dir = tmp_path / "spec"
    _write_manifest(spec_dir, {"/if/already-gone": ["FooGroup"]})
    _generate(tmp_path,
              _foo_group_config(spec_dir),
              _foo_group_xml_files(),
              prune=True)
    assert "/if/already-gone" not in _read_manifest(spec_dir)


def test_prune_refuses_to_delete_outside_spec_directory(tmp_path, capsys):
    # A manifest is trusted state from a prior run of this same tool, but
    # it's still just a file on disk. A UID escaping spec-directory via
    # ".." must never be deleted, regardless of how it got there:
    # hand-edited, corrupted, or copied from a differently-configured
    # checkout.
    outside = tmp_path / "outside-spec-directory.yml"
    outside.write_text("must not be deleted\n")
    spec_dir = tmp_path / "spec"
    escaping_uid = "/" + os.path.relpath(outside, spec_dir)[:-len(".yml")]
    _write_manifest(spec_dir, {escaping_uid: "FooGroup"})

    _generate(tmp_path,
              _foo_group_config(spec_dir),
              _foo_group_xml_files(),
              prune=True)

    assert outside.is_file()
    assert outside.read_text() == "must not be deleted\n"
    assert "escapes spec-directory" in capsys.readouterr().out


def test_prune_removes_item_for_a_declaration_deleted_from_the_header(
        tmp_path):
    spec_dir = tmp_path / "spec"
    config = {
        "data": {},
        "groups": {
            "QueueAPI": {
                "uid": "/if/group"
            }
        },
        "enabled-groups": ["QueueAPI"],
        "spec-directory": str(spec_dir),
    }

    def queue_xml(revision: str) -> list[str]:
        return [
            _get_path(f"source-to-spec/prune-removed-declaration/{revision}"
                      f"/xml/{name}")
            for name in ("group__QueueAPI.xml", "queue_8h.xml")
        ]

    # First run: queue_create and queue_destroy both exist.
    _generate(tmp_path, config, queue_xml("before"), prune=True)
    assert (spec_dir / "if" / "queue-create.yml").is_file()
    assert (spec_dir / "if" / "queue-destroy.yml").is_file()

    # Second run: queue_destroy has been removed from the header.
    _generate(tmp_path, config, queue_xml("after"), prune=True)

    assert (spec_dir / "if" / "queue-create.yml").is_file()
    assert not (spec_dir / "if" / "queue-destroy.yml").exists()
    manifest = _read_manifest(spec_dir)
    assert "/if/queue-destroy" not in manifest
    assert manifest["/if/queue-create"] == ["QueueAPI"]


def test_doxygen_xml_dir_generates_the_same_items_as_listing_the_files(
        tmp_path):
    config = {
        "data": {},
        "groups": {
            "WidgetAPI": {
                "uid": "/if/group"
            }
        },
        "enabled-groups": ["WidgetAPI"],
    }

    def run(name, extra_argv, xml_files) -> list[str]:
        work = tmp_path / name
        work.mkdir()
        spec_dir = work / "spec"
        config_file = _write_config(work, {
            **config, "spec-directory": str(spec_dir)
        })
        clifromsource(["specfromsource", "--config-file", config_file] +
                      extra_argv + list(xml_files))
        return sorted(
            str(path.relative_to(spec_dir))
            for path in spec_dir.rglob("*.yml"))

    listed = run("listed", [], _widget_api_xml_files())
    globbed = run("globbed", [
        "--doxygen-xml-dir",
        _get_path("source-to-spec/null-item-to-group/xml")
    ], [])
    assert listed
    assert globbed == listed


def test_doxygen_xml_dir_and_listed_files_are_mutually_exclusive(tmp_path):
    with pytest.raises(ValueError, match="mutually exclusive"):
        clifromsource([
            "specfromsource", "--config-file",
            _write_config(tmp_path, _foo_group_config(tmp_path / "spec")),
            "--doxygen-xml-dir", "some/dir", "a.xml"
        ])


def test_no_doxygen_xml_files_given_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="no Doxygen XML files given"):
        clifromsource([
            "specfromsource", "--config-file",
            _write_config(tmp_path, _foo_group_config(tmp_path / "spec"))
        ])


def test_an_empty_doxygen_xml_dir_is_rejected(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match=r"no \*\.xml files found"):
        clifromsource([
            "specfromsource", "--config-file",
            _write_config(tmp_path, _foo_group_config(tmp_path / "spec")),
            "--doxygen-xml-dir",
            str(empty)
        ])


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


def _shared_header_config(spec_dir, enabled_groups=None) -> dict:
    return {
        "data": {},
        "groups": {
            "AlphaAPI": {
                "uid": "/if/alpha"
            },
            "BetaAPI": {
                "uid": "/if/beta"
            }
        },
        "enabled-groups": (["AlphaAPI", "BetaAPI"]
                           if enabled_groups is None else enabled_groups),
        "spec-directory":
        str(spec_dir),
    }


def test_prune_manifest_records_every_owner_of_a_shared_header(tmp_path):
    # shared.h belongs to both enabled groups, so neither one owns its
    # items alone. Recording a single owner would make the survivor
    # depend on group iteration order.
    spec_dir = tmp_path / "spec"
    _generate(tmp_path,
              _shared_header_config(spec_dir),
              _shared_header_xml_files(),
              prune=True)
    manifest = _read_manifest(spec_dir)
    assert manifest["/if/header-shared"] == ["AlphaAPI", "BetaAPI"]
    assert manifest["/if/alpha"] == ["AlphaAPI"]
    assert manifest["/if/beta"] == ["BetaAPI"]


def test_prune_removes_a_shared_item_when_one_owner_is_still_enabled(tmp_path):
    # A jointly-owned item that this run no longer produces is stale as
    # soon as any one of its owners is present to notice. Requiring all
    # of them would leave it on disk forever whenever the other owner is
    # disabled.
    spec_dir = tmp_path / "spec"
    _write_manifest(spec_dir, {"/if/gone": ["AlphaAPI", "BetaAPI"]})
    (spec_dir / "if").mkdir(parents=True, exist_ok=True)
    (spec_dir / "if" / "gone.yml").write_text("stale: true\n")

    _generate(tmp_path,
              _shared_header_config(spec_dir, enabled_groups=["AlphaAPI"]),
              _shared_header_xml_files(),
              prune=True)

    assert not (spec_dir / "if" / "gone.yml").exists()
    assert "/if/gone" not in _read_manifest(spec_dir)


def test_prune_spares_an_item_when_no_owner_is_enabled(tmp_path):
    # The other half of the same rule: with every owner absent, nothing
    # in this run can tell whether the item is obsolete.
    spec_dir = tmp_path / "spec"
    _write_manifest(spec_dir, {"/if/kept": ["BetaAPI"]})
    (spec_dir / "if").mkdir(parents=True, exist_ok=True)
    (spec_dir / "if" / "kept.yml").write_text("x: 1\n")

    _generate(tmp_path,
              _shared_header_config(spec_dir, enabled_groups=["AlphaAPI"]),
              _shared_header_xml_files(),
              prune=True)

    assert (spec_dir / "if" / "kept.yml").is_file()
    assert _read_manifest(spec_dir)["/if/kept"] == ["BetaAPI"]


def test_prune_reads_a_legacy_single_owner_manifest(tmp_path):
    # A manifest written before ownership became a list stores a bare
    # group name. Iterating that string character by character would
    # match no group, silently sparing every entry it records.
    spec_dir = tmp_path / "spec"
    _write_manifest(spec_dir, {"/if/gone": "FooGroup"})
    (spec_dir / "if").mkdir(parents=True, exist_ok=True)
    (spec_dir / "if" / "gone.yml").write_text("stale: true\n")

    _generate(tmp_path,
              _foo_group_config(spec_dir),
              _foo_group_xml_files(),
              prune=True)

    assert not (spec_dir / "if" / "gone.yml").exists()
    assert _read_manifest(spec_dir)["/if/group"] == ["FooGroup"]


def test_prune_manifest_records_each_owner_once(tmp_path):
    # Two headers in one group can yield the same UID, for example an
    # enumerator reachable through either of them. The owner is still
    # recorded once.
    spec_dir = tmp_path / "spec"
    _generate(tmp_path,
              _foo_group_config(spec_dir),
              _foo_group_xml_files(),
              prune=True)
    manifest = _read_manifest(spec_dir)
    duplicated = {
        uid: owners
        for uid, owners in manifest.items() if len(owners) != len(set(owners))
    }
    assert not duplicated


@pytest.mark.parametrize("bad_owners", [None, 5, {"FooGroup": 1}, [7]])
def test_prune_spares_an_entry_with_unreadable_owners(tmp_path, bad_owners):
    # A manifest is read back as a plain file that could be stale or
    # hand-edited. An entry whose owners can't be read yields no owners,
    # so it is spared rather than raising.
    spec_dir = tmp_path / "spec"
    _write_manifest(spec_dir, {"/if/odd": bad_owners})
    (spec_dir / "if").mkdir(parents=True, exist_ok=True)
    (spec_dir / "if" / "odd.yml").write_text("x: 1\n")

    _generate(tmp_path,
              _foo_group_config(spec_dir),
              _foo_group_xml_files(),
              prune=True)

    assert (spec_dir / "if" / "odd.yml").is_file()
    assert _read_manifest(spec_dir)["/if/odd"] == []


def test_prune_ignores_a_manifest_that_is_not_a_mapping(tmp_path):
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)
    with open(_manifest_path(spec_dir), "w", encoding="utf-8") as dst:
        json.dump(["not", "a", "mapping"], dst)

    _generate(tmp_path,
              _foo_group_config(spec_dir),
              _foo_group_xml_files(),
              prune=True)

    assert _read_manifest(spec_dir)["/if/group"] == ["FooGroup"]
