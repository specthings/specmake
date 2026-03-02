/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup FooGroup
 *
 * @brief This header file declares various C constructs with Doxygen
 * comments.
 *
 * This file contains examples of functions, macros, typedefs, defines,
 * structs, unions, and enums with Doxygen comments. Some of these are group
 * members, and some are not.
 */

/*
 * Copyright (c) 2024, 2025 embedded brains GmbH & Co. KG
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

#ifndef HEADER_H
#define HEADER_H

/**
 * @defgroup FooGroup Example Group
 *
 * @brief This group contains example items.
 * @{
 */

/**
 * @brief Brief gf_0().
 *
 * Description gf_0().
 *
 * @param[in] in gf_0() in description.
 *
 * @param[out] out gf_0() out description.
 *
 * @param[in,out] inout gf_0() inout description.
 *
 * @param none gf_0() none description.
 *
 * @return gf_0() return description.
 *
 * @retval retval gf_0() retval description.
 */
int gf_0(const int *in, int *out, int *inout, int none);

/**
 * @brief Brief gf_1().
 *
 * Description gf_1().
 */
void gf_1(void);

/**
 * @brief Brief gf_2().
 *
 * Description gf_2().
 *
 * @param[in] x gf_2() x description.
 *
 * @param[in] y gf_2() y description.
 *
 * @return gf_2() return description.
 *
 * @retval retval gf_2() retval description.
 */
static inline int gf_2(int x, int y)
{
  return x + y;
}

/* No doxygen comment.  */
void gf_3(int x, int y);

/**
 * @brief Brief gf_4().
 *
 * Description gf_4().
 *
 * @param[in] in gf_4() in description.
 *
 * @param[out] out gf_4() out description.
 *
 * @return gf_4() return description.
 */
int gf_4(const int *in, int *out);

/**
 * @brief Brief GM_0().
 *
 * Description GM_0().
 *
 * @param[in] a GM_0() a description.
 *
 * @param[in] b GM_0() b description.
 *
 * @return GM_0() return description.
 */
#define GM_0(a, b) ((a) > (b) ? (a) : (b))

/**
 * @brief Brief GD_1.
 */
#define GD_1 4096

/**
 * @brief Brief gt_0.
 *
 * Description gt_0.
 */
typedef struct {
  int x;
  int y;
} gt_0;

/**
 * @brief Brief gs_0.
 *
 * Description gs_0.
 */
struct gs_0 {
  int a;
  int b;
};

/**
 * @brief Brief gu_0.
 *
 * Description gu_0.
 */
typedef union {
  int i;
  float f;
} gu_0;

/**
 * @brief Brief gu_1.
 *
 * Description gu_1.
 */
union gu_1 {
  int i;
  float f;
};

/**
 * @brief Brief ge_0.
 *
 * Description ge_0.
 */
typedef enum {
  /**
   * @brief Brief GE_0_A.
   *
   * Description GE_0_A.
   */
  GE_0_A,

  /**
   * @brief Brief GE_0_B.
   *
   * Description GE_0_B.
   */
  GE_0_B,

  /**
   * @brief Brief GE_0_C.
   *
   * Description GE_0_C.
   */
  GE_0_C
} ge_0;

/** @} */

/**
 * @brief Brief f_0().
 *
 * Description f_0().
 *
 * @param[in] in f_0() in description.
 *
 * @param[out] out f_0() out description.
 *
 * @param[in,out] inout f_0() inout description.
 *
 * @param none f_0() none description.
 *
 * @param f f_0() function pointer description.
 *
 * @return
 * - f_0() return description list item 0
 * - f_0() return description list item 1
 *
 * @retval retval f_0() retval description.
 */
int f_0(const int *in, int *out, int *inout, int none, int *(*f)(int i, int *, int *(*f2)(void)));

/**
 * @brief Brief f_1().
 *
 * Description f_1().
 */
void f_1(void);

/**
 * @brief Brief f_2().
 *
 * Description f_2().
 *
 * @param[in] x f_2() x description.
 *
 * @param[in] y f_2() y description.
 *
 * @return f_2() return description.
 *
 * @retval retval f_2() retval description.
 */
static inline int f_2(int x, int y)
{
  return x + y;
}

/**
 * @brief Brief M_0().
 *
 * Description M_0().
 *
 * @param[in] a M_0() a description.
 *
 * @param[in] b M_0() b description.
 *
 * @return M_0() return description.
 */
#define M_0(a, b) ((a) < (b) ? (a) : (b))

/**
 * @brief Brief D_1.
 */
#define D_1 1024

/**
 * @brief Brief t_0.
 *
 * Description t_0.
 */
typedef struct {
  int x;
  int y;
} t_0;

/**
 * @brief Brief s_0.
 *
 * Description s_0.
 */
struct s_0 {
  int a;
  int b;
};

/**
 * @brief Brief u_0.
 *
 * Description u_0.
 */
typedef union {
  char c;
  int i;
} u_0;

/**
 * @brief Brief u_1.
 *
 * Description u_1.
 */
union u_1 {
  char c;
  int i;
};

/**
 * @brief Brief e_0.
 *
 * Description e_0.
 */
typedef enum e_0 {
  /**
   * @brief Brief E_0_A.
   *
   * Description E_0_A.
   */
  E_0_A
} e_0;

/**
 * @brief Brief e_1.
 *
 * Description e_1.
 */
enum e_1 {
  /**
   * @brief Brief E_1_A.
   *
   * Description E_1_A.
   */
  E_1_A
};

#endif /* HEADER_H */
