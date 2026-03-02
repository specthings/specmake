/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RtemsReqAction
 */

/*
 * Copyright (C) 2021, 2026 embedded brains GmbH & Co. KG
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

#include <limits.h>
#include <strings.h>

#include <rtems/test.h>

/**
 * @defgroup RtemsReqAction spec:/rtems/req/action
 *
 * @ingroup TestsuitesTestSuiteFail
 *
 * @{
 */

typedef enum {
  RtemsReqAction_Pre_Value_Zero,
  RtemsReqAction_Pre_Value_NonZero,
  RtemsReqAction_Pre_Value_NA
} RtemsReqAction_Pre_Value;

typedef enum {
  RtemsReqAction_Post_Result_Zero,
  RtemsReqAction_Post_Result_LastBitSet,
  RtemsReqAction_Post_Result_NA
} RtemsReqAction_Post_Result;

typedef struct {
  uint8_t Skip : 1;
  uint8_t Pre_Value_NA : 1;
  uint8_t Post_Result : 2;
} RtemsReqAction_Entry;

/**
 * @brief Test context for spec:/rtems/req/action test case.
 */
typedef struct {
  struct {
    /**
     * @brief This member defines the pre-condition states for the next action.
     */
    size_t pcs[ 1 ];

    /**
     * @brief If this member is true, then the test action loop is executed.
     */
    bool in_action_loop;

    /**
     * @brief This member contains the next transition map index.
     */
    size_t index;

    /**
     * @brief This member contains the current transition map entry.
     */
    RtemsReqAction_Entry entry;

    /**
     * @brief If this member is true, then the current transition variant
     *   should be skipped.
     */
    bool skip;
  } Map;
} RtemsReqAction_Context;

static RtemsReqAction_Context
  RtemsReqAction_Instance;

static const char * const RtemsReqAction_PreDesc_Value[] = {
  "Zero",
  "NonZero",
  "NA"
};

static const char * const * const RtemsReqAction_PreDesc[] = {
  RtemsReqAction_PreDesc_Value,
  NULL
};

static void RtemsReqAction_Pre_Value_Prepare( RtemsReqAction_Pre_Value state )
{
  switch ( state ) {
    case RtemsReqAction_Pre_Value_Zero: {
      /*
       * While the parameter value is equal to zero.
       */
      /* Nothing to prepare */
      break;
    }

    case RtemsReqAction_Pre_Value_NonZero: {
      /*
       * While the parameter value is not equal to zero.
       */
      /* Nothing to prepare */
      break;
    }

    case RtemsReqAction_Pre_Value_NA:
      break;
  }
}

static void RtemsReqAction_Post_Result_Check(
  RtemsReqAction_Post_Result state
)
{
  int    expected_result;
  long   value;
  size_t i;

  switch ( state ) {
    case RtemsReqAction_Post_Result_Zero: {
      /*
       * The return value of UnspecFunction() shall be equal to zero.
       */
      T_eq_int( flsl( 0 ), 0 );
      break;
    }

    case RtemsReqAction_Post_Result_LastBitSet: {
      /*
       * The return value of UnspecFunction() shall be equal to the index of
       * the most-significant bit set in the parameter value.
       */
      expected_result = 1;
      value = 1;

      for ( i = 0; i < sizeof( long ) * CHAR_BIT; ++i ) {
        T_eq_int( flsl( value ), expected_result );
        ++expected_result;
        value <<= 1;
      }
      break;
    }

    case RtemsReqAction_Post_Result_NA:
      break;
  }
}

static void RtemsReqAction_Action( void )
{
  /* The action is performed in the post-condition states */
}

static const RtemsReqAction_Entry
RtemsReqAction_Entries[] = {
  { 0, 0, RtemsReqAction_Post_Result_Zero },
  { 0, 0, RtemsReqAction_Post_Result_LastBitSet }
};

static const uint8_t
RtemsReqAction_Map[] = {
  0, 1
};

static size_t RtemsReqAction_Scope( void *arg, char *buf, size_t n )
{
  RtemsReqAction_Context *ctx;

  ctx = arg;

  if ( ctx->Map.in_action_loop ) {
    return T_get_scope( RtemsReqAction_PreDesc, buf, n, ctx->Map.pcs );
  }

  return 0;
}

static T_fixture RtemsReqAction_Fixture = {
  .setup = NULL,
  .stop = NULL,
  .teardown = NULL,
  .scope = RtemsReqAction_Scope,
  .initial_context = &RtemsReqAction_Instance
};

static inline RtemsReqAction_Entry RtemsReqAction_PopEntry(
  RtemsReqAction_Context *ctx
)
{
  size_t index;

  index = ctx->Map.index;
  ctx->Map.index = index + 1;
  return RtemsReqAction_Entries[
    RtemsReqAction_Map[ index ]
  ];
}

static void RtemsReqAction_TestVariant( RtemsReqAction_Context *ctx )
{
  RtemsReqAction_Pre_Value_Prepare( ctx->Map.pcs[ 0 ] );
  RtemsReqAction_Action();
  RtemsReqAction_Post_Result_Check( ctx->Map.entry.Post_Result );
}

/**
 * @fn void T_case_body_RtemsReqAction( void )
 */
T_TEST_CASE_FIXTURE( RtemsReqAction, &RtemsReqAction_Fixture )
{
  RtemsReqAction_Context *ctx;

  ctx = T_fixture_context();
  ctx->Map.in_action_loop = true;
  ctx->Map.index = 0;

  for (
    ctx->Map.pcs[ 0 ] = RtemsReqAction_Pre_Value_Zero;
    ctx->Map.pcs[ 0 ] < RtemsReqAction_Pre_Value_NA;
    ++ctx->Map.pcs[ 0 ]
  ) {
    ctx->Map.entry = RtemsReqAction_PopEntry( ctx );
    RtemsReqAction_TestVariant( ctx );
  }
}

/** @} */
