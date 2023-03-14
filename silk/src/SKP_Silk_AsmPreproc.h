/***********************************************************************
Copyright (c) 2006-2012, Skype Limited. All rights reserved. 
Redistribution and use in source and binary forms, with or without 
modification, (subject to the limitations in the disclaimer below) 
are permitted provided that the following conditions are met:
- Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright 
notice, this list of conditions and the following disclaimer in the 
documentation and/or other materials provided with the distribution.
- Neither the name of Skype Limited, nor the names of specific 
contributors, may be used to endorse or promote products derived from 
this software without specific prior written permission.
NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED 
BY THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
CONTRIBUTORS ''AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE 
COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF 
USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON 
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
***********************************************************************/

/* SKP_Silk_AsmPreProc.h
 * 
 * General header for all ARM asms uses SigProcLib. 
 * It contains C preprocessor part and asm preprocessor part.
 * C preprocessor part: 
 *		* Interfacing makefile, arch, fpu and neon support
 *      * Interfacing different symbol styles and asm directives.
 *		* Interfacing compiling time standard output
 * ASM preprocessor part:
 *		* Defining general asm header/footer for stack/return value
 *		* Allocating stack for local variables and nasted function
 *		* Defining simple syntax checking and debugging routines
 */ 


/*
 * C preprocessor part
 */
#ifndef _SKP_ASM_PREPROC_H_
#define _SKP_ASM_PREPROC_H_

#include "SKP_Silk_AsmHelper.h"


/* Checking compilier __ARMEL__ defines */
#if !__ARMEL__ && (!defined(NO_ASM)) && (!defined(_WINRT))
#error	Currently SKP_Silk_AsmPreProc only supports little endian.
// above line can be replaced by 
// #warning	__ARMEL__=0
// #define NOASM
#endif

/* Defining macro for different user label prefix. */                               
#ifndef __USER_LABEL_PREFIX__
#define __USER_LABEL_PREFIX__
#endif

#define CONCAT1(a, b) CONCAT2(a, b)
#define CONCAT2(a, b) a ## b

#define SYM(x) CONCAT1 (__USER_LABEL_PREFIX__, x)

/* Remapping register for iphone. */

#ifdef IPHONE
#	define _fp r7
#	define _r7 r11
#else
#	define _fp fp
#	define _r7 r7
#endif

/* Checking compiler __ARM_EABI__ defines */

#if __ARMEB__
#define NO_ASM			//remove asm optimization for ARM big endian.
#else
#define ARM_LITTLE_ENDIAN
#endif

/* Interfacing some asm directives to macros*/
#define 	GBL		.globl

/* Legacy definition wrapper */
#ifndef	NO_ASM
#if defined (__ARM_ARCH_4__) || defined (__ARM_ARCH_4T__) || defined (__ARM_ARCH_5__) || defined (__ARM_ARCH_5T__)
#define EMBEDDED_ARM 4
#define EMBEDDED_ARMv4
#elif  defined (__ARM_ARCH_5TE__) || defined (__ARM_ARCH_5TEJ__)
#define EMBEDDED_ARM 5
#define EMBEDDED_ARMv5
#elif defined (__ARM_ARCH_6__) ||defined (__ARM_ARCH_6J__) || defined (__ARM_ARCH_6Z__) || defined (__ARM_ARCH_6K__) || defined(__ARM_ARCH_6ZK__) || defined(__ARM_ARCH_6T2__)
#define EMBEDDED_ARM 6
#define EMBEDDED_ARMv6
#elif defined (__ARM_ARCH_7A__) && defined (__ARM_NEON__)
#define EMBEDDED_ARM 7
#define EMBEDDED_ARMv6
#elif defined (__ARM_ARCH_7A__)
#define EMBEDDED_ARM 6
#define EMBEDDED_ARMv6
#endif
#endif

#ifdef _WINRT
#define L(a)	a
#define LR(a,d)	%##d##a

#define TABLE(L, symbol) symbol
#else
#define L(a) 	a:
#define LR(a,d)	a##d
#define DCD	.long
#define DCW	.short
#define TABLE(L, symbol) L
#endif

#ifdef _WINRT
#define streqh strheq
#define strneh strhne
#define strgth strhgt
#define strlth strhlt
#define ldrgtsh ldrshgt
#define ldmgtia ldmiagt
#define ldmgtdb ldmdbgt
#define ldrneh ldrhne
#define ldmltia ldmialt
#endif
/*
 *	ASM preprocessor part:
 */

#ifdef _WINRT
#else
//	AT&T Format
#if EMBEDDED_ARM >= 7
.set	_ARCH, 7
#elif EMBEDDED_ARM >= 6
.set	_ARCH, 6
#elif EMBEDDED_ARM >= 5	// Should be re-considerred as ARMv5 != ARMv5E
.set	_ARCH, 5
#elif EMBEDDED_ARM >= 4
.set	_ARCH, 4
#else
.set	_ARCH, 0
#endif

#if NEON
.set	_NEON, 1
#else
.set	_NEON, 0
#endif

MACRO	SKP_TABLE  ARG0_in, ARG1_in
SYM(ARG0):
END_MACRO



MACRO SKP_SMLAD	ARG0_in, ARG1_in, ARG2_in, ARG3_in
#if EMBEDDED_ARM>=6
	smlad	ARG0, ARG1, ARG2, ARG3
#elif EMBEDDED_ARM>=5
	smlabb	ARG0, ARG1, ARG2, ARG3
	smlatt	ARG0, ARG1, ARG2, ARG0
#else
	.abort "SKP_SMUAD can't be used for armv4 or lower device.."
#endif
END_MACRO

MACRO SKP_SMUAD	ARG0_in, ARG1_in, ARG2_in
#if EMBEDDED_ARM>=6
	smuad	ARG0, ARG1, ARG2
#elif EMBEDDED_ARM>=5
	smulbb	ARG0, ARG1, ARG2
	smlatt	ARG0, ARG1, ARG2, ARG0
#else
	.abort "SKP_SMUAD can't be used for armv4 or lower device.."
#endif
END_MACRO

MACRO SKP_SMLALD	ARG0_in, ARG1_in, ARG2_in, ARG3_in
#if EMBEDDED_ARM>=6
	smlald	ARG0, ARG1, ARG2, ARG3
#elif EMBEDDED_ARM>=5
	smlalbb	ARG0, ARG1, ARG2, ARG3
	smlaltt	ARG0, ARG1, ARG2, ARG3
#else
	.abort "SKP_SMLALD can't be used for armv4 or lower device.."
#endif
END_MACRO

MACRO SKP_RSHIFT_ROUND ARG0_in, ARG1_in, ARG2_in
#if EMBEDDED_ARM>=4
	mov		ARG0, ARG1, asr #(ARG2-1)
	add		ARG0, ARG0, #1
	mov		ARG0, ARG0, asr #1
#else
	.abort "SKP_RSHIFT_ROUND can't be used for armv3 or lower device.."
#endif
END_MACRO

MACRO ADD_SHIFT ARG0_in, ARG1_in, ARG2_in, ARG3_in, ARG4_in
		add ARG0, ARG1, ARG2, ARG3 ARG4
END_MACRO

MACRO POST_IR 	ARG0_in, ARG1_in, ARG2_in, ARG3_in
		ARG0 ARG1, [ARG2], ARG3
END_MACRO

#endif
#endif //_SKP_ASM_PREPROC_H_
