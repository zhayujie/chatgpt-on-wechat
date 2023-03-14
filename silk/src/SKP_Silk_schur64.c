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
 * SKP_Silk_schur64.c                                                 *
 *                                                                      *
 * Calculates the reflection coefficients from the correlation sequence *
 * using extra precision                                                *
 *                                                                      *
 * Copyright 2008 (c), Skype Limited                                    *
 * Date: 080103                                                         *
 *                                                                      */
#include "SKP_Silk_SigProc_FIX.h"

/* Slower than schur(), but more accurate.                              */
/* Uses SMULL(), available on armv4                                     */ 
#if EMBEDDED_ARM<6
SKP_int32 SKP_Silk_schur64(                    /* O:    Returns residual energy                     */
    SKP_int32            rc_Q16[],               /* O:    Reflection coefficients [order] Q16         */
    const SKP_int32      c[],                    /* I:    Correlations [order+1]                      */
    SKP_int32            order                   /* I:    Prediction order                            */
)
{
    SKP_int   k, n;
    SKP_int32 C[ SKP_Silk_MAX_ORDER_LPC + 1 ][ 2 ];
    SKP_int32 Ctmp1_Q30, Ctmp2_Q30, rc_tmp_Q31;

    /* Check for invalid input */
    if( c[ 0 ] <= 0 ) {
        SKP_memset( rc_Q16, 0, order * sizeof( SKP_int32 ) );
        return 0;
    }
    
    for( k = 0; k < order + 1; k++ ) {
        C[ k ][ 0 ] = C[ k ][ 1 ] = c[ k ];
    }

    for( k = 0; k < order; k++ ) {
        /* Get reflection coefficient: divide two Q30 values and get result in Q31 */
        rc_tmp_Q31 = SKP_DIV32_varQ( -C[ k + 1 ][ 0 ], C[ 0 ][ 1 ], 31 );

        /* Save the output */
        rc_Q16[ k ] = SKP_RSHIFT_ROUND( rc_tmp_Q31, 15 );

        /* Update correlations */
        for( n = 0; n < order - k; n++ ) {
            Ctmp1_Q30 = C[ n + k + 1 ][ 0 ];
            Ctmp2_Q30 = C[ n ][ 1 ];
            
            /* Multiply and add the highest int32 */
            C[ n + k + 1 ][ 0 ] = Ctmp1_Q30 + SKP_SMMUL( SKP_LSHIFT( Ctmp2_Q30, 1 ), rc_tmp_Q31 );
            C[ n ][ 1 ]         = Ctmp2_Q30 + SKP_SMMUL( SKP_LSHIFT( Ctmp1_Q30, 1 ), rc_tmp_Q31 );
        }
    }

    return C[ 0 ][ 1 ];
}
#endif
