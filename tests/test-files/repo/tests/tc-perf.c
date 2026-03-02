/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup ScoreCpuValPerf
 */

/*
 * Copyright (C) 2025 embedded brains GmbH & Co. KG
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file is part of the RTEMS quality process and was automatically
 * generated.  If you find something that needs to be fixed or
 * worded better please post a report or patch to an RTEMS mailing list
 * or raise a bug report:
 *
 * https://www.rtems.org/bugs.html
 *
 * For information on updating and regenerating please refer to the How-To
 * section in the Software Requirements Engineering chapter of the
 * RTEMS Software Engineering manual.  The manual is provided as a part of
 * a release.  For development sources please refer to the online
 * documentation at:
 *
 * https://docs.rtems.org
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <rtems/test.h>

/**
 * @defgroup ScoreCpuValPerf spec:/score/cpu/val/perf
 *
 * @ingroup TestsuitesPerformanceNoClock0
 *
 * @brief Brief.
 *
 * Description.
 *
 * @{
 */

/**
 * @brief Test context for spec:/score/cpu/val/perf test case.
 */
typedef struct {
  /**
   * @brief This member references the measure runtime context.
   */
  T_measure_runtime_context *context;

  /**
   * @brief This member provides the measure runtime request.
   */
  T_measure_runtime_request request;

  /**
   * @brief This member provides an optional measurement begin time point.
   */
  T_ticks begin;

  /**
   * @brief This member provides an optional measurement end time point.
   */
  T_ticks end;
} ScoreCpuValPerf_Context;

static ScoreCpuValPerf_Context
  ScoreCpuValPerf_Instance;

static void ScoreCpuValPerf_Setup_Context( ScoreCpuValPerf_Context *ctx )
{
  T_measure_runtime_config config;

  memset( &config, 0, sizeof( config ) );
  config.sample_count = 100;
  ctx->request.arg = ctx;
  ctx->request.flags = T_MEASURE_RUNTIME_REPORT_SAMPLES;
  ctx->context = T_measure_runtime_create( &config );
  T_assert_not_null( ctx->context );
}

static void ScoreCpuValPerf_Setup_Wrap( void *arg )
{
  ScoreCpuValPerf_Context *ctx;

  ctx = arg;
  ScoreCpuValPerf_Setup_Context( ctx );
}

static T_fixture ScoreCpuValPerf_Fixture = {
  .setup = ScoreCpuValPerf_Setup_Wrap,
  .stop = NULL,
  .teardown = NULL,
  .scope = NULL,
  .initial_context = &ScoreCpuValPerf_Instance
};

/**
 * @defgroup RtemsReqPerf spec:/rtems/req/perf
 *
 * @{
 */

/**
 * @brief Brief.
 *
 * Description.
 */
static void RtemsReqPerf_Body( void )
{
  code();
}

static void RtemsReqPerf_Body_Wrap( void *arg )
{
  (void) arg;
  RtemsReqPerf_Body();
}

/** @} */

/**
 * @defgroup RtemsReqPerfNoResults spec:/rtems/req/perf-no-results
 *
 * @{
 */

/**
 * @brief Brief.
 *
 * Description.
 */
static void RtemsReqPerfNoResults_Body( void )
{
  code();
}

static void RtemsReqPerfNoResults_Body_Wrap( void *arg )
{
  (void) arg;
  RtemsReqPerfNoResults_Body();
}

/** @} */

/**
 * @fn void T_case_body_ScoreCpuValPerf( void )
 */
T_TEST_CASE_FIXTURE( ScoreCpuValPerf, &ScoreCpuValPerf_Fixture )
{
  ScoreCpuValPerf_Context *ctx;

  ctx = T_fixture_context();

  ctx->request.name = "RtemsReqPerf";
  ctx->request.setup = NULL;
  ctx->request.body = RtemsReqPerf_Body_Wrap;
  ctx->request.teardown = NULL;
  T_measure_runtime( ctx->context, &ctx->request );

  ctx->request.name = "RtemsReqPerfNoResults";
  ctx->request.setup = NULL;
  ctx->request.body = RtemsReqPerfNoResults_Body_Wrap;
  ctx->request.teardown = NULL;
  T_measure_runtime( ctx->context, &ctx->request );
}

/** @} */
