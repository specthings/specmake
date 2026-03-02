/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RtemsReqAction2
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

#include <rtems/test.h>

/**
 * @defgroup RtemsReqAction2 spec:/rtems/req/action-2
 *
 * @ingroup TestsuitesTestSuiteFail
 *
 * @{
 */

typedef enum {
  RtemsReqAction2_Pre_A_AA,
  RtemsReqAction2_Pre_A_AB,
  RtemsReqAction2_Pre_A_NA
} RtemsReqAction2_Pre_A;

typedef enum {
  RtemsReqAction2_Pre_B_BA,
  RtemsReqAction2_Pre_B_BB,
  RtemsReqAction2_Pre_B_NA
} RtemsReqAction2_Pre_B;

typedef enum {
  RtemsReqAction2_Pre_C_CA,
  RtemsReqAction2_Pre_C_CB,
  RtemsReqAction2_Pre_C_NA
} RtemsReqAction2_Pre_C;

typedef enum {
  RtemsReqAction2_Post_X_XA,
  RtemsReqAction2_Post_X_XB,
  RtemsReqAction2_Post_X_NA
} RtemsReqAction2_Post_X;

typedef enum {
  RtemsReqAction2_Post_Y_YA,
  RtemsReqAction2_Post_Y_YB,
  RtemsReqAction2_Post_Y_NA
} RtemsReqAction2_Post_Y;

typedef struct {
  uint8_t Skip : 1;
  uint8_t Pre_A_NA : 1;
  uint8_t Pre_B_NA : 1;
  uint8_t Pre_C_NA : 1;
  uint8_t Post_X : 2;
  uint8_t Post_Y : 2;
} RtemsReqAction2_Entry;

/**
 * @brief Test context for spec:/rtems/req/action-2 test case.
 */
typedef struct {
  struct {
    /**
     * @brief This member defines the pre-condition indices for the next
     *   action.
     */
    size_t pci[ 3 ];

    /**
     * @brief This member defines the pre-condition states for the next action.
     */
    size_t pcs[ 3 ];

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
    RtemsReqAction2_Entry entry;

    /**
     * @brief If this member is true, then the current transition variant
     *   should be skipped.
     */
    bool skip;
  } Map;
} RtemsReqAction2_Context;

static RtemsReqAction2_Context
  RtemsReqAction2_Instance;

static const char * const RtemsReqAction2_PreDesc_A[] = {
  "AA",
  "AB",
  "NA"
};

static const char * const RtemsReqAction2_PreDesc_B[] = {
  "BA",
  "BB",
  "NA"
};

static const char * const RtemsReqAction2_PreDesc_C[] = {
  "CA",
  "CB",
  "NA"
};

static const char * const * const RtemsReqAction2_PreDesc[] = {
  RtemsReqAction2_PreDesc_A,
  RtemsReqAction2_PreDesc_B,
  RtemsReqAction2_PreDesc_C,
  NULL
};

static void RtemsReqAction2_Pre_A_Prepare( RtemsReqAction2_Pre_A state )
{
  switch ( state ) {
    case RtemsReqAction2_Pre_A_AA: {
      /*
       * AA
       */
      /* Code */
      break;
    }

    case RtemsReqAction2_Pre_A_AB: {
      /*
       * AB
       */
      /* Code */
      break;
    }

    case RtemsReqAction2_Pre_A_NA:
      break;
  }
}

static void RtemsReqAction2_Pre_B_Prepare( RtemsReqAction2_Pre_B state )
{
  switch ( state ) {
    case RtemsReqAction2_Pre_B_BA: {
      /*
       * BA
       */
      /* Code */
      break;
    }

    case RtemsReqAction2_Pre_B_BB: {
      /*
       * BB
       */
      /* Code */
      break;
    }

    case RtemsReqAction2_Pre_B_NA:
      break;
  }
}

static void RtemsReqAction2_Pre_C_Prepare( RtemsReqAction2_Pre_C state )
{
  switch ( state ) {
    case RtemsReqAction2_Pre_C_CA: {
      /*
       * CA
       */
      /* Code */
      break;
    }

    case RtemsReqAction2_Pre_C_CB: {
      /*
       * CB
       */
      /* Code */
      break;
    }

    case RtemsReqAction2_Pre_C_NA:
      break;
  }
}

static void RtemsReqAction2_Post_X_Check( RtemsReqAction2_Post_X state )
{
  switch ( state ) {
    case RtemsReqAction2_Post_X_XA: {
      /*
       * XA
       */
      /* Code */
      break;
    }

    case RtemsReqAction2_Post_X_XB: {
      /*
       * XB
       */
      /* Code */
      break;
    }

    case RtemsReqAction2_Post_X_NA:
      break;
  }
}

