# SPDX-License-Identifier: BSD-2-Clause
""" Builds a package manual. """

# Copyright (C) 2020, 2025 embedded brains GmbH & Co. KG
# Copyright (C) 2021 EDISOFT
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
import os
from typing import Iterator

from specitems import (COL_SPAN, Copyrights, Item, ItemGetValueContext,
                       make_label, Link, SphinxContent, SphinxMapper)
from specware import (BSD_2_CLAUSE_LICENSE, MIT_LICENSE, gather_api_items,
                      run_command)

from .archiver import Archiver
from .directorystate import DirectoryState, RepositoryState
from .docbuilder import DocumentBuilder
from .membench import generate, generate_variants_table, MembenchVariant
from .pkgitems import PackageBuildDirector, PackageComponent
from .packagechanges import PackageChanges
from .testaggregator import TestAggregator
from .testrunner import TestLog

_EnvToStats = dict[str, tuple[float, float, float]]
_ItemToEnvStats = dict[str, _EnvToStats]

_LICENSE_LISTING = {"BSD-2-Clause": BSD_2_CLAUSE_LICENSE, "MIT": MIT_LICENSE}


def _run_pkg_config(content: SphinxContent, cmd: list[str]) -> None:
    cmd = ["pkg-config"] + cmd
    content.add(f"$ {' '.join(cmd)}")
    stdout: list[str] = []
    status = run_command(cmd, stdout=stdout)
    assert status == 0
    content.append(stdout)


def _gather_runtime_performance_items(items: set[Item], item: Item) -> None:
    if item.type == "requirement/non-functional/performance-runtime":
        items.add(item)
    for child in item.children("requirement-refinement"):
        _gather_runtime_performance_items(items, child)


def _environment_order(name: str) -> int:
    if name == "HotCache":
        return 0
    if name == "FullCache":
        return 1
    if name == "DirtyCache":
        return 2
    return int(name[5:]) + 2


def _add_licenses(content: SphinxContent, deployment_directory: str,
                  member: DirectoryState,
                  license_listing: dict[str, Copyrights]) -> None:
    copyrights_by_license = member["copyrights-by-license"]
    files = copyrights_by_license.get("files", None)
    if files is not None:
        directory = os.path.relpath(member.directory, deployment_directory)
        with content.section(f"Directory - {directory}"):
            content.add(copyrights_by_license.get("description", None))
            for name in files:
                with content.section(f"File - {name}"):
                    content.add(f"""The license file
{content.path(os.path.join(directory, name))}
is applicable to this directory or parts of the directory:""")
                    content.add_blank_line()
                    file_path = os.path.join(member.directory, name)
                    with open(file_path, "r", encoding="utf-8") as src:
                        content.add_code_block(src.readlines(),
                                               line_numbers=False)
    for the_license in license_listing:
        license_listing[the_license].register(
            copyrights_by_license.get(the_license, []))


def _get_performance_environments(
        measurements_by_variant: dict[int, _ItemToEnvStats]) -> list[str]:
    # We cannot use the performance runtime measurement environments specified
    # by items, since we have a target defined number of the Load/N
    # environments.
    #
    # Iterate over all gathered performance statistics since some providers may
    # have no results.  Try the best to produce a report even with insufficient
    # data.
    all_envs: set[str] = set()
    for item_to_env_stats in measurements_by_variant.values():
        for env_to_stats in item_to_env_stats.values():
            all_envs.update(env_to_stats.keys())
    return sorted(all_envs, key=_environment_order)


def _gather_targets(component: PackageComponent, targets: set[str]) -> None:
    with component.item.cache.selection(component.selection):
        targets.update(item.uid
                       for item in component.item.parents("design-target"))
    for child in component.item.children("input"):
        if child.type.startswith("pkg/component"):
            _gather_targets(component.director[child.uid], targets)


