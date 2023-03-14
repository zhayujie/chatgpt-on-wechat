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
 * SKP_Silk_LPC_inverse_pred_gain.c                                   *
 *                                                                      *
 * Compute inverse of LPC prediction gain, and                          *
 * test if LPC coefficients are stable (all poles within unit circle)   *
 *                                                                      *
 * Copyright 2008 (c), Skype Limited                                    *
 *                                                                      */
#include "SKP_Silk_SigProc_FIX.h"

#define QA          16
#define A_LIMIT     SKP_FIX_CONST( 0.99975, QA )

/* Compute inverse of LPC prediction gain, and                          */
/* test if LPC coefficients are stable (all poles within unit circle)   */
static SKP_int LPC_inverse_pred_gain_QA(        /* O:   Returns 1 if unstable, otherwise 0          */
    SKP_int32           *invGain_Q30,           /* O:   Inverse prediction gain, Q30 energy domain  */
    SKP_int32           A_QA[ 2 ][ SKP_Silk_MAX_ORDER_LPC ],         
                                                /* I:   Prediction coefficients                     */
    const SKP_int       order                   /* I:   Prediction order                            */
)
{
    SKP_int   k, n, headrm;
    SKP_int32 rc_Q31, rc_mult1_Q30, rc_mult2_Q16, tmp_QA;
    SKP_int32 *Aold_QA, *Anew_QA;

    Anew_QA = A_QA[ order & 1 ];

    *invGain_Q30 = ( 1 << 30 );
    for( k = order - 1; k > 0; k-- ) {
        /* Check for stability */
        if( ( Anew_QA[ k ] > A_LIMIT ) || ( Anew_QA[ k ] < -A_LIMIT ) ) {
            return 1;
        }

        /* Set RC equal to negated AR coef */
        rc_Q31 = -SKP_LSHIFT( Anew_QA[ k ], 31 - QA );
        
        /* rc_mult1_Q30 range: [ 1 : 2^30-1 ] */
        rc_mult1_Q30 = ( SKP_int32_MAX >> 1 ) - SKP_SMMUL( rc_Q31, rc_Q31 );
        SKP_assert( rc_mult1_Q30 > ( 1 << 15 ) );                   /* reduce A_LIMIT if fails */
        SKP_assert( rc_mult1_Q30 < ( 1 << 30 ) );

        /* rc_mult2_Q16 range: [ 2^16 : SKP_int32_MAX ] */
        rc_mult2_Q16 = SKP_INVERSE32_varQ( rc_mult1_Q30, 46 );      /* 16 = 46 - 30 */

        /* Update inverse gain */
        /* invGain_Q30 range: [ 0 : 2^30 ] */
        *invGain_Q30 = SKP_LSHIFT( SKP_SMMUL( *invGain_Q30, rc_mult1_Q30 ), 2 );
        SKP_assert( *invGain_Q30 >= 0           );
        SKP_assert( *invGain_Q30 <= ( 1 << 30 ) );

        /* Swap pointers */
        Aold_QA = Anew_QA;
        Anew_QA = A_QA[ k & 1 ];
        
        /* Update AR coefficient */
        headrm = SKP_Silk_CLZ32( rc_mult2_Q16 ) - 1;
        rc_mult2_Q16 = SKP_LSHIFT( rc_mult2_Q16, headrm );          /* Q: 16 + headrm */
        for( n = 0; n < k; n++ ) {
            tmp_QA = Aold_QA[ n ] - SKP_LSHIFT( SKP_SMMUL( Aold_QA[ k - n - 1 ], rc_Q31 ), 1 );
            Anew_QA[ n ] = SKP_LSHIFT( SKP_SMMUL( tmp_QA, rc_mult2_Q16 ), 16 - headrm );
        }
    }

    /* Check for stability */
    if( ( Anew_QA[ 0 ] > A_LIMIT ) || ( Anew_QA[ 0 ] < -A_LIMIT ) ) {
        return 1;
    }

    /* Set RC equal to negated AR coef */
    rc_Q31 = -SKP_LSHIFT( Anew_QA[ 0 ], 31 - QA );

    /* Range: [ 1 : 2^30 ] */
    rc_mult1_Q30 = ( SKP_int32_MAX >> 1 ) - SKP_SMMUL( rc_Q31, rc_Q31 );

    /* Update inverse gain */
    /* Range: [ 0 : 2^30 ] */
    *invGain_Q30 = SKP_LSHIFT( SKP_SMMUL( *invGain_Q30, rc_mult1_Q30 ), 2 );
    SKP_assert( *invGain_Q30 >= 0     );
    SKP_assert( *invGain_Q30 <= 1<<30 );

    return 0;
}
/* For input in Q12 domain */
SKP_int SKP_Silk_LPC_inverse_pred_gain(       /* O:   Returns 1 if unstable, otherwise 0          */
    SKP_int32           *invGain_Q30,           /* O:   Inverse prediction gain, Q30 energy domain  */
    const SKP_int16     *A_Q12,                 /* I:   Prediction coefficients, Q12 [order]        */
    const SKP_int       order                   /* I:   Prediction order                            */
)
{
    SKP_int   k;
    SKP_int32 Atmp_QA[ 2 ][ SKP_Silk_MAX_ORDER_LPC ];
    SKP_int32 *Anew_QA;

    Anew_QA = Atmp_QA[ order & 1 ];

    /* Increase Q domain of the AR coefficients */
    for( k = 0; k < order; k++ ) {
        Anew_QA[ k ] = SKP_LSHIFT( (SKP_int32)A_Q12[ k ], QA - 12 );
    }

    return LPC_inverse_pred_gain_QA( invGain_Q30, Atmp_QA, order );
}

/* For input in Q24 domain */
SKP_int SKP_Silk_LPC_inverse_pred_gain_Q24(   /* O:   Returns 1 if unstable, otherwise 0          */
    SKP_int32           *invGain_Q30,           /* O:   Inverse prediction gain, Q30 energy domain  */
    const SKP_int32     *A_Q24,                 /* I:   Prediction coefficients, Q24 [order]        */
    const SKP_int       order                   /* I:   Prediction order                            */
)
{
    SKP_int   k;
    SKP_int32 Atmp_QA[ 2 ][ SKP_Silk_MAX_ORDER_LPC ];
    SKP_int32 *Anew_QA;

    Anew_QA = Atmp_QA[ order & 1 ];

    /* Increase Q domain of the AR coefficients */
    for( k = 0; k < order; k++ ) {
        Anew_QA[ k ] = SKP_RSHIFT_ROUND( A_Q24[ k ], 24 - QA );
    }

    return LPC_inverse_pred_gain_QA( invGain_Q30, Atmp_QA, order );
}

