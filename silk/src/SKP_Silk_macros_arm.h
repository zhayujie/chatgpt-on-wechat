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

#ifndef _SKP_SILK_API_ARM_H_
#define _SKP_SILK_API_ARM_H_

// This is an inline header file for embedded arm platform.

#if EMBEDDED_ARM==4
extern SKP_int32 SKP_Silk_CLZ16(SKP_int16 in16);
extern SKP_int32 SKP_Silk_CLZ32(SKP_int32 in32);

// (a32 * (SKP_int32)((SKP_int16)(b32))) >> 16
#define SKP_SMULWB(a32, b32)			((((a32) >> 16) * (SKP_int32)((SKP_int16)(b32))) + ((((a32) & 0x0000FFFF) * (SKP_int32)((SKP_int16)(b32))) >> 16))

// a32 + (b32 * (SKP_int32)((SKP_int16)(c32))) >> 16
#define SKP_SMLAWB(a32, b32, c32)		((a32) + ((((b32) >> 16) * (SKP_int32)((SKP_int16)(c32))) + ((((b32) & 0x0000FFFF) * (SKP_int32)((SKP_int16)(c32))) >> 16)))

/*SKP_INLINE SKP_int32 SKP_SMULWT(SKP_int32 a32, SKP_int32 b32)
{
	SKP_int32 out32, tmp; 
	SKP_int32 tmp32=0xFFFF0000;
	asm volatile("and %1, %3, %4 \n\t smull %3, %0, %2, %1" : "=&r" (out32), "=&r" (tmp) : "r" (a32), "r" (b32), "r" (tmp32));
	return(out32);
}*/

// (a32 * (b32 >> 16)) >> 16
#define SKP_SMULWT(a32, b32)			(((a32) >> 16) * ((b32) >> 16) + ((((a32) & 0x0000FFFF) * ((b32) >> 16)) >> 16))

// a32 + (b32 * (c32 >> 16)) >> 16
#define SKP_SMLAWT(a32, b32, c32)		((a32) + (((b32) >> 16) * ((c32) >> 16)) + ((((b32) & 0x0000FFFF) * ((c32) >> 16)) >> 16))

// (SKP_int32)((SKP_int16)(a3))) * (SKP_int32)((SKP_int16)(b32))
#define SKP_SMULBB(a32, b32)			((SKP_int32)((SKP_int16)(a32)) * (SKP_int32)((SKP_int16)(b32)))

// a32 + (SKP_int32)((SKP_int16)(b32)) * (SKP_int32)((SKP_int16)(c32))
#define SKP_SMLABB(a32, b32, c32)		((a32) + ((SKP_int32)((SKP_int16)(b32))) * (SKP_int32)((SKP_int16)(c32)))

// a32 + (SKP_int32)((SKP_int16)(b32)) * (SKP_int32)((SKP_int16)(c32))
#define SKP_SMLABB_ovflw(a32, b32, c32)	((a32) + ((SKP_int32)((SKP_int16)(b32))) * (SKP_int32)((SKP_int16)(c32)))

// (SKP_int32)((SKP_int16)(a32)) * (b32 >> 16)
#define SKP_SMULBT(a32, b32)			((SKP_int32)((SKP_int16)(a32)) * ((b32) >> 16))

// a32 + (SKP_int32)((SKP_int16)(b32)) * (c32 >> 16)
#define SKP_SMLABT(a32, b32, c32)		((a32) + ((SKP_int32)((SKP_int16)(b32))) * ((c32) >> 16))

SKP_INLINE SKP_int64 SKP_SMLAL(SKP_int64 a64, SKP_int32 b32, SKP_int32 c32)
{
#ifdef IPHONE
    // IPHONE LLVM compiler doesn't understand Q/R representation. 
    a64 = (SKP_int64)b32 * c32;
    return(a64);
#else
	__asm__ __volatile__ ("smlal %Q0, %R0, %2, %3" : "=r" (a64) : "0" (a64), "r" (b32), "r" (c32));	
	return(a64);
#endif    
}

// (a32 * b32) >> 16
#define SKP_SMULWW(a32, b32)			SKP_MLA(SKP_SMULWB((a32), (b32)), (a32), SKP_RSHIFT_ROUND((b32), 16))

