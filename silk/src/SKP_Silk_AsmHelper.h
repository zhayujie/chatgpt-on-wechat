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

/*
 * SKP_Silk_AsmHelper.h
 *
 *
 *
 *
 */
 
 
#ifndef _SKP_ASM_HELPER_H_
#define _SKP_ASM_HELPER_H_

//  Register bank
#define _REG 0
#define _DREG 1

//  Arg registers
#define _R0 0
#define _R1 1
#define _R2 2
#define _R3 3
#define _R4 4
//  GP registers
#define _R5 5
#define _R6 6
#define _R7 7
#define _R8 8
#define _SB 9
#define _SL 10
// fp and ip registers
#define _FP 11
#define _IP 12
// lr and sp registers
#define _SP 13
#define _LR 14


// Extension register bank
#define _numDReg 

#define _Q0 0
#define _Q1 1
#define _Q2 2
#define _Q3 3
#define _Q4 4
#define _Q5 5
#define _Q6 6
#define _Q7 7
#define _Q8 8
#define _Q9 9
#define _Q10 10
#define _Q11 11
#define _Q12 12
#define _Q13 13
#define _Q14 14
#define _Q15 15

#if defined (_WINRT)
#else
#if defined (IPHONE)
#define MACRO			.macro
#define END_MACRO		.endmacro
#define ARG0_in	
#define ARG1_in	
#define ARG2_in	
#define ARG3_in
#define ARG4_in
#define ARG5_in
#define ARG6_in
#define ARG7_in
#define ARG0			$0
#define ARG1			$1
#define ARG2			$2
#define ARG3			$3
#define ARG4			$4
#define ARG5			$5
#define ARG6			$6
#define ARG7			$7
#define RARG0			r$0
#define RARG1			r$1
#define QARG0			q$0
#define QARG1			q$1

MACRO CHECK_ABS	ARG0_in, ARG1_in
	.abs is_abs, ARG1
	.if	is_abs==1
		.set ARG0, ARG1
	.else
		.set ARG0, -1
	.endif
END_MACRO

#else
#define MACRO			.macro
#define END_MACRO		.endm
#define ARG0_in			arg0=-1
#define ARG1_in			arg1=-1
#define ARG2_in			arg2=-1
#define ARG3_in			arg3=-1
#define ARG4_in			arg4=-1
#define ARG5_in			arg5=-1
#define ARG6_in			arg6=-1
#define ARG7_in			arg7=-1
#define ARG0			\arg0
#define ARG1			\arg1
#define ARG2			\arg2
#define ARG3			\arg3
#define ARG4			\arg4
#define ARG5			\arg5
#define ARG6			\arg6
#define ARG7			\arg7
#define RARG0			r\arg0
#define RARG1			r\arg1
#define QARG0			q\arg0
#define QARG1			q\arg1

MACRO CHECK_ABS	ARG0_in, ARG1_in
	.set ARG0, ARG1
END_MACRO
#endif

MACRO VARDEF ARG0_in, ARG1_in
ARG0	.req	ARG1
END_MACRO

MACRO VARDEFD ARG0_in, ARG1_in
ARG0	.req	ARG1
END_MACRO
	
MACRO VARDEFQ ARG0_in, ARG1_in
ARG0	.req	ARG1
END_MACRO

MACRO END
END_MACRO

MACRO EXTERN ARG0_in
END_MACRO

MACRO ALIGN ARG0_in
.align ARG0
END_MACRO

MACRO DATA
.data
END_MACRO

MACRO EXPORT ARG0_in
.globl ARG0
END_MACRO

#endif
#endif
