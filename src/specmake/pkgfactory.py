# SPDX-License-Identifier: BSD-2-Clause
""" Provides the default build item factory. """

# Copyright (C) 2023, 2026 embedded brains GmbH & Co. KG
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

from .archiver import Archiver, IndexGroup, Indexer
from .ctrfcollector import CTRFCollector
from .directorystate import DirectoryState, RepositoryState
from .docbuilder import DocumentBuilder
from .doxyfile import Doxyfile
from .gcdaproducer import GCDAProducer
from .icdbuilder import ICDBuilder
from .itemcachestate import ItemCacheDirectoryState
from .linkhub import LinkHub
from .membenchcollector import MembenchCollector
from .notruncoverage import NotRunCoverage
from .pkgitems import (BuildItemFactory, GenericPackageComponent, Redirection,
                       export_component_data, export_template_data)
from .packagechanges import PackageChanges
from .packagemanual import PackageManualBuilder, PackageSummary
from .perfimages import BuildPerformanceImages
from .qualityscanner import QualityScanner
from .repositoryfilter import export_no_data
from .reposubset import RepositorySubset
from .rtems import RTEMSItemCache, RTEMSPackageComponent
from .rtemstestsimages import BuildRTEMSTestsImages
from .runactions import RunActions
from .runexecutablecmd import RunExecutableCommand
from .sddlinker import SDDLinker
from .spamrbuilder import SpamrBuilder
from .speccompare import CompareSpecsRegistry
from .specdocbuilder import SpecDocumentBuilder
from .specitemcache import SpecItemCache
from .sreldbuilder import SRelDBuilder
from .srsbuilder import SRSBuilder
from .stdtailoring import ECSSAnnex, ECSSClause
from .svrbuilder import SVRBuilder
from .testaggregator import TestAggregator
from .testplanbuilder import TestPlanBuilder
from .testreporter import TestReporter
from .testrunner import (TestRunner, GRMONManualTestRunner,
                         SubprocessTestRunner, TestLog)
from .testrunneragent import AgentTestRunner
from .testrunneresa import ESATestRunner

_CONSTRUCTORS = (
    ("pkg/component/generic", GenericPackageComponent),
    ("pkg/component/rtems", RTEMSPackageComponent),
    ("pkg/directory-state/explicit", DirectoryState),
    ("pkg/directory-state/patterns", DirectoryState),
    ("pkg/directory-state/test-coverage", DirectoryState),
    ("pkg/directory-state/unpacked-archive", DirectoryState),
    ("pkg/directory-state/archive", Archiver),
    ("pkg/directory-state/ctrf", CTRFCollector),
    ("pkg/directory-state/doxyfile", Doxyfile),
    ("pkg/directory-state/gcda-producer", GCDAProducer),
    ("pkg/directory-state/index", Indexer),
    ("pkg/directory-state/not-run-coverage", NotRunCoverage),
    ("pkg/directory-state/item-cache", ItemCacheDirectoryState),
    ("pkg/directory-state/membench-collector", MembenchCollector),
    ("pkg/directory-state/package-summary", PackageSummary),
    ("pkg/directory-state/performance-images", BuildPerformanceImages),
    ("pkg/directory-state/quality-scanner", QualityScanner),
    ("pkg/directory-state/repository", RepositoryState),
    ("pkg/directory-state/repository-subset", RepositorySubset),
    ("pkg/directory-state/rtems-tests-images", BuildRTEMSTestsImages),
    ("pkg/directory-state/run-executable-command", RunExecutableCommand),
    ("pkg/directory-state/sdd-linker", SDDLinker),
    ("pkg/directory-state/sphinx/ddf-sreld", SRelDBuilder),
    ("pkg/directory-state/sphinx/djf-svr", SVRBuilder),
    ("pkg/directory-state/sphinx/generic", DocumentBuilder),
    ("pkg/directory-state/sphinx/package-manual", PackageManualBuilder),
    ("pkg/directory-state/sphinx/paf-spamr", SpamrBuilder),
    ("pkg/directory-state/sphinx/spec", SpecDocumentBuilder),
    ("pkg/directory-state/sphinx/test-plan", TestPlanBuilder),
    ("pkg/directory-state/sphinx/test-report", TestReporter),
    ("pkg/directory-state/sphinx/ts-icd", ICDBuilder),
    ("pkg/directory-state/sphinx/ts-srs", SRSBuilder),
    ("pkg/directory-state/test-log", TestLog),
    ("pkg/index-group", IndexGroup),
    ("pkg/link-hub", LinkHub),
    ("pkg/package-changes", PackageChanges),
    ("pkg/redirection", Redirection),
    ("pkg/rtems-item-cache", RTEMSItemCache),
    ("pkg/run-actions", RunActions),
    ("pkg/spec-compare-registry", CompareSpecsRegistry),
    ("pkg/spec-item-cache", SpecItemCache),
    ("pkg/test-aggregator", TestAggregator),
    ("pkg/test-runner/esa", ESATestRunner),
    ("pkg/test-runner/dummy", TestRunner),
    ("pkg/test-runner/grmon-manual", GRMONManualTestRunner),
    ("pkg/test-runner/agent", AgentTestRunner),
    ("pkg/test-runner/subprocess", SubprocessTestRunner),
    ("requirement/non-functional/ecss", ECSSClause),
    ("requirement/non-functional/ecss-annex", ECSSAnnex),
)

_EXPORT_DATA = (
    ("pkg/component/generic", export_component_data),
    ("pkg/component/rtems", export_component_data),
    ("pkg/template/component", export_template_data),
    ("pkg/template/file-item", export_template_data),
    ("pkg/template/inline-item", export_template_data),
    ("pkg/template/redirect", export_template_data),
    ("pkg/repository-filter", export_no_data),
)


def create_build_item_factory() -> BuildItemFactory:
    """ Create the default build item factory. """
    factory = BuildItemFactory()
    for type_name, constructor in _CONSTRUCTORS:
        factory.add_constructor(type_name, constructor)
    for type_name, export_data in _EXPORT_DATA:
        factory.add_export_data(type_name, export_data)
    return factory
