# SPDX-License-Identifier: BSD-2-Clause
""" Provides a command line interface to generate interface items. """

# Copyright (C) 2024, 2025 embedded brains GmbH & Co. KG
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

from specitems import create_argument_parser, init_logging, save_data
from specware import load_specware_config

from .sourcetospec import (doxygen_xml_to_spec, DoxygenContext, DoxygenGroup,
                           DoxygenFile, DoxygenFunction)


def _propose_config(ctx: DoxygenContext, spec_dir: str, config: dict) -> None:
    print("spec-from-source:")
    print(f"  spec-directory: {spec_dir}")
    print("  groups:")
    for group in sorted(ctx.items_by_kind["group"].values()):
        print(f"    {group.doxygen_id}: # {group.name} "
              f"({group.data['title']})")
        print(f"      uid: {group.uid}")
    for group in sorted(ctx.items_by_kind["group"].values()):
        assert isinstance(group, DoxygenGroup)
        if group.doxygen_id not in config["enabled-groups"]:
            continue
        print(group.doxygen_id)
        for group_member in group.members():
            if group_member.is_header:
                assert isinstance(group_member, DoxygenFile)
                print("  ", group_member.uid)
                for header_member in group_member.members():
                    if not isinstance(header_member, DoxygenFunction):
                        continue
                    path = os.path.join(spec_dir,
                                        f"{header_member.uid[1:]}.yml")
                    print("    ", header_member.uid, path)
                    save_data(path, header_member.export())


def clifromsource(argv: list[str] = sys.argv) -> None:
    """
    Generates interface items from Doxygen generated XML files using the
    configuration.
    """
    parser = create_argument_parser()
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
    args = parser.parse_args(argv[1:])
    init_logging(args)
    config, working_directory = load_specware_config(args.config_file)
    config = config["spec-from-source"]
    with contextlib.chdir(working_directory):
        spec_dir = config["spec-directory"]
        os.makedirs(spec_dir, exist_ok=True)
        ctx = doxygen_xml_to_spec(config, args.doxygen_xml_files)
        if args.propose_config:
            _propose_config(ctx, spec_dir, config)
        else:
            for item in ctx.items_by_kind["function"].values():
                print(item.name, item.data)
