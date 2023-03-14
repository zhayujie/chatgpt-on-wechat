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
 * SKP_Silk_biquad.c                                                  *
 *                                                                      *
 * Second order ARMA filter                                             *
 * Can handle slowly varying filter coefficients                        *
 *                                                                      *
 * Copyright 2006 (c), Skype Limited                                    *
 * Date: 060221                                                         *
 *                                                                      */
#include "SKP_Silk_SigProc_FIX.h"

/* Second order ARMA filter */
/* Can handle slowly varying filter coefficients */
void SKP_Silk_biquad(
    const SKP_int16      *in,        /* I:    input signal               */
    const SKP_int16      *B,         /* I:    MA coefficients, Q13 [3]   */
    const SKP_int16      *A,         /* I:    AR coefficients, Q13 [2]   */
    SKP_int32            *S,         /* I/O:  state vector [2]           */
    SKP_int16            *out,       /* O:    output signal              */
    const SKP_int32      len         /* I:    signal length              */
)
{
    SKP_int   k, in16;
    SKP_int32 A0_neg, A1_neg, S0, S1, out32, tmp32;

    S0 = S[ 0 ];
    S1 = S[ 1 ];
    A0_neg = -A[ 0 ];
    A1_neg = -A[ 1 ];
    for( k = 0; k < len; k++ ) {
        /* S[ 0 ], S[ 1 ]: Q13 */
        in16  = in[ k ];
        out32 = SKP_SMLABB( S0, in16, B[ 0 ] );

        S0 = SKP_SMLABB( S1, in16, B[ 1 ] );
        S0 += SKP_LSHIFT( SKP_SMULWB( out32, A0_neg ), 3 );

        S1 = SKP_LSHIFT( SKP_SMULWB( out32, A1_neg ), 3 );
        S1 = SKP_SMLABB( S1, in16, B[ 2 ] );
        tmp32    = SKP_RSHIFT_ROUND( out32, 13 ) + 1;
        out[ k ] = (SKP_int16)SKP_SAT16( tmp32 );
    }
    S[ 0 ] = S0;
    S[ 1 ] = S1;
}
