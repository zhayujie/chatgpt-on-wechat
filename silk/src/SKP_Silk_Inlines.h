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

/*! \file SKP_Silk_Inlines.h
 *  \brief SKP_Silk_Inlines.h defines inline signal processing functions.
 */

#ifndef _SKP_SILK_FIX_INLINES_H_
#define _SKP_SILK_FIX_INLINES_H_

#include <assert.h>

#ifdef  __cplusplus
extern "C"
{
#endif

/* count leading zeros of SKP_int64 */
SKP_INLINE SKP_int32 SKP_Silk_CLZ64(SKP_int64 in)
{
    SKP_int32 in_upper;

    in_upper = (SKP_int32)SKP_RSHIFT64(in, 32);
    if (in_upper == 0) {
        /* Search in the lower 32 bits */
        return 32 + SKP_Silk_CLZ32( (SKP_int32) in );
    } else {
        /* Search in the upper 32 bits */
        return SKP_Silk_CLZ32( in_upper );
    }
}

/* get number of leading zeros and fractional part (the bits right after the leading one */
SKP_INLINE void SKP_Silk_CLZ_FRAC(SKP_int32 in,            /* I: input */
                                    SKP_int32 *lz,           /* O: number of leading zeros */
                                    SKP_int32 *frac_Q7)      /* O: the 7 bits right after the leading one */
{
    SKP_int32 lzeros = SKP_Silk_CLZ32(in);

    * lz = lzeros;
    * frac_Q7 = SKP_ROR32(in, 24 - lzeros) & 0x7f;
}

/* Approximation of square root                                          */
/* Accuracy: < +/- 10%  for output values > 15                           */
/*           < +/- 2.5% for output values > 120                          */
SKP_INLINE SKP_int32 SKP_Silk_SQRT_APPROX(SKP_int32 x)
{
    SKP_int32 y, lz, frac_Q7;

    if( x <= 0 ) {
        return 0;
    }

    SKP_Silk_CLZ_FRAC(x, &lz, &frac_Q7);

    if( lz & 1 ) {
        y = 32768;
    } else {
        y = 46214;        /* 46214 = sqrt(2) * 32768 */
    }

    /* get scaling right */
    y >>= SKP_RSHIFT(lz, 1);

    /* increment using fractional part of input */
    y = SKP_SMLAWB(y, y, SKP_SMULBB(213, frac_Q7));

    return y;
}

/* returns the number of left shifts before overflow for a 16 bit number (ITU definition with norm(0)=0) */
SKP_INLINE SKP_int32 SKP_Silk_norm16(SKP_int16 a) {

  SKP_int32 a32;

  /* if ((a == 0) || (a == SKP_int16_MIN)) return(0); */
  if ((a << 1) == 0) return(0);

  a32 = a;
  /* if (a32 < 0) a32 = -a32 - 1; */
  a32 ^= SKP_RSHIFT(a32, 31);

  return SKP_Silk_CLZ32(a32) - 17;
}

/* returns the number of left shifts before overflow for a 32 bit number (ITU definition with norm(0)=0) */
SKP_INLINE SKP_int32 SKP_Silk_norm32(SKP_int32 a) {
  
  /* if ((a == 0) || (a == SKP_int32_MIN)) return(0); */
  if ((a << 1) == 0) return(0);

  /* if (a < 0) a = -a - 1; */
  a ^= SKP_RSHIFT(a, 31);

  return SKP_Silk_CLZ32(a) - 1;
}

/* Divide two int32 values and return result as int32 in a given Q-domain */
SKP_INLINE SKP_int32 SKP_DIV32_varQ(    /* O    returns a good approximation of "(a32 << Qres) / b32" */
    const SKP_int32     a32,            /* I    numerator (Q0)                  */
    const SKP_int32     b32,            /* I    denominator (Q0)                */
    const SKP_int       Qres            /* I    Q-domain of result (>= 0)       */
)
{
    SKP_int   a_headrm, b_headrm, lshift;
    SKP_int32 b32_inv, a32_nrm, b32_nrm, result;

    SKP_assert( b32 != 0 );
    SKP_assert( Qres >= 0 );

    /* Compute number of bits head room and normalize inputs */
    a_headrm = SKP_Silk_CLZ32( SKP_abs(a32) ) - 1;
    a32_nrm = SKP_LSHIFT(a32, a_headrm);                                    /* Q: a_headrm                    */
    b_headrm = SKP_Silk_CLZ32( SKP_abs(b32) ) - 1;
    b32_nrm = SKP_LSHIFT(b32, b_headrm);                                    /* Q: b_headrm                    */

    /* Inverse of b32, with 14 bits of precision */
    b32_inv = SKP_DIV32_16( SKP_int32_MAX >> 2, SKP_RSHIFT(b32_nrm, 16) );  /* Q: 29 + 16 - b_headrm        */

    /* First approximation */
    result = SKP_SMULWB(a32_nrm, b32_inv);                                  /* Q: 29 + a_headrm - b_headrm    */

    /* Compute residual by subtracting product of denominator and first approximation */
    a32_nrm -= SKP_LSHIFT_ovflw( SKP_SMMUL(b32_nrm, result), 3 );           /* Q: a_headrm                    */

    /* Refinement */
    result = SKP_SMLAWB(result, a32_nrm, b32_inv);                          /* Q: 29 + a_headrm - b_headrm    */

    /* Convert to Qres domain */
    lshift = 29 + a_headrm - b_headrm - Qres;
    if( lshift <= 0 ) {
        return SKP_LSHIFT_SAT32(result, -lshift);
    } else {
        if( lshift < 32){
            return SKP_RSHIFT(result, lshift);
        } else {
            /* Avoid undefined result */
            return 0;
        }
    }
}

/* Invert int32 value and return result as int32 in a given Q-domain */
SKP_INLINE SKP_int32 SKP_INVERSE32_varQ(    /* O    returns a good approximation of "(1 << Qres) / b32" */
    const SKP_int32     b32,                /* I    denominator (Q0)                */
    const SKP_int       Qres                /* I    Q-domain of result (> 0)        */
)
{
    SKP_int   b_headrm, lshift;
    SKP_int32 b32_inv, b32_nrm, err_Q32, result;

    SKP_assert( b32 != 0 );
    SKP_assert( b32 != SKP_int32_MIN ); /* SKP_int32_MIN is not handled by SKP_abs */
    SKP_assert( Qres > 0 );

    /* Compute number of bits head room and normalize input */
    b_headrm = SKP_Silk_CLZ32( SKP_abs(b32) ) - 1;
    b32_nrm = SKP_LSHIFT(b32, b_headrm);                                    /* Q: b_headrm                */

    /* Inverse of b32, with 14 bits of precision */
    b32_inv = SKP_DIV32_16( SKP_int32_MAX >> 2, SKP_RSHIFT(b32_nrm, 16) );  /* Q: 29 + 16 - b_headrm    */

    /* First approximation */
    result = SKP_LSHIFT(b32_inv, 16);                                       /* Q: 61 - b_headrm            */

    /* Compute residual by subtracting product of denominator and first approximation from one */
    err_Q32 = SKP_LSHIFT_ovflw( -SKP_SMULWB(b32_nrm, b32_inv), 3 );         /* Q32                        */

    /* Refinement */
    result = SKP_SMLAWW(result, err_Q32, b32_inv);                          /* Q: 61 - b_headrm            */

    /* Convert to Qres domain */
    lshift = 61 - b_headrm - Qres;
    if( lshift <= 0 ) {
        return SKP_LSHIFT_SAT32(result, -lshift);
    } else {
        if( lshift < 32){
            return SKP_RSHIFT(result, lshift);
        }else{
            /* Avoid undefined result */
            return 0;
        }
    }
}

#define SKP_SIN_APPROX_CONST0       (1073735400)
#define SKP_SIN_APPROX_CONST1        (-82778932)
#define SKP_SIN_APPROX_CONST2          (1059577)
#define SKP_SIN_APPROX_CONST3            (-5013)

/* Sine approximation; an input of 65536 corresponds to 2 * pi */
/* Uses polynomial expansion of the input to the power 0, 2, 4 and 6 */
/* The relative error is below 1e-5 */
SKP_INLINE SKP_int32 SKP_Silk_SIN_APPROX_Q24(        /* O    returns approximately 2^24 * sin(x * 2 * pi / 65536) */
    SKP_int32        x
)
{
    SKP_int y_Q30;

    /* Keep only bottom 16 bits (the function repeats itself with period 65536) */
    x &= 65535;

    /* Split range in four quadrants */
    if( x <= 32768 ) {
        if( x < 16384 ) {
            /* Return cos(pi/2 - x) */
            x = 16384 - x;
        } else {
            /* Return cos(x - pi/2) */
            x -= 16384;
        }
        if( x < 1100 ) {
            /* Special case: high accuracy */
            return SKP_SMLAWB( 1 << 24, SKP_MUL( x, x ), -5053 );
        }
        x = SKP_SMULWB( SKP_LSHIFT( x, 8 ), x );        /* contains x^2 in Q20 */
        y_Q30 = SKP_SMLAWB( SKP_SIN_APPROX_CONST2, x, SKP_SIN_APPROX_CONST3 );
        y_Q30 = SKP_SMLAWW( SKP_SIN_APPROX_CONST1, x, y_Q30 );
        y_Q30 = SKP_SMLAWW( SKP_SIN_APPROX_CONST0 + 66, x, y_Q30 );
    } else {
        if( x < 49152 ) {
            /* Return -cos(3*pi/2 - x) */
            x = 49152 - x;
        } else {
            /* Return -cos(x - 3*pi/2) */
            x -= 49152;
        }
        if( x < 1100 ) {
            /* Special case: high accuracy */
            return SKP_SMLAWB( -1 << 24, SKP_MUL( x, x ), 5053 );
        }
        x = SKP_SMULWB( SKP_LSHIFT( x, 8 ), x );        /* contains x^2 in Q20 */
        y_Q30 = SKP_SMLAWB( -SKP_SIN_APPROX_CONST2, x, -SKP_SIN_APPROX_CONST3 );
        y_Q30 = SKP_SMLAWW( -SKP_SIN_APPROX_CONST1, x, y_Q30 );
        y_Q30 = SKP_SMLAWW( -SKP_SIN_APPROX_CONST0, x, y_Q30 );
    }
    return SKP_RSHIFT_ROUND( y_Q30, 6 );
}

/* Cosine approximation; an input of 65536 corresponds to 2 * pi */
/* The relative error is below 1e-5 */
SKP_INLINE SKP_int32 SKP_Silk_COS_APPROX_Q24(        /* O    returns approximately 2^24 * cos(x * 2 * pi / 65536) */
    SKP_int32        x
)
{
    return SKP_Silk_SIN_APPROX_Q24( x + 16384 );
}

#ifdef  __cplusplus
}
#endif

#endif /*_SKP_SILK_FIX_INLINES_H_*/