class PackageManualBuilder(DocumentBuilder):
    """ Builds a package user manual. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self._membench: dict[str, dict] = {}
        my_type = self.item.type
        self.mapper.add_get_value(f"{my_type}:/benchmark-variants-list",
                                  self._get_benchmark_variants_list)
        self.mapper.add_get_value(f"{my_type}:/memory-benchmarks",
                                  self._get_membench)
        self.mapper.add_get_value(f"{my_type}:/memory-benchmark-section",
                                  self._get_membench_section)
        self.mapper.add_get_value(f"{my_type}:/memory-benchmark-reference",
                                  self._get_membench_ref)
        self.mapper.add_get_value(
            f"{my_type}:/memory-benchmark-based-on-reference",
            self._get_membench_based_on_ref)
        self.mapper.add_get_value(
            f"{my_type}:/memory-benchmark-compare-section",
            self._get_membench_compare_section)
        self.mapper.add_get_value(
            f"{my_type}:/memory-benchmark-variants-table",
            self._get_membench_variants_table)
        self.mapper.add_get_value(f"{my_type}:/performance-variants-table",
                                  self._get_performance_variants_table)
        self.mapper.add_get_value(f"{my_type}:/pkg-config",
                                  self._get_pkg_config)
        self.mapper.add_get_value(f"{my_type}:/pre-qualified-interfaces",
                                  self._get_pre_qualified_interfaces)
        self.mapper.add_get_value(f"{my_type}:/repositories", self._get_repos)
        self.mapper.add_get_value(f"{my_type}:/change-list",
                                  self._get_change_list)
        self.mapper.add_get_value(f"{my_type}:/open-issues",
                                  self._get_open_issues)
        self.mapper.add_get_value(f"{my_type}:/license-info",
                                  self._get_license_info)
        self.mapper.add_get_value(f"{my_type}:/targets", self._get_targets)
        for name in [my_type, "pkg/sphinx-section"]:
            self.mapper.add_get_value(f"{name}:/object-size",
                                      self._get_object_size)

    def run(self) -> None:
        for membench in self.inputs("membench-results"):
            assert isinstance(membench, DirectoryState)
            self._membench.update(membench.json_load())
        super().run()

    def _get_benchmark_variants_list(self, ctx: ItemGetValueContext) -> str:
        with self.section_level_scope(ctx):
            content = SphinxContent(section_level=self.section_level)
            for link, test_log in self._yield_benchmark_variants():
                content.add_definition_item(
                    test_log.substitute(link["variant-name"]),
                    test_log.substitute(link["description"]))
            return content.join()

    def _get_membench_build_label(self) -> str:
        return self.substitute("${.:/component/membench-build-label}")

    def _get_membench(self, ctx: ItemGetValueContext) -> str:
        with self.section_level_scope(ctx):
            content = SphinxContent(section_level=self.section_level)
            content.push_label(
                make_label(self.substitute("${.:/component/ident}")))
            label = self._get_membench_build_label()
            sections_by_uid = self._membench[label]["membench"]
            root = self.item.cache["/rtems/req/mem-basic"]
            table_pivots = ["/rtems/req/mem-smp-1"]
            generate(content, sections_by_uid, root, table_pivots,
                     SphinxMapper(root))
            return content.join()

    def _get_membench_section(self, ctx: ItemGetValueContext) -> str:
        assert ctx.args
        uid, section = ctx.args.split(":")
        item = self.item.cache[uid]
        label = self._get_membench_build_label()
        sections = self._membench[label]["membench"][item.uid]
        return str(sections[section])

    def _membench_get_ref(self, ctx: ItemGetValueContext, section: str) -> str:
        assert ctx.args
        item = self.item.cache[ctx.args]
        scope = make_label(self.substitute("${.:/component/ident}"))
        label = f"{scope}{section}{item.ident}"
        return f":ref:`{item.spec_2} <{label}>`"

    def _get_membench_ref(self, ctx: ItemGetValueContext) -> str:
        return self._membench_get_ref(ctx, "BenchmarkSpec")

    def _get_membench_based_on_ref(self, ctx: ItemGetValueContext) -> str:
        return self._membench_get_ref(ctx, "BenchmarksBasedOnSpec")

    def _get_membench_compare_section(self, ctx: ItemGetValueContext) -> str:
        assert ctx.args
        uid, other_uid, section = ctx.args.split(":")
        item = self.item.cache[uid]
        label = self._get_membench_build_label()
        sections = self._membench[label]["membench"][item.uid]
        other_item = self.item.cache[other_uid]
        other_sections = self._membench[label]["membench"][other_item.uid]
        return f"{other_sections[section] - sections[section]:+}"

    def _yield_benchmark_variants(self) -> Iterator[tuple[Link, TestLog]]:
        for link, test_log in sorted(self.input_links("benchmark-variant"),
                                     key=lambda x: x[0]["priority"]):
            logging.info("%s: use benchmark variant of: %s", self.uid,
                         test_log.uid)
            assert isinstance(test_log, TestLog)
            yield link, test_log

    def _get_membench_variants_table(self, ctx: ItemGetValueContext) -> str:
        with self.section_level_scope(ctx):
            content = SphinxContent(section_level=self.section_level)
            root = self.item.cache["/rtems/req/mem-basic"]
            variants: list[MembenchVariant] = []
            for link, test_log in self._yield_benchmark_variants():
                build_label = test_log.input(
                    "build-configuration")["build-label"]
                if build_label not in self._membench:
                    logging.warning(
                        "%s: no memory benchmark for build label: %s",
                        self.uid, build_label)
                    continue
                variants.append(
                    MembenchVariant(test_log.substitute(link["variant-name"]),
                                    build_label))
            generate_variants_table(content, self._membench, root, variants)
            return content.join()

    def _get_measurements_by_variant(self) -> dict[int, _ItemToEnvStats]:
        measurements_by_variant: dict[int, _ItemToEnvStats] = {}
        for index, (_,
                    test_log) in enumerate(self._yield_benchmark_variants()):
            with open(test_log.file, "r", encoding="utf-8") as src:
                data = json.load(src)
            measurements: _ItemToEnvStats = {}
            for report in data["reports"]:
                for test_case in report.get("test-suite",
                                            {}).get("test-cases", []):
                    for measurement in test_case["runtime-measurements"]:
                        stats = (measurement["min"], measurement["q2"],
                                 measurement["max"])
                        measurements.setdefault(
                            measurement["name"],
                            {})[measurement["variant"]] = stats
            measurements_by_variant[index] = measurements
        return measurements_by_variant

    def _make_performance_variants_rows(
        self, item: Item, envs: list[str], env_links: dict[str, str],
        measurements_by_variant: dict[int, _ItemToEnvStats]
    ) -> list[tuple[str | int, ...]]:
        # pylint: disable=too-many-locals
        rows: list[tuple[str | int, ...]] = []
        info_spec: str | int = self.mapper.get_link(item)
        for env in envs:
            env_link = env_links[env.split("/")[0]]
            info_env: str | int = f"`{env} <{env_link}>`__"
            for index, (link, test_log) in enumerate(
                    self._yield_benchmark_variants()):
                stats = measurements_by_variant[index].get(item.ident,
                                                           {}).get(env, None)
                info = (info_spec, info_env,
                        test_log.substitute(link["variant-name"]))
                if index == 0:
                    if not stats:
                        rows.append(info + ("?", "?", "?"))
                        continue
                    base = stats
                    rows.append(info + tuple(f"{value * 1e6:.3f}"
                                             for value in stats))
                elif stats:
                    rows.append(info + tuple(
                        f"{(value - base[j]) / base[j] * 100.0:+.3g} %"
                        for j, value in enumerate(stats)))
                else:
                    rows.append(info + ("?", "?", "?"))
                info_spec = COL_SPAN
                info_env = COL_SPAN
        return rows

    def _get_performance_variants_table(self, ctx: ItemGetValueContext) -> str:
        with self.section_level_scope(ctx):
            measurements_by_variant = self._get_measurements_by_variant()
            if not measurements_by_variant:
                return "There is no performance variants table available."
            items: set[Item] = set()
            _gather_runtime_performance_items(items,
                                              self.item.cache["/req/root"])
            _, test_log = next(self._yield_benchmark_variants())
            envs = _get_performance_environments(measurements_by_variant)
            req_path = test_log.substitute(
                "${.:/component/deployment-directory}/doc/ts/srs/"
                "html/requirements.html#spec-req-perf-runtime-environment-")
            env_links = {
                "HotCache": f"{req_path}hot-cache",
                "FullCache": f"{req_path}full-cache",
                "DirtyCache": f"{req_path}dirty-cache",
                "Load": f"{req_path}load"
            }
            rows: list[tuple[str | int, ...]] = [
                ("Specification", "Environment", "Variant", "Min [μs]",
                 "Median [μs]", "Max [μs]")
            ]
            for item in sorted(items):
                rows.extend(
                    self._make_performance_variants_rows(
                        item, envs, env_links, measurements_by_variant))
            content = SphinxContent(section_level=self.section_level)
            content.add_grid_table(rows, [31, 14, 19, 12, 12, 12],
                                   font_size=-3)
            return content.join()

    def _get_pkg_config(self, _ctx: ItemGetValueContext) -> str:
        pkg = self.substitute(
            "${.:/component/deployment-directory}/lib/pkgconfig/"
            "${.:/component/arch}-rtems${.:/component/rtems-version}-"
            "${.:/component/bsp}${.:/component/config:dash}"
            "${.:/component/bsp-qual-only:dash}.pc")
        content = SphinxContent()
        with content.directive("code-block", value="none"):
            _run_pkg_config(content, ["--variable=ABI_FLAGS", pkg])
            _run_pkg_config(content, ["--cflags", pkg])
            _run_pkg_config(content, ["--variable=LDFLAGS", pkg])
        return content.join()

    def _get_pre_qualified_interfaces(self, ctx: ItemGetValueContext) -> str:
        with self.section_level_scope(ctx):
            content = SphinxContent(section_level=self.section_level)
            content.push_label(
                make_label(self.substitute("${.:/component/ident}")))
            items: dict[str, list[Item]] = {}
            gather_api_items(self.item.cache, items)
            for group, group_items in sorted(items.items()):
                with content.section(group):
                    content.add_list(
                        self.mapper.get_link(item) for item in group_items)
            return content.join()

    def _get_repos(self, ctx: ItemGetValueContext) -> str:
        with self.section_level_scope(ctx):
            content = SphinxContent(section_level=self.section_level)
            prefix = self.substitute("${.:/component/deployment-directory}")
            for item in self.component.item.children("repository"):
                repo = self.director[item.uid]
                assert isinstance(repo, RepositoryState)
                assert repo.lazy_verify()
                origin_branch = repo["origin-branch"]
                origin_commit = repo["origin-commit"]
                if origin_branch and origin_commit:
                    dest = os.path.relpath(repo["directory"], prefix)
                    with content.section(f"Git Repository: {dest}"):
                        content.add(repo["description"])
                        content.add(f"""The ``{repo["branch"]}`` branch with
