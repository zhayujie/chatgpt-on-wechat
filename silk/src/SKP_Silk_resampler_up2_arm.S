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
#define SKP_Silk_resampler_up2_lq_0 0x1FA6
#define SKP_Silk_resampler_up2_lq_1 0x8FAF

	VARDEF xy0, r4
	VARDEF xy1, r5
	VARDEF up2_coefs, _r7
	VARDEF S_0, r6
	VARDEF S_1, r8
	VARDEF in, sb
	VARDEF out0, sl
	VARDEF out1, r0

.set	sp_S, 0 
.globl	SYM(SKP_Silk_resampler_up2)
SYM(SKP_Silk_resampler_up2):
	stmdb	sp!,  {r4-r10, fp, ip, lr}
	add		fp, sp, #36
	sub		sp, sp, #4
	mov	up2_coefs, #0x1F000000
	ldrsh	in, [r2], #2
	add	up2_coefs, up2_coefs, #0xA60000
	str	r0, [sp, #sp_S]
	add	up2_coefs, up2_coefs, #0x8F00
	ldmia	r0, {S_0, S_1}
	add	up2_coefs, up2_coefs, #0xAF
	mov	ip, #512
	cmp	r3, #0
	beq	LR(1, f)
L(0)
	mov	in, in, lsl #10
	sub	xy0, in, S_0
	sub	xy1, in, S_1
	smulwt	xy0, xy0, up2_coefs
	smlawb	xy1, xy1, up2_coefs, xy1
	add	out0, S_0, xy0
	add	out1, S_1, xy1
	add	S_0, in, xy0
	add	S_1, in, xy1
	qadd	out0, out0, ip
	qadd	out1, out1, ip
#if EMBEDDED_ARM<6	
	cmp	out0, #0x2000000
	movge	out0, #0x2000000
	subge	out0, out0, #1
	cmn	out0, #0x2000000
	movlt	out0, #0x2000000
	cmp	out1, #0x2000000
	movge	out1, #0x2000000
	subge	out1 ,out1, #1
	cmn	out1, #0x2000000
	movlt	out1, #0x2000000
	mov	out0, out0, asr #10
	mov	out1, out1, asr #10
#else	
	ssat	out0, #16, out0, asr #10
	ssat	out1, #16, out1, asr #10
#endif	
	subs	r3, r3, #1
#ifdef _WINRT
	ble		LR(2, f)
	ldrsh	in, [r2], #2
	strh	out0, [r1], #2
	strh	out1, [r1], #2
	b		LR(0, b)
L(2)
	strh	out0, [r1], #2
	strh	out1, [r1], #2
#else	
	ldrgtsh	in, [r2], #2
	strh	out0, [r1], #2
	strh	out1, [r1], #2
	bgt	LR(0, b)
#endif	
	
	ldr	r0, [sp, #sp_S]
	stmia	r0, {S_0, S_1}
L(1)
	add		sp, sp, #4
	ldmia	sp!,  {r4-r10, fp, ip, pc}
	END
#endif
#endif
