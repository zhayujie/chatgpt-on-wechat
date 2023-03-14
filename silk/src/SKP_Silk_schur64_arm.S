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
#if EMBEDDED_ARM>=6

	VARDEF ptr_rc, r4
	VARDEF ptr_C0, r3
	VARDEF val_C0, _r7

	VARDEF ptr_C1, _r7
	VARDEF val_a32, r0
	VARDEF val_b32, r1
	VARDEF val_a32_tmp, r2
	VARDEF val_b32_tmp, r3
	VARDEF a_headrm, r0
	VARDEF b_headrm, r1


	VARDEF a32_nrm, r5
	VARDEF b32_nrm, sl
	VARDEF headrm_tmp, r8
	VARDEF result, r1
	VARDEF tmp0, r2
	VARDEF lshift, r3

	VARDEF rc_tmp_Q31, r0
	VARDEF tmp1, r1
	VARDEF val_rc, r2

	VARDEF ptr_C2, r8
	VARDEF ptr_C3, sb
	VARDEF val_C2, r1
	VARDEF val_C3, r2
	VARDEF out_C2, r5
	VARDEF out_C3, sl

	VARDEF order1, r6
	VARDEF order2, r3

	EXTERN SYM(SKP_DIV32_arm)
.set	sp_ptr_C, 0 
.globl	SYM(SKP_Silk_schur64)
SYM(SKP_Silk_schur64):
	stmdb	sp!,  {r4-r10, fp, ip, lr}
	add		fp, sp, #36
	sub		sp, sp, #136

	mov		ptr_rc, r0							/*rc_Q16*/
	mov		order1, r2							/*order*/
	
	mov		ptr_C0, sp
	ldr		val_C0, [r1], #4
L(0)
	subs	r2, r2, #1
	str		val_C0, [ptr_C0], #4
	str		val_C0, [ptr_C0], #4
	ldr		val_C0, [r1], #4
	bgt		LR(0, b)
	str		val_C0, [ptr_C0], #4
	str		val_C0, [ptr_C0], #4
	add		ptr_C1, sp, #8
L(1)
	ldr		val_a32, [ptr_C1], #8
	ldr		val_b32, [sp, #4]
	rsb		val_a32, val_a32, #0				/*-C[k + 1][0]*/
	mov		val_a32_tmp, val_a32				/*a32*/
	mov		val_b32_tmp, val_b32				/*b32*/
	cmp		val_a32, #0
	rsblt	val_a32, val_a32_tmp, #0			/*a_headrm*/ 
	clz		a_headrm, val_a32
	cmp		val_b32, #0
	rsblt	val_b32, val_b32_tmp, #0			/*b_headrm*/
	clz		b_headrm, val_b32
	sub		a_headrm, a_headrm, #1
	sub		b_headrm, b_headrm, #1
	mov		a32_nrm, val_a32_tmp, lsl a_headrm	/*a32_nrm*/
	mov		b32_nrm, val_b32_tmp, lsl b_headrm	/*b32_nrm*/
	sub		headrm_tmp, a_headrm, b_headrm		/*a_headrm - b_headrm*/
	
	mvn		r0, #0x80000000						/*r0 = 0x7FFF FFFF*/
	mov		r1, b32_nrm, asr #16				/*SKP_RSHIFT(b32_nrm, 16)*/
	mov		r0, r0, asr #2
//      registers need to preserve: ptr_rc  (r4)
//                                  a32_nrm (r5)
//                                  order1  (r6)
//                                  ptr_C1  (r7)
//                                  headrm_tmp (r8)
//                                  b32_nrm (sl)
    bl		SYM(SKP_DIV32_arm)
	smulwb	result, a32_nrm, r0					/*result = SKP_SMULWB(a32_nrm, b32_inv);*/
	
	smmul	tmp0, b32_nrm, result				/*SKP_SMMUL(b32_nrm, result)*/
	sub		a32_nrm, a32_nrm, tmp0, lsl #3		/*a32_nrm -= SKP_LSHIFT_ovflw( SKP_SMMUL(b32_nrm, result), 3 );*/
	smlawb	result, a32_nrm, r0, result			/*result = SKP_SMLAWB(result, a32_nrm, b32_inv);*/
	
	subs	lshift, headrm_tmp, #2				/*lshift= 29 + a_headrm - b_headrm - Qres;*/
	rsble	lshift, lshift, #0
#ifdef _WINRT
	bgt		LR(3, f)
	mov		rc_tmp_Q31, result, lsl lshift
	b		LR(4, f)
L(3)	
	mov		rc_tmp_Q31, result, asr lshift
L(4)	
#else	
	movle	rc_tmp_Q31, result, lsl lshift
	movgt	rc_tmp_Q31, result, asr lshift
#endif	
	
	mov		tmp1, rc_tmp_Q31, asr #14			/*SKP_RSHIFT_ROUND( rc_tmp_Q31, 15 )*/
	add		val_rc, tmp1, #1
	mov		val_rc, val_rc, asr #1
	str		val_rc, [ptr_rc], #4

	mov		order2, order1						/*order-k*/
	sub		ptr_C2, ptr_C1, #8					/*r8 = &C[k+1][0]*/
	add		ptr_C3, sp, #4						/*sb = &C[0][1]*/
L(2)	
	ldr		val_C2, [ptr_C2]
	ldr		val_C3, [ptr_C3]
	subs	order2, order2, #1
	mov		out_C2, val_C2, lsl #1
	mov		out_C3, val_C3, lsl #1
	smmul	out_C2, out_C2, rc_tmp_Q31
	smmul	out_C3, out_C3, rc_tmp_Q31
	add		out_C2, out_C2, val_C3
	add		out_C3, out_C3, val_C2
	str		out_C2, [ptr_C3], #8
	str		out_C3, [ptr_C2], #8
	bgt		LR(2, b)
	subs	order1, order1, #1
	bgt		LR(1, b)
		
	ldr		r0, [sp, #4]						/*r0 = C[0][1]*/

	add		sp, sp, #136
	ldmia	sp!,  {r4-r10, fp, ip, pc}
	END	
#endif

#endif

