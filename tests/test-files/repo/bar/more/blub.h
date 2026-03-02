/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup Blub
 *
 * @brief Brief.
 */

/*
 * Copyright (C) 2023, 2026 embedded brains GmbH & Co. KG
 * Copyright (C) 2023 Bob
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

/* Generated from spec:/rtems/if/header */

#ifndef _BLUB_H
#define _BLUB_H

#include <bar/more/unspec.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Generated from spec:/rtems/if/group */

/**
 * @defgroup Blub Blub
 *
 * @brief Brief.
 *
 * Description.
 */

#if 0
  /* Generated from spec:/rtems/if/group-disabled */

  /**
   * @defgroup Blub Blub
   *
   * @brief Brief.
   *
   * Description.
   */
#endif

#if 0
  /* Generated from spec:/rtems/if/define-disabled */

  /**
   * @ingroup Blub
   *
   * @brief Disabled define brief.
   *
   * Disabled define description.
   */
  #define DISABLED 123
#endif

/* Generated from spec:/rtems/if/define-not-defined */

/**
 * @ingroup Blub
 *
 * @brief Define not defined brief.
 *
 * Define not defined description.
 */
#if 0
  #define DEFINE_NOT_DEFINED 321
#endif

/* Generated from spec:/rtems/if/define-real */

/**
 * @ingroup Blub
 *
 * @brief Define brief.
 *
 * Define description.
 */
#if 1
  #define BLUB 123
#endif

/* Generated from spec:/rtems/if/define-third-duplicate */

/**
 * @ingroup Blub
 *
 * @brief Define brief.
 *
 * Define description.
 */
#define BLUB 123

#if 0
  /* Generated from spec:/rtems/if/enum-disabled */

  /**
   * @ingroup Blub
   *
   * @brief Enum brief.
   *
   * Description.
   */
  typedef enum {
    /**
     * @brief Enumerator brief.
     *
     * Description.
     */
    ENUMERATOR
  } the_enum;
#endif

/* Generated from spec:/rtems/if/enum-duplicate */

/**
 * @ingroup Blub
 *
 * @brief Enum brief.
 *
 * Description.
 */
typedef enum {
  /**
   * @brief Enumerator brief.
   *
   * Description.
   */
  ENUMERATOR
} the_enum;

/* Generated from spec:/rtems/if/enum-real */

/**
 * @ingroup Blub
 *
 * @brief Enum brief.
 *
 * Description.
 */
typedef enum {
  /**
   * @brief Enumerator brief.
   *
   * Description.
   */
  ENUMERATOR,

  /**
   * @brief Enumerator 2 brief.
   *
   * Description 2.
   */
  ENUMERATOR_2 = 2
} the_enum;

/* Generated from spec:/rtems/if/func */

/**
 * @ingroup Blub
 *
 * @brief Brief.
 *
 * @param param Parameter.
 *
 * Description.
 *
 * @return Returns.
 */
static inline int blub( int param )
{
  return param;
}

#if 0
  /* Generated from spec:/rtems/if/func-disabled */

  /**
   * @ingroup Blub
   *
   * @brief Brief.
   *
   * Description.
   */
  void disabled( void );
#endif

/* Generated from spec:/rtems/if/obj */

/**
 * @ingroup Blub
 *
 * @brief The obj brief.
 *
 * Description.
 */
extern int obj;

/* Generated from spec:/rtems/if/reg-block-2 */

/**
 * @defgroup RegBlock2 Reg Block 2
 *
 * @ingroup Blub
 *
 * @brief This group contains the Reg Block 2 interfaces.
 *
 * @{
 */

/**
 * @defgroup RegBlock2REGBLOCK2A REG_BLOCK_2_A bits. (REG_BLOCK_2_A)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

#define REGBLOCK2_REG_BLOCK_2_A_BITS_A_SHIFT 0
#define REGBLOCK2_REG_BLOCK_2_A_BITS_A_MASK 0xffffffffU
#define REGBLOCK2_REG_BLOCK_2_A_BITS_A_GET( _reg ) \
  ( ( ( _reg ) & REGBLOCK2_REG_BLOCK_2_A_BITS_A_MASK ) >> \
    REGBLOCK2_REG_BLOCK_2_A_BITS_A_SHIFT )
#define REGBLOCK2_REG_BLOCK_2_A_BITS_A_SET( _reg, _val ) \
  ( ( ( _reg ) & ~REGBLOCK2_REG_BLOCK_2_A_BITS_A_MASK ) | \
    ( ( ( _val ) << REGBLOCK2_REG_BLOCK_2_A_BITS_A_SHIFT ) & \
      REGBLOCK2_REG_BLOCK_2_A_BITS_A_MASK ) )
#define REGBLOCK2_REG_BLOCK_2_A_BITS_A( _val ) \
  ( ( ( _val ) << REGBLOCK2_REG_BLOCK_2_A_BITS_A_SHIFT ) & \
    REGBLOCK2_REG_BLOCK_2_A_BITS_A_MASK )

/** @} */

