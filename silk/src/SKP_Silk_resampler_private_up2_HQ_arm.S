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

	VARDEF S_ptr, r0
	VARDEF xy0, r4
	VARDEF xy1, r5
	VARDEF up2_coefs, r6
#ifdef IPHONE
	VARDEF S_0, r8
	VARDEF S_1, _r7
	VARDEF S_2, r8
	VARDEF S_3, _r7
	VARDEF S_4, r8
	VARDEF S_5, _r7
#else
	VARDEF S_0, _r7
	VARDEF S_1, r8
	VARDEF S_2, _r7
	VARDEF S_3, r8
	VARDEF S_4, _r7
	VARDEF S_5, r8
#endif
	VARDEF in, sb
	VARDEF out1, sl
	VARDEF out2, ip
	VARDEF out, lr

.globl	SYM(SKP_Silk_resampler_private_up2_HQ)
SYM(SKP_Silk_resampler_private_up2_HQ):
	stmdb	sp!,  {r4-r10, fp, ip, lr}
	add		fp, sp, #36
L(0)
	ldrsh	in, [r2], #2
	ldmia	S_ptr, {S_0, S_1}
	ldr	up2_coefs, SYM(resampler_up2_hq_0)
	mov	in, in, lsl #10
	sub	xy0, in, S_0
	smulwb	xy0, xy0, up2_coefs
	add	out1, S_0, xy0
	sub	xy1, out1, S_1
	smlawt	xy1, xy1, up2_coefs, xy1
	add	out2, S_1, xy1
	add	S_0, in, xy0
	add	S_1, out1, xy1
	stmia	S_ptr, {S_0, S_1}
	
	add	S_ptr, S_ptr, #16	// &S[4]
	ldmia	S_ptr, {S_4, S_5}
	ldr	xy1, SYM(resampler_up2_hq_notch_2)
	ldr	xy0, SYM(resampler_up2_hq_notch_1)
	ldr	up2_coefs, SYM(resampler_up2_hq_1)
	sub	S_ptr, S_ptr, #8	// &S[2]
	mov	out, #256
	smlawb	out2, S_5, xy1, out2
	smlawt	out2, S_4, xy0, out2
	smlawb	out1, S_4, xy0, out2
	smlawt	out, out1, xy1, out
	sub	S_5, out2, S_5
#if EMBEDDED_ARM<6	
	cmp	out, #0x1000000
	movge	out, #0x1000000
	subge	out, out, #1
	cmn	out, #0x1000000
	movlt	out, #0x1000000
	mov	out, out, asr #9
#else	
	ssat	out, #16, out, asr #9
#endif	
	str	S_5, [S_ptr, #12]	// S[5]
	strh	out, [r1], #2
	
	ldmia	S_ptr, {S_2, S_3}
	sub	xy0, in, S_2
	smulwb	xy0, xy0, up2_coefs
	add	out1, S_2, xy0
	sub	xy1, out1, S_3
	smlawt	xy1, xy1, up2_coefs, xy1
	add	out2, S_3, xy1
	add	S_2, in, xy0
	add	S_3, out1, xy1
	stmia	S_ptr!, {S_2, S_3}
	
	ldmia	S_ptr, {S_4, S_5}
	ldr	xy1, SYM(resampler_up2_hq_notch_2)
	ldr	xy0, SYM(resampler_up2_hq_notch_1)
	mov	out, #256
	smlawb	out2, S_4, xy1, out2
	smlawt	out2, S_5, xy0, out2
	smlawb	out1, S_5, xy0, out2
	smlawt	out, out1, xy1, out
	sub	S_4, out2, S_4
#if EMBEDDED_ARM<6	
	cmp	out, #0x1000000
	movge	out, #0x1000000
	subge	out, out, #1
	cmn	out, #0x1000000
	movlt	out, #0x1000000
	mov	out, out, asr #9
#else		
	ssat	out, #16, out, asr #9
#endif	
	subs	r3, r3, #1
	str	S_4, [S_ptr], #-16	// &S[0]
	strh	out, [r1], #2
	bgt	LR(0, b)
		
	ldmia	sp!,  {r4-r10, fp, ip, pc}

L(SYM(resampler_up2_hq_0))
	DCD	0x83BF10B8

L(SYM(resampler_up2_hq_1))
	DCD 	0xD2FF3FA7

L(SYM(resampler_up2_hq_notch_1))
	DCD	0xF1EC1EB8

L(SYM(resampler_up2_hq_notch_2))
	DCD	0x6F5C3333
	END
#endif
#endif
