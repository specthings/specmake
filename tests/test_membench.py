# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the membench module. """

# Copyright (C) 2021 embedded brains GmbH & Co. KG
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

import logging

from specitems import ItemCache, ItemMapper, SphinxContent

from specmake import (MembenchVariant, gather_object_sizes, gather_sections,
                      generate, generate_tables, generate_variants_table)

from .util import create_item_cache


def run_command(args, cwd=None, stdout=None):
    if args[0] == "object-sizes":
        if "Thread" in args[2]:
            stdout.append("$1 = 42")
            return 0
        return 1
    if args[0] == "gdb" and "t3" in args[-1]:
        stdout.append("$1 = 133")
        return 0
    if "t2" in args[-1]:
        return 1
    if "t1" in args[-1] and "path-2" in args[-1]:
        return 1
    stdout.extend([
        "  0 .start        00000708  00100000  00100000  00010000  2**2",
        "                  CONTENTS, ALLOC, LOAD, READONLY, CODE",
        "  2 .text         000090bc  00100740  00100740  00010740  2**6",
        "                  CONTENTS, ALLOC, LOAD, READONLY, CODE",
        " 22 .debug_aranges 000011d8  00000000  00000000  000202e8  2**3"
    ])
    if "t1" in args[-1]:
        stdout.extend([
            "  3 .noinit       00001900  400809e0  400809e0  000909e0  2**3",
            "                  ALLOC"
        ])
    return 0


_OBJDUMP_LINES = [
    "  0 .text         00000100  00100000  00100000  00010000  2**2",
    "                  CONTENTS, ALLOC, LOAD, READONLY, CODE",
    "  1 .sframe       00000010  00100100  00100100  00010100  2**3",
    "                  CONTENTS, ALLOC, LOAD, READONLY, DATA",
    "  2 .blue_debug   00000020  00000000  00000000  00010110  2**0",
    "                  CONTENTS, READONLY, DEBUGGING, OCTETS",
    "  3 .blue_tls     00000004  00100110  00100110  00010110  2**2",
    "                  CONTENTS, ALLOC, LOAD, DATA, THREAD_LOCAL",
    "  4 .blue_code    00000030  00100120  00100120  00010120  2**2",
    "                  CONTENTS, ALLOC, LOAD, READONLY, CODE",
    "  5 .blue_rodata  00000040  00100150  00100150  00010150  2**2",
    "                  CONTENTS, ALLOC, LOAD, READONLY, DATA",
    "  6 .blue_data    00000050  00200000  00200000  00020000  2**2",
    "                  CONTENTS, ALLOC, LOAD, DATA",
    "  7 .blue_bss     00000060  00200050  00200050  00020050  2**2",
    "                  ALLOC",
    "  8 .blue_empty   00000000  00200100  00200100  00020100  2**2",
    "                  CONTENTS, ALLOC, LOAD, DATA",
    "  9 .blue_no_flags 00000070  00200100  00200100  00020100  2**2",
]


def run_command_2(args, cwd=None, stdout=None):
    if args[0] == "gdb":
        return 1
    if "t0" in args[-1] or "t1" in args[-1]:
        stdout.extend(_OBJDUMP_LINES)
        return 0
    return 1


def test_membench_unknown_sections(caplog, tmpdir, monkeypatch):
    caplog.set_level(logging.WARNING)
    monkeypatch.setattr("specmake.membench.run_command", run_command_2)
    item_cache = create_item_cache(tmpdir, "spec-membench")
    sections_by_uid = gather_sections(item_cache, "path", "objdump", "gdb")
    sections = {
        ".text": 0x150,
        ".rodata": 0x90,
        ".data": 0x50,
        ".bss": 0x60,
        ".noinit": 0
    }
    assert sections_by_uid == {"/t0": sections, "/t1": sections}
    log = caplog.text
    assert log.count("unknown ELF section '.blue_code'") == 2
    assert ("unknown ELF section '.blue_debug' with flags 'CONTENTS, "
            "DEBUGGING, OCTETS, READONLY' accounted as 'no section'") in log
    assert ("unknown ELF section '.blue_tls' with flags 'ALLOC, CONTENTS, "
            "DATA, LOAD, THREAD_LOCAL' accounted as 'no section'") in log
    assert ("unknown ELF section '.blue_code' with flags 'ALLOC, CODE, "
            "CONTENTS, LOAD, READONLY' accounted as '.text'") in log
    assert ("unknown ELF section '.blue_bss' with flags 'ALLOC' accounted "
            "as '.bss'") in log
    assert ("unknown ELF section '.blue_rodata' with flags 'ALLOC, CONTENTS, "
            "DATA, LOAD, READONLY' accounted as '.rodata'") in log
    assert ("unknown ELF section '.blue_data' with flags 'ALLOC, CONTENTS, "
            "DATA, LOAD' accounted as '.data'") in log
    assert ("unknown ELF section '.blue_no_flags' with flags '' accounted "
            "as 'no section'") in log
    assert ".sframe" not in log
    assert ".blue_empty" not in log


