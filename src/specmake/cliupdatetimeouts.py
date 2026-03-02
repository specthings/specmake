# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a command line interface to update the test timeouts using the
specified test reports.
"""

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

import argparse
import contextlib
import json
import logging
from pathlib import Path
import sys

from specitems import (ItemCache, ItemCacheConfig, create_argument_parser,
                       create_config, init_logging, item_is_enabled)
from specware import load_specware_config, SpecWareTypeProvider


def _update_timeouts(args: argparse.Namespace, report_path: str,
                     timeouts: dict[str, list[int]], reports: list) -> None:
    error_factor = args.error_factor
    warning_factor = args.warning_factor
    minimum_timeout = args.minimum_timeout
    for report in reports:
        name = Path(report["executable"]).name
        new_duration = report.get("execution-duration-in-seconds",
                                  report["duration"])
        if new_duration == 0.0:
            continue
        durations = timeouts.setdefault(name, [])
        try:
            maximum = max(durations)
        except ValueError:
            pass
        else:
            if new_duration > error_factor * maximum + minimum_timeout:
                logging.error(
                    "%s: %s: duration %s is greater than %s * %s + %s",
                    report_path, name, new_duration, error_factor, maximum,
                    minimum_timeout)
                continue
            if new_duration > warning_factor * maximum + minimum_timeout:
                logging.warning(
                    "%s: %s: duration %s is greater than %s * %s + %s",
                    report_path, name, new_duration, warning_factor, maximum,
                    minimum_timeout)
        durations.append(new_duration)


def cliupdatetimeouts(argv: list[str] = sys.argv) -> None:
    """ Update the test timeouts using the specified test reports. """
    parser = create_argument_parser()
    parser.add_argument("--config-file",
                        type=str,
                        default=None,
                        help="use this configuration file")
    parser.add_argument('--dry-run',
                        action="store_true",
                        default=False,
                        help="do not save timeout items")
    parser.add_argument('--reset',
                        action="store_true",
                        help="reset the timeouts")
    parser.add_argument('--test-timeouts',
                        type=str,
                        default="test-timeouts",
                        help="the test timeouts item UID basename")
    parser.add_argument('--minimum-timeout',
                        type=float,
                        default=10.0,
                        help="the minimum timeout used by the test runner")
    parser.add_argument(
        '--warning-factor',
        type=float,
        default=1.2,
        help="a new duration greater than the factor times "
        "the current maximum duration plus the minimum timeout is a warning")
    parser.add_argument(
        '--error-factor',
        type=float,
        default=1.9,
        help="a new duration greater than the factor times "
        "the current maximum duration plus the minimum timeout is an error")
    parser.add_argument("reports",
                        metavar="REPORTS",
                        nargs="+",
                        help="the test report files")
    args = parser.parse_args(argv[1:])
    init_logging(args)
    config, working_directory = load_specware_config(args.config_file)
    with contextlib.chdir(working_directory):
        item_cache = ItemCache(create_config(config["spec"], ItemCacheConfig),
                               type_provider=SpecWareTypeProvider({}),
                               is_item_enabled=item_is_enabled)
        reset_done: set[str] = set()
        for report_path in args.reports:
            logging.info("%s: evaluate reports", report_path)
            with open(report_path, "r", encoding="utf-8") as src:
                data = json.load(src)
            try:
                target = data['target']
            except KeyError:
                continue
            timeout_key = data["timeout-key"]
            item = item_cache[f"{target}/{args.test_timeouts}"]
            reset_key = f"{item.uid} {timeout_key}"
            if args.reset and reset_key not in reset_done:
                reset_done.add(reset_key)
                timeouts = {}
            else:
                timeouts = item["timeouts"].get(timeout_key, {})
            item["timeouts"][timeout_key] = timeouts
            _update_timeouts(args, report_path, timeouts, data["reports"])
            if not args.dry_run:
                item.save()
