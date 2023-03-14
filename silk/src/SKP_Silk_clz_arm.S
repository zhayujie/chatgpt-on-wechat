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
#if (EMBEDDED_ARM>0) && (EMBEDDED_ARM<5)

.globl SYM(SKP_Silk_CLZ16)
.globl SYM(SKP_Silk_CLZ32)

SYM(SKP_Silk_CLZ16):
	str		lr, [sp, #-4]!
	
	mov		r2, r0
	mov		r0, #0
	ands	r1, r2, #0xF000
	movne	r1, r2, asr #12 
	bne		0f
	add		r0, r0, #4
	ands	r1, r2, #0xF00
	movne	r1, r2, asr #8
	bne		0f
	add		r0, r0, #4
	ands	r1, r2, #0xF0
	movne	r1, r2, asr #4
	bne		0f
	add		r0, r0, #4
	mov		r1, r2
0:
	ands	r2, r1, #0x8
	bne		1f
	add		r0, r0, #1
	ands	r2, r1, #0x4
	bne		1f
	add		r0, r0, #1
	ands	r2, r1, #0x2
	bne		1f
	add		r0, r0, #1	
	ands	r2, r1, #0x1
	bne		1f
	add		r0, r0, #1
1:	
	ldr		pc, [sp], #4 

SYM(SKP_Silk_CLZ32):

	str		lr, [sp, #-4]!
	
	mov		r2, r0
	mov		r0, #0
	ands	r1, r2, #0xF0000000
	movne	r1, r2, asr #28 
	bne		0f
	add		r0, r0, #4
	ands	r1, r2, #0xF000000
	movne	r1, r2, asr #24 
	bne		0f
	add		r0, r0, #4
	ands	r1, r2, #0xF00000
	movne	r1, r2, asr #20 
	bne		0f
	add		r0, r0, #4
	ands	r1, r2, #0xF0000
	movne	r1, r2, asr #16 
	bne		0f
	add		r0, r0, #4
	ands	r1, r2, #0xF000
	movne	r1, r2, asr #12 
	bne		0f
	add		r0, r0, #4
	ands	r1, r2, #0xF00
	movne	r1, r2, asr #8
	bne		0f
	add		r0, r0, #4
	ands	r1, r2, #0xF0
	movne	r1, r2, asr #4
	bne		0f
	add		r0, r0, #4
	mov		r1, r2
0:
	ands	r2, r1, #0x8
	bne		1f
	add		r0, r0, #1
	ands	r2, r1, #0x4
	bne		1f
	add		r0, r0, #1
	ands	r2, r1, #0x2
	bne		1f
	add		r0, r0, #1	
	ands	r2, r1, #0x1
	bne		1f
	add		r0, r0, #1
1:	
	ldr		pc, [sp], #4 
	
#endif
#endif