def test_membench(tmpdir, monkeypatch):
    monkeypatch.setattr("specmake.membench.run_command", run_command)
    item_cache = create_item_cache(tmpdir, "spec-membench")
    object_sizes = gather_object_sizes(item_cache, "path", "object-sizes")
    assert len(object_sizes) == 2
    assert object_sizes["/rtems/task/obj"] == 42
    sections_by_uid = gather_sections(item_cache, "path", "objdump", "gdb")
    sections_by_uid_2 = gather_sections(item_cache, "path-2", "objdump", "gdb")
    root = item_cache["/r0"]
    content = SphinxContent()
    generate(content, sections_by_uid, root, ["r0", "r4"], ItemMapper(root))
    assert str(content) == """.. _BenchmarksBasedOnSpecT0:

Benchmarks based on: spec:/t0
#############################

The following static memory benchmarks are based on the
reference memory benchmark specified by
:ref:`spec:/​t0 <BenchmarkSpecT0>`.
The numbers of the first row represent the section sizes of the reference
memory benchmark program in bytes.  The numbers in the following rows indicate
the change in bytes of the section sizes with respect to the reference memory
benchmark program of the first row.  A ``+`` indicates a size increase and a
``-`` indicates a size decrease.  This hints how the static memory usage
changes when the feature set changes with respect to the reference memory
benchmark.

.. raw:: latex

    \\begin{scriptsize}

.. table::
    :class: longtable
    :widths: 50,10,10,10,10,10

    ============================ ===== ======= ===== ==== =======
    Specification                .text .rodata .data .bss .noinit
    ============================ ===== ======= ===== ==== =======
    :ref:`/t0 <BenchmarkSpecT0>` 38908 0       0     0    0
    :ref:`/t1 <BenchmarkSpecT1>` +0    +0      +0    +0   +6400
    :ref:`/t2 <BenchmarkSpecT2>` ?     ?       ?     ?    ?
    :ref:`/t3 <BenchmarkSpecT3>` +0    +0      +0    +0   +133
    ============================ ===== ======= ===== ==== =======

.. raw:: latex

    \\end{scriptsize}

.. _BenchmarksBasedOnSpecT0:

Benchmarks based on: spec:/t0
#############################

The following static memory benchmarks are based on the
reference memory benchmark specified by
:ref:`spec:/​t0 <BenchmarkSpecT0>`.
The numbers of the first row represent the section sizes of the reference
memory benchmark program in bytes.  The numbers in the following rows indicate
the change in bytes of the section sizes with respect to the reference memory
benchmark program of the first row.  A ``+`` indicates a size increase and a
``-`` indicates a size decrease.  This hints how the static memory usage
changes when the feature set changes with respect to the reference memory
benchmark.

.. raw:: latex

    \\begin{scriptsize}

.. table::
    :class: longtable
    :widths: 50,10,10,10,10,10

    ============================ ===== ======= ===== ==== =======
    Specification                .text .rodata .data .bss .noinit
    ============================ ===== ======= ===== ==== =======
    :ref:`/t0 <BenchmarkSpecT0>` 38908 0       0     0    0
    :ref:`/t1 <BenchmarkSpecT1>` +0    +0      +0    +0   +6400
    :ref:`/t2 <BenchmarkSpecT2>` ?     ?       ?     ?    ?
    :ref:`/t3 <BenchmarkSpecT3>` +0    +0      +0    +0   +133
    ============================ ===== ======= ===== ==== =======

.. raw:: latex

    \\end{scriptsize}

.. _BenchmarkSpecT0:

Benchmark: spec:/t0
###################

The Blue Green brief description.

The Blue Green description.

.. raw:: latex

    \\begin{scriptsize}

.. table::
    :class: longtable
    :widths: 20,20,20,20,20

    ===== ======= ===== ==== =======
    .text .rodata .data .bss .noinit
    ===== ======= ===== ==== =======
    38908 0       0     0    0
    ===== ======= ===== ==== =======

.. raw:: latex

    \\end{scriptsize}

.. _BenchmarkSpecT1:

Benchmark: spec:/t1
###################

The Blue Green brief description.

The Blue Green description.

.. raw:: latex

    \\begin{scriptsize}

.. table::
    :class: longtable
    :widths: 20,20,20,20,20

    ===== ======= ===== ==== =======
    .text .rodata .data .bss .noinit
    ===== ======= ===== ==== =======
    38908 0       0     0    6400
    ===== ======= ===== ==== =======

.. raw:: latex

    \\end{scriptsize}

.. _BenchmarkSpecT2:

Benchmark: spec:/t2
###################

The Blue Green brief description.

The Blue Green description.

.. topic:: WARNING

    There are no results available for this static memory usage benchmark.

.. _BenchmarkSpecT3:

Benchmark: spec:/t3
###################

The Blue Green brief description.

The Blue Green description.

.. raw:: latex

    \\begin{scriptsize}

.. table::
    :class: longtable
    :widths: 20,20,20,20,20

    ===== ======= ===== ==== =======
    .text .rodata .data .bss .noinit
    ===== ======= ===== ==== =======
    38908 0       0     0    133
    ===== ======= ===== ==== =======

.. raw:: latex

    \\end{scriptsize}
"""
    content = SphinxContent()
    generate_tables(content, sections_by_uid, root, ["r0", "r4"])
    assert str(content) == """.. _BenchmarksBasedOnSpecT0:

Benchmarks based on: spec:/t0
#############################

The following static memory benchmarks are based on the
reference memory benchmark specified by
:ref:`spec:/​t0 <BenchmarkSpecT0>`.
The numbers of the first row represent the section sizes of the reference
memory benchmark program in bytes.  The numbers in the following rows indicate
the change in bytes of the section sizes with respect to the reference memory
benchmark program of the first row.  A ``+`` indicates a size increase and a
``-`` indicates a size decrease.  This hints how the static memory usage
changes when the feature set changes with respect to the reference memory
benchmark.

.. raw:: latex

    \\begin{scriptsize}

.. table::
    :class: longtable
    :widths: 50,10,10,10,10,10

    ============================ ===== ======= ===== ==== =======
    Specification                .text .rodata .data .bss .noinit
    ============================ ===== ======= ===== ==== =======
    :ref:`/t0 <BenchmarkSpecT0>` 38908 0       0     0    0
    :ref:`/t1 <BenchmarkSpecT1>` +0    +0      +0    +0   +6400
    :ref:`/t2 <BenchmarkSpecT2>` ?     ?       ?     ?    ?
    :ref:`/t3 <BenchmarkSpecT3>` +0    +0      +0    +0   +133
    ============================ ===== ======= ===== ==== =======

.. raw:: latex

    \\end{scriptsize}

.. _BenchmarksBasedOnSpecT0:

Benchmarks based on: spec:/t0
#############################

The following static memory benchmarks are based on the
reference memory benchmark specified by
:ref:`spec:/​t0 <BenchmarkSpecT0>`.
The numbers of the first row represent the section sizes of the reference
memory benchmark program in bytes.  The numbers in the following rows indicate
the change in bytes of the section sizes with respect to the reference memory
benchmark program of the first row.  A ``+`` indicates a size increase and a
``-`` indicates a size decrease.  This hints how the static memory usage
changes when the feature set changes with respect to the reference memory
benchmark.

.. raw:: latex

    \\begin{scriptsize}

.. table::
    :class: longtable
    :widths: 50,10,10,10,10,10

    ============================ ===== ======= ===== ==== =======
    Specification                .text .rodata .data .bss .noinit
    ============================ ===== ======= ===== ==== =======
    :ref:`/t0 <BenchmarkSpecT0>` 38908 0       0     0    0
    :ref:`/t1 <BenchmarkSpecT1>` +0    +0      +0    +0   +6400
    :ref:`/t2 <BenchmarkSpecT2>` ?     ?       ?     ?    ?
    :ref:`/t3 <BenchmarkSpecT3>` +0    +0      +0    +0   +133
    ============================ ===== ======= ===== ==== =======

.. raw:: latex

    \\end{scriptsize}
"""
    content = SphinxContent()
    root_2 = item_cache["/r1"]
    generate_variants_table(
        content, {
            "bla": {
                "membench": sections_by_uid
            },
            "blb": {
                "membench": sections_by_uid_2
            }
        }, root_2, [MembenchVariant("a", "bla"),
                    MembenchVariant("b", "blb")])
    assert str(content) == """.. raw:: latex

    \\begin{scriptsize}

.. table::
    :class: longtable
    :widths: 35,20,9,9,9,9,9

    +------------------------------+---------+-------+---------+-------+------+---------+
    | Specification                | Variant | .text | .rodata | .data | .bss | .noinit |
    +==============================+=========+=======+=========+=======+======+=========+
    | :ref:`/t0 <BenchmarkSpecT0>` | a       | 38908 | 0       | 0     | 0    | 0       |
    +                              +---------+-------+---------+-------+------+---------+
    |                              | b       | +0    | +0      | +0    | +0   | +0      |
    +------------------------------+---------+-------+---------+-------+------+---------+
    | :ref:`/t1 <BenchmarkSpecT1>` | a       | 38908 | 0       | 0     | 0    | 6400    |
    +                              +---------+-------+---------+-------+------+---------+
    |                              | b       | ?     | ?       | ?     | ?    | ?       |
    +------------------------------+---------+-------+---------+-------+------+---------+

.. raw:: latex

    \\end{scriptsize}
"""
