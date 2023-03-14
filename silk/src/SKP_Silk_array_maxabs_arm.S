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

#if defined(__arm__)

#include "SKP_Silk_AsmPreproc.h"

#if EMBEDDED_ARM>=5

	VARDEF ptr_vec, r0
	VARDEF val_vec, r2
	VARDEF val_return, r0
	VARDEF len, r1
	VARDEF val1_max, r3
	VARDEF val2_max, r4
	VARDEF val_lvl, r5
	VARDEF val_ind, r6

	VARDEF const_int16_MAX, r5

.globl	SYM(SKP_Silk_int16_array_maxabs)
SYM(SKP_Silk_int16_array_maxabs):
	stmdb	sp!,  {r4-r6, fp, ip, lr}
	add		fp, sp, #20

	cmp		r1, #6
	mvn		r5, #0						/*r5 = -1(max)*/
	blt		LR(7, f)
	ands	r2, r0, #3
	bne		LR(3, f)
	ands	r2, r1, #0x1
	bne		LR(1, f)	
	
	ldr		val_vec, [ptr_vec], #4
	sub		len, len, #2
L(0)
	smulbb	val1_max, val_vec, val_vec
	smultt	val2_max, val_vec, val_vec
	ldr		val_vec, [ptr_vec], #4
	cmp		val1_max, r5
	movge	val_lvl, val1_max
#ifdef _WINRT
	subge	val_ind, ptr_vec, #4					/*address*/
	subge	val_ind, val_ind, #4					/*address*/
#else	
	subge	val_ind, ptr_vec, #8					/*address*/
#endif
	cmp		val2_max, val_lvl
	movge	val_lvl, val2_max
	subge	val_ind, ptr_vec, #6						
	subs	len, len, #2
	bgt		LR(0, b)
	smulbb	val1_max, val_vec, val_vec
	smultt	val2_max, val_vec, val_vec
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #4					/*address*/
	cmp		val2_max, val_lvl
	movge	val_lvl, val2_max
	subge	val_ind, ptr_vec, #2						
	b		LR(9, f)
/*Odd number of iterations*/	
L(1)
	ldr		val_vec, [ptr_vec], #4
	sub		len, len, #3
L(2)
	smulbb	val1_max, val_vec, val_vec
	smultt	val2_max, val_vec, val_vec
	ldr		val_vec, [ptr_vec], #4
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
#ifdef _WINRT
	subge	val_ind, ptr_vec, #4					/*address*/
	subge	val_ind, val_ind, #4					/*address*/
#else		
	subge	val_ind, ptr_vec, #8					/*address*/
#endif	
	cmp		val2_max, val_lvl
	movge	val_lvl, val2_max
	subge	val_ind, ptr_vec, #6						
	subs	len, len, #2
	bgt		LR(2, b)
	smulbb	val1_max, val_vec, val_vec
	smultt	val2_max, val_vec, val_vec
	ldrsh	val_vec, [ptr_vec], #2
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #6					/*address*/
	smulbb	val1_max, val_vec, val_vec
	cmp		val2_max, val_lvl
	movge	val_lvl, val2_max
	subge	val_ind, ptr_vec, #4
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #2					/*address*/
	b		LR(9, f)						
/*Oddly aligned*/
L(3)
	ands	r2, r1, #0x1
	bne		LR(5, f)
	
	ldrsh	val_vec, [ptr_vec], #2
	smulbb	val1_max, val_vec, val_vec
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #2
	ldr		val_vec, [ptr_vec], #4
	sub		len, len, #4
L(4)
	smulbb	val1_max, val_vec, val_vec
	smultt	val2_max, val_vec, val_vec
	ldr		val_vec, [ptr_vec], #4
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
#ifdef _WINRT
	subge	val_ind, ptr_vec, #4					/*address*/
	subge	val_ind, val_ind, #4					/*address*/
#else		
	subge	val_ind, ptr_vec, #8					/*address*/
#endif	
	cmp		val2_max, val_lvl
	movge	val_lvl, val2_max
	subge	val_ind, ptr_vec, #6						
	subs	len, len, #2
	bgt		LR(4, b)
	smulbb	val1_max, val_vec, val_vec
	smultt	val2_max, val_vec, val_vec
	ldrsh	val_vec, [ptr_vec], #2
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #6					/*address*/
	smulbb	val1_max, val_vec, val_vec
	cmp		val2_max, val_lvl
	movge	val_lvl, val2_max
	subge	val_ind, ptr_vec, #4
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #2					/*address*/
	b		LR(9, f)
