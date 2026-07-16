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
import os
import sys
import yaml

from specitems import get_arguments
from specware import load_specware_config

from .sourcetospec import (DoxygenContext, DoxygenEnum, DoxygenGroup,
                           DoxygenFile, DoxygenTypedef)


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


def _generate_header(header: DoxygenFile) -> None:
    print("  ", header.uid)
    header.save()
    for header_member in header.members():
        if isinstance(header_member, DoxygenTypedef):
            continue
        print("    ", header_member.uid)
        header_member.save()
        if isinstance(header_member, DoxygenEnum):
            for enumerator in header_member.members():
                print("      ", enumerator.uid)
                enumerator.save()


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


def _generate_groups(ctx: DoxygenContext, config: dict) -> None:
    # A header carrying several @ingroup blocks, or one reached
    # transitively by members of different groups, is reachable from
    # more than one enabled group. Its content does not depend on which
    # group discovered it, so generate it once for the whole run rather
    # than rewriting the identical file under every owner.
    generated_headers: set[str] = set()
    for group in sorted(ctx.items_by_kind["group"].values()):
        assert isinstance(group, DoxygenGroup)
        if group.name not in config["enabled-groups"]:
            continue
        print(group.doxygen_id)
        group.save()
        for header in _reachable_headers(group):
            if header.doxygen_id in generated_headers:
                continue
            generated_headers.add(header.doxygen_id)
            _generate_header(header)


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
        parser.add_argument("doxygen_xml_files",
                            metavar="DOXYGEN_XML_FILES",
                            nargs="+",
                            help="the Doxygen generated XML files")

    args = get_arguments(argv[1:],
                         description=clifromsource.__doc__,
                         add_arguments=(_add_arguments, ))
    config, working_directory = load_specware_config(args.config_file)
    config = config["spec-from-source"]
    with contextlib.chdir(working_directory):
        ctx = DoxygenContext(config)
        os.makedirs(ctx.spec_directory, exist_ok=True)
        ctx.doxygen_xml_to_spec(args.doxygen_xml_files)
        if args.propose_config:
            _propose_config(ctx, config)
        else:
            _generate_groups(ctx, config)