commit ``{repo["commit"]}``
was used to build the package.  This branch is checked out after unpacking the
archive.  It is based on
commit `{origin_commit} <{repo['origin-commit-url']}>`_
of the ``{origin_branch}`` branch of the ``origin`` remote repository.""")
            return content.join()

    def _get_object_size(self, ctx: ItemGetValueContext) -> str:
        assert ctx.args
        label = self._get_membench_build_label()
        return str(self._membench[label]["object-sizes"][ctx.args])

    def _get_change_list(self, ctx: ItemGetValueContext) -> str:
        with self.section_level_scope(ctx):
            changes = self.input("package-changes")
            assert isinstance(changes, PackageChanges)
            return changes.get_change_list(self.section_level)

    def _get_open_issues(self, ctx: ItemGetValueContext) -> str:
        with self.section_level_scope(ctx):
            changes = self.input("package-changes")
            assert isinstance(changes, PackageChanges)
            return changes.get_open_issues(self.section_level)

    def _get_license_info(self, ctx: ItemGetValueContext) -> str:
        archiver = self.input("archive")
        assert isinstance(archiver, Archiver)
        with self.section_level_scope(ctx):
            content = SphinxContent(section_level=self.section_level)
            license_listing = {
                "BSD-2-Clause": Copyrights(),
                "MIT": Copyrights()
            }
            deployment_directory = self.substitute(
                "${.:/component/deployment-directory}")
            content.add(f"""All directories and file paths in this section are
