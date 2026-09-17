# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a command line interface to update the test timeouts using the
specified test reports.
"""

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

import argparse
import dataclasses
import datetime
import json
import logging
from pathlib import Path

from specitems import (Item, ItemCache, ItemCacheConfig,
                       get_item_cache_arguments)

from .util import command_arguments

_EPOCH = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


@dataclasses.dataclass
class _LastUpdate:
    old: datetime.datetime
    new: datetime.datetime


@dataclasses.dataclass
class _State:
    """ Hold the items and the update state of a command run. """
    item_cache: ItemCache
    reset_done: set[str] = dataclasses.field(default_factory=set)
    last_updates: dict[str,
                       _LastUpdate] = dataclasses.field(default_factory=dict)
    items: dict[str, Item] = dataclasses.field(default_factory=dict)
    changed: set[str] = dataclasses.field(default_factory=set)


def _as_utc(value: datetime.datetime) -> datetime.datetime:
    """
    Get a time as an aware time.

    A time without a time zone offset counts as UTC.  Two times compare
    only if both of them carry an offset.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=datetime.timezone.utc)
    return value


def _time_of_last_update(item: Item) -> datetime.datetime:
    """
    Get the time of the last update of a test timeouts item.

    An item which never ran an update has no such time.  A YAML file states
    an unquoted timestamp as a datetime and a quoted one as a string.
    """
    value = item.get("time-of-last-update", None)
    if value is None:
        return _EPOCH
    if isinstance(value, str):
        value = datetime.datetime.fromisoformat(value)
    elif not isinstance(value, datetime.datetime):
        value = datetime.datetime(value.year, value.month, value.day)
    return _as_utc(value)


def _get_measurement(report: dict, report_path: str, name: str,
                     last_update: _LastUpdate) -> tuple[float, bool] | None:
    """
    Get the duration which a test report adds to the timeouts and tell if
    the run reached its end.

    A report without a duration and a report of a run which is older than the
    last update of the item add nothing.  A run which timed out, which raised
    an exception or which a discard pattern rejected measures nothing either.
    A run which stopped before the end of test line measures the point of the
    stop, so it adds nothing.  An output without a begin of test line holds
    no test report.  Its duration lands, and the run counts as incomplete.
    """
    error = report.get("error", "")
    if error:
        logging.debug("%s: %s: skip the report of an error: %s", report_path,
                      name, error)
        return None
    duration = report.get("execution-duration-in-seconds",
                          report.get("duration"))
    if not duration:
        logging.debug("%s: %s: has no execution duration", report_path, name)
        return None
    info = report.get("info", {})
    if "line-begin-of-test" in info:
        if "line-end-of-test" not in info:
            logging.warning(
                "%s: %s: skip the report of a run which did "
                "not end", report_path, name)
            return None
        complete = True
    else:
        logging.warning("%s: %s: the output holds no test report", report_path,
                        name)
        complete = False
    update_time: str | None = report.get("start-time")
    if update_time is not None:
        update_datetime = _as_utc(datetime.datetime.fromisoformat(update_time))
        if update_datetime <= last_update.old:
            logging.debug("%s: %s: skip out of date result", report_path, name)
            return None
        last_update.new = max(last_update.new, update_datetime)
    return duration, complete


def _check_range(args: argparse.Namespace, report_path: str, name: str,
                 measurement: tuple[float, bool], maximum: float) -> bool:
    """
    Tell if a duration is in range and log why it is not.

    The error factor bounds a duration which no complete run backs up.  A
    run which reached its end line measures the time which the test needs,
    so no bound rejects it.
    """
    duration, complete = measurement
    minimum_timeout = args.minimum_timeout
    if duration > args.error_factor * maximum + minimum_timeout:
        if not complete:
            logging.error("%s: %s: duration %s is greater than %s * %s + %s",
                          report_path, name, duration, args.error_factor,
                          maximum, minimum_timeout)
            return False
        logging.warning(
            "%s: %s: take the duration %s of a complete run above %s * %s "
            "+ %s", report_path, name, duration, args.error_factor, maximum,
            minimum_timeout)
    elif duration > args.warning_factor * maximum + minimum_timeout:
        logging.warning("%s: %s: duration %s is greater than %s * %s + %s",
                        report_path, name, duration, args.warning_factor,
                        maximum, minimum_timeout)
    return True


def _update_timeouts(args: argparse.Namespace, report_path: str,
                     last_update: _LastUpdate,
                     timeouts: dict[str, list[float]], reports: list) -> bool:
    """ Add the durations of the reports and tell if one of them lands. """
    changed = False
    for report in reports:
        name = Path(report["executable"]).name
        measurement = _get_measurement(report, report_path, name, last_update)
        if measurement is None:
            continue
        new_duration, _ = measurement
        durations = timeouts.setdefault(name, [])
        maximum = max(durations, default=None)
        if maximum is not None:
            if not _check_range(args, report_path, name, measurement, maximum):
                continue
            if args.lazy and new_duration <= maximum:
                logging.debug("%s: %s: keep the maximum duration: %s",
                              report_path, name, maximum)
                continue
        if args.lazy:
            durations.clear()
        logging.debug("%s: %s: add duration: %s", report_path, name,
                      new_duration)
        durations.append(new_duration)
        changed = True
    return changed


