# SPDX-License-Identifier: BSD-2-Clause
""" Provides a command line interface to generate interface items. """

# Copyright (C) 2024, 2026 embedded brains GmbH & Co. KG
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

import contextlib
import glob
import json
import os
import sys
import yaml

from specitems import get_arguments
from specware import load_specware_config

from .sourcetospec import (ConfigError, DoxygenContext, DoxygenEnum,
                           DoxygenGroup, DoxygenFile, DoxygenTypedef)


def _propose_config(ctx: DoxygenContext, config: dict) -> None:
    config_2 = {"spec-from-source": config}
    config_2["spec-from-source"].pop("item-to-group", None)
    text = yaml.dump(config_2, default_flow_style=False, allow_unicode=True)
    print(text.rstrip())
    if ctx.item_to_group:
        print("  item-to-group:")
        for doxygen_id, group_ident in sorted(ctx.item_to_group.items()):
            item = ctx.items[doxygen_id]
            # Serialise each entry through yaml rather than formatting it
            # directly, so a null group and any group name that would
            # otherwise need quoting both survive a copy-paste back into
            # the configuration.
            entry = yaml.safe_dump({
                doxygen_id: group_ident
            },
                                   default_flow_style=False).strip()
            print(f"    {entry} # {item.kind}/{item.name}")
    else:
        print("  item-to-group: {}")


def _generate_header(header: DoxygenFile) -> list[str]:
    """ Generate a header and its members. Returns every saved UID. """
    print("  ", header.uid)
    header.save()
    uids = [header.uid]
    for header_member in header.members():
        if (isinstance(header_member, DoxygenTypedef)
                and header_member.aliases_compound):
            # For example `typedef enum e { ... } e;`. The enum item already
            # covers this under the same name, marked via definition-kind.
            continue
        print("    ", header_member.uid)
        header_member.save()
        uids.append(header_member.uid)
        if isinstance(header_member, DoxygenEnum):
            for enumerator in header_member.members():
                print("      ", enumerator.uid)
                enumerator.save()
                uids.append(enumerator.uid)
    return uids


def _reachable_headers(group: DoxygenGroup) -> list[DoxygenFile]:
    """
    Find every header file reachable from a group's members.

    A header is reachable directly, when the file itself is a group
    member via ``@file \\ingroup``, or transitively, when a group
    member such as a function is declared in that file via a bare
    ``@ingroup``.
    """
    headers: dict[str, DoxygenFile] = {}
    for group_member in group.members():
        if group_member.is_header:
            assert isinstance(group_member, DoxygenFile)
            headers.setdefault(group_member.doxygen_id, group_member)
            continue
        for file in group_member.files:
            if not file.is_header:
                continue
            if not file.group_ids:
                # Reached only transitively, for example via a function
                # that carries its own @ingroup with no @file @ingroup on the
                # header itself: place it under the discovering group, the
                # same way it would be placed had it been an explicit group
                # member. If a later group also transitively reaches the
                # same file through a different member, that first
                # assignment wins (groups are processed in a fixed,
                # doxygen_id-sorted order): the file is placed once, under
                # whichever enabled group's member is encountered first.
                file.group_ids.append(group.doxygen_id)
            headers.setdefault(file.doxygen_id, file)
    return sorted(headers.values())


def _record_owner(generated: dict[str, list[str]], uid: str,
                  group_name: str) -> None:
    """
    Record ``group_name`` as an owner of ``uid``, at most once.

    Two headers in the same group can yield the same UID, for example
    an enumerator reachable through either of them, so the same owner
    can be offered for one UID more than once.
    """
    owners = generated.setdefault(uid, [])
    if group_name not in owners:
        owners.append(group_name)