relative to {content.path(deployment_directory)}.""")
            for member in archiver.inputs("member"):
                assert isinstance(member, DirectoryState)
                _add_licenses(content, deployment_directory, member,
                              license_listing)
            for the_license, copyrights in license_listing.items():
                if copyrights:
                    with content.section(f"{the_license} copyrights"):
                        content.add(copyrights.get_statements("| ©"))
                        content.add_code_block(
                            _LICENSE_LISTING[the_license].split("\n"),
                            line_numbers=False)
            return content.join()

    def _get_targets(self, ctx: ItemGetValueContext) -> str:
        with self.section_level_scope(ctx):
            content = SphinxContent(section_level=self.section_level)
            targets: set[str] = set()
            _gather_targets(self.component, targets)
            for uid in sorted(targets):
                target = self.item.cache[uid]
                with content.section(target["name"], label=self.label(target)):
                    content.add(self.substitute(target["brief"]))
                    content.add(self.substitute(target["description"]))
            return content.join()


class PackageSummary(DirectoryState):
    """ Builds a package summary. """

    def run(self) -> None:
        package_manual = self.input("source")
        content = SphinxContent(section_level=0)
        with content.section(f"Package Summary - {self.component['ident']}"):
            with content.section("Unexpected Test Failures"):
                for item in self.item.cache.items_by_type.get(
                        "pkg/directory-state/sphinx/test-report", []):
                    ident = self.substitute(
                        f"${{{item.uid}:/component/ident}}")
                    with content.section(f"Component - {ident}"):
                        for target, failures in item[
                                "unexpected-test-failures"].items():
                            content.add_list_item(target)
                            content.add_blank_line()
                            with content.indent("  "):
                                content.add_list(failures)
            with content.section("Code/Branch Coverage"):
                self._add_coverage_achievement(content)
            with content.section("Repositories"):
                prefix = package_manual.substitute(
                    "${.:/component/deployment-directory}")
                for item in package_manual.component.item.children(
                        "repository"):
                    repo = self.director[item.uid]
                    repo_dir = repo["directory"]
                    with content.section(os.path.relpath(repo_dir, prefix)):
                        stdout: list[str] = []
                        status = run_command(["git", "log", "-1"], repo_dir,
                                             stdout)
                        assert status == 0
                        content.add_code_block(stdout)
        content.write(self.file)
        self.description.add(f"""Produce the package summary file
{content.path(self.file)}.""")

    def _add_coverage_achievement(self, content: SphinxContent) -> None:
        for test_aggregator in self.inputs("test-aggregation"):
            assert isinstance(test_aggregator, TestAggregator)
            ident = test_aggregator.substitute("${.:/component/ident}")
            with content.section(f"Component - {ident}"):
                test_aggregator.add_coverage_achievement(content)
