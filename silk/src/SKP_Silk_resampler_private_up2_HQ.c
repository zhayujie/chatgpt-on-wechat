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
 * SKP_Silk_resampler_private_up2_HQ.c                                *
 *                                                                      *
 * Upsample by a factor 2, high quality                                 *
 *                                                                      *
 * Copyright 2010 (c), Skype Limited                                    *
 *                                                                      */

#include "SKP_Silk_SigProc_FIX.h"
#include "SKP_Silk_resampler_private.h"

/* Upsample by a factor 2, high quality */
/* Uses 2nd order allpass filters for the 2x upsampling, followed by a      */
/* notch filter just above Nyquist.                                         */
#if (EMBEDDED_ARM<5) 
void SKP_Silk_resampler_private_up2_HQ(
	SKP_int32	                    *S,			    /* I/O: Resampler state [ 6 ]					*/
    SKP_int16                       *out,           /* O:   Output signal [ 2 * len ]               */
    const SKP_int16                 *in,            /* I:   Input signal [ len ]                    */
    SKP_int32                       len             /* I:   Number of INPUT samples                 */
)
{
    SKP_int32 k;
    SKP_int32 in32, out32_1, out32_2, Y, X;

    SKP_assert( SKP_Silk_resampler_up2_hq_0[ 0 ] > 0 );
    SKP_assert( SKP_Silk_resampler_up2_hq_0[ 1 ] < 0 );
    SKP_assert( SKP_Silk_resampler_up2_hq_1[ 0 ] > 0 );
    SKP_assert( SKP_Silk_resampler_up2_hq_1[ 1 ] < 0 );
    
    /* Internal variables and state are in Q10 format */
    for( k = 0; k < len; k++ ) {
        /* Convert to Q10 */
        in32 = SKP_LSHIFT( (SKP_int32)in[ k ], 10 );

        /* First all-pass section for even output sample */
        Y       = SKP_SUB32( in32, S[ 0 ] );
        X       = SKP_SMULWB( Y, SKP_Silk_resampler_up2_hq_0[ 0 ] );
        out32_1 = SKP_ADD32( S[ 0 ], X );
        S[ 0 ]  = SKP_ADD32( in32, X );

        /* Second all-pass section for even output sample */
        Y       = SKP_SUB32( out32_1, S[ 1 ] );
        X       = SKP_SMLAWB( Y, Y, SKP_Silk_resampler_up2_hq_0[ 1 ] );
        out32_2 = SKP_ADD32( S[ 1 ], X );
        S[ 1 ]  = SKP_ADD32( out32_1, X );

        /* Biquad notch filter */
        out32_2 = SKP_SMLAWB( out32_2, S[ 5 ], SKP_Silk_resampler_up2_hq_notch[ 2 ] );
        out32_2 = SKP_SMLAWB( out32_2, S[ 4 ], SKP_Silk_resampler_up2_hq_notch[ 1 ] );
        out32_1 = SKP_SMLAWB( out32_2, S[ 4 ], SKP_Silk_resampler_up2_hq_notch[ 0 ] );
        S[ 5 ]  = SKP_SUB32(  out32_2, S[ 5 ] );
        
        /* Apply gain in Q15, convert back to int16 and store to output */
        out[ 2 * k ] = (SKP_int16)SKP_SAT16( SKP_RSHIFT32( 
            SKP_SMLAWB( 256, out32_1, SKP_Silk_resampler_up2_hq_notch[ 3 ] ), 9 ) );

        /* First all-pass section for odd output sample */
        Y       = SKP_SUB32( in32, S[ 2 ] );
        X       = SKP_SMULWB( Y, SKP_Silk_resampler_up2_hq_1[ 0 ] );
        out32_1 = SKP_ADD32( S[ 2 ], X );
        S[ 2 ]  = SKP_ADD32( in32, X );

        /* Second all-pass section for odd output sample */
        Y       = SKP_SUB32( out32_1, S[ 3 ] );
        X       = SKP_SMLAWB( Y, Y, SKP_Silk_resampler_up2_hq_1[ 1 ] );
        out32_2 = SKP_ADD32( S[ 3 ], X );
        S[ 3 ]  = SKP_ADD32( out32_1, X );

        /* Biquad notch filter */
        out32_2 = SKP_SMLAWB( out32_2, S[ 4 ], SKP_Silk_resampler_up2_hq_notch[ 2 ] );
        out32_2 = SKP_SMLAWB( out32_2, S[ 5 ], SKP_Silk_resampler_up2_hq_notch[ 1 ] );
        out32_1 = SKP_SMLAWB( out32_2, S[ 5 ], SKP_Silk_resampler_up2_hq_notch[ 0 ] );
        S[ 4 ]  = SKP_SUB32(  out32_2, S[ 4 ] );
        
        /* Apply gain in Q15, convert back to int16 and store to output */
        out[ 2 * k + 1 ] = (SKP_int16)SKP_SAT16( SKP_RSHIFT32( 
            SKP_SMLAWB( 256, out32_1, SKP_Silk_resampler_up2_hq_notch[ 3 ] ), 9 ) );
    }
}
#endif


void SKP_Silk_resampler_private_up2_HQ_wrapper(
	void	                        *SS,		    /* I/O: Resampler state (unused)				*/
    SKP_int16                       *out,           /* O:   Output signal [ 2 * len ]               */
    const SKP_int16                 *in,            /* I:   Input signal [ len ]                    */
    SKP_int32                       len             /* I:   Number of input samples                 */
)
{
    SKP_Silk_resampler_state_struct *S = (SKP_Silk_resampler_state_struct *)SS;
    SKP_Silk_resampler_private_up2_HQ( S->sIIR, out, in, len );
}
