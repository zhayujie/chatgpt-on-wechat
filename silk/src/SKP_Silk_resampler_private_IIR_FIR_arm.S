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

	VARDEF ind, r4
	VARDEF tab1, r5
	VARDEF tab2, r6
	VARDEF tab3, _r7
	VARDEF val1, r8
	VARDEF val2, sb
	VARDEF val3, r2
	VARDEF val4, r3
	VARDEF tmp1, sl
	VARDEF tmp2, r2
	VARDEF tmp3, r3
	VARDEF tmp4, ip
	VARDEF out, sl

.set	sp_max_i, 0 
.set	sp_inc, 4 

	EXTERN SYM(SKP_Silk_resampler_frac_FIR_144_alt)
.globl	SYM(SKP_Silk_resampler_private_IIR_FIR_INTERPOL)
SYM(SKP_Silk_resampler_private_IIR_FIR_INTERPOL):
	stmdb	sp!,  {r4-r10, fp, ip, lr}
	add		fp, sp, #36
	sub		sp, sp, #8
	str		r2, [sp, #sp_max_i]
	str		r3, [sp, #sp_inc]
	cmp		r2, #0
	mov		tmp3, #0xFF00
	mov		ind, #0
	ble		LR(1, f)
	add		tmp3, tmp3, #0xFF
L(0)
	ldr		tmp1, TABLE(L0, =SKP_Silk_resampler_frac_FIR_144_alt)
	and		tmp3, ind, tmp3
	mov		tmp2, #144
	mov		tmp4, ind, asr #16
	smulwb	tmp2, tmp3, tmp2
	add		tmp1, tmp1, tmp2, lsl #3
	add		tmp1, tmp1, tmp2, lsl #2
	add		tmp4, r1, tmp4, lsl #1
	
	ldmia	tmp1, {tab1, tab2, tab3}
	ldrsh	val1, [tmp4], #2
	ldrsh	val2, [tmp4], #2
	ldrsh	val3, [tmp4], #2
	ldrsh	val4, [tmp4], #2
	smulbb	out, val1, tab1
	smlabt	out, val2, tab1, out
	ldrsh	val1, [tmp4], #2
	ldrsh	val2, [tmp4]
	smlabb	out, val3, tab2, out
	smlabt	out, val4, tab2, out
	ldr		r2, [sp, #sp_max_i]
	ldr		r3, [sp, #sp_inc]
	smlabb	out, val1, tab3, out
	smlabt	out, val2, tab3, out
	add		ind, ind, r3
	adds	out, out, #1<<14
	mov		tmp3, #0xFF00
#ifdef _WINRT
	bvc		LR(2, f)
	mvn		out, #0x80000000
	b		LR(3, f)
L(2)	
	qadd	out, out, out
L(3)	
#else
	mvnvs	out, #0x80000000
	qaddvc	out, out, out
#endif	
	add		tmp3, tmp3, #0xFF
	mov		out, out, asr #16
	cmp		ind, r2
	strh	out, [r0], #2
	blt		LR(0, b)
L(1)	
	add		sp, sp, #8
	ldmia	sp!,  {r4-r10, fp, ip, pc}

L(L0)
	DCD	SYM(SKP_Silk_resampler_frac_FIR_144_alt)
	END
#endif
#endif
