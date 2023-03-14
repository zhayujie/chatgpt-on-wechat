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
 * SKP_Silk_MA.c                                                      *
 *                                                                      *
 * Variable order MA filter                                             *
 *                                                                      *
 * Copyright 2006 (c), Skype Limited                                    *
 * Date: 060221                                                         *
 *                                                                      */
#include "SKP_Silk_SigProc_FIX.h"

#if EMBEDDED_ARM<5
/* Variable order MA prediction error filter */
void SKP_Silk_MA_Prediction(
    const SKP_int16      *in,            /* I:   Input signal                                */
    const SKP_int16      *B,             /* I:   MA prediction coefficients, Q12 [order]     */
    SKP_int32            *S,             /* I/O: State vector [order]                        */
    SKP_int16            *out,           /* O:   Output signal                               */
    const SKP_int32      len,            /* I:   Signal length                               */
    const SKP_int32      order           /* I:   Filter order                                */
)
{
    SKP_int   k, d, in16;
    SKP_int32 out32;

    for( k = 0; k < len; k++ ) {
        in16 = in[ k ];
        out32 = SKP_LSHIFT( in16, 12 ) - S[ 0 ];
        out32 = SKP_RSHIFT_ROUND( out32, 12 );
        
        for( d = 0; d < order - 1; d++ ) {
            S[ d ] = SKP_SMLABB_ovflw( S[ d + 1 ], in16, B[ d ] );
        }
        S[ order - 1 ] = SKP_SMULBB( in16, B[ order - 1 ] );

        /* Limit */
        out[ k ] = (SKP_int16)SKP_SAT16( out32 );
    }
}
#endif

#if EMBEDDED_ARM<5

void SKP_Silk_LPC_analysis_filter(
    const SKP_int16      *in,            /* I:   Input signal                                */
    const SKP_int16      *B,             /* I:   MA prediction coefficients, Q12 [order]     */
    SKP_int16            *S,             /* I/O: State vector [order]                        */
    SKP_int16            *out,           /* O:   Output signal                               */
    const SKP_int32      len,            /* I:   Signal length                               */
    const SKP_int32      Order           /* I:   Filter order                                */
)
{
    SKP_int   k, j, idx, Order_half = SKP_RSHIFT( Order, 1 );
    SKP_int32 out32_Q12, out32;
    SKP_int16 SA, SB;
    /* Order must be even */
    SKP_assert( 2 * Order_half == Order );

    /* S[] values are in Q0 */
    for( k = 0; k < len; k++ ) {
        SA = S[ 0 ];
        out32_Q12 = 0;
        for( j = 0; j < ( Order_half - 1 ); j++ ) {
            idx = SKP_SMULBB( 2, j ) + 1;
            /* Multiply-add two prediction coefficients for each loop */
            SB = S[ idx ];
            S[ idx ] = SA;
            out32_Q12 = SKP_SMLABB( out32_Q12, SA, B[ idx - 1 ] );
            out32_Q12 = SKP_SMLABB( out32_Q12, SB, B[ idx ] );
            SA = S[ idx + 1 ];
            S[ idx + 1 ] = SB;
        }

        /* Unrolled loop: epilog */
        SB = S[ Order - 1 ];
        S[ Order - 1 ] = SA;
        out32_Q12 = SKP_SMLABB( out32_Q12, SA, B[ Order - 2 ] );
        out32_Q12 = SKP_SMLABB( out32_Q12, SB, B[ Order - 1 ] );

        /* Subtract prediction */
        out32_Q12 = SKP_SUB_SAT32( SKP_LSHIFT( (SKP_int32)in[ k ], 12 ), out32_Q12 );

        /* Scale to Q0 */
        out32 = SKP_RSHIFT_ROUND( out32_Q12, 12 );

        /* Saturate output */
        out[ k ] = ( SKP_int16 )SKP_SAT16( out32 );

        /* Move input line */
        S[ 0 ] = in[ k ];
    }
}
#endif

