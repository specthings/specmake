# SPDX-License-Identifier: BSD-2-Clause
""" Provides a command line interface to record the digests of inspections. """

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
import logging
import sys

from specitems import (ItemCache, ItemCacheConfig, get_item_cache_arguments,
                       save_data)

from .inspection import baseline, renew
from .util import command_arguments


def cliupdateinspections(argv: list[str] | None = None) -> None:
    """
    Record the digests of an inspection check report in an inspection item.

    The command works on the inspection items of the workspace.  The report
    is the output of an inspection check of a package build.
    """

    def _add_arguments(parser):
        parser.add_argument("--output",
                            help="write the new inspection round of --renew "
                            "to this file")
        parser.add_argument("--renew",
                            action="store_true",
                            help="write a new inspection round which "
                            "supersedes the inspection item, otherwise record "
                            "the digests of the scopes which have none")
        parser.add_argument("inspection_uid",
                            metavar="INSPECTION_UID",
                            help="the UID of an inspection item")
        parser.add_argument("report",
                            metavar="REPORT",
                            help="an inspection check report JSON file")

    args = get_item_cache_arguments(command_arguments(argv),
                                    description=cliupdateinspections.__doc__,
                                    add_arguments=(_add_arguments, ))
    if args.renew and args.output is None:
        sys.exit("--renew needs an --output file")
    cache_config = ItemCacheConfig(paths=args.spec_directories,
                                   cache_directory=args.cache_directory,
                                   initialize_links=False,
                                   resolve_proxies=False)
    item_cache = ItemCache(cache_config)
    uid = args.inspection_uid
    try:
        item = item_cache[uid]
    except KeyError:
        sys.exit(f"there is no item {uid}")
    with open(args.report, "r", encoding="utf-8") as src:
        report = json.load(src)
    try:
        if args.renew:
            save_data(args.output, renew(item.data, uid, report))
            logging.info("%s: wrote the new inspection round to %s", uid,
                         args.output)
            return
        count = baseline(item.data, uid, report)
    except ValueError as err:
        sys.exit(f"{uid}: {err}")
    if count:
        item.save()
    logging.info("%s: recorded %d digests in %s", uid, count, item.file)
