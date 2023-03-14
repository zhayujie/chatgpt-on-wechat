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
/*
 *	void SKP_Silk_ana_filt_bank_1(
 *		const SKP_int16		*in,		 I:	Input signal [N]		
 *		SKP_int32			*S,    		 I/O: State vector [2]		
 *		SKP_int16			*outL,     	 O:	Low band [N/2]          
 *		SKP_int16			*outH,     	 O:	High band [N/2]     	
 *		SKP_int32			*scratch,    I:	Scratch memory [3*N/2]	
 *		const SKP_int32		N            I:   Number of input samples 
 *  )
 */
	VARDEF ptr_in_lo, r0
	VARDEF ptr_in_hi, r3
	VARDEF val_in_lo, sb
	VARDEF val_in_hi, sl
	VARDEF ptr_scratch, r4
	VARDEF ptr_scratch_N, r1
	VARDEF ptr_scratch_halfN, r2
	VARDEF idx_k, ip
	VARDEF val_N, r8
	VARDEF val_halfN, r8
	VARDEF val_scratch1, r5
	VARDEF val_scratch2, r6
	VARDEF ptr_out_lo, r5
	VARDEF ptr_out_hi, r6
	VARDEF ptr_s, _r7

	VARDEF val_const1, r2
	VARDEF val_const2, ip			// 0x03FF F800
	VARDEF val_const3, sl			// 0x0000 7FFF
	VARDEF val_const4, lr			// 0xFFFF 8000
	VARDEF idx_k2, r8
	VARDEF ptr_scratch_halfN_2, r3
	VARDEF val_scratch3, r0
	VARDEF val_scratch4, r1
	VARDEF out_tmpla, sb
	VARDEF out_tmplb, r2
	VARDEF out_tmpha, r0
	VARDEF out_tmphb, _r7

.set	halfN, 0 
.set	sp_ptr_out_lo, 4 
.set	sp_ptr_out_hi, 8 

	EXTERN SYM(SKP_Silk_allpass_int)

.globl	SYM(SKP_Silk_ana_filt_bank_1)
SYM(SKP_Silk_ana_filt_bank_1):
	stmdb	sp!,  {r4-r10, fp, ip, lr}
	add		fp, sp, #36
	sub		sp, sp, #12

.set	arg_scratch, 52 
.set	arg_N, 56 

	ldr		ptr_scratch, [sp, #arg_scratch]
	ldr		val_N, [sp, #arg_N]
	
	str		r2, [sp, #sp_ptr_out_lo]
	str		r3, [sp, #sp_ptr_out_hi]
	mov		ptr_s, r1
	mov		val_halfN, val_N, asr #1
	sub		idx_k, val_halfN, #1	
	add		ptr_in_hi, ptr_in_lo, #2
	str		val_halfN, [sp, #halfN]	
	ldrsh	val_in_lo, [ptr_in_lo], #4
	ldrsh	val_in_hi, [ptr_in_hi], #4
	add		ptr_scratch_N, ptr_scratch, val_halfN, lsl #3
	add		ptr_scratch_halfN, ptr_scratch, val_halfN, lsl #2
	
L(0)
	mov		val_scratch1, val_in_lo, lsl #10
	mov		val_scratch2, val_in_hi, lsl #10
	ldrsh	val_in_lo, [ptr_in_lo], #4
	ldrsh	val_in_hi, [ptr_in_hi], #4
	subs	idx_k, idx_k, #1
	str		val_scratch1, [ptr_scratch_N], #4
	str		val_scratch2, [ptr_scratch_halfN], #4
	bgt		LR(0, b)
	
	mov		val_scratch1, val_in_lo, lsl #10
	mov		val_scratch2, val_in_hi, lsl #10
	str		val_scratch1, [ptr_scratch_N], #4
	str		val_scratch2, [ptr_scratch_halfN], #4
	
	mov		val_const1, #0x1500
	add		r0, ptr_scratch, val_halfN, lsl #2
	add		r1, ptr_s, #4
	add		val_const1, val_const1, #0x12
	mov		r3, ptr_scratch
	bl		SYM(SKP_Silk_allpass_int)
	
	mov		val_const1, #0x5000
	add		r0, ptr_scratch, val_halfN, lsl #3
	mov		r1, ptr_s
	add		val_const1, val_const1, #0x8F
	add		r3, ptr_scratch, val_halfN, lsl #2
	bl		SYM(SKP_Silk_allpass_int)
	
	mvn		val_const2, #0x80000000
	add		ptr_scratch_halfN_2, ptr_scratch, val_halfN, lsl #2
	mov		val_const3, val_const2, asr #16
	rsb		val_const4, val_const3, #0
	mov		idx_k2, val_halfN
	mov		val_const2, val_const3, lsl #11
	ldr		ptr_out_lo, [sp, #sp_ptr_out_lo]
	ldr		ptr_out_hi, [sp, #sp_ptr_out_hi]
	
L(1)
	ldr		val_scratch3, [ptr_scratch], #4
	ldr		val_scratch4, [ptr_scratch_halfN_2], #4
	add		out_tmpla, val_scratch3, val_scratch4
	sub		out_tmpha, val_scratch3, val_scratch4	
	add		out_tmplb,  out_tmpla, #1024
	add		out_tmphb,  out_tmpha, #1024
	mov		out_tmplb,  out_tmplb, asr #11
	mov		out_tmphb,  out_tmphb, asr #11
	strh	out_tmplb,  [ptr_out_lo], #2
	strh	out_tmphb,  [ptr_out_hi], #2
#ifdef _WINRT
	cmp		out_tmpla,  val_const2
	ble		LR(2, f)
	strh	val_const3, [ptr_out_lo, #-2]
L(2)	
	cmn		out_tmpla,  val_const2
	bge		LR(2, f)
	strh	val_const4, [ptr_out_lo, #-2]
L(2)	
	cmp		out_tmpha,  val_const2
	ble		LR(2, f)
	strh	val_const3, [ptr_out_hi, #-2]
L(2)	
	cmn		out_tmpha,  val_const2
	bge		LR(2, f)
	strh	val_const4, [ptr_out_hi, #-2]
L(2)	
#else	
	cmp		out_tmpla,  val_const2
	strgth	val_const3, [ptr_out_lo, #-2]
	cmn		out_tmpla,  val_const2
	strlth	val_const4, [ptr_out_lo, #-2]
	cmp		out_tmpha,  val_const2
	strgth	val_const3, [ptr_out_hi, #-2]
	cmn		out_tmpha,  val_const2
	strlth	val_const4, [ptr_out_hi, #-2]
#endif	
	subs	idx_k2, idx_k2, #1
	bgt		LR(1, b)
	
	add		sp, sp, #12
	ldmia	sp!,  {r4-r10, fp, ip, pc}
	END
#endif

#endif
