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
 * SKP_Silk_resampler_private_up4.c                                   *
 *                                                                      *
 * Upsample by a factor 4, low quality                                  *
 *                                                                      *
 * Copyright 2010 (c), Skype Limited                                    *
 *                                                                      */

#include "SKP_Silk_SigProc_FIX.h"
#include "SKP_Silk_resampler_private.h"

/* Upsample by a factor 4, Note: very low quality, only use with output sampling rates above 96 kHz. */
void SKP_Silk_resampler_private_up4(
    SKP_int32                       *S,             /* I/O: State vector [ 2 ]                      */
    SKP_int16                       *out,           /* O:   Output signal [ 4 * len ]               */
    const SKP_int16                 *in,            /* I:   Input signal [ len ]                    */
    SKP_int32                       len             /* I:   Number of INPUT samples                 */
)
{
    SKP_int32 k;
    SKP_int32 in32, out32, Y, X;
    SKP_int16 out16;

    SKP_assert( SKP_Silk_resampler_up2_lq_0 > 0 );
    SKP_assert( SKP_Silk_resampler_up2_lq_1 < 0 );

    /* Internal variables and state are in Q10 format */
    for( k = 0; k < len; k++ ) {
        /* Convert to Q10 */
        in32 = SKP_LSHIFT( (SKP_int32)in[ k ], 10 );

        /* All-pass section for even output sample */
        Y      = SKP_SUB32( in32, S[ 0 ] );
        X      = SKP_SMULWB( Y, SKP_Silk_resampler_up2_lq_0 );
        out32  = SKP_ADD32( S[ 0 ], X );
        S[ 0 ] = SKP_ADD32( in32, X );

        /* Convert back to int16 and store to output */
        out16 = (SKP_int16)SKP_SAT16( SKP_RSHIFT_ROUND( out32, 10 ) );
        out[ 4 * k ]     = out16;
        out[ 4 * k + 1 ] = out16;

        /* All-pass section for odd output sample */
        Y      = SKP_SUB32( in32, S[ 1 ] );
        X      = SKP_SMLAWB( Y, Y, SKP_Silk_resampler_up2_lq_1 );
        out32  = SKP_ADD32( S[ 1 ], X );
        S[ 1 ] = SKP_ADD32( in32, X );

        /* Convert back to int16 and store to output */
        out16 = (SKP_int16)SKP_SAT16( SKP_RSHIFT_ROUND( out32, 10 ) );
        out[ 4 * k + 2 ] = out16;
        out[ 4 * k + 3 ] = out16;
    }
}