/*Odd number of iterations+Oddly aligned*/
L(5)	
	ldrsh	val_vec, [ptr_vec], #2
	smulbb	val1_max, val_vec, val_vec
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #2
	ldr		val_vec, [ptr_vec], #4
	sub		len, len, #3
L(6)
	smulbb	val1_max, val_vec, val_vec
	smultt	val2_max, val_vec, val_vec
	ldr		val_vec, [ptr_vec], #4
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
#ifdef _WINRT
	subge	val_ind, ptr_vec, #4					/*address*/
	subge	val_ind, val_ind, #4					/*address*/
#else		
	subge	val_ind, ptr_vec, #8					/*address*/
#endif	
	cmp		val2_max, val_lvl
	movge	val_lvl, val2_max
	subge	val_ind, ptr_vec, #6						
	subs	len, len, #2
	bgt		LR(6, b)
	smulbb	val1_max, val_vec, val_vec
	smultt	val2_max, val_vec, val_vec
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #4					/*address*/
	cmp		val2_max, val_lvl
	movge	val_lvl, val2_max
	subge	val_ind, ptr_vec, #2
	b		LR(9, f)
/*Less than 6 iterations*/	
L(7)	
	ldrsh	val_vec, [ptr_vec], #2
	sub		len, len, #1	
L(8)
	smulbb	val1_max, val_vec, val_vec
	ldrsh	val_vec, [ptr_vec], #2
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #4
	subs	len, len, #1
	bgt		LR(8, b)
	smulbb	val1_max, val_vec, val_vec
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #2
L(9)	
	ldrsh	val_return, [val_ind]
	mvn		const_int16_MAX, #0x80000000
	mov		const_int16_MAX, const_int16_MAX, asr #16
	cmp		val_return, #0
	rsblt	val_return, val_return, #0
	cmp		val_return, const_int16_MAX
	movge	val_return, const_int16_MAX
	
	ldmia	sp!,  {r4-r6, fp, ip, pc}

#elif EMBEDDED_ARM>=4	



	VARDEF ptr_vec, r0
	VARDEF val1_vec, r2
	VARDEF val2_vec, r7
	VARDEF len, r1
	VARDEF val1_max, r3
	VARDEF val2_max, r8
	VARDEF val_lvl, r5
	VARDEF val_ind, r6

	VARDEF val_return, r0
	VARDEF const_int16_MAX, r5

.globl	SYM(SKP_Silk_int16_array_maxabs)
SYM(SKP_Silk_int16_array_maxabs):
	stmdb	sp!,  {r4-r8, fp, ip, lr}
	add		fp, sp, #28
	
	mvn		val_lvl, #0						/*r5 = -1(max)*/

	ldrsh	val1_vec, [ptr_vec], #2
	ldrsh	val2_vec, [ptr_vec], #2
	sub		len, len, #2	
L(0)
	mul		val1_max, val1_vec, val1_vec
	mul		val2_max, val2_vec, val2_vec
	ldrsh	val1_vec, [ptr_vec], #2
	ldrsh	val2_vec, [ptr_vec], #2
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #8
	cmp		val2_max, val_lvl
	movge	val_lvl, val2_max
	subge	val_ind, ptr_vec, #6
	subs	len, len, #2
	bgt		LR(0, b)
	mul		val1_max, val1_vec, val1_vec
	mul		val2_max, val2_vec, val2_vec
	cmp		val1_max, val_lvl
	movge	val_lvl, val1_max
	subge	val_ind, ptr_vec, #4
	cmn		len, #1						/*r1?=-1*/
	beq		LR(1, f)
	cmp		val2_max, val_lvl
	movge	val_lvl, val2_max
	subge	val_ind, ptr_vec, #2
L(1)	
	ldrsh	val_return, [val_ind]
	mvn		const_int16_MAX, #0x80000000
	mov		const_int16_MAX, const_int16_MAX, asr #16
	cmp		val_return, #0
	rsblt	val_return, val_return, #0
	cmp		val_return, const_int16_MAX
	movge	val_return, const_int16_MAX
	
	ldmia	sp!,  {r4-r8, fp, ip, pc}
	
#endif
	END
#endif