// a32 + ((b32 * c32) >> 16)
#define SKP_SMLAWW(a32, b32, c32)		SKP_MLA(SKP_SMLAWB((a32), (b32), (c32)), (b32), SKP_RSHIFT_ROUND((c32), 16))

/* add/subtract with output saturated */
#define SKP_ADD_SAT32(a, b)				((((a) + (b)) & 0x80000000) == 0 ?								\
										((((a) & (b)) & 0x80000000) != 0 ? SKP_int32_MIN : (a)+(b)) :	\
										((((a) | (b)) & 0x80000000) == 0 ? SKP_int32_MAX : (a)+(b)) )

#define SKP_SUB_SAT32(a, b)				((((a)-(b)) & 0x80000000) == 0 ?										\
										(( (a) & ((b)^0x80000000) & 0x80000000) ? SKP_int32_MIN : (a)-(b)) :	\
										((((a)^0x80000000) & (b)  & 0x80000000) ? SKP_int32_MAX : (a)-(b)) )

#define SKP_SMMUL(a32, b32)				(SKP_int32)SKP_RSHIFT64(SKP_SMULL((a32), (b32)), 32)


#else
SKP_INLINE SKP_int32 SKP_SMULWB(SKP_int32 a32, SKP_int32 b32) {
	SKP_int32 out32;
	__asm__ __volatile__ ("smulwb %0, %1, %2" : "=r" (out32) : "r" (a32), "r" (b32));	
	return(out32);
}


SKP_INLINE SKP_int32 SKP_SMLAWB(SKP_int32 a32, SKP_int32 b32, SKP_int32 c32) {
	SKP_int32 out32;
	__asm__ __volatile__ ("smlawb %0, %2, %3, %1" : "=r" (out32) : "r" (a32), "r" (b32), "r" (c32));	
	return(out32);
}

SKP_INLINE SKP_int32 SKP_SMULWT(SKP_int32 a32, SKP_int32 b32)
{
	SKP_int32 out32;
	__asm__ __volatile__ ("smulwt %0, %1, %2" : "=r" (out32) : "r" (a32), "r" (b32));
	return(out32);
}

SKP_INLINE SKP_int32 SKP_SMLAWT(SKP_int32 a32, SKP_int32 b32, SKP_int32 c32)
{
	SKP_int32 out32;
	__asm__ __volatile__ ("smlawt %0, %2, %3, %1" : "=r" (out32) : "r" (a32), "r" (b32), "r" (c32));
	return(out32);
}

SKP_INLINE SKP_int32 SKP_SMULBB(SKP_int32 a32, SKP_int32 b32) {
	SKP_int32 out32;
	__asm__ __volatile__ ("smulbb %0, %1, %2" : "=r" (out32) : "r" (a32), "r" (b32));	
	return(out32);
}

SKP_INLINE SKP_int32 SKP_SMLABB(SKP_int32 a32, SKP_int32 b32, SKP_int32 c32) {
	SKP_int32 out32;
	__asm__ __volatile__ ("smlabb %0, %2, %3, %1" : "=r" (out32) : "r" (a32), "r" (b32), "r" (c32));	
	return(out32);
}

SKP_INLINE SKP_int32 SKP_SMLABB_ovflw(SKP_int32 a32, SKP_int32 b32, SKP_int32 c32) {
	SKP_int32 out32;
	__asm__ __volatile__ ("smlabb %0, %2, %3, %1" : "=r" (out32) : "r" (a32), "r" (b32), "r" (c32));	
	return(out32);
}

SKP_INLINE SKP_int32 SKP_SMULBT(SKP_int32 a32, SKP_int32 b32) {
	SKP_int32 out32;
	__asm__ __volatile__ ("smulbt %0, %1, %2" : "=r" (out32) : "r" (a32), "r" (b32));	
	return(out32);
}

SKP_INLINE SKP_int32 SKP_SMLABT(SKP_int32 a32, SKP_int32 b32, SKP_int32 c32) {
	SKP_int32 out32;
	__asm__ __volatile__ ("smlabt %0, %2, %3, %1" : "=r" (out32) : "r" (a32), "r" (b32), "r" (c32));	
	return(out32);
}