def _prepare_timeouts(
        item: Item, report_path: str, data: dict, reset: bool,
        reset_done: set[str]) -> tuple[dict[str, list[float]], bool]:
    """ Get the timeouts of the key of the report and tell if they reset. """
    timeout_key = data["timeout-key"]
    logging.info("%s: timeout key: %s", report_path, timeout_key)
    timeouts_of_keys = item.get("timeouts", None)
    if timeouts_of_keys is None:
        timeouts_of_keys = {}
        item["timeouts"] = timeouts_of_keys
    reset_key = f"{item.uid} {timeout_key}"
    do_reset = reset and reset_key not in reset_done
    if do_reset:
        reset_done.add(reset_key)
        timeouts: dict[str, list[float]] = {}
    else:
        timeouts = timeouts_of_keys.get(timeout_key, {})
    timeouts_of_keys[timeout_key] = timeouts
    return timeouts, do_reset


def _evaluate_report(args: argparse.Namespace, state: _State,
                     report_path: str) -> None:
    """ Add the durations of one test report to the test timeouts item. """
    logging.info("%s: evaluate reports", report_path)
    with open(report_path, "r", encoding="utf-8") as src:
        data = json.load(src)
    try:
        target = data["target"]
    except KeyError:
        logging.warning("%s: report has no target attribute", report_path)
        return
    uid = f"{target.removesuffix('/target')}/{args.test_timeouts}"
    logging.info("%s: test timeouts item UID: %s", report_path, uid)
    item = state.item_cache[uid]
    state.items[uid] = item
    time_of_last_update = _time_of_last_update(item)
    last_update = state.last_updates.setdefault(
        uid, _LastUpdate(time_of_last_update, time_of_last_update))
    timeouts, do_reset = _prepare_timeouts(item, report_path, data, args.reset,
                                           state.reset_done)
    if do_reset:
        # The reset drops every measurement, so the time of the last update
        # holds nothing back.
        last_update.old = _EPOCH
    if _update_timeouts(args, report_path, last_update, timeouts,
                        data["reports"]) or do_reset:
        state.changed.add(uid)


def _save_items(args: argparse.Namespace, state: _State) -> None:
    """ Save the items which the reports changed. """
    for uid, item in state.items.items():
        if args.lazy and uid not in state.changed:
            logging.info("%s: no timeout changed", uid)
            continue
        item["time-of-last-update"] = state.last_updates[uid].new.isoformat()
        item.save()


def _get_arguments(argv: list[str]) -> argparse.Namespace:

    def _add_arguments(parser):
        parser.add_argument('--dry-run',
                            action="store_true",
                            default=False,
                            help="do not save timeout items")
        parser.add_argument('--reset',
                            action="store_true",
                            help="reset the timeouts")
        parser.add_argument('--lazy',
                            action="store_true",
                            help="keep one duration per test, the maximum, "
                            "and save an item only if a duration changes")
        parser.add_argument(
            '--test-timeouts',
            type=str,
            default="test-timeouts",
            help="the test timeouts item UID basename (default: test-timeouts)"
        )
        parser.add_argument(
            '--minimum-timeout',
            type=float,
            default=10.0,
            help="the minimum timeout used by the test runner (default: 10.0)")
        parser.add_argument(
            '--warning-factor',
            type=float,
            default=1.2,
            help="a new duration greater than the factor times the current "
            "maximum duration plus the minimum timeout "
            "is a warning (default: 1.2)")
        parser.add_argument(
            '--error-factor',
            type=float,
            default=1.9,
            help="a new duration greater than the factor times the current "
            "maximum duration plus the minimum timeout is an error, unless "
            "the output of the test holds a begin and an end of test line "
            "(default: 1.9)")
        parser.add_argument("reports",
                            metavar="REPORT",
                            nargs="+",
                            help="a test report JSON file")

    return get_item_cache_arguments(argv,
                                    description=cliupdatetimeouts.__doc__,
                                    add_arguments=(_add_arguments, ))


def cliupdatetimeouts(argv: list[str] | None = None) -> None:
    """
    Update the test timeouts using the specified test reports.

    The target UID and the timeout key are obtained from the test report.
    """
    args = _get_arguments(command_arguments(argv))
    cache_config = ItemCacheConfig(paths=args.spec_directories,
                                   cache_directory=args.cache_directory,
                                   initialize_links=False,
                                   resolve_proxies=False)
    state = _State(ItemCache(cache_config))
    for report_path in args.reports:
        _evaluate_report(args, state, report_path)
    if not args.dry_run:
        _save_items(args, state)
