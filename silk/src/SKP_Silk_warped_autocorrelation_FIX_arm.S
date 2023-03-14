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
#define QC  10
#define QS  14

#include "SKP_Silk_AsmPreproc.h"


#if ( EMBEDDED_ARM >= 6 )
	VARDEF tmp1_QS, r4
	VARDEF length, r5
	VARDEF state_QS_ptr, r6
	VARDEF val_i, _r7
	VARDEF tmp3, r8
	VARDEF tmp4, sb
	VARDEF corr_QC_ptr, sl

	VARDEF state_QS1, ip
	VARDEF state_QS2, lr


	VARDEF ret0, r0
	VARDEF ret1, r1
	VARDEF state_QS0, r2
	VARDEF warping_Q16, r3

.set	sp_state_QS, 0 
.set	sp_corr_QS, 68 
.set	sp_corr_ptr, 204 
.set	sp_scale_ptr, 208 
.set	sp_input_ptr, 212 
.globl	SYM(SKP_Silk_warped_autocorrelation_FIX)
SYM(SKP_Silk_warped_autocorrelation_FIX):
	stmdb	sp!,  {r4-r10, fp, ip, lr}
	add		fp, sp, #36
	sub		sp, sp, #216
.set	ptr_length, 256 
.set	ptr_order, 260 
.set	ptr_tmp1_QS, 264 
.set	ptr_state_QS, 268 
.set	ptr_corr_QC, 272 

	
	str		r0, [sp, #sp_corr_ptr]
	str		r1, [sp, #sp_scale_ptr]
	add		state_QS_ptr, sp, #sp_state_QS
	add 		corr_QC_ptr, sp, #sp_corr_QS
	mov		r4, #0
	mov		r5, #0
	mov		_r7, #17
L(2)
	subs		_r7, _r7, #1
	str		r4, [state_QS_ptr], #4
	stmia		corr_QC_ptr!, {r4, r5}
	bgt		LR(2, b)

	ldr		length, [sp, #ptr_length]
/*OUTTER_LOOP*/
L(1)
	ldrsh		tmp1_QS, [r2], #2
	add		state_QS_ptr, sp, #sp_state_QS
	add		corr_QC_ptr, sp, #sp_corr_QS
	ldr		val_i, [sp, #ptr_order]
	str		r2, [sp, #sp_input_ptr]
	mov		tmp1_QS, tmp1_QS, lsl #14

	sub		val_i, val_i, #2
	ldr		state_QS1, [state_QS_ptr], #4
	ldr		state_QS2, [state_QS_ptr], #4
	str		tmp1_QS, [state_QS_ptr, #-8]
	sub		ret0, state_QS2, tmp1_QS
	mov		state_QS0, tmp1_QS
	smull		tmp3, tmp4, tmp1_QS, state_QS0
	smlawb		tmp1_QS, ret0, warping_Q16, state_QS1
	ldmia		corr_QC_ptr, {ret0, ret1}
	mov		tmp3, tmp3, lsr #18
	orr		tmp3, tmp3, tmp4, lsl #14
	adds		ret0, ret0, tmp3
	adc		ret1, ret1, tmp4, asr #18
	stmia		corr_QC_ptr!, {ret0, ret1}
	
	ldr		state_QS1, [state_QS_ptr], #4
	str		tmp1_QS, [state_QS_ptr, #-8]
	sub		ret0, state_QS1, tmp1_QS
	smull		tmp3, tmp4, tmp1_QS, state_QS0
	smlawb		tmp1_QS, ret0, warping_Q16, state_QS2
	ldmia		corr_QC_ptr, {ret0, ret1}
	mov		tmp3, tmp3, lsr #18
	orr		tmp3, tmp3, tmp4, lsl #14
	adds		ret0, ret0, tmp3
	adc		ret1, ret1, tmp4, asr #18
	stmia		corr_QC_ptr!, {ret0, ret1}
/*INNER_LOOP*/
L(0)	
	ldr		state_QS2, [state_QS_ptr], #4
	str		tmp1_QS, [state_QS_ptr, #-8]
	smull		tmp3, tmp4, tmp1_QS, state_QS0
	ldmia		corr_QC_ptr, {ret0, ret1}
	sub		tmp1_QS, state_QS2, tmp1_QS
	smlawb		tmp1_QS, tmp1_QS, warping_Q16, state_QS1
	mov		tmp3, tmp3, lsr #18
	orr		tmp3, tmp3, tmp4, lsl #14
	
	ldr		state_QS1, [state_QS_ptr], #4
	str		tmp1_QS, [state_QS_ptr, #-8]
	adds		ret0, ret0, tmp3
	adc		ret1, ret1, tmp4, asr #18
	stmia		corr_QC_ptr!, {ret0, ret1}
	smull		tmp3, tmp4, tmp1_QS, state_QS0
	ldmia		corr_QC_ptr, {ret0, ret1}
	sub		tmp1_QS, state_QS1, tmp1_QS
	smlawb		tmp1_QS, tmp1_QS, warping_Q16, state_QS2
	mov		tmp3, tmp3, lsr #18
	orr		tmp3, tmp3, tmp4, lsl #14
	adds		ret0, ret0, tmp3
	adc		ret1, ret1, tmp4, asr #18
	subs		val_i, val_i, #2
	stmia		corr_QC_ptr!, {ret0, ret1}
	bgt		LR(0, b)

	str		tmp1_QS, [state_QS_ptr, #-4]
	smull		tmp3, tmp4, tmp1_QS, state_QS0
	ldmia		corr_QC_ptr, {ret0, ret1}
	ldr		r2, [sp, #sp_input_ptr]
	mov		tmp3, tmp3, lsr #18
	orr		tmp3, tmp3, tmp4, lsl #14
	adds		ret0, ret0, tmp3
	adc		ret1, ret1, tmp4, asr #18
	subs		length, length, #1
	stmia		corr_QC_ptr!, {ret0, ret1}
	bgt		LR(1, b)

	ldr		r4, [sp, #sp_corr_ptr]
	ldr		state_QS_ptr, [sp, #sp_scale_ptr]
	add		corr_QC_ptr, sp, #sp_corr_QS
	ldr		val_i, [sp, #ptr_order]
	ldmia		corr_QC_ptr!, {state_QS1, state_QS2}
	cmp		state_QS2, #0
	clz		tmp3, state_QS1
	clz		tmp4, state_QS2
#ifdef _WINRT
	bne		LR(6, f)
	add		tmp4, tmp3, #32
L(6)	
#else
	addeq		tmp4, tmp3, #32
#endif
	sub		tmp4, tmp4, #35
	
	cmn		tmp4, #22
#ifdef _WINRT
	bge		LR(6, f)
	mov		tmp4, #-22
L(6)	
	cmp		tmp4, #20
	ble		LR(6, f)
	mov		tmp4, #20
L(6)	
#else	
	movlt		tmp4, #-22
	cmp		tmp4, #20
	movgt		tmp4, #20
#endif
	add		tmp3, tmp4, #10
	rsb		tmp3, tmp3, #0
	str		tmp3, [state_QS_ptr]
	
	cmp		tmp4, #0
	bge		LR(3, f)
	
	rsb		tmp4, tmp4, #0
	rsb		tmp3, tmp4, #32
	mov		state_QS2, state_QS2, lsl tmp3
	mov		state_QS1, state_QS1, lsr tmp4
	orr		state_QS1, state_QS1, state_QS2
	ldmia		corr_QC_ptr!, {r0, r1, r2, r3}		
	str		state_QS1, [r4], #4
	
L(4)	
	subs		val_i, val_i, #2
	mov		r0, r0, lsr tmp4
#ifdef _WINRT
	mov		state_QS1, r1, lsl tmp3
	orr		state_QS1, r0, state_QS1
#else
	orr		state_QS1, r0, r1, lsl tmp3
#endif
	mov		r2, r2, lsr tmp4
#ifdef _WINRT
	mov		state_QS2, r3, lsl tmp3
	orr		state_QS2, r2, state_QS2
#else
	orr		state_QS2, r2, r3, lsl tmp3
#endif
#ifdef _WINRT
	ble		LR(6, f)
	ldmia		corr_QC_ptr!, {r0, r1, r2, r3}		
	stmia		r4!, {state_QS1, state_QS2}
	b		LR(4, b)
L(6)
	stmia		r4!, {state_QS1, state_QS2}
#else
	ldmgtia		corr_QC_ptr!, {r0, r1, r2, r3}		
	stmia		r4!, {state_QS1, state_QS2}
	bgt		LR(4, b)
#endif	
	add		sp, sp, #216
	ldmia	sp!,  {r4-r10, fp, ip, pc}

L(3)
	mov		state_QS1, state_QS1, lsl tmp4
	ldr		r1, [corr_QC_ptr], #8
	ldr		r3, [corr_QC_ptr], #8
	str		state_QS1, [r4], #4
	
L(5)
	subs		val_i, val_i, #2
	mov		r0, r1, lsl tmp4
	mov		r2, r3, lsl tmp4
#ifdef _WINRT
	ble		LR(6, f)
	ldr		r1, [corr_QC_ptr], #8
	ldr		r3, [corr_QC_ptr], #8
	stmia		r4!, {r0, r2}
	b		LR(5, b)
L(6)
	stmia		r4!, {r0, r2}
#else	
	ldrgt		r1, [corr_QC_ptr], #8
	ldrgt		r3, [corr_QC_ptr], #8
	stmia		r4!, {r0, r2}
	bgt		LR(5, b)
#endif	
	add		sp, sp, #216
	ldmia	sp!,  {r4-r10, fp, ip, pc}
	END
#endif
#endif

