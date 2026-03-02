# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the sddlinker module. """

# Copyright (C) 2025 embedded brains GmbH & Co. KG
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

from pathlib import Path

from .util import create_package


def test_sddlinker(caplog, tmpdir):
    tmp_dir = Path(tmpdir)
    package = create_package(caplog, tmp_dir, Path("spec-packagebuild"),
                             ["djf-svs", "link-hub", "sdd-linker"])
    director = package.director
    director.build_package()
    spec_links = director["/pkg/deployment/sdd-linker"].file
    with open(spec_links, "r", encoding="utf-8") as src:
        assert src.read() == f"""/**
 * @def BLUB
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/define-real]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifdefinereal).
 */

/**
 * @def BLUB
 *
 * @ingroup Blub2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/define-real]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifdefinereal).
 */

/**
 * @def CONFIGURE_APPLICATION_DISABLE_FILESYSTEM
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_APPLICATION_DOES_NOT_NEED_CLOCK_DRIVER
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_DISABLE_NEWLIB_REENTRANCY
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_IDLE_TASK_STORAGE_SIZE
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_INIT
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_INIT_TASK_ATTRIBUTES
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_INIT_TASK_CONSTRUCT_STORAGE_SIZE
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_INIT_TASK_INITIAL_MODES
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_INTEGER
 *
 * @ingroup RTEMSApplConfigSomethingConfiguration
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/acfg-integer]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifacfginteger).
 */

/**
 * @def CONFIGURE_MAXIMUM_FILE_DESCRIPTORS
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_MAXIMUM_TASKS
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_RTEMS_INIT_TASKS_TABLE
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def CONFIGURE_UNRELATED
 *
 * @ingroup GroupA
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group-a]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroupa).
 */

/**
 * @def DISABLED
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup).
 */

/**
 * @def FOO
 *
 * @par Traceability
 * @parblock
 * This design element is related to:
 *
 * - [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup)
 *
 * - [spec:/rtems/if/group-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup2)
 * @endparblock
 */

/**
 * @def FOO
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup2).
 */

/**
 * @def REGBLOCK2_REG_BLOCK_2_A_BITS_A(_val)
 *
 * @ingroup RegBlock2REGBLOCK2A
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @def REGBLOCK2_REG_BLOCK_2_A_BITS_A_GET(_reg)
 *
 * @ingroup RegBlock2REGBLOCK2A
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @def REGBLOCK2_REG_BLOCK_2_A_BITS_A_MASK
 *
 * @ingroup RegBlock2REGBLOCK2A
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @def REGBLOCK2_REG_BLOCK_2_A_BITS_A_SET(_reg, _val)
 *
 * @ingroup RegBlock2REGBLOCK2A
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @def REGBLOCK2_REG_BLOCK_2_A_BITS_A_SHIFT
 *
 * @ingroup RegBlock2REGBLOCK2A
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @def REGBLOCK2_REG_BLOCK_2_B_BITS_B(_val)
 *
 * @ingroup RegBlock2REGBLOCK2B
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @def REGBLOCK2_REG_BLOCK_2_B_BITS_B_GET(_reg)
 *
 * @ingroup RegBlock2REGBLOCK2B
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @def REGBLOCK2_REG_BLOCK_2_B_BITS_B_MASK
 *
 * @ingroup RegBlock2REGBLOCK2B
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @def REGBLOCK2_REG_BLOCK_2_B_BITS_B_SET(_reg, _val)
 *
 * @ingroup RegBlock2REGBLOCK2B
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @def REGBLOCK2_REG_BLOCK_2_B_BITS_B_SHIFT
 *
 * @ingroup RegBlock2REGBLOCK2B
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @def REG_BLOCK_REG_BLOCK_A_BIT_A
 *
 * @ingroup RegBlockREGBLOCKA
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock).
 */

/**
 * @def TASK_ATTRIBUTES
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def TASK_STORAGE_SIZE
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @def UnspecDefine
 *
 * @ingroup UnspecGroup
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/unspec-define]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunspecdefine).
 */

/**
 * @def UnspecMacro(x)
 *
 * @ingroup UnspecGroup
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/unspec-macro]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunspecmacro).
 */

/**
 * @enum RtemsReqAction2_Post_X
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @enum RtemsReqAction2_Post_Y
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @enum RtemsReqAction2_Pre_A
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @enum RtemsReqAction2_Pre_B
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @enum RtemsReqAction2_Pre_C
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @enum RtemsReqAction_Post_Result
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @enum RtemsReqAction_Pre_Value
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @enum UnspecEnum
 *
 * @ingroup UnspecGroup
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/unspec-enum]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunspecenum).
 */

/**
 * @enum the_enum
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/enum-real]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifenumreal).
 */

/**
 * @var ENUMERATOR
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/enumerator]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifenumerator).
 */

/**
 * @var ENUMERATOR_2
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/enumerator-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifenumerator2).
 */

/**
 * @var RtemsReqAction2_Post_X_NA
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Post_X_XA
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Post_X_XB
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Post_Y_NA
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Post_Y_YA
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Post_Y_YB
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Pre_A_AA
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Pre_A_AB
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Pre_A_NA
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Pre_B_BA
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Pre_B_BB
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Pre_B_NA
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Pre_C_CA
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Pre_C_CB
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction2_Pre_C_NA
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var RtemsReqAction_Post_Result_LastBitSet
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var RtemsReqAction_Post_Result_NA
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var RtemsReqAction_Post_Result_Zero
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var RtemsReqAction_Pre_Value_NA
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var RtemsReqAction_Pre_Value_NonZero
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var RtemsReqAction_Pre_Value_Zero
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var UnspecEnumerator
 *
 * @ingroup UnspecGroup
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/unspec-enumerator]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunspecenumerator).
 */

/**
 * @file a.c
 *
 * @ingroup Blub2
 *
 * @ingroup Blub
 *
 * @par Traceability
 * @parblock
 * This design element is related to:
 *
 * - [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup)
 *
 * - [spec:/rtems/if/group-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup2)
 * @endparblock
 */

/**
 * @file appl-config.h
 *
 * @ingroup RTEMSImplDoxygen
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup).
 */

/**
 * @file b.c
 *
 * @ingroup Blub2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup2).
 */

/**
 * @file bar/more/blub-2.h
 *
 * @ingroup Blub2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/header-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifheader2).
 */

/**
 * @file bar/more/blub.h
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/header]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifheader).
 */

/**
 * @file bar/more/unspec.h
 *
 * @ingroup UnspecGroup
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/unspec-header]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunspecheader).
 */

/**
 * @file bsp.c
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup).
 */

/**
 * @file c.cc
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup).
 */

/**
 * @file extra.c
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup).
 */

/**
 * @file tests/mem-rtems-basic.c
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @file tests/tc-action-2.c
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @file tests/tc-action.c
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @file tests/tc-blub.c
 *
 * @ingroup RtemsValTestCase
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcase).
 */

/**
 * @file tests/tc-fail.c
 *
 * @ingroup RtemsValTestCaseFail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-fail]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcasefail).
 */

/**
 * @file tests/tc-pass.c
 *
 * @ingroup RtemsValTestCasePass
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-pass]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcasepass).
 */

/**
 * @file tests/tc-perf.c
 *
 * @ingroup ScoreCpuValPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @file tests/tc-unit.c
 *
 * @ingroup RtemsValTestCaseUnit
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-unit]({tmpdir}/pkg/doc-djf-suitp/html/test-case-specification.html#specrtemsvaltestcaseunit).
 */

/**
 * @file tests/tc-xfail.c
 *
 * @ingroup RtemsValTestCaseXfail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-xfail]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcasexfail).
 */

/**
 * @file tests/tr-test-case.c
 *
 * @ingroup RtemsValTestCaseRun
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-run]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcaserun).
 */

/**
 * @file tests/tr-test-case.h
 *
 * @ingroup RtemsValTestCaseRun
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-run]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcaserun).
 */

/**
 * @file tests/ts-blub.c
 *
 * @ingroup TestsuitesPerformanceNoClock0
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/performance-no-clock-0]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#spectestsuitesperformancenoclock0).
 */

/**
 * @file tests/ts-empty.c
 *
 * @ingroup TestsuitesTestSuiteEmpty
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/test-suite-empty]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#spectestsuitestestsuiteempty).
 */

/**
 * @file tests/ts-fail.c
 *
 * @ingroup TestsuitesTestSuiteFail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/test-suite-fail]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#spectestsuitestestsuitefail).
 */

/**
 * @file tests/ts-pass.c
 *
 * @ingroup TestsuitesTestSuitePass
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/test-suite-pass]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#spectestsuitestestsuitepass).
 */

/**
 * @file tests/ts-unit.c
 *
 * @ingroup TestsuitesUnit0
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/unit-0]({tmpdir}/pkg/doc-djf-suitp/html/test-design.html#spectestsuitesunit0).
 */

/**
 * @file tests/ts-xfail.c
 *
 * @ingroup TestsuitesTestSuiteXfail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/test-suite-xfail]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#spectestsuitestestsuitexfail).
 */

/**
 * @fn static void Init(rtems_task_argument arg)
 *
 * @ingroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @fn static void RtemsReqAction2_Action(void)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn static RtemsReqAction2_Entry RtemsReqAction2_PopEntry(RtemsReqAction2_Context *ctx)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn static void RtemsReqAction2_Post_X_Check(RtemsReqAction2_Post_X state)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn static void RtemsReqAction2_Post_Y_Check(RtemsReqAction2_Post_Y state)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn static void RtemsReqAction2_Pre_A_Prepare(RtemsReqAction2_Pre_A state)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn static void RtemsReqAction2_Pre_B_Prepare(RtemsReqAction2_Pre_B state)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn static void RtemsReqAction2_Pre_C_Prepare(RtemsReqAction2_Pre_C state)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn static size_t RtemsReqAction2_Scope(void *arg, char *buf, size_t n)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn static void RtemsReqAction2_SetPreConditionStates(RtemsReqAction2_Context *ctx)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn static void RtemsReqAction2_TestVariant(RtemsReqAction2_Context *ctx)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn static void RtemsReqAction_Action(void)
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @fn static RtemsReqAction_Entry RtemsReqAction_PopEntry(RtemsReqAction_Context *ctx)
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @fn static void RtemsReqAction_Post_Result_Check(RtemsReqAction_Post_Result state)
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @fn static void RtemsReqAction_Pre_Value_Prepare(RtemsReqAction_Pre_Value state)
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @fn static size_t RtemsReqAction_Scope(void *arg, char *buf, size_t n)
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @fn static void RtemsReqAction_TestVariant(RtemsReqAction_Context *ctx)
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @fn static void RtemsReqPerfNoResults_Body(void)
 *
 * @ingroup RtemsReqPerfNoResults
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @fn static void RtemsReqPerfNoResults_Body_Wrap(void *arg)
 *
 * @ingroup RtemsReqPerfNoResults
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @fn static void RtemsReqPerf_Body(void)
 *
 * @ingroup RtemsReqPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @fn static void RtemsReqPerf_Body_Wrap(void *arg)
 *
 * @ingroup RtemsReqPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @fn static void RtemsValTestCaseRun_Action_0(void)
 *
 * @ingroup RtemsValTestCaseRun
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-run]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcaserun).
 */

/**
 * @fn void RtemsValTestCaseRun_Run(int source)
 *
 * @ingroup RtemsValTestCaseRun
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-run]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcaserun).
 */

/**
 * @fn static void RtemsValTestCase_Action_0(void)
 *
 * @ingroup RtemsValTestCase
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcase).
 */

/**
 * @fn static void ScoreCpuValPerf_Setup_Context(ScoreCpuValPerf_Context *ctx)
 *
 * @ingroup ScoreCpuValPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @fn static void ScoreCpuValPerf_Setup_Wrap(void *arg)
 *
 * @ingroup ScoreCpuValPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @fn void T_case_body_RtemsReqAction(void)
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @fn void T_case_body_RtemsReqAction2(void)
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @fn void T_case_body_RtemsValTestCase(void)
 *
 * @ingroup RtemsValTestCase
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcase).
 */

/**
 * @fn void T_case_body_RtemsValTestCaseFail(void)
 *
 * @ingroup RtemsValTestCaseFail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-fail]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcasefail).
 */

/**
 * @fn void T_case_body_RtemsValTestCasePass(void)
 *
 * @ingroup RtemsValTestCasePass
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-pass]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcasepass).
 */

/**
 * @fn void T_case_body_RtemsValTestCaseUnit(void)
 *
 * @ingroup RtemsValTestCaseUnit
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-unit]({tmpdir}/pkg/doc-djf-suitp/html/test-case-specification.html#specrtemsvaltestcaseunit).
 */

/**
 * @fn void T_case_body_RtemsValTestCaseXfail(void)
 *
 * @ingroup RtemsValTestCaseXfail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-xfail]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcasexfail).
 */

/**
 * @fn void T_case_body_ScoreCpuValPerf(void)
 *
 * @ingroup ScoreCpuValPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @fn int UnspecFunction(int param)
 *
 * @ingroup UnspecGroup
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/unspec-function]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunspecfunction).
 */

/**
 * @fn static int blub(int param)
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/func]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsiffunc).
 */

/**
 * @addtogroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup).
 */

/**
 * @addtogroup Blub2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup2).
 */

/**
 * @addtogroup Blub3
 *
 * @ingroup Blub2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/group]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqgroup).
 */

/**
 * @addtogroup GroupA
 *
 * @ingroup Blub2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group-a]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroupa).
 */

/**
 * @addtogroup GroupB
 *
 * @ingroup Blub2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group-b]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroupb).
 */

/**
 * @addtogroup RTEMSAPI
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup).
 */

/**
 * @addtogroup RTEMSApplConfig
 *
 * @ingroup RTEMSAPI
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup).
 */

/**
 * @addtogroup RTEMSApplConfigSomethingConfiguration
 *
 * @ingroup RTEMSApplConfig
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group-acfg]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroupacfg).
 */

/**
 * @addtogroup RTEMSImplDoxygen
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup).
 */

/**
 * @addtogroup RegBlock
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock).
 */

/**
 * @addtogroup RegBlock2
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @addtogroup RegBlock2REGBLOCK2A
 *
 * @ingroup RegBlock2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @addtogroup RegBlock2REGBLOCK2B
 *
 * @ingroup RegBlock2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */

/**
 * @addtogroup RegBlockREGBLOCKA
 *
 * @ingroup RegBlock
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock).
 */

/**
 * @addtogroup RegBlockREGBLOCKB
 *
 * @ingroup RegBlock
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock).
 */

/**
 * @addtogroup RtemsReqAction
 *
 * @ingroup TestsuitesTestSuiteFail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @addtogroup RtemsReqAction2
 *
 * @ingroup TestsuitesTestSuiteFail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @addtogroup RtemsReqPerf
 *
 * @ingroup ScoreCpuValPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @addtogroup RtemsReqPerfNoResults
 *
 * @ingroup ScoreCpuValPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @addtogroup RtemsValMemBasic
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/mem-basic]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#specrtemsvalmembasic).
 */

/**
 * @addtogroup RtemsValTestCase
 *
 * @ingroup TestsuitesPerformanceNoClock0
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcase).
 */

/**
 * @addtogroup RtemsValTestCaseFail
 *
 * @ingroup TestsuitesTestSuiteFail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-fail]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcasefail).
 */

/**
 * @addtogroup RtemsValTestCasePass
 *
 * @ingroup TestsuitesTestSuitePass
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-pass]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcasepass).
 */

/**
 * @addtogroup RtemsValTestCaseRun
 *
 * @ingroup TestsuitesTestSuiteFail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-run]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcaserun).
 */

/**
 * @addtogroup RtemsValTestCaseUnit
 *
 * @ingroup TestsuitesUnit0
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-unit]({tmpdir}/pkg/doc-djf-suitp/html/test-case-specification.html#specrtemsvaltestcaseunit).
 */

/**
 * @addtogroup RtemsValTestCaseXfail
 *
 * @ingroup TestsuitesTestSuiteXfail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-xfail]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcasexfail).
 */

/**
 * @addtogroup ScoreCpuValPerf
 *
 * @ingroup TestsuitesPerformanceNoClock0
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @addtogroup TestsuitesPerformanceNoClock0
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/performance-no-clock-0]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#spectestsuitesperformancenoclock0).
 */

/**
 * @addtogroup TestsuitesTestSuiteEmpty
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/test-suite-empty]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#spectestsuitestestsuiteempty).
 */

/**
 * @addtogroup TestsuitesTestSuiteFail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/test-suite-fail]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#spectestsuitestestsuitefail).
 */

/**
 * @addtogroup TestsuitesTestSuitePass
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/test-suite-pass]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#spectestsuitestestsuitepass).
 */

/**
 * @addtogroup TestsuitesTestSuiteXfail
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/test-suite-xfail]({tmpdir}/pkg/doc-djf-svs/html/test-design.html#spectestsuitestestsuitexfail).
 */

/**
 * @addtogroup TestsuitesUnit0
 *
 * @par Traceability
 * This design element is related to
 * [spec:/testsuites/unit-0]({tmpdir}/pkg/doc-djf-suitp/html/test-design.html#spectestsuitesunit0).
 */

/**
 * @addtogroup UnspecGroup
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/group]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifgroup).
 */

/**
 * @var static const RtemsReqAction2_Entry RtemsReqAction2_Entries[]
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var static T_fixture RtemsReqAction2_Fixture
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var static RtemsReqAction2_Context RtemsReqAction2_Instance
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var static const uint8_t RtemsReqAction2_Map[]
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var static const char *const  *const RtemsReqAction2_PreDesc[]
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var static const char *const RtemsReqAction2_PreDesc_A[]
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var static const char *const RtemsReqAction2_PreDesc_B[]
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var static const char *const RtemsReqAction2_PreDesc_C[]
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @var static const RtemsReqAction_Entry RtemsReqAction_Entries[]
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var static T_fixture RtemsReqAction_Fixture
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var static RtemsReqAction_Context RtemsReqAction_Instance
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var static const uint8_t RtemsReqAction_Map[]
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var static const char *const  *const RtemsReqAction_PreDesc[]
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var static const char *const RtemsReqAction_PreDesc_Value[]
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @var static T_fixture RtemsValTestCaseRun_Fixture
 *
 * @ingroup RtemsValTestCaseRun
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-run]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcaserun).
 */

/**
 * @var static RtemsValTestCaseRun_Context RtemsValTestCaseRun_Instance
 *
 * @ingroup RtemsValTestCaseRun
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-run]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcaserun).
 */

/**
 * @var static T_fixture ScoreCpuValPerf_Fixture
 *
 * @ingroup ScoreCpuValPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @var static ScoreCpuValPerf_Context ScoreCpuValPerf_Instance
 *
 * @ingroup ScoreCpuValPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @var int UnspecObject
 *
 * @ingroup UnspecGroup
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/unspec-object]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunspecobject).
 */

/**
 * @var int obj
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/obj]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifobj).
 */

/**
 * @var int obj
 *
 * @ingroup GroupA
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/obj]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifobj).
 */

/**
 * @var int obj
 *
 * @ingroup GroupB
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/obj]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifobj).
 */

/**
 * @struct RtemsReqAction2_Context
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @struct RtemsReqAction2_Entry
 *
 * @ingroup RtemsReqAction2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action-2]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction2).
 */

/**
 * @struct RtemsReqAction_Context
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @struct RtemsReqAction_Entry
 *
 * @ingroup RtemsReqAction
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/req/action]({tmpdir}/pkg/doc-ts-srs/html/requirements.html#specrtemsreqaction).
 */

/**
 * @struct RtemsValTestCaseRun_Context
 *
 * @ingroup RtemsValTestCaseRun
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/val/test-case-run]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specrtemsvaltestcaserun).
 */

/**
 * @struct ScoreCpuValPerf_Context
 *
 * @ingroup ScoreCpuValPerf
 *
 * @par Traceability
 * This design element is related to
 * [spec:/score/cpu/val/perf]({tmpdir}/pkg/doc-djf-svs/html/test-case-specification.html#specscorecpuvalperf).
 */

/**
 * @struct Struct
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/struct]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifstruct).
 */

/**
 * @typedef struct StructBoth StructBoth
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/struct-both]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifstructboth).
 */

/**
 * @struct StructOnly
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/struct-only]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifstructonly).
 */

/**
 * @typedef int Typedef
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/typedef]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsiftypedef).
 */

/**
 * @union Union
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/union]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunion).
 */

/**
 * @typedef union UnionBoth UnionBoth
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/union-both]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunionboth).
 */

/**
 * @union UnionOnly
 *
 * @ingroup Blub
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/union-only]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifuniononly).
 */

/**
 * @struct UnspecStruct
 *
 * @ingroup UnspecGroup
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/unspec-struct]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunspecstruct).
 */

/**
 * @typedef struct UnspecStruct UnspecTypedef
 *
 * @ingroup UnspecGroup
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/unspec-typedef]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunspectypedef).
 */

/**
 * @union UnspecUnion
 *
 * @ingroup UnspecGroup
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/unspec-union]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifunspecunion).
 */

/**
 * @typedef struct reg_block reg_block
 *
 * @ingroup RegBlock
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock).
 */

/**
 * @typedef struct reg_block_2 reg_block_2
 *
 * @ingroup RegBlock2
 *
 * @par Traceability
 * This design element is related to
 * [spec:/rtems/if/reg-block-2]({tmpdir}/pkg/doc-ts-icd/html/requirements-and-design.html#specrtemsifregblock2).
 */
"""