SKP_INLINE SKP_int64 SKP_SMLAL(SKP_int64 a64, SKP_int32 b32, SKP_int32 c32)
{
#ifdef IPHONE
    // IPHONE LLVM compiler doesn't understand Q/R representation. 
    a64 = (SKP_int64)b32 * c32;
    return(a64);
#else
	__asm__ __volatile__ ("smlal %Q0, %R0, %2, %3" : "=r" (a64) : "0" (a64), "r" (b32), "r" (c32));	
	return(a64);
#endif    
}

#define SKP_SMULWW(a32, b32)			SKP_MLA(SKP_SMULWB((a32), (b32)), (a32), SKP_RSHIFT_ROUND((b32), 16))

/*SKP_INLINE SKP_int32 SKP_SMULWW(SKP_int32 a32, SKP_int32 b32)
{
	SKP_int64 tmp;
	SKP_int32 out32;
	__asm__ __volatile__ ("smull %Q1, %R1, %2, %3 \n\t mov %0, %R1, lsl #16 \n\t add %0, %0, %Q1, lsr #16" : "=&r" (out32), "=&r" (tmp) : "r" (a32), "r" (b32));	
	return(out32);
}*/
#define SKP_SMLAWW(a32, b32, c32)		SKP_MLA(SKP_SMLAWB((a32), (b32), (c32)), (b32), SKP_RSHIFT_ROUND((c32), 16))
/*SKP_INLINE SKP_int32 SKP_SMLAWW(a32, b32, c32){
	SKP_int64 tmp;
	SKP_int32 out32;
	__asm__ __volatile__ ("smull %Q1, %R1, %3, %4 \n\t add %0, %2, %R1, lsl #16 \n\t add %0, %0, %Q1, lsr #16" : "=&r" (out32), "=&r" (tmp) : "r" (a32), "r" (b32), "r" (c32));	
	return(out32);
}*/

SKP_INLINE SKP_int32 SKP_ADD_SAT32(SKP_int32 a32, SKP_int32 b32) {
	SKP_int32 out32;
	__asm__ __volatile__ ("qadd %0, %1, %2" : "=r" (out32) : "r" (a32), "r" (b32));	
	return(out32);
}

SKP_INLINE SKP_int32 SKP_SUB_SAT32(SKP_int32 a32, SKP_int32 b32) {
	SKP_int32 out32;
	__asm__ __volatile__ ("qsub %0, %1, %2" : "=r" (out32) : "r" (a32), "r" (b32));	
	return(out32);
}

SKP_INLINE SKP_int32 SKP_Silk_CLZ16(SKP_int16 in16)
{
	SKP_int32 out32;
	__asm__ __volatile__ ("movs %0, %1, lsl #16 \n\tclz %0, %0 \n\t it eq \n\t moveq %0, #16" : "=r" (out32) : "r" (in16) : "cc");	
	return(out32);
}

SKP_INLINE SKP_int32 SKP_Silk_CLZ32(SKP_int32 in32)
{
	SKP_int32 out32;
	__asm__ __volatile__ ("clz %0, %1" : "=r" (out32) : "r" (in32));	
	return(out32);
}
#if EMBEDDED_ARM < 6
#define SKP_SMMUL(a32, b32)				(SKP_int32)SKP_RSHIFT64(SKP_SMULL((a32), (b32)), 32)
#endif
#endif

// Some ARMv6 specific instructions:

#if EMBEDDED_ARM>=6

SKP_INLINE SKP_int32 SKP_SMMUL(SKP_int32 a32, SKP_int32 b32){			
	SKP_int32 out32;
	__asm__ __volatile__ ("smmul %0, %1, %2" : "=r" (out32) : "r" (a32), "r" (b32));	
	return(out32);
}

SKP_INLINE SKP_int32 SKP_SMUAD(SKP_int32 a32, SKP_int32 b32)
{
	SKP_int32 out32;
	__asm__ __volatile__ ("smuad %0, %1, %2" : "=r" (out32) : "r" (a32), "r" (b32));
	return(out32);
}

SKP_INLINE SKP_int32 SKP_SMLAD(SKP_int32 a32, SKP_int32 b32, SKP_int32 c32)
{
	SKP_int32 out32;
	__asm__ __volatile__ ("smlad %0, %2, %3, %1" : "=r" (out32) : "r" (a32), "r" (b32), "r" (c32));
	return(out32);
}

#endif

#endif // _SKP_SILK_API_ARM_H_



