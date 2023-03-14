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
 * SKP_Silk_resampler_down3.c                                         *
 *                                                                      *
 * Downsample by a factor 3, low quality                                *
 *                                                                      *
 * Copyright 2010 (c), Skype Limited                                    *
 *                                                                      */

#include "SKP_Silk_SigProc_FIX.h"
#include "SKP_Silk_resampler_private.h"

#define ORDER_FIR                   6

/* Downsample by a factor 3, low quality */
void SKP_Silk_resampler_down3(
    SKP_int32                           *S,         /* I/O: State vector [ 8 ]                  */
    SKP_int16                           *out,       /* O:   Output signal [ floor(inLen/3) ]    */
    const SKP_int16                     *in,        /* I:   Input signal [ inLen ]              */
    SKP_int32                           inLen       /* I:   Number of input samples             */
)
{
	SKP_int32 nSamplesIn, counter, res_Q6;
	SKP_int32 buf[ RESAMPLER_MAX_BATCH_SIZE_IN + ORDER_FIR ];
	SKP_int32 *buf_ptr;

	/* Copy buffered samples to start of buffer */	
	SKP_memcpy( buf, S, ORDER_FIR * sizeof( SKP_int32 ) );

	/* Iterate over blocks of frameSizeIn input samples */
	while( 1 ) {
		nSamplesIn = SKP_min( inLen, RESAMPLER_MAX_BATCH_SIZE_IN );

	    /* Second-order AR filter (output in Q8) */
	    SKP_Silk_resampler_private_AR2( &S[ ORDER_FIR ], &buf[ ORDER_FIR ], in, 
            SKP_Silk_Resampler_1_3_COEFS_LQ, nSamplesIn );

		/* Interpolate filtered signal */
        buf_ptr = buf;
        counter = nSamplesIn;
        while( counter > 2 ) {
            /* Inner product */
            res_Q6 = SKP_SMULWB(         SKP_ADD32( buf_ptr[ 0 ], buf_ptr[ 5 ] ), SKP_Silk_Resampler_1_3_COEFS_LQ[ 2 ] );
            res_Q6 = SKP_SMLAWB( res_Q6, SKP_ADD32( buf_ptr[ 1 ], buf_ptr[ 4 ] ), SKP_Silk_Resampler_1_3_COEFS_LQ[ 3 ] );
            res_Q6 = SKP_SMLAWB( res_Q6, SKP_ADD32( buf_ptr[ 2 ], buf_ptr[ 3 ] ), SKP_Silk_Resampler_1_3_COEFS_LQ[ 4 ] );

            /* Scale down, saturate and store in output array */
            *out++ = (SKP_int16)SKP_SAT16( SKP_RSHIFT_ROUND( res_Q6, 6 ) );

            buf_ptr += 3;
            counter -= 3;
        }

		in += nSamplesIn;
		inLen -= nSamplesIn;

		if( inLen > 0 ) {
			/* More iterations to do; copy last part of filtered signal to beginning of buffer */
			SKP_memcpy( buf, &buf[ nSamplesIn ], ORDER_FIR * sizeof( SKP_int32 ) );
		} else {
			break;
		}
	}

	/* Copy last part of filtered signal to the state for the next call */
	SKP_memcpy( S, &buf[ nSamplesIn ], ORDER_FIR * sizeof( SKP_int32 ) );
}
