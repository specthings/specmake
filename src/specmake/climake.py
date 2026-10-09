# SPDX-License-Identifier: BSD-2-Clause
""" Provides a command line interface to make items of a package. """

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

import argparse
import logging

from specitems import (ItemCache, ItemCacheConfig, get_item_cache_arguments,
                       verify_specification_format)

from .pkgfactory import create_build_item_factory
from .pkgitems import BuildItemTypeProvider, PackageBuildDirector
from .pkgworkspace import BuildspaceConfig, load_buildspace
from .util import command_arguments


def _get_arguments(argv: list[str]) -> argparse.Namespace:

    def _add_arguments(parser):
        parser.add_argument(
            "--force",
            type=str,
            action="append",
            default=None,
            help="building items with an UID matching this pattern is forced")
        parser.add_argument(
            "--package-uid",
            help="the package component UID (default: /pkg/component)",
            default="/pkg/component")
        parser.add_argument("--spec-verify",
                            action="store_true",
                            help="verify the specification")
        parser.add_argument("--use-git",
                            action="store_true",
                            help="use Git to track build steps")
        parser.add_argument("--package",
                            action="store_true",
                            help="build the whole package of a buildspace "
                            "which a previous export created; the spec "
                            "directory is the one of the buildspace")
        parser.add_argument("--only",
                            type=str,
                            action="append",
                            default=None,
                            help="build only these steps of the package")
        parser.add_argument("--skip",
                            type=str,
                            action="append",
                            default=None,
                            help="skip these steps of the package")
        parser.add_argument("--enabled-set",
                            help="the comma-separated names of the enabled "
                            "set of the package build",
                            default="")
        parser.add_argument("uids",
                            metavar="UID",
                            nargs="*",
                            help="the UID of an item to make")

    return get_item_cache_arguments(argv,
                                    description=climake.__doc__,
                                    add_arguments=(_add_arguments, ))


def _make_package(args: argparse.Namespace) -> None:
    if len(args.spec_directories) != 1 or args.uids:
        raise ValueError("a package build takes exactly the spec directory "
                         "of the buildspace and no UID")
    config = BuildspaceConfig(spec_directory=args.spec_directories[0],
                              cache_directory=args.cache_directory,
                              verify_specification_format=args.spec_verify)
    buildspace = load_buildspace(
        config, args.package_uid,
        [name.strip() for name in args.enabled_set.split(",") if name.strip()])
    director = buildspace.director
    if args.use_git:
        director.git_directory = director.package["deployment-directory"]
    director.build_package(args.only, args.force, args.skip)


def climake(argv: list[str] | None = None) -> None:
    """ Make items of a package. """

    args = _get_arguments(command_arguments(argv))
    if args.package:
        _make_package(args)
        return
    cache_config = ItemCacheConfig(paths=args.spec_directories,
                                   cache_directory=args.cache_directory)
    type_provider = BuildItemTypeProvider({})
    uid = args.package_uid
    logging.info("%s: load item cache", uid)
    item_cache = ItemCache(cache_config, type_provider=type_provider)
    logging.info("%s: loading done", uid)
    if args.spec_verify:
        logger = logging.getLogger()
        level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)
        status = verify_specification_format(item_cache)
        logger.setLevel(level)
        if status.critical or status.error:
            return
    factory = create_build_item_factory()
    director = PackageBuildDirector(item_cache, uid, factory)
    if args.use_git:
        director.git_directory = director.package["deployment-directory"]
    director.build_only(args.uids, force_patterns=args.force)