def _generate_groups(ctx: DoxygenContext,
                     config: dict) -> dict[str, list[str]]:
    """
    Generate every enabled group's contents.

    Returns every generated item's UID mapped to the names of the
    enabled groups that own it, for ``--prune`` to compare against a
    previous run's manifest. A header reachable from several enabled
    groups is owned by all of them, so ownership is a list rather than
    a single name.
    """
    generated: dict[str, list[str]] = {}
    # A header carrying several @ingroup blocks, or one reached
    # transitively by members of different groups, is reachable from
    # more than one enabled group. Its content does not depend on which
    # group discovered it, so generate it once for the whole run rather
    # than rewriting the identical file under every owner. The UIDs it
    # produced are cached, because every later owner still has to be
    # recorded against them.
    header_uids: dict[str, list[str]] = {}
    for group in sorted(ctx.items_by_kind["group"].values()):
        assert isinstance(group, DoxygenGroup)
        if group.name not in config["enabled-groups"]:
            continue
        print(group.doxygen_id)
        group.save()
        _record_owner(generated, group.uid, group.name)
        for header in _reachable_headers(group):
            uids = header_uids.get(header.doxygen_id)
            if uids is None:
                uids = _generate_header(header)
                header_uids[header.doxygen_id] = uids
            for uid in uids:
                _record_owner(generated, uid, group.name)
    return generated


_MANIFEST_FILENAME = ".specfromsource-manifest.json"


def _load_manifest(path: str) -> dict[str, list[str]]:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as src:
        manifest = json.load(src)
    if not isinstance(manifest, dict):
        return {}
    # A manifest is written by this tool but read back as a plain file
    # that could be stale, hand-edited, or shared across checkouts, the
    # same reason pruning refuses to unlink outside spec-directory. A
    # value that isn't a group name or a list of them yields no owners,
    # which spares the entry rather than raising on it. A bare name is
    # what a manifest written before ownership became a list records.
    owners_by_uid: dict[str, list[str]] = {}
    for uid, owners in manifest.items():
        if isinstance(owners, str):
            owners_by_uid[uid] = [owners]
        elif isinstance(owners, list):
            owners_by_uid[uid] = [
                owner for owner in owners if isinstance(owner, str)
            ]
        else:
            owners_by_uid[uid] = []
    return owners_by_uid


def _save_manifest(path: str, manifest: dict[str, list[str]]) -> None:
    with open(path, "w", encoding="utf-8") as dst:
        json.dump(manifest, dst, indent=2, sort_keys=True)
        dst.write("\n")


def _prune(ctx: DoxygenContext, enabled_groups: list[str],
           generated: dict[str, list[str]]) -> None:
    """
    Remove previously-generated items no longer produced by this run.

    Uses a manifest tracking each UID's owning enabled groups from the
    last ``--prune`` run. A UID is stale once this run produced no such
    item and at least one of its recorded owners is enabled: that owner
    is present and no longer generating it, which is what makes the
    item obsolete rather than merely unvisited. A UID none of whose
    owners are enabled is left alone, so a group left out of
    ``enabled-groups`` this time around (by oversight or otherwise)
    never has its previously-generated items pruned out from under it.
    """
    manifest_path = str(ctx.spec_directory / _MANIFEST_FILENAME)
    previous = _load_manifest(manifest_path)
    this_run_groups = set(enabled_groups)
    stale = {
        uid
        for uid, owners in previous.items()
        if uid not in generated and any(owner in this_run_groups
                                        for owner in owners)
    }
    spec_directory = ctx.spec_directory.resolve()
    for uid in sorted(stale):
        item_path = (ctx.spec_directory / f"{uid[1:]}.yml").resolve()
        if not item_path.is_relative_to(spec_directory):
            # A manifest is trusted state written by a prior run of this
            # same tool, but it's still just a file on disk that could be
            # stale, hand-edited, or shared across checkouts. Never unlink
            # outside spec-directory on its say-so.
            print("  skipped pruning", uid, "(escapes spec-directory)")
            continue
        if item_path.is_file():
            print("  pruned", uid)
            item_path.unlink()
    # Entries this run had nothing to say about, because none of their
    # owners took part, carry over untouched. Everything else is
    # replaced by what this run actually produced.
    new_manifest = {
        uid: owners
        for uid, owners in previous.items()
        if not any(owner in this_run_groups for owner in owners)
    }
    new_manifest.update(
        (uid, sorted(owners)) for uid, owners in generated.items())
    _save_manifest(manifest_path, new_manifest)


