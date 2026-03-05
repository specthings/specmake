# SPDX-License-Identifier: BSD-2-Clause
""" Functions for Building RTEMS SPAMR document. """

# Copyright (C) 2020 EDISOFT
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

# pylint: disable=consider-using-f-string

import os
import ast
import glob
import logging
from typing import Any, List, Tuple

from specitems import Item, ItemCache, ItemGetValueContext, SphinxContent
from specware import run_command

from .directorystate import DirectoryState
from .docbuilder import DocumentBuilder
from .pkgitems import PackageBuildDirector
from .rtems import RTEMSItemCache


def _get_specs_by_type(item_cache: ItemCache, spec_type: str,
                       enabled_by: List) -> List[Item]:
    """
    Returns a list of all enabled specifications of a certain type
    which are present on the given item cache.
    """
    specs = []
    for spec in item_cache.values():
        if spec.type.startswith(spec_type) and spec.is_enabled(enabled_by):
            specs.append(spec)
    return specs


def _get_test_cases_by_type(item_cache: ItemCache, enabled_by: Any,
                            test_type: str) -> List[Item]:
    """ Returns only the test cases of a given type. """
    test_cases = []  # type: List[Item]
    for case in _get_specs_by_type(item_cache, "test-case", enabled_by):
        links = list(case.parents(test_type))
        if links:
            test_cases.append(case)
    return sorted(test_cases)