static void RtemsReqAction2_Post_Y_Check( RtemsReqAction2_Post_Y state )
{
  switch ( state ) {
    case RtemsReqAction2_Post_Y_YA: {
      /*
       * YA
       */
      /* Code */
      break;
    }

    case RtemsReqAction2_Post_Y_YB: {
      /*
       * YB
       */
      /* Code */
      break;
    }

    case RtemsReqAction2_Post_Y_NA:
      break;
  }
}

static void RtemsReqAction2_Action( void )
{
  /* Action */
}

static const RtemsReqAction2_Entry
RtemsReqAction2_Entries[] = {
  { 0, 0, 1, 0, RtemsReqAction2_Post_X_XB, RtemsReqAction2_Post_Y_NA },
  { 0, 0, 1, 0, RtemsReqAction2_Post_X_XA, RtemsReqAction2_Post_Y_YA },
  { 1, 0, 0, 0, RtemsReqAction2_Post_X_NA, RtemsReqAction2_Post_Y_NA }
};

static const uint8_t
RtemsReqAction2_Map[] = {
  2, 1, 1, 1, 0, 0, 0, 0
};

static size_t RtemsReqAction2_Scope( void *arg, char *buf, size_t n )
{
  RtemsReqAction2_Context *ctx;

  ctx = arg;

  if ( ctx->Map.in_action_loop ) {
    return T_get_scope( RtemsReqAction2_PreDesc, buf, n, ctx->Map.pcs );
  }

  return 0;
}

static T_fixture RtemsReqAction2_Fixture = {
  .setup = NULL,
  .stop = NULL,
  .teardown = NULL,
  .scope = RtemsReqAction2_Scope,
  .initial_context = &RtemsReqAction2_Instance
};

static inline RtemsReqAction2_Entry RtemsReqAction2_PopEntry(
  RtemsReqAction2_Context *ctx
)
{
  size_t index;

  index = ctx->Map.index;
  ctx->Map.index = index + 1;
  return RtemsReqAction2_Entries[
    RtemsReqAction2_Map[ index ]
  ];
}

static void RtemsReqAction2_SetPreConditionStates(
  RtemsReqAction2_Context *ctx
)
{
  ctx->Map.pcs[ 0 ] = ctx->Map.pci[ 0 ];

  if ( ctx->Map.entry.Pre_B_NA ) {
    ctx->Map.pcs[ 1 ] = RtemsReqAction2_Pre_B_NA;
  } else {
    ctx->Map.pcs[ 1 ] = ctx->Map.pci[ 1 ];
  }

  ctx->Map.pcs[ 2 ] = ctx->Map.pci[ 2 ];
}

static void RtemsReqAction2_TestVariant( RtemsReqAction2_Context *ctx )
{
  RtemsReqAction2_Pre_A_Prepare( ctx->Map.pcs[ 0 ] );
  RtemsReqAction2_Pre_B_Prepare( ctx->Map.pcs[ 1 ] );
  RtemsReqAction2_Pre_C_Prepare( ctx->Map.pcs[ 2 ] );
  RtemsReqAction2_Action();
  RtemsReqAction2_Post_X_Check( ctx->Map.entry.Post_X );
  RtemsReqAction2_Post_Y_Check( ctx->Map.entry.Post_Y );
}

/**
 * @fn void T_case_body_RtemsReqAction2( void )
 */
T_TEST_CASE_FIXTURE( RtemsReqAction2, &RtemsReqAction2_Fixture )
{
  RtemsReqAction2_Context *ctx;

  ctx = T_fixture_context();
  ctx->Map.in_action_loop = true;
  ctx->Map.index = 0;

  for (
    ctx->Map.pci[ 0 ] = RtemsReqAction2_Pre_A_AA;
    ctx->Map.pci[ 0 ] < RtemsReqAction2_Pre_A_NA;
    ++ctx->Map.pci[ 0 ]
  ) {
    for (
      ctx->Map.pci[ 1 ] = RtemsReqAction2_Pre_B_BA;
      ctx->Map.pci[ 1 ] < RtemsReqAction2_Pre_B_NA;
      ++ctx->Map.pci[ 1 ]
    ) {
      for (
        ctx->Map.pci[ 2 ] = RtemsReqAction2_Pre_C_CA;
        ctx->Map.pci[ 2 ] < RtemsReqAction2_Pre_C_NA;
        ++ctx->Map.pci[ 2 ]
      ) {
        ctx->Map.entry = RtemsReqAction2_PopEntry( ctx );

        if ( ctx->Map.entry.Skip ) {
          continue;
        }

        RtemsReqAction2_SetPreConditionStates( ctx );
        RtemsReqAction2_TestVariant( ctx );
      }
    }
  }
}

/** @} */