def _resolve_xml_files(doxygen_xml_files: list[str],
                       doxygen_xml_dir: str | None) -> list[str]:
    """
    Resolve the Doxygen XML files to process.

    Either from an explicit list or by globbing ``*.xml`` in
    ``--doxygen-xml-dir``. Exactly one of the two must be given.
    """
    if doxygen_xml_dir is not None:
        if doxygen_xml_files:
            raise ConfigError(
                "DOXYGEN_XML_FILES and --doxygen-xml-dir are mutually "
                "exclusive")
        resolved = sorted(glob.glob(os.path.join(doxygen_xml_dir, "*.xml")))
        if not resolved:
            raise ConfigError("no *.xml files found in --doxygen-xml-dir "
                              f"{doxygen_xml_dir!r}")
        return resolved
    if not doxygen_xml_files:
        raise ConfigError(
            "no Doxygen XML files given: pass DOXYGEN_XML_FILES or "
            "--doxygen-xml-dir")
    return doxygen_xml_files


def _run(args) -> None:
    try:
        config, working_directory = load_specware_config(args.config_file)
    except FileNotFoundError as err:
        raise ConfigError(str(err)) from err
    try:
        config = config["spec-from-source"]
    except KeyError as err:
        raise ConfigError(
            f"{args.config_file or 'specware.yml'} is missing the "
            "top-level 'spec-from-source' attribute") from err
    with contextlib.chdir(working_directory):
        xml_files = _resolve_xml_files(args.doxygen_xml_files,
                                       args.doxygen_xml_dir)
        ctx = DoxygenContext(config,
                             require_enabled_groups=not args.propose_config)
        os.makedirs(ctx.spec_directory, exist_ok=True)
        ctx.doxygen_xml_to_spec(xml_files)
        if args.propose_config:
            _propose_config(ctx, config)
        else:
            generated = _generate_groups(ctx, config)
            if args.prune:
                _prune(ctx, config["enabled-groups"], generated)


def clifromsource(argv: list[str] = sys.argv) -> None:
    """
    Generate interface items from Doxygen generated XML files using the
    configuration.
    """

    def _add_arguments(parser):
        parser.add_argument("--config-file",
                            type=str,
                            default=None,
                            help="use this configuration file")
        parser.add_argument("--propose-config",
                            action="store_true",
                            help="propose a configuration")
        parser.add_argument(
            "--prune",
            action="store_true",
            help="remove previously generated items no longer produced by "
            "this run, tracked via a manifest file in spec-directory")
        parser.add_argument(
            "--doxygen-xml-dir",
            type=str,
            default=None,
            help="use every *.xml file in this directory instead of "
            "listing DOXYGEN_XML_FILES individually")
        parser.add_argument("doxygen_xml_files",
                            metavar="DOXYGEN_XML_FILES",
                            nargs="*",
                            help="the Doxygen generated XML files")

    args = get_arguments(argv[1:],
                         description=clifromsource.__doc__,
                         add_arguments=(_add_arguments, ))
    try:
        _run(args)
    except ConfigError as err:
        # Every known, anticipated failure mode (a bad --config-file path,
        # a malformed config, no XML source given, an item-to-group entry
        # naming an unknown group, ...) is raised as a ConfigError with a
        # message that already names the offending attribute/item. Surface
        # that message directly instead of a traceback. Catching only
        # ConfigError, not ValueError generally, means a ValueError raised
        # by an actual internal bug elsewhere still surfaces as a
        # traceback instead of being mistaken for a config problem.
        sys.exit(f"specfromsource: error: {err}")
