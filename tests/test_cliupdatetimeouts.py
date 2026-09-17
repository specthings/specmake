# SPDX-License-Identifier: BSD-2-Clause
""" Tests the command to update the test timeouts. """

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

import pytest
import yaml

from specmake.cliupdatetimeouts import cliupdatetimeouts

_TARGET = "/target/sim/target"

_ITEM = """SPDX-License-Identifier: CC-BY-SA-4.0 OR BSD-2-Clause
copyrights:
- Copyright (C) 2026 embedded brains GmbH & Co. KG
enabled-by: true
links: []
timeouts: {}
type: test-timeouts
"""


def _spec_directory(tmp_path, item=_ITEM):
    directory = tmp_path / "spec" / "target" / "sim"
    directory.mkdir(parents=True)
    (directory / "test-timeouts.yml").write_text(item, encoding="utf-8")
    return str(tmp_path / "spec")


_COMPLETE = {"line-begin-of-test": 0, "line-end-of-test": 1}


def _report(tmp_path,
            name,
            durations,
            start_time="2026-09-16T10:00:00+00:00",
            info=None):
    path = tmp_path / name
    path.write_text(json.dumps({
        "target":
        _TARGET,
        "timeout-key":
        "default",
        "reports": [{
            "executable": f"build/{executable}",
            "duration": duration,
            "start-time": start_time,
            "info": _COMPLETE if info is None else info
        } for executable, duration in durations.items()]
    }),
                    encoding="utf-8")
    return str(path)


def _item_path(tmp_path):
    return tmp_path / "spec" / "target" / "sim" / "test-timeouts.yml"


def _update(tmp_path, reports, *extra):
    argv = [
        "specupdatetimeouts", "--spec-directory",
        str(tmp_path / "spec"), "--cache-directory",
        str(tmp_path / "cache"), *extra, *reports
    ]
    cliupdatetimeouts(argv)
    return yaml.safe_load(_item_path(tmp_path).read_text(encoding="utf-8"))


def test_initialize_a_fresh_item(tmp_path):
    _spec_directory(tmp_path)
    report = _report(tmp_path, "one.json", {"a.exe": 1.5})
    data = _update(tmp_path, [report])

    # An item without a time of the last update takes the durations
    assert data["timeouts"] == {"default": {"a.exe": [1.5]}}
    assert data["time-of-last-update"] == "2026-09-16T10:00:00+00:00"


@pytest.mark.parametrize("value",
                         ["'1970-01-01T00:00:00+00:00'", "1970-01-01"])
def test_the_time_of_the_last_update_may_be_a_date(tmp_path, value):
    _spec_directory(tmp_path, _ITEM + f"time-of-last-update: {value}\n")
    report = _report(tmp_path, "one.json", {"a.exe": 1.5})
    data = _update(tmp_path, [report])

    # A quoted value is a string and an unquoted one is a date
    assert data["timeouts"] == {"default": {"a.exe": [1.5]}}


def test_every_duration_is_kept(tmp_path):
    _spec_directory(tmp_path)
    first = _report(tmp_path, "one.json", {"a.exe": 1.5})
    second = _report(tmp_path,
                     "two.json", {"a.exe": 1.0},
                     start_time="2026-09-16T11:00:00+00:00")
    data = _update(tmp_path, [first, second])

    assert data["timeouts"]["default"]["a.exe"] == [1.5, 1.0]


def test_the_lazy_mode_keeps_the_maximum(tmp_path):
    _spec_directory(tmp_path)
    first = _report(tmp_path, "one.json", {"a.exe": 1.5})
    second = _report(tmp_path,
                     "two.json", {"a.exe": 1.0},
                     start_time="2026-09-16T11:00:00+00:00")
    third = _report(tmp_path,
                    "three.json", {"a.exe": 2.0},
                    start_time="2026-09-16T12:00:00+00:00")
    data = _update(tmp_path, [first, second, third], "--lazy")

    assert data["timeouts"]["default"]["a.exe"] == [2.0]


def test_the_lazy_mode_saves_nothing_without_a_change(tmp_path):
    _spec_directory(tmp_path)
    first = _report(tmp_path, "one.json", {"a.exe": 1.5})
    _update(tmp_path, [first], "--lazy")
    before = _item_path(tmp_path).read_text(encoding="utf-8")
    second = _report(tmp_path,
                     "two.json", {"a.exe": 1.0},
                     start_time="2026-09-16T11:00:00+00:00")
    _update(tmp_path, [second], "--lazy")

    assert _item_path(tmp_path).read_text(encoding="utf-8") == before


