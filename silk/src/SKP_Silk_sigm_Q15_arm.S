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
#if EMBEDDED_ARM>=4

	VARDEF ptr_slope, r6
	VARDEF ptr_LUT, _r7
	VARDEF in_Q5, r1
	VARDEF ind, r2
	VARDEF val_slope, r5
	VARDEF val_PUT, r4
	VARDEF in_Q5_tmp, r3

.globl	SYM(SKP_Silk_sigm_Q15)
SYM(SKP_Silk_sigm_Q15):
	stmdb	sp!,  {r4-r7, fp, ip, lr}
	add		fp, sp, #24
	cmp		r0, #0
	ldr		ptr_slope, TABLE(L0, =SKP_Silk_sigm_tab)

	mov		in_Q5, r0
	rsblt	in_Q5, r0, #0
	mov		r0, #32768
	addlt	ptr_slope, ptr_slope, #24
	movlt	r0, #1
	add		ptr_LUT, ptr_slope, #12											/*sigm_LUT_pos_Q15*/
	cmp		in_Q5, #192											/*6*32*/
	sub		r0, r0, #1
	
	bge		LR(1, f)
	mov		ind, in_Q5, asr #5										/*ind*/	
	mov		ind, ind, lsl #1
	and		in_Q5_tmp,	in_Q5, #0x1F
	ldrsh	val_slope, [ptr_slope, ind]										/*sigm_LUT_slope_Q10*/
	ldrsh	val_PUT, [ptr_LUT, ind]										/*sigm_LUT_pos/neg_Q15*/
	mla		r0, val_slope, in_Q5_tmp, val_PUT
L(1)	
	ldmia	sp!,  {r4-r7, fp, ip, pc}
	
L(L0)		
	DCD	SYM(SKP_Silk_sigm_tab)

	SKP_TABLE SKP_Silk_sigm_tab, 2
	DCW		237, 153, 73, 30, 12, 7,						\
			16384, 23955, 28861, 31213, 32178, 32548,		\
			-237, -153, -73, -30, -12, -7,					\
			16384, 8812, 3906, 1554, 589, 219
	END	
#endif
#endif
