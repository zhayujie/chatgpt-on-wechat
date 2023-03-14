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

#include "SKP_Silk_AsmPreproc.h"


#if ( EMBEDDED_ARM >= 6 )
	VARDEF ptr_state, r0
	VARDEF ptr_res, r1
	VARDEF val_tmp2, r1
	VARDEF val_state0, r1
	VARDEF ptr_coef, r2
	VARDEF ptr_input, r3
	VARDEF val_tmp, r3
	VARDEF val_lambda, r4
	VARDEF val_state1, r5
	VARDEF val_state2, r6
	VARDEF val_tmp1, _r7
	VARDEF val_coef, r8
	VARDEF val_input, sb
	VARDEF val_acc, sl
	VARDEF val_order, ip
	VARDEF val_length, lr


.set	sp_state_ptr, 0 
.set	sp_res_ptr, 4 
.set	sp_coef_Q13_ptr, 8 
.set	sp_input_ptr, 12 
.globl	SYM(SKP_Silk_warped_LPC_analysis_filter_FIX)
SYM(SKP_Silk_warped_LPC_analysis_filter_FIX):
	stmdb	sp!,  {r4-r10, fp, ip, lr}
	add		fp, sp, #36
	sub		sp, sp, #16
.set	ptr_lambda_Q16, 56 
.set	ptr_length, 60 
.set	ptr_order, 64 


	str	r0, [sp, #sp_state_ptr]
	str	r1, [sp, #sp_res_ptr]
	str	r2, [sp, #sp_coef_Q13_ptr]
	str	r3, [sp, #sp_input_ptr]

	ldr	val_lambda, [sp, #ptr_lambda_Q16]
	ldr	val_length, [sp, #ptr_length]

/*OUTTER_LOOP*/
L(1)
	ldmia	ptr_state, {val_state0, val_state1, val_state2}
	ldrsh	val_input, [ptr_input], #2
	ldrh	val_coef, [ptr_coef], #2
	ldr	val_order, [sp, #ptr_order]
	smlawb	val_tmp2, val_state1, val_lambda, val_state0
	str	ptr_input, [sp, #sp_input_ptr]
	mov	val_tmp1, val_input, lsl #14
	sub	val_tmp, val_state2, val_tmp2 
	str	val_tmp1, [ptr_state], #4
	str	val_tmp2, [ptr_state], #4
	smlawb	val_tmp1, val_tmp, val_lambda, val_state1
	smulwb	val_acc, val_tmp2, val_coef
	sub	val_order, val_order, #2
	
/*INNER_LOOP*/
L(0)
	ldrh	val_coef, [ptr_coef], #2	
	ldr	val_state1, [ptr_state, #4]
	str	val_tmp1, [ptr_state], #4
	smlawb	val_acc, val_tmp1, val_coef, val_acc
	sub	val_tmp, val_state1, val_tmp1
	smlawb	val_tmp2, val_tmp, val_lambda, val_state2

	ldrh	val_coef, [ptr_coef], #2	
	ldr	val_state2, [ptr_state, #4]
	str	val_tmp2, [ptr_state], #4
	subs	val_order, val_order, #2
	smlawb	val_acc, val_tmp2, val_coef, val_acc
	sub	val_tmp, val_state2, val_tmp2
	smlawb	val_tmp1, val_tmp, val_lambda, val_state1
	bgt	LR(0, b)

	str	val_tmp1, [ptr_state]
	ldrh	val_coef, [ptr_coef], #2
	ldr	ptr_res, [sp, #sp_res_ptr]
	ldr	ptr_input, [sp, #sp_input_ptr]
	ldr	ptr_coef, [sp, #sp_coef_Q13_ptr]
	ldr	ptr_state, [sp, #sp_state_ptr]
	smlawb	val_acc, val_tmp1, val_coef, val_acc
	mov	val_acc, val_acc, asr #10
	add	val_acc, val_acc, #1
	mov	val_acc, val_acc, asr #1
	sub	val_input, val_input, val_acc
	ssat	val_input, #16, val_input

	strh	val_input, [ptr_res], #2
	subs	val_length, val_length, #1
	str	ptr_res, [sp, #sp_res_ptr]
	bgt	LR(1, b)

	add		sp, sp, #16
	ldmia	sp!,  {r4-r10, fp, ip, pc}
	END

#endif
