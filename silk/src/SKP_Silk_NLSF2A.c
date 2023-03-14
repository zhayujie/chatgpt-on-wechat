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

/* conversion between prediction filter coefficients and LSFs   */
/* order should be even                                         */
/* a piecewise linear approximation maps LSF <-> cos(LSF)       */
/* therefore the result is not accurate LSFs, but the two       */
/* function are accurate inverses of each other                 */

#include "SKP_Silk_SigProc_FIX.h"

/* helper function for NLSF2A(..) */
SKP_INLINE void SKP_Silk_NLSF2A_find_poly(
    SKP_int32        *out,        /* o    intermediate polynomial, Q20            */
    const SKP_int32    *cLSF,     /* i    vector of interleaved 2*cos(LSFs), Q20  */
    SKP_int            dd         /* i    polynomial order (= 1/2 * filter order) */
)
{
    SKP_int        k, n;
    SKP_int32    ftmp;

    out[0] = SKP_LSHIFT( 1, 20 );
    out[1] = -cLSF[0];
    for( k = 1; k < dd; k++ ) {
        ftmp = cLSF[2*k];            // Q20
        out[k+1] = SKP_LSHIFT( out[k-1], 1 ) - (SKP_int32)SKP_RSHIFT_ROUND64( SKP_SMULL( ftmp, out[k] ), 20 );
        for( n = k; n > 1; n-- ) {
            out[n] += out[n-2] - (SKP_int32)SKP_RSHIFT_ROUND64( SKP_SMULL( ftmp, out[n-1] ), 20 );
        }
        out[1] -= ftmp;
    }
}

/* compute whitening filter coefficients from normalized line spectral frequencies */
void SKP_Silk_NLSF2A(
    SKP_int16       *a,               /* o    monic whitening filter coefficients in Q12,  [d]    */
    const SKP_int    *NLSF,           /* i    normalized line spectral frequencies in Q15, [d]    */
    const SKP_int    d                /* i    filter order (should be even)                       */
)
{
    SKP_int k, i, dd;
    SKP_int32 cos_LSF_Q20[SKP_Silk_MAX_ORDER_LPC];
    SKP_int32 P[SKP_Silk_MAX_ORDER_LPC/2+1], Q[SKP_Silk_MAX_ORDER_LPC/2+1];
    SKP_int32 Ptmp, Qtmp;
    SKP_int32 f_int;
    SKP_int32 f_frac;
    SKP_int32 cos_val, delta;
    SKP_int32 a_int32[SKP_Silk_MAX_ORDER_LPC];
    SKP_int32 maxabs, absval, idx=0, sc_Q16; 

    SKP_assert(LSF_COS_TAB_SZ_FIX == 128);

    /* convert LSFs to 2*cos(LSF(i)), using piecewise linear curve from table */
    for( k = 0; k < d; k++ ) {
        SKP_assert(NLSF[k] >= 0 );
        SKP_assert(NLSF[k] <= 32767 );

        /* f_int on a scale 0-127 (rounded down) */
        f_int = SKP_RSHIFT( NLSF[k], 15 - 7 ); 
        
        /* f_frac, range: 0..255 */
        f_frac = NLSF[k] - SKP_LSHIFT( f_int, 15 - 7 ); 

        SKP_assert(f_int >= 0);
        SKP_assert(f_int < LSF_COS_TAB_SZ_FIX );

        /* Read start and end value from table */
        cos_val = SKP_Silk_LSFCosTab_FIX_Q12[ f_int ];                /* Q12 */
        delta   = SKP_Silk_LSFCosTab_FIX_Q12[ f_int + 1 ] - cos_val;  /* Q12, with a range of 0..200 */

        /* Linear interpolation */
        cos_LSF_Q20[k] = SKP_LSHIFT( cos_val, 8 ) + SKP_MUL( delta, f_frac ); /* Q20 */
    }
    
    dd = SKP_RSHIFT( d, 1 );

    /* generate even and odd polynomials using convolution */
    SKP_Silk_NLSF2A_find_poly( P, &cos_LSF_Q20[0], dd );
    SKP_Silk_NLSF2A_find_poly( Q, &cos_LSF_Q20[1], dd );

    /* convert even and odd polynomials to SKP_int32 Q12 filter coefs */
    for( k = 0; k < dd; k++ ) {
        Ptmp = P[k+1] + P[k];
        Qtmp = Q[k+1] - Q[k];

        /* the Ptmp and Qtmp values at this stage need to fit in int32 */

        a_int32[k]     = -SKP_RSHIFT_ROUND( Ptmp + Qtmp, 9 ); /* Q20 -> Q12 */
        a_int32[d-k-1] =  SKP_RSHIFT_ROUND( Qtmp - Ptmp, 9 ); /* Q20 -> Q12 */
    }

    /* Limit the maximum absolute value of the prediction coefficients */
    for( i = 0; i < 10; i++ ) {
        /* Find maximum absolute value and its index */
        maxabs = 0;
        for( k = 0; k < d; k++ ) {
            absval = SKP_abs( a_int32[k] );
            if( absval > maxabs ) {
                maxabs = absval;
                idx       = k;
            }    
        }
    
        if( maxabs > SKP_int16_MAX ) {    
            /* Reduce magnitude of prediction coefficients */
            maxabs = SKP_min( maxabs, 98369 ); // ( SKP_int32_MAX / ( 65470 >> 2 ) ) + SKP_int16_MAX = 98369 
            sc_Q16 = 65470 - SKP_DIV32( SKP_MUL( 65470 >> 2, maxabs - SKP_int16_MAX ), 
                                        SKP_RSHIFT32( SKP_MUL( maxabs, idx + 1), 2 ) );
            SKP_Silk_bwexpander_32( a_int32, d, sc_Q16 );
        } else {
            break;
        }
    }    

    /* Reached the last iteration */
    if( i == 10 ) {
        SKP_assert(0);
        for( k = 0; k < d; k++ ) {
            a_int32[k] = SKP_SAT16( a_int32[k] ); 
        }
    }

    /* Return as SKP_int16 Q12 coefficients */
    for( k = 0; k < d; k++ ) {
        a[k] = (SKP_int16)a_int32[k];
    }
}