def test_the_reset_drops_the_durations(tmp_path):
    _spec_directory(tmp_path)
    first = _report(tmp_path, "one.json", {"a.exe": 1.5, "b.exe": 2.5})
    _update(tmp_path, [first])
    second = _report(tmp_path,
                     "two.json", {"a.exe": 1.0},
                     start_time="2026-09-16T11:00:00+00:00")
    data = _update(tmp_path, [second], "--reset")

    assert data["timeouts"]["default"] == {"a.exe": [1.0]}


def test_an_item_without_the_timeouts_key(tmp_path):
    _spec_directory(tmp_path, _ITEM.replace("timeouts: {}\n", ""))
    report = _report(tmp_path, "one.json", {"a.exe": 1.5})
    data = _update(tmp_path, [report])

    assert data["timeouts"] == {"default": {"a.exe": [1.5]}}


def test_a_report_without_a_duration(tmp_path):
    _spec_directory(tmp_path)
    path = tmp_path / "one.json"
    path.write_text(json.dumps({
        "target": _TARGET,
        "timeout-key": "default",
        "reports": [{
            "executable": "build/a.exe"
        }]
    }),
                    encoding="utf-8")
    data = _update(tmp_path, [str(path)])

    assert data["timeouts"] == {"default": {}}


def test_an_out_of_date_report(tmp_path):
    _spec_directory(tmp_path,
                    _ITEM + "time-of-last-update: '2026-09-16T12:00:00+00:00'")
    report = _report(tmp_path, "one.json", {"a.exe": 1.5})
    data = _update(tmp_path, [report])

    assert data["timeouts"] == {"default": {}}


def test_a_report_without_a_target(tmp_path, capsys):
    _spec_directory(tmp_path)
    path = tmp_path / "one.json"
    path.write_text(json.dumps({"reports": []}), encoding="utf-8")
    _update(tmp_path, [str(path)])

    assert "report has no target attribute" in capsys.readouterr().err


def test_a_duration_above_the_warning_factor(tmp_path, capsys):
    _spec_directory(tmp_path)
    first = _report(tmp_path, "one.json", {"a.exe": 100.0})
    _update(tmp_path, [first])
    second = _report(tmp_path,
                     "two.json", {"a.exe": 140.0},
                     start_time="2026-09-16T11:00:00+00:00")
    data = _update(tmp_path, [second])

    # The duration is above 1.2 * 100 + 10 and below 1.9 * 100 + 10
    assert "is greater than 1.2 * 100.0 + 10.0" in capsys.readouterr().err
    assert data["timeouts"]["default"]["a.exe"] == [100.0, 140.0]


def test_a_duration_above_the_error_factor(tmp_path, capsys):
    _spec_directory(tmp_path)
    first = _report(tmp_path, "one.json", {"a.exe": 100.0}, info={})
    _update(tmp_path, [first])
    second = _report(tmp_path,
                     "two.json", {"a.exe": 300.0},
                     start_time="2026-09-16T11:00:00+00:00",
                     info={})
    data = _update(tmp_path, [second])

    # The duration is above 1.9 * 100 + 10 and no complete run backs it up
    assert "is greater than 1.9 * 100.0 + 10.0" in capsys.readouterr().err
    assert data["timeouts"]["default"]["a.exe"] == [100.0]


def test_a_complete_run_above_the_error_factor(tmp_path, capsys):
    _spec_directory(tmp_path)
    first = _report(tmp_path, "one.json", {"a.exe": 100.0})
    _update(tmp_path, [first])
    second = _report(tmp_path,
                     "two.json", {"a.exe": 300.0},
                     start_time="2026-09-16T11:00:00+00:00")
    data = _update(tmp_path, [second])

    # A run which reached its end line needs the time which it took
    err = capsys.readouterr().err
    assert "take the duration 300.0 of a complete run above 1.9 * 100.0 " \
        "+ 10.0" in err
    assert "is greater than 1.2 * 100.0 + 10.0" not in err
    assert data["timeouts"]["default"]["a.exe"] == [100.0, 300.0]


