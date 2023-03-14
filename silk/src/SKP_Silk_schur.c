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

/*                                                                      *
 * SKP_Silk_schur.c                                                   *
 *                                                                      *
 * Calculates the reflection coefficients from the correlation sequence *
 *                                                                      *
 * Copyright 2008 (c), Skype Limited                                    *
 * Date: 080103                                                         *
 *                                                                      */
#include "SKP_Silk_SigProc_FIX.h"

/* Faster than schur64(), but much less accurate.                       */
/* uses SMLAWB(), requiring armv5E and higher.                          */ 
SKP_int32 SKP_Silk_schur(                     /* O:    Returns residual energy                     */
    SKP_int16            *rc_Q15,               /* O:    reflection coefficients [order] Q15         */
    const SKP_int32      *c,                    /* I:    correlations [order+1]                      */
    const SKP_int32      order                  /* I:    prediction order                            */
)
{
    SKP_int        k, n, lz;
    SKP_int32    C[ SKP_Silk_MAX_ORDER_LPC + 1 ][ 2 ];
    SKP_int32    Ctmp1, Ctmp2, rc_tmp_Q15;

    /* Get number of leading zeros */
    lz = SKP_Silk_CLZ32( c[ 0 ] );

    /* Copy correlations and adjust level to Q30 */
    if( lz < 2 ) {
        /* lz must be 1, so shift one to the right */
        for( k = 0; k < order + 1; k++ ) {
            C[ k ][ 0 ] = C[ k ][ 1 ] = SKP_RSHIFT( c[ k ], 1 );
        }
    } else if( lz > 2 ) {
        /* Shift to the left */
        lz -= 2; 
        for( k = 0; k < order + 1; k++ ) {
            C[ k ][ 0 ] = C[ k ][ 1 ] = SKP_LSHIFT( c[k], lz );
        }
    } else {
        /* No need to shift */
        for( k = 0; k < order + 1; k++ ) {
            C[ k ][ 0 ] = C[ k ][ 1 ] = c[ k ];
        }
    }

    for( k = 0; k < order; k++ ) {
        
        /* Get reflection coefficient */
        rc_tmp_Q15 = -SKP_DIV32_16( C[ k + 1 ][ 0 ], SKP_max_32( SKP_RSHIFT( C[ 0 ][ 1 ], 15 ), 1 ) );

        /* Clip (shouldn't happen for properly conditioned inputs) */
        rc_tmp_Q15 = SKP_SAT16( rc_tmp_Q15 );

        /* Store */
        rc_Q15[ k ] = (SKP_int16)rc_tmp_Q15;

        /* Update correlations */
        for( n = 0; n < order - k; n++ ) {
            Ctmp1 = C[ n + k + 1 ][ 0 ];
            Ctmp2 = C[ n ][ 1 ];
            C[ n + k + 1 ][ 0 ] = SKP_SMLAWB( Ctmp1, SKP_LSHIFT( Ctmp2, 1 ), rc_tmp_Q15 );
            C[ n ][ 1 ]         = SKP_SMLAWB( Ctmp2, SKP_LSHIFT( Ctmp1, 1 ), rc_tmp_Q15 );
        }
    }

    /* return residual energy */
    return C[0][1];
}
