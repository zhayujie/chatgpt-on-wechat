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

	VARDEF y32, r3
	VARDEF pn1, r4
	VARDEF pn2, r5
	VARDEF lo, r6
	VARDEF hi, r8
.globl	SYM(SKP_Silk_A2NLSF_eval_poly)
SYM(SKP_Silk_A2NLSF_eval_poly):
	stmdb	sp!,  {r4-r8, fp, ip, lr}
	add		fp, sp, #28
	add		r0, r0, r2, lsl #2
	ldr		y32, [r0], #-4
	tst		r2, #1
	beq		LR(1, f)
	ldr		pn1, [r0], #-4
	sub		r2, r2, #1
	mov		r1, r1, lsl #4
L(0)
	smull	lo, hi, y32, r1
	subs	r2, r2, #1
	add		y32, pn1, hi, lsl #16
	ldr		pn1, [r0], #-4
	add		y32, y32, lo, lsr #16
	bgt		LR(0, b)
	smull	lo, hi, y32, r1
	add		y32, pn1, hi, lsl #16
	add		r0, y32, lo, lsr #16
	ldmia	sp!,  {r4-r8, fp, ip, pc}

L(1)/*EVEN:*/
	add		r0, r0, #4
	ldmdb	r0!, {pn1, pn2}
	sub		r2, r2, #2
	mov		r1, r1, lsl #4
L(0)
	smull	lo, hi, y32, r1
	subs	r2, r2, #2
	add		y32, pn2, hi, lsl #16
	add		y32, y32, lo, lsr #16
	smull	lo, hi, y32, r1
	add		y32, pn1, hi, lsl #16
	ldmdb	r0!, {pn1, pn2}
	add		y32, y32, lo, lsr #16
	bgt		LR(0, b)
	smull	lo, hi, y32, r1
	add		y32, pn2, hi, lsl #16
	add		y32, y32, lo, lsr #16
	smull	lo, hi, y32, r1
	add		y32, pn1, hi, lsl #16
	add		r0, y32, lo, lsr #16
	ldmia	sp!,  {r4-r8, fp, ip, pc}
	END
#endif
#endif
