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

	VARDEF		x0,		r4
	VARDEF		nrg_tmp,	r5
	VARDEF		shift, 		r6
	VARDEF		nrg,	 	_r7
	VARDEF		idx, 		r8

.globl	SYM(SKP_Silk_sum_sqr_shift)
SYM(SKP_Silk_sum_sqr_shift):
	stmdb	sp!,  {r4-r8, fp, ip, lr}
	add		fp, sp, #28
  	mov		idx, r3
 	ands		nrg_tmp, r2, #2
  	mov		nrg, #0
#ifdef _WINRT
	beq		LR(6, f)
	ldrh	x0, [r2], #2
  	smulbb	nrg, x0, x0
  	sub		idx, idx, #1
L(6)	
#else	
  	ldrneh	x0, [r2], #2
  	smulbbne	nrg, x0, x0
  	subne		idx, idx, #1
#endif	

  	ldr		r4, [r2], #4
 	mov		shift, #0
  	sub		idx, idx, #1
L(0)
  	subs		idx, idx, #2
 	SKP_SMLAD	nrg, x0, x0, nrg
#ifdef _WINRT
	ldrgt		x0, [r2]
	addgt		r2, r2, #4
#else	
  	ldrgt		x0, [r2], #4
#endif	
  	cmp		nrg, #0
  	blt		LR(1, f)
  	cmp		idx, #0
  	bgt 		LR(0, b)
  	beq		LR(4, f)
 	b		LR(5, f)
L(1)
  	mov		nrg, nrg, lsr #2
  	mov		shift, #2
  	cmp		idx, #0
  	beq		LR(4, f)
 	blt		LR(5, f)
L(3)
  	subs		idx, idx, #2  
  	SKP_SMUAD	nrg_tmp, x0, x0
#ifdef _WINRT
	ldrgt		x0, [r2]
	addgt		r2, r2, #4
	mov			nrg_tmp, nrg_tmp, lsr shift
	adds		nrg, nrg, nrg_tmp
#else
	ldrgt		x0, [r2], #4
  	add		nrg, nrg, nrg_tmp, lsr shift
	cmp		nrg, #0
#endif
  	movlt		nrg, nrg, lsr #2
  	addlt		shift, shift, #2
  	cmp		idx, #0
  	bgt		LR(3, b)
  	blt		LR(5, f)
L(4)  
  	ldrh		x0, [r2]
  	smulbb	nrg_tmp, x0, x0
#ifdef _WINRT
	mov		nrg_tmp, nrg_tmp, lsr shift
	add		nrg, nrg, nrg_tmp
#else	
  	add		nrg, nrg, nrg_tmp, lsr shift
#endif
L(5)
 	ands		nrg_tmp, nrg, #0xC0000000
 	movne		nrg, nrg, lsr #2
  	addne		shift, shift, #2
  	str		shift, [r1]
  	str		nrg, [r0]
  
	ldmia	sp!,  {r4-r8, fp, ip, pc}
	END
#endif
#endif
