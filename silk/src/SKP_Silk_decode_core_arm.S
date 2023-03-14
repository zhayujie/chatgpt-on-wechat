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

#define MAX_LPC_ORDER			16
#define MAX_LPC_ORDER_INT32_OFFSET	64


#if EMBEDDED_ARM >= 5

	VARDEF ptr_vec_Q10, r0
	VARDEF ptr_pres_Q10, r1
	VARDEF ptr_sLPC_Q14, r2
	VARDEF ptr_A_Q12_tmp, r3
	VARDEF ptr_LPC_Q14, r4
	VARDEF val1_LPC_Q14, r5
	VARDEF val_pres_Q10, r5
	VARDEF val2_LPC_Q14, r6
	VARDEF val_vec_Q10, r6
	VARDEF val3_LPC_Q14, r8
	VARDEF val4_LPC_Q14, sb
	VARDEF val1_Atmp, sl
	VARDEF val_LPC_Q14, sl
	VARDEF val2_Atmp, ip

	VARDEF val_subfr_length, _r7
	VARDEF val_LPC_order, lr
	VARDEF val_LPC_pred_Q10, lr

.globl	SYM(SKP_Silk_decode_short_term_prediction)
SYM(SKP_Silk_decode_short_term_prediction):
	stmdb	sp!,  {r4-r10, fp, ip, lr}
	add		fp, sp, #36
.set	ptr_LPC_order, 40 
.set	ptr_subfr_length, 44 


	ldr	val_LPC_order, [sp, #ptr_LPC_order]
	ldr	val_subfr_length, [sp, #ptr_subfr_length]
	ands	val1_Atmp, ptr_A_Q12_tmp, #3
	add	ptr_sLPC_Q14, ptr_sLPC_Q14, #MAX_LPC_ORDER_INT32_OFFSET
	bne	LR(2, f)
	cmp	val_LPC_order, #16
	bne	LR(1, f)
/*LPC_order == 16*/
L(0)
	mov	ptr_LPC_Q14, ptr_sLPC_Q14
	ldmia	ptr_A_Q12_tmp!, {val1_Atmp, val2_Atmp}
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	smulwb	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp
	smlawt	val_LPC_pred_Q10, val1_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val3_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #4

	smlawb	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val1_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val3_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #4

	smlawb	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val1_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val3_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #-28

	smlawb	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val1_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldr	val_pres_Q10, [ptr_pres_Q10], #4
	smlawb	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val3_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	subs	val_subfr_length, val_subfr_length, #1
	add	val_vec_Q10, val_LPC_pred_Q10, val_pres_Q10
	mov	val_LPC_Q14, val_vec_Q10, lsl #4
	str	val_vec_Q10, [ptr_vec_Q10], #4
	str	val_LPC_Q14, [ptr_sLPC_Q14], #4
	bgt	LR(0, b)

	ldmia	sp!,  {r4-r10, fp, ip, pc}

/*LPC_order == 10*/
L(1)
	mov	ptr_LPC_Q14, ptr_sLPC_Q14
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #4
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #4
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}
	
	smulwb	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp
	smlawt	val_LPC_pred_Q10, val3_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #4

	smlawb	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val1_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val3_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #-16

	smlawb	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val1_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldr	val_pres_Q10, [ptr_pres_Q10], #4
	smlawb	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	smlawt	val_LPC_pred_Q10, val3_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	subs	val_subfr_length, val_subfr_length, #1
	add	val_vec_Q10, val_LPC_pred_Q10, val_pres_Q10
	mov	val_LPC_Q14, val_vec_Q10, lsl #4
	str	val_vec_Q10, [ptr_vec_Q10], #4
	str	val_LPC_Q14, [ptr_sLPC_Q14], #4
	bgt	LR(1, b)

	ldmia	sp!,  {r4-r10, fp, ip, pc}

L(2)
	cmp	val_LPC_order, #16
	bne	LR(4, f)
/*LPC_order == 16*/
L(3)
	mov	ptr_LPC_Q14, ptr_sLPC_Q14
	ldrh	val1_Atmp, [ptr_A_Q12_tmp], #2
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #4
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	smulwb	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val1_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}

	smlawt	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val3_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}

	smlawt	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val1_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}

	smlawt	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val3_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}


	smlawt	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val1_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}

	smlawt	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val3_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}


	smlawt	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldrh	val1_Atmp, [ptr_A_Q12_tmp], #-30
	smlawb	val_LPC_pred_Q10, val1_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldr	val_pres_Q10, [ptr_pres_Q10], #4
	smlawt	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	smlawb	val_LPC_pred_Q10, val3_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	subs	val_subfr_length, val_subfr_length, #1
	add	val_vec_Q10, val_LPC_pred_Q10, val_pres_Q10
	mov	val_LPC_Q14, val_vec_Q10, lsl #4
	str	val_vec_Q10, [ptr_vec_Q10], #4
	str	val_LPC_Q14, [ptr_sLPC_Q14], #4
	bgt	LR(3, b)

	ldmia	sp!,  {r4-r10, fp, ip, pc}

/*LPC_order == 10*/
L(4)
	mov	ptr_LPC_Q14, ptr_sLPC_Q14
	ldrh	val2_Atmp, [ptr_A_Q12_tmp], #2
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #4
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}
	
	smulwb	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val3_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	
	smlawt	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val1_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val1_LPC_Q14, val2_LPC_Q14}
	
	smlawt	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldr	val2_Atmp, [ptr_A_Q12_tmp], #4
	smlawb	val_LPC_pred_Q10, val3_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldmdb	ptr_LPC_Q14!, {val3_LPC_Q14, val4_LPC_Q14}
	
	smlawt	val_LPC_pred_Q10, val2_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	ldr	val1_Atmp, [ptr_A_Q12_tmp], #-18
	smlawb	val_LPC_pred_Q10, val1_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	ldr	val_pres_Q10, [ptr_pres_Q10], #4
	smlawt	val_LPC_pred_Q10, val4_LPC_Q14, val2_Atmp, val_LPC_pred_Q10
	smlawb	val_LPC_pred_Q10, val3_LPC_Q14, val1_Atmp, val_LPC_pred_Q10
	subs	val_subfr_length, val_subfr_length, #1
	add	val_vec_Q10, val_LPC_pred_Q10, val_pres_Q10
	mov	val_LPC_Q14, val_vec_Q10, lsl #4
	str	val_vec_Q10, [ptr_vec_Q10], #4
	str	val_LPC_Q14, [ptr_sLPC_Q14], #4
	bgt	LR(4, b)

	ldmia	sp!,  {r4-r10, fp, ip, pc}
	END
#endif