def test_the_dry_run_saves_nothing(tmp_path):
    _spec_directory(tmp_path)
    before = _item_path(tmp_path).read_text(encoding="utf-8")
    report = _report(tmp_path, "one.json", {"a.exe": 1.5})
    _update(tmp_path, [report], "--dry-run")

    assert _item_path(tmp_path).read_text(encoding="utf-8") == before


def test_the_time_of_the_last_update_may_be_a_datetime(tmp_path):
    _spec_directory(tmp_path,
                    _ITEM + "time-of-last-update: 2026-09-16 09:00:00+00:00\n")
    report = _report(tmp_path, "one.json", {"a.exe": 1.5})
    data = _update(tmp_path, [report])

    # YAML gives an unquoted timestamp with an offset as an aware datetime
    assert data["timeouts"] == {"default": {"a.exe": [1.5]}}


def test_a_report_without_a_start_time(tmp_path):
    _spec_directory(tmp_path)
    path = tmp_path / "one.json"
    path.write_text(json.dumps({
        "target":
        _TARGET,
        "timeout-key":
        "default",
        "reports": [{
            "executable": "build/a.exe",
            "duration": 1.5,
            "info": _COMPLETE
        }]
    }),
                    encoding="utf-8")
    data = _update(tmp_path, [str(path)])

    assert data["timeouts"] == {"default": {"a.exe": [1.5]}}


def test_a_report_with_a_start_time_without_an_offset(tmp_path):
    _spec_directory(tmp_path)
    report = _report(tmp_path,
                     "one.json", {"a.exe": 1.5},
                     start_time="2026-09-16T10:00:00")
    data = _update(tmp_path, [report])

    # A test log of an earlier release states the start time as a UTC time
    # without an offset
    assert data["timeouts"] == {"default": {"a.exe": [1.5]}}
    assert data["time-of-last-update"] == "2026-09-16T10:00:00+00:00"


def test_a_report_of_an_error(tmp_path):
    _spec_directory(tmp_path)
    path = tmp_path / "one.json"
    path.write_text(json.dumps({
        "target":
        _TARGET,
        "timeout-key":
        "default",
        "reports": [{
            "executable": "build/a.exe",
            "duration": 720.0,
            "error": "timeout",
            "start-time": "2026-09-16T10:00:00+00:00"
        }]
    }),
                    encoding="utf-8")
    data = _update(tmp_path, [str(path)])

    # The duration of a run which timed out is the timeout, not a measurement
    assert data["timeouts"] == {"default": {}}


def test_a_run_which_did_not_end(tmp_path, capsys):
    _spec_directory(tmp_path)
    report = _report(tmp_path,
                     "one.json", {"a.exe": 1.5},
                     info={"line-begin-of-test": 0})
    data = _update(tmp_path, [report])

    # The duration of a run which stopped tells where it stopped
    assert "skip the report of a run which did not end" in \
        capsys.readouterr().err
    assert data["timeouts"] == {"default": {}}


def test_a_run_which_did_not_end_keeps_the_durations(tmp_path):
    _spec_directory(tmp_path)
    first = _report(tmp_path, "one.json", {"a.exe": 1.5})
    _update(tmp_path, [first])
    second = _report(tmp_path,
                     "two.json", {"a.exe": 2.5},
                     start_time="2026-09-16T11:00:00+00:00",
                     info={"line-begin-of-test": 0})
    data = _update(tmp_path, [second])

    # A stored maximum makes no difference to a run which did not end
    assert data["timeouts"]["default"]["a.exe"] == [1.5]


def test_an_output_without_a_test_report(tmp_path, capsys):
    _spec_directory(tmp_path)
    report = _report(tmp_path, "one.json", {"a.exe": 1.5}, info={})
    data = _update(tmp_path, [report])

    assert "the output holds no test report" in capsys.readouterr().err
    assert data["timeouts"] == {"default": {"a.exe": [1.5]}}


def test_the_reset_takes_a_report_of_the_last_update(tmp_path):
    _spec_directory(tmp_path)
    report = _report(tmp_path, "one.json", {"a.exe": 1.5})
    _update(tmp_path, [report])
    data = _update(tmp_path, [report], "--reset")

    # The same report fills the item again, so the reset is repeatable
    assert data["timeouts"]["default"] == {"a.exe": [1.5]}
