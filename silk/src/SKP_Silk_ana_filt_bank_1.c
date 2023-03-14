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

/*                                                                          *
 * SKP_ana_filt_bank_1.c                                                    *
 *                                                                          *
 * Split signal into two decimated bands using first-order allpass filters  *
 *                                                                          *
 * Copyright 2006 (c), Skype Limited                                        *
 * Date: 060221                                                             *
 *                                                                          */
#include "SKP_Silk_SigProc_FIX.h"

#if EMBEDDED_ARM<5
/* Coefficients for 2-band filter bank based on first-order allpass filters */
// old
static SKP_int16 A_fb1_20[ 1 ] = {  5394 << 1 };
static SKP_int16 A_fb1_21[ 1 ] = { 20623 << 1 };        /* wrap-around to negative number is intentional */

/* Split signal into two decimated bands using first-order allpass filters */
void SKP_Silk_ana_filt_bank_1(
    const SKP_int16      *in,        /* I:   Input signal [N]        */
    SKP_int32            *S,         /* I/O: State vector [2]        */
    SKP_int16            *outL,      /* O:   Low band [N/2]          */
    SKP_int16            *outH,      /* O:   High band [N/2]         */
    SKP_int32            *scratch,   /* I:   Scratch memory [3*N/2]  */   // todo: remove - no longer used
    const SKP_int32      N           /* I:   Number of input samples */
)
{
    SKP_int      k, N2 = SKP_RSHIFT( N, 1 );
    SKP_int32    in32, X, Y, out_1, out_2;

    /* Internal variables and state are in Q10 format */
    for( k = 0; k < N2; k++ ) {
        /* Convert to Q10 */
        in32 = SKP_LSHIFT( (SKP_int32)in[ 2 * k ], 10 );

        /* All-pass section for even input sample */
        Y      = SKP_SUB32( in32, S[ 0 ] );
        X      = SKP_SMLAWB( Y, Y, A_fb1_21[ 0 ] );
        out_1  = SKP_ADD32( S[ 0 ], X );
        S[ 0 ] = SKP_ADD32( in32, X );

        /* Convert to Q10 */
        in32 = SKP_LSHIFT( (SKP_int32)in[ 2 * k + 1 ], 10 );

        /* All-pass section for odd input sample */
        Y      = SKP_SUB32( in32, S[ 1 ] );
        X      = SKP_SMULWB( Y, A_fb1_20[ 0 ] );
        out_2  = SKP_ADD32( S[ 1 ], X );
        S[ 1 ] = SKP_ADD32( in32, X );

        /* Add/subtract, convert back to int16 and store to output */
        outL[ k ] = (SKP_int16)SKP_SAT16( SKP_RSHIFT_ROUND( SKP_ADD32( out_2, out_1 ), 11 ) );
        outH[ k ] = (SKP_int16)SKP_SAT16( SKP_RSHIFT_ROUND( SKP_SUB32( out_2, out_1 ), 11 ) );
    }
}
#endif