class SpamrManager(DocumentBuilder):
    """ Class which manages the SPAMR document build step """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self.mapper.add_get_value(f"{self.item.type}:/cppcheck-results",
                                  self._cppcheck_analysis)
        self.mapper.add_get_value(
            f"{self.item.type}:/" +
            "requirement-implementation-and-vv-coverage",
            self._requirement_implementation_and_vv_coverage)
        self.mapper.add_get_value(
            f"{self.item.type}:/requirements-completeness",
            self._requirements_completeness)
        self.mapper.add_get_value(
            f"{self.item.type}:/vv-coverage-unit-integration-level",
            self._vv_coverage_unit_integration)
        self.mapper.add_get_value(f"{self.item.type}:/requirement-testability",
                                  self._requirement_testability)
        self.mapper.add_get_value(f"{self.item.type}:/code-metrics",
                                  self._code_metrics)
        self.mapper.add_get_value(
            f"{self.item.type}:/user-documentation-completeness",
            self._user_documentation_completeness)
        self.mapper.add_get_value(f"{self.item.type}:/code-size",
                                  self._code_size)
        self.mapper.add_get_value(f"{self.item.type}:/sprs-and-ncrws",
                                  self._sprs_and_ncrws)
        self.mapper.add_get_value(f"{self.item.type}:/spr-ncr-status",
                                  self._spr_ncr_status)

    def _get_related_requirements(self) -> list[Item]:
        spec = self.input("spec")
        assert isinstance(spec, RTEMSItemCache)
        return spec.get_related_requirements()

    def _cppcheck_analysis(self, _ctx: ItemGetValueContext) -> Any:
        command: List[str] = []
        for argument in self.item["cppcheck-command"]:
            command.append(self.mapper.substitute(argument))
        stdout: List[str] = []
        run_command(command, stdout=stdout)
        content = SphinxContent()
        for line in stdout:
            if not (("Checking " in line) or (" files checked " in line)):
                with content.directive("code-block", value="bash"):
                    content.add(
                        line.replace(self.component["deployment-directory"],
                                     ""))
        return content.join()

    def _requirement_implementation_and_vv_coverage(
            self, _ctx: ItemGetValueContext) -> Any:
        reqs_with_val_metho = 0
        requirements = self._get_related_requirements()
        number_requirements = len(requirements)
        not_validated_requirements = []
        for req in requirements:
            if req.view["validated"]:
                reqs_with_val_metho += 1
            else:
                not_validated_requirements.append(req.uid)
        report = []
        report.append("Number of software requirements with " +
                      "an associated validation method: " +
                      str(reqs_with_val_metho) + "\n")
        report.append("Total Number of software requirements: " +
                      str(number_requirements) + "\n")
        req_imp_cov = reqs_with_val_metho / number_requirements
        report.append("Requirement implementation coverage: " +
                      "{:.2f}".format(req_imp_cov) + "\n")
        if req_imp_cov >= self.item["metrics-thresholds"][
                "requirement-implementation-coverage"]:
            report.append("This metric is OK")
        else:
            report.append("This metric is NOK\n")
            report.append("The following requirements are not validated:\n")
            for requirement_uid in sorted(not_validated_requirements):
                report.append(requirement_uid + "\n")

        content = SphinxContent()
        content.add(report)
        return content.join()

    def _requirement_testability(self, _ctx: ItemGetValueContext) -> Any:
        reqs_with_val_test = 0
        requirements = self._get_related_requirements()
        number_requirements = len(requirements)
        for item in requirements:
            if item.type in [
                    "requirement/functional/action",
                    "requirement/non-functional/performance-runtime",
                    "runtime-measurement-test"
            ]:
                reqs_with_val_test += 1
                continue
            try:
                item.child("validation")
                reqs_with_val_test += 1
            except IndexError:
                pass
        report = []
        report.append("Number of software requirements verified by test: " +
                      str(reqs_with_val_test) + "\n")
        report.append("Total Number of software requirements: " +
                      str(number_requirements) + "\n")
        req_testability = reqs_with_val_test / number_requirements
        report.append("Requirement testability: " +
                      "{:.2f}".format(req_testability) + "\n")
        if req_testability * 100 >= self.item["metrics-thresholds"][
                "requirement-testability"]:
            report.append("This metric is OK")
        else:
            report.append("This metric is NOK")

        content = SphinxContent()
        content.add(report)
        return content.join()

    def _get_tbd_requirements(self) -> List[Item]:
        tbd_reqs = []
        for req in self._get_related_requirements():
            tbd_check_command = ["egrep", "-wq", "TBD|TBC", req.file]
            if run_command(tbd_check_command, stdout=[]) == 0:
                tbd_reqs.append(req)
        return tbd_reqs

    def _requirements_completeness(self, _ctx: ItemGetValueContext) -> Any:
        content = SphinxContent()
        number_tbds = len(self._get_tbd_requirements())
        requirement_count = len(self._get_related_requirements())
        req_comp = number_tbds / requirement_count
        content.add("Number of software requirements with TBCs/TBDs: " +
                    str(number_tbds))
        content.add(
            f"Total Number of software requirements: {requirement_count}")
        content.add("Requirements completeness: " + "{:.2f}".format(req_comp) +
                    " %")
        if req_comp <= \
                self.item["metrics-thresholds"]["requirements-completeness"]:
            content.add("This metric is OK")
        else:
            content.add("This metric is NOK")
        return content.join()

    def _user_documentation_completeness(self,
                                         _ctx: ItemGetValueContext) -> Any:
        build = self.output("build")
        assert isinstance(build, DirectoryState)
        build_dir = build.directory

        content = SphinxContent()
        sections: List[str] = []
        command_section = ["grep", r"\*\*\*\*\*$", "filename"]
        tbd_docs: List[str] = []
        command_tbd = ["grep", "TB[CD]", "filename"]

        # Search through the ReST documentation files
        for directory_state in self.inputs("rst-files"):
            assert isinstance(directory_state, DirectoryState)
            files = sorted(
                glob.glob(os.path.join(directory_state.directory, "**/*.rst")))
            logging.debug("%s: inspect documentation files in '%s': %s",
                          self.uid, directory_state.directory, files)
            for rst_file in files:
                command_section[2] = rst_file
                command_tbd[2] = rst_file
                tbd_file_doc: List[str] = []
                run_command(command_section, stdout=sections)
                run_command(command_tbd, stdout=tbd_file_doc)
                tbd_docs.extend([
                    os.path.relpath(rst_file, build_dir) + ": " + line
                    for line in tbd_file_doc
                ])

        # Write number of sections in RTEMS documentation
        content.add("Total number of sections in the documentation:")
        content.add_blank_line()
        content.add_list_item("sphinx documentation in RTEMS repository: " +
                              str(len(sections)))

        # Get number of TBD/TBC in requirements and documentation
        content.add_blank_line()
        content.add("Total number of TBC/TBD in the documentation:")
        content.add_blank_line()
        tbd_reqs = self._get_tbd_requirements()
        content.add_list_item("yml documentation (requirements): " +
                              str(len(tbd_reqs)))
        content.add_list_item("sphinx documentation in RTEMS repository: " +
                              str(len(tbd_docs)))
        content.add_blank_line()

        # Calculate user documentation completeness
        completeness = (len(tbd_docs) + len(tbd_reqs)) / len(sections)
        content.add(("User Documentation Completeness: (%d + %d) / %d = " %
                     (len(tbd_reqs), len(tbd_docs), len(sections))) +
                    "{:.2f}".format(completeness))
        content.add_blank_line()

        # Get relevant TBC/TBD lines
        content.add("Relevant list of TBC/TBD:")
        content.add_blank_line()
        if len(tbd_docs) != 0:
            content.add_list(tbd_docs)
            content.add_list(["Requirement: " + req.uid for req in tbd_reqs])
        else:
            content.add("No TBD/TBC found.")

        # Verify if metric is OK
        if completeness <= (self.item["metrics-thresholds"]
                            ["user-documentation-completeness"]):
            content.add("This metric is OK")
        else:
            content.add("This metric is NOK")
        return content.join()

    # pylint: disable=too-many-locals
    # pylint: disable=too-many-nested-blocks
    def _code_metrics(self, _ctx: ItemGetValueContext) -> Any:
        all_metrics = ""
        directory = ""
        # Run the metrics
        command = []
        for argument in self.item["metrixplusplus-collect"]:
            command.append(self.mapper.substitute(argument))
        run_command(command)
        # Gather and process the metrics
        command = self["metrixplusplus-view"]
        directory = command[-1]
        incorrect_metrics_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".c") or file.endswith(".h"):
                    command[-1] = os.path.join(root, file)
                    stdout: List[str] = []
                    if run_command(command, stdout=stdout) == 0:
                        metrics, metrics_result, metrics_file = \
                            self._process_metrics(stdout, directory)
                        if len(metrics) != 1:
                            if not metrics_result:
                                incorrect_metrics_files.append(metrics_file)
                            content = SphinxContent()
                            with content.directive("code-block", value="text"):
                                content.add(metrics)
                            all_metrics = all_metrics + "\n\n" + content.join()

        wrong_files_content = SphinxContent()
        wrong_files_content.add("The following files contain errors in the " +
                                "the metrics. For more details see the " +
                                "above report of each file.\n\n")
        wrong_files_content.add_list(incorrect_metrics_files)

        return all_metrics + "\n\n" + wrong_files_content.join()

    def _process_metrics(self, metrics_output: List[str],
                         base_dir: str) -> Tuple[List[str], bool, str]:
        results_output = []
        for line in metrics_output:
            # Only one entry of the stdout will have the metrics dictionary
            if line.startswith("{"):
                while True:
                    if line.endswith("}"):
                        break
                    line = line[:-1]
                metrics_dict = ast.literal_eval(line)
        data = metrics_dict["view"][0]["data"]
        file_name = data["info"]["path"].replace(base_dir, "")
        results_output.append("File: " + file_name)
        metrics_ok = True
        code_size_file = int(
            data["aggregated-data"]["std.code.lines"]["code"]["total"] +
            data["aggregated-data"]["std.code.lines"]["preprocessor"]["total"])
        for region in data["file-data"]["regions"]:
            if region["info"]["type"] == "global":
                results_output[0] = results_output[0] + " " + str(
                    code_size_file)
                if code_size_file > self.item["metrics-thresholds"][
                        "lines-of-code"]:
                    overall_result = "NOK"
                    metrics_ok = False
                else:
                    overall_result = "OK"
                results_output[0] = results_output[0] + " " + overall_result
            if region["info"]["type"] == "function":
                cyclomatic = region["data"]["std.code.complexity"][
                    "cyclomatic"]
                nesting_level = region["data"]["std.code.complexity"][
                    "maxindent"]
                code_size = region["data"]["std.code.lines"]["code"] + region[
                    "data"]["std.code.lines"]["preprocessor"]
                comment_size = region["data"]["std.code.lines"]["comments"]
                comment_frequency = int(
                    (100 * comment_size) / (comment_size + code_size))
                if (cyclomatic > self.item[
                        "metrics-thresholds"]["cyclomatic-number"]) or \
                        (nesting_level > self.item[
                            "metrics-thresholds"]["nesting-level"]):
                    overall_result = "NOK"
                    metrics_ok = False
                else:
                    overall_result = "OK"
                results = "    " + region["info"]["name"] + " " + \
                          str(cyclomatic) + " " + str(nesting_level) + " " + \
                          str(code_size) + " " + str(comment_frequency) + \
                          "%" + " " + overall_result
                results_output.append(results)
        return results_output, metrics_ok, file_name

    def _code_size(self, _ctx: ItemGetValueContext) -> Any:
        # Action status
        sphinx_content = SphinxContent()
        actions = ["Actions issued", "Actions closed", "Actions open"]
        actions_count = [0, 0, 0]
        for issue in sorted(self.item.cache.values()):
            if not (issue.type == "issue" and "ESA" in issue["origin"]
                    and issue["issue-type"] == "MAI"):
                continue
            actions_count[0] += 1
            if issue["status"] == "closed":
                actions_count[1] += 1
            else:
                actions_count[2] += 1
        sphinx_content.add("Since this metric refers to project actions, "
                           "it will only consider the actions in Gitlab, "
                           "specific for the RTEMS SMP project.")
        sphinx_content.add("Below is presented the action status "
                           "(issues with label MAI in Gitlab):")
        for index, title in enumerate(actions):
            sphinx_content.add_list_item(title + ": " +
                                         str(actions_count[index]))
        sphinx_content.add_blank_line()
        # Code size
        command = self["metrixplusplus-view"]
        stdout: List[str] = []
        run_command(command, stdout=stdout)
        for line in stdout:
            # Only one entry of the stdout will have the metrics dictionary
            if line.startswith("{"):
                while True:
                    if line.endswith("}"):
                        break
                    line = line[:-1]
                metrics_dict = ast.literal_eval(line)
        info_dict = metrics_dict["view"][0]["data"]["aggregated-data"][
            "std.code.lines"]
        code_size = int(info_dict["code"]["total"] +
                        info_dict["preprocessor"]["total"])
        sphinx_content.add("The RTEMS code size is " + str(code_size))
        return sphinx_content.join()

    def _sprs_and_ncrws(self, _ctx: ItemGetValueContext) -> str:
        sphinx_content = SphinxContent()
        existing_rids = False
        sphinx_content.add("The following RIDs are currently open:")
        for issue in sorted(self.item.cache.values()):
            if not (issue.type == "issue" and issue["status"] != "closed"
                    and issue["issue-type"] == "RID"):
                continue
            existing_rids = True
            name = issue["origin"] + " #" + issue["issue-number"]
            url = f"`{name.strip()} <{issue['url']}>`_"
            with sphinx_content.indent():
                sphinx_content.add_list_item(url)
        output = {
            False: "There are no RIDs currently open.",
            True: sphinx_content.join()
        }
        return output[existing_rids]

    def _spr_ncr_status(self, _ctx: ItemGetValueContext) -> str:
        sphinx_content = SphinxContent()
        actions = ["Actions issued", "Actions closed", "Actions open"]
        actions_gitlab = [0, 0, 0]
        actions_rtems = [0, 0, 0]
        for issue in sorted(self.item.cache.values()):
            if not issue.type == "issue":
                continue
            action_origin = actions_gitlab if "ESA" in issue["origin"] \
                else actions_rtems
            action_origin[0] += 1
            if issue["status"] == "closed":
                action_origin[1] += 1
            else:
                action_origin[2] += 1
        sphinx_content.add(
            "Below is presented the action status for ESA Gitlab issues:")
        for index, title in enumerate(actions):
            sphinx_content.add_list_item(title + ": " +
                                         str(actions_gitlab[index]))
        sphinx_content.add_blank_line()
        sphinx_content.add_blank_line()
        sphinx_content.add("Below is presented the action status"
                           " for RTEMS Ticket System issues:")
        for index, title in enumerate(actions):
            sphinx_content.add_list_item(title + ": " +
                                         str(actions_rtems[index]))
        return sphinx_content.join()

    def _vv_coverage_unit_integration(self, _ctx: ItemGetValueContext) -> str:
        sphinx_content = SphinxContent()
        test_cases = _get_test_cases_by_type(self.item.cache, self.enabled_set,
                                             "unit-test")
        spec = self.input("spec")
        assert isinstance(spec, RTEMSItemCache)

        covered = set()
        modules = set(name for name in spec.name_to_item.keys()
                      if name.startswith("function/"))
        for item in test_cases:
            for link in item.links_to_parents("unit-test"):
                covered.add(link["name"])
        coverage = round((len(covered) / len(modules)) * 100)
        sphinx_content.add(f"Modules covered by V&V: {len(covered)}")
        sphinx_content.add(f"Total number of modules: {len(modules)}")
        sphinx_content.add(
            f"V&V coverage: {len(covered)} / {len(modules)} = {coverage} %")
        metric_ok = {True: "This metric is OK.", False: "This metric is NOK."}
        sphinx_content.add(
            metric_ok[self.item["metrics-thresholds"]["vv-coverage"] *
                      100 <= coverage])
        return sphinx_content.join()
