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
#define SKP_Silk_resampler_down2_0 0x2690
#define SKP_Silk_resampler_down2_1 0x9B81

	VARDEF xy0, r4
	VARDEF xy1, r5
	VARDEF down2_coefs, _r7
	VARDEF S_0, r6
	VARDEF S_1, r8
	VARDEF in0, sb
	VARDEF in1, sl
	VARDEF out32, r0

.set	sp_S, 0 
.globl	SYM(SKP_Silk_resampler_down2)
SYM(SKP_Silk_resampler_down2):
	stmdb	sp!,  {r4-r10, fp, ip, lr}
	add		fp, sp, #36
	sub		sp, sp, #4
	ldrsh		in0, [r2], #2			// Avoid un-aligned access
	ldrsh		in1, [r2], #2
	str		r0, [sp, #sp_S]
	ldmia		r0, {S_0, S_1}
	mov		down2_coefs, #0x26000000
	add		down2_coefs, down2_coefs, #0x900000
	add		down2_coefs, down2_coefs, #0x9B00
	add		down2_coefs, down2_coefs, #0x81		
	mov		r3, r3, asr #1
	mov		ip, #1024
L(0)
	add		out32, S_0, S_1
	rsb		xy0, S_0, in0, lsl #10
	rsb		xy1, S_1, in1, lsl #10
	smlawb		xy0, xy0, down2_coefs, xy0
	smulwt		xy1, xy1, down2_coefs
	add		out32, out32, xy0
	add		S_0, xy0, in0, lsl #10
	add		out32, out32, xy1
	add		S_1, xy1, in1, lsl #10
#if EMBEDDED_ARM>=6
	qadd		out32, out32, ip
	subs		r3, r3, #1
	ssat		out32, #16, out32, asr #11
#ifdef	_WINRT
	ble			LR(1, f)
	ldrsh		in0, [r2], #2
	ldrsh		in1, [r2], #2
L(1)	
#else	
	ldrgtsh		in0, [r2], #2
	ldrgtsh		in1, [r2], #2
#endif	
#else
	qadd		out32, out32, ip
	cmp		out32, #0x4000000
	movge		out32, #0x4000000
	subge		out32, out32, #1
	cmn		out32, #0x4000000
	movlt		out32, #0x4000000
	subs		r3, r3, #1
	mov		out32, out32, asr #11
	ldrgtsh		in0, [r2], #2	
	ldrgtsh		in1, [r2], #2
#endif	
	
	strh		out32, [r1], #2
	bgt		LR(0, b)

	ldr		r0, [sp, #sp_S]
	stmia		r0, {S_0, S_1}

	add		sp, sp, #4
	ldmia	sp!,  {r4-r10, fp, ip, pc}
	END
#endif
#endif