/**
 * @defgroup RegBlock2REGBLOCK2B REG_BLOCK_2_B bits. (REG_BLOCK_2_B)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

#define REGBLOCK2_REG_BLOCK_2_B_BITS_B_SHIFT 27
#define REGBLOCK2_REG_BLOCK_2_B_BITS_B_MASK 0xf8000000U
#define REGBLOCK2_REG_BLOCK_2_B_BITS_B_GET( _reg ) \
  ( ( ( _reg ) & REGBLOCK2_REG_BLOCK_2_B_BITS_B_MASK ) >> \
    REGBLOCK2_REG_BLOCK_2_B_BITS_B_SHIFT )
#define REGBLOCK2_REG_BLOCK_2_B_BITS_B_SET( _reg, _val ) \
  ( ( ( _reg ) & ~REGBLOCK2_REG_BLOCK_2_B_BITS_B_MASK ) | \
    ( ( ( _val ) << REGBLOCK2_REG_BLOCK_2_B_BITS_B_SHIFT ) & \
      REGBLOCK2_REG_BLOCK_2_B_BITS_B_MASK ) )
#define REGBLOCK2_REG_BLOCK_2_B_BITS_B( _val ) \
  ( ( ( _val ) << REGBLOCK2_REG_BLOCK_2_B_BITS_B_SHIFT ) & \
    REGBLOCK2_REG_BLOCK_2_B_BITS_B_MASK )

/** @} */

/**
 * @brief This structure defines the Reg Block 2 register block memory map.
 */
typedef struct reg_block_2 {
  /**
   * @brief See @ref RegBlock2REGBLOCK2A.
   */
  uint32_t reg_block_2_a;

  /**
   * @brief See @ref RegBlock2REGBLOCK2B.
   */
  uint32_t reg_block_2_b;

  uint32_t reserved_8_10[ 2 ];
} reg_block_2;

/** @} */

/* Generated from spec:/rtems/if/reg-block */

/**
 * @defgroup RegBlock Reg Block
 *
 * @ingroup Blub
 *
 * @brief This group contains the Reg Block interfaces.
 *
 * @{
 */

/**
 * @defgroup RegBlockREGBLOCKA REG_BLOCK_A bits. (REG_BLOCK_A)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

#define REG_BLOCK_REG_BLOCK_A_BIT_A 0x2U

/** @} */

/**
 * @defgroup RegBlockREGBLOCKB REG_BLOCK_B bits. (REG_BLOCK_B)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

/** @} */

/**
 * @brief This structure defines the Reg Block register block memory map.
 */
typedef struct reg_block {
  /**
   * @brief See @ref RegBlockREGBLOCKA.
   */
  uint32_t reg_block_a;

  /**
   * @brief See @ref RegBlockREGBLOCKB.
   */
  uint8_t reg_block_b[ 4 ];

  uint32_t reserved_8_100[ 62 ];

  /**
   * @brief See @ref RegBlock2.
   */
  reg_block_2 reg_block_2[ 16 ];

  uint32_t reserved_200_400[ 128 ];
} reg_block;

/** @} */

/* Generated from spec:/rtems/if/struct */

/**
 * @ingroup Blub
 *
 * @brief The Struct brief.
 *
 * Description.
 */
typedef struct {
  #if 0
    /**
     * @brief The disabled Struct member.
     *
     * Description.
     */
    int b;
  #elif 1
    /**
     * @brief The Struct member.
     */
    int a;
  #endif

  #if 0
    /**
     * @brief The other disabled Struct member.
     *
     * Description.
     */
    int c;
  #endif
} Struct;

/* Generated from spec:/rtems/if/struct-both */

/**
 * @ingroup Blub
 *
 * @brief The StructBoth brief.
 *
 * Description.
 */
typedef struct StructBoth {
  /**
   * @brief The StructBoth member.
   *
   * Description.
   */
  int a;
} StructBoth;

/* Generated from spec:/rtems/if/struct-only */

/**
 * @ingroup Blub
 *
 * @brief The StructOnly brief.
 *
 * Description.
 */
struct StructOnly {
  /**
   * @brief The StructOnly member.
   *
   * Description.
   */
  int a;
};

/* Generated from spec:/rtems/if/typedef */

/**
 * @ingroup Blub
 *
 * @brief Typedef brief.
 */
typedef int Typedef;

/* Generated from spec:/rtems/if/union */

/**
 * @ingroup Blub
 *
 * @brief The Union brief.
 *
 * Description.
 */
typedef union {
  /**
   * @brief The Union member.
   *
   * Description.
   */
  int a;
} Union;

/* Generated from spec:/rtems/if/union-both */

/**
 * @ingroup Blub
 *
 * @brief The UnionBoth brief.
 *
 * Description.
 */
typedef union UnionBoth {
  /**
   * @brief The UnionBoth member.
   *
   * Description.
   */
  int a;
} UnionBoth;

/* Generated from spec:/rtems/if/union-only */

/**
 * @ingroup Blub
 *
 * @brief The UnionOnly brief.
 *
 * Description.
 */
union UnionOnly {
  /**
   * @brief The UnionOnly member.
   *
   * Description.
   */
  int a;
};

#ifdef __cplusplus
}
#endif

#endif /* _BLUB_H */
