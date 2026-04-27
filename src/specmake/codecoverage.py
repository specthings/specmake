# SPDX-License-Identifier: BSD-2-Clause
""" Provides code-coverage value providers. """

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

from specitems import ItemGetValueContext, ItemValueProvider

from .pkgitems import BuildItemMapper
from .sphinxbuilder import SphinxBuilder
from .testaggregator import TestAggregator


class CodeCoverageProvider(ItemValueProvider):
    """ Provides code coverage achievements and limits. """

    # pylint: disable=too-few-public-methods
    def __init__(self, builder: SphinxBuilder) -> None:
        super().__init__(builder.mapper)
        self.mapper: BuildItemMapper
        self._builder = builder
        my_type = builder.item.type
        self.mapper.add_get_value(f"{my_type}:/code-coverage-achievement",
                                  self._code_coverage_achievement)
        self.mapper.add_get_value(f"{my_type}:/code-coverage-limits",
                                  self._code_coverage_limits)

    def _code_coverage_achievement(self, ctx: ItemGetValueContext) -> str:
        builder = self._builder
        with builder.section_content(ctx) as (content, _):
            for test_aggregator in builder.inputs("test-aggregation"):
                assert isinstance(test_aggregator, TestAggregator)
                test_aggregator.add_coverage_achievement(content, self.mapper)
            return content.join()

    def _code_coverage_limits(self, ctx: ItemGetValueContext) -> str:
        builder = self._builder
        with builder.section_content(ctx) as (content, _):
            for test_aggregator in builder.inputs("test-aggregation"):
                assert isinstance(test_aggregator, TestAggregator)
                item = test_aggregator.component.item
                with content.section(f"Component - {item.spec}",
                                     label=f"CoverageLimits{item.ident}"):
                    test_aggregator.add_coverage_limits(content, self.mapper)
            return content.join()
