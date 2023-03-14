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

/*																		*
 * File Name:	SKP_Silk_resampler.c									*
 *																		*
 * Description: Interface to collection of resamplers					*
 *                                                                      *
 * Copyright 2010 (c), Skype Limited                                    *
 * All rights reserved.													*
 *                                                                      */

/* Matrix of resampling methods used:
 *                                        Fs_out (kHz)
 *                        8      12     16     24     32     44.1   48
 *
 *               8        C      UF     U      UF     UF     UF     UF
 *              12        AF     C      UF     U      UF     UF     UF
 *              16        D      AF     C      UF     U      UF     UF
 * Fs_in (kHz)  24        AIF    D      AF     C      UF     UF     U
 *              32        UF     AF     D      AF     C      UF     UF
 *              44.1      AMI    AMI    AMI    AMI    AMI    C      UF
 *              48        DAF    DAF    AF     D      AF     UF     C
 *
 * default method: UF
 *
 * C   -> Copy (no resampling)
 * D   -> Allpass-based 2x downsampling
 * U   -> Allpass-based 2x upsampling
 * DAF -> Allpass-based 2x downsampling followed by AR2 filter followed by FIR interpolation
 * UF  -> Allpass-based 2x upsampling followed by FIR interpolation
 * AMI -> ARMA4 filter followed by FIR interpolation
 * AF  -> AR2 filter followed by FIR interpolation
 *
 * Input signals sampled above 48 kHz are first downsampled to at most 48 kHz.
 * Output signals sampled above 48 kHz are upsampled from at most 48 kHz.
 */

#include "SKP_Silk_resampler_private.h"

/* Greatest common divisor */
static SKP_int32 gcd(
    SKP_int32 a,
    SKP_int32 b
)
{
    SKP_int32 tmp;
    while( b > 0 ) {
        tmp = a - b * SKP_DIV32( a, b );
        a   = b;
        b   = tmp;
    }
    return a;
}

/* Initialize/reset the resampler state for a given pair of input/output sampling rates */
SKP_int SKP_Silk_resampler_init( 
	SKP_Silk_resampler_state_struct	*S,		    /* I/O: Resampler state 			*/
	SKP_int32							Fs_Hz_in,	/* I:	Input sampling rate (Hz)	*/
	SKP_int32							Fs_Hz_out	/* I:	Output sampling rate (Hz)	*/
)
{
    SKP_int32 cycleLen, cyclesPerBatch, up2 = 0, down2 = 0;

	/* Clear state */
	SKP_memset( S, 0, sizeof( SKP_Silk_resampler_state_struct ) );

	/* Input checking */
#if RESAMPLER_SUPPORT_ABOVE_48KHZ
	if( Fs_Hz_in < 8000 || Fs_Hz_in > 192000 || Fs_Hz_out < 8000 || Fs_Hz_out > 192000 ) {
#else
    if( Fs_Hz_in < 8000 || Fs_Hz_in >  48000 || Fs_Hz_out < 8000 || Fs_Hz_out >  48000 ) {
#endif
		SKP_assert( 0 );
		return -1;
	}

#if RESAMPLER_SUPPORT_ABOVE_48KHZ
	/* Determine pre downsampling and post upsampling */
	if( Fs_Hz_in > 96000 ) {
		S->nPreDownsamplers = 2;
        S->down_pre_function = SKP_Silk_resampler_private_down4;
    } else if( Fs_Hz_in > 48000 ) {
		S->nPreDownsamplers = 1;
        S->down_pre_function = SKP_Silk_resampler_down2;
    } else {
		S->nPreDownsamplers = 0;
        S->down_pre_function = NULL;
    }

	if( Fs_Hz_out > 96000 ) {
		S->nPostUpsamplers = 2;
        S->up_post_function = SKP_Silk_resampler_private_up4;
    } else if( Fs_Hz_out > 48000 ) {
		S->nPostUpsamplers = 1;
        S->up_post_function = SKP_Silk_resampler_up2;
    } else {
		S->nPostUpsamplers = 0;
        S->up_post_function = NULL;
    }

    if( S->nPreDownsamplers + S->nPostUpsamplers > 0 ) {
        /* Ratio of output/input samples */
	    S->ratio_Q16 = SKP_LSHIFT32( SKP_DIV32( SKP_LSHIFT32( Fs_Hz_out, 13 ), Fs_Hz_in ), 3 );
        /* Make sure the ratio is rounded up */
        while( SKP_SMULWW( S->ratio_Q16, Fs_Hz_in ) < Fs_Hz_out ) S->ratio_Q16++;

        /* Batch size is 10 ms */
        S->batchSizePrePost = SKP_DIV32_16( Fs_Hz_in, 100 );

        /* Convert sampling rate to those after pre-downsampling and before post-upsampling */
	    Fs_Hz_in  = SKP_RSHIFT( Fs_Hz_in,  S->nPreDownsamplers  );
	    Fs_Hz_out = SKP_RSHIFT( Fs_Hz_out, S->nPostUpsamplers  );
    }
#endif

    /* Number of samples processed per batch */
    /* First, try 10 ms frames */
    S->batchSize = SKP_DIV32_16( Fs_Hz_in, 100 );
    if( ( SKP_MUL( S->batchSize, 100 ) != Fs_Hz_in ) || ( Fs_Hz_in % 100 != 0 ) ) {
        /* No integer number of input or output samples with 10 ms frames, use greatest common divisor */
        cycleLen = SKP_DIV32( Fs_Hz_in, gcd( Fs_Hz_in, Fs_Hz_out ) );
        cyclesPerBatch = SKP_DIV32( RESAMPLER_MAX_BATCH_SIZE_IN, cycleLen );
        if( cyclesPerBatch == 0 ) {
            /* cycleLen too big, let's just use the maximum batch size. Some distortion will result. */
            S->batchSize = RESAMPLER_MAX_BATCH_SIZE_IN;
            SKP_assert( 0 );
        } else {
            S->batchSize = SKP_MUL( cyclesPerBatch, cycleLen );
        }
    }


	/* Find resampler with the right sampling ratio */
    if( Fs_Hz_out > Fs_Hz_in ) {
        /* Upsample */
        if( Fs_Hz_out == SKP_MUL( Fs_Hz_in, 2 ) ) {                             /* Fs_out : Fs_in = 2 : 1 */
            /* Special case: directly use 2x upsampler */
    	    S->resampler_function = SKP_Silk_resampler_private_up2_HQ_wrapper;
        } else {
	        /* Default resampler */
	        S->resampler_function = SKP_Silk_resampler_private_IIR_FIR;
            up2 = 1;
            if( Fs_Hz_in > 24000 ) {
                /* Low-quality all-pass upsampler */
                S->up2_function = SKP_Silk_resampler_up2;
            } else {
                /* High-quality all-pass upsampler */
                S->up2_function = SKP_Silk_resampler_private_up2_HQ;
            }
        }
    } else if ( Fs_Hz_out < Fs_Hz_in ) {
        /* Downsample */
        if( SKP_MUL( Fs_Hz_out, 4 ) == SKP_MUL( Fs_Hz_in, 3 ) ) {               /* Fs_out : Fs_in = 3 : 4 */
    	    S->FIR_Fracs = 3;
    	    S->Coefs = SKP_Silk_Resampler_3_4_COEFS;
    	    S->resampler_function = SKP_Silk_resampler_private_down_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 3 ) == SKP_MUL( Fs_Hz_in, 2 ) ) {        /* Fs_out : Fs_in = 2 : 3 */
    	    S->FIR_Fracs = 2;
    	    S->Coefs = SKP_Silk_Resampler_2_3_COEFS;
    	    S->resampler_function = SKP_Silk_resampler_private_down_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 2 ) == Fs_Hz_in ) {                      /* Fs_out : Fs_in = 1 : 2 */
    	    S->FIR_Fracs = 1;
    	    S->Coefs = SKP_Silk_Resampler_1_2_COEFS;
    	    S->resampler_function = SKP_Silk_resampler_private_down_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 8 ) == SKP_MUL( Fs_Hz_in, 3 ) ) {        /* Fs_out : Fs_in = 3 : 8 */
    	    S->FIR_Fracs = 3;
    	    S->Coefs = SKP_Silk_Resampler_3_8_COEFS;
    	    S->resampler_function = SKP_Silk_resampler_private_down_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 3 ) == Fs_Hz_in ) {                      /* Fs_out : Fs_in = 1 : 3 */
    	    S->FIR_Fracs = 1;
    	    S->Coefs = SKP_Silk_Resampler_1_3_COEFS;
    	    S->resampler_function = SKP_Silk_resampler_private_down_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 4 ) == Fs_Hz_in ) {                      /* Fs_out : Fs_in = 1 : 4 */
    	    S->FIR_Fracs = 1;
            down2 = 1;
    	    S->Coefs = SKP_Silk_Resampler_1_2_COEFS;
            S->resampler_function = SKP_Silk_resampler_private_down_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 6 ) == Fs_Hz_in ) {                      /* Fs_out : Fs_in = 1 : 6 */
    	    S->FIR_Fracs = 1;
            down2 = 1;
    	    S->Coefs = SKP_Silk_Resampler_1_3_COEFS;
            S->resampler_function = SKP_Silk_resampler_private_down_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 441 ) == SKP_MUL( Fs_Hz_in, 80 ) ) {     /* Fs_out : Fs_in = 80 : 441 */
    	    S->Coefs = SKP_Silk_Resampler_80_441_ARMA4_COEFS;
    	    S->resampler_function = SKP_Silk_resampler_private_IIR_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 441 ) == SKP_MUL( Fs_Hz_in, 120 ) ) {    /* Fs_out : Fs_in = 120 : 441 */
    	    S->Coefs = SKP_Silk_Resampler_120_441_ARMA4_COEFS;
    	    S->resampler_function = SKP_Silk_resampler_private_IIR_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 441 ) == SKP_MUL( Fs_Hz_in, 160 ) ) {    /* Fs_out : Fs_in = 160 : 441 */
    	    S->Coefs = SKP_Silk_Resampler_160_441_ARMA4_COEFS;
    	    S->resampler_function = SKP_Silk_resampler_private_IIR_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 441 ) == SKP_MUL( Fs_Hz_in, 240 ) ) {    /* Fs_out : Fs_in = 240 : 441 */
    	    S->Coefs = SKP_Silk_Resampler_240_441_ARMA4_COEFS;
    	    S->resampler_function = SKP_Silk_resampler_private_IIR_FIR;
        } else if( SKP_MUL( Fs_Hz_out, 441 ) == SKP_MUL( Fs_Hz_in, 320 ) ) {    /* Fs_out : Fs_in = 320 : 441 */
    	    S->Coefs = SKP_Silk_Resampler_320_441_ARMA4_COEFS;
    	    S->resampler_function = SKP_Silk_resampler_private_IIR_FIR;
        } else {
	        /* Default resampler */
	        S->resampler_function = SKP_Silk_resampler_private_IIR_FIR;
            up2 = 1;
            if( Fs_Hz_in > 24000 ) {
                /* Low-quality all-pass upsampler */
                S->up2_function = SKP_Silk_resampler_up2;
            } else {
                /* High-quality all-pass upsampler */
                S->up2_function = SKP_Silk_resampler_private_up2_HQ;
            }
        }
    } else {
        /* Input and output sampling rates are equal: copy */
        S->resampler_function = SKP_Silk_resampler_private_copy;
    }

    S->input2x = up2 | down2;

    /* Ratio of input/output samples */
    S->invRatio_Q16 = SKP_LSHIFT32( SKP_DIV32( SKP_LSHIFT32( Fs_Hz_in, 14 + up2 - down2 ), Fs_Hz_out ), 2 );
    /* Make sure the ratio is rounded up */
    while( SKP_SMULWW( S->invRatio_Q16, SKP_LSHIFT32( Fs_Hz_out, down2 ) ) < SKP_LSHIFT32( Fs_Hz_in, up2 ) ) {
        S->invRatio_Q16++;
    }

	S->magic_number = 123456789;

	return 0;
}

/* Clear the states of all resampling filters, without resetting sampling rate ratio */
SKP_int SKP_Silk_resampler_clear( 
	SKP_Silk_resampler_state_struct	*S		    /* I/O: Resampler state 			*/
)
{
	/* Clear state */
	SKP_memset( S->sDown2, 0, sizeof( S->sDown2 ) );
	SKP_memset( S->sIIR,   0, sizeof( S->sIIR ) );
	SKP_memset( S->sFIR,   0, sizeof( S->sFIR ) );
#if RESAMPLER_SUPPORT_ABOVE_48KHZ
	SKP_memset( S->sDownPre, 0, sizeof( S->sDownPre ) );
	SKP_memset( S->sUpPost,  0, sizeof( S->sUpPost ) );
#endif
    return 0;
}

/* Resampler: convert from one sampling rate to another                                 */
SKP_int SKP_Silk_resampler( 
	SKP_Silk_resampler_state_struct	*S,		    /* I/O: Resampler state 			*/
	SKP_int16							out[],	    /* O:	Output signal 				*/
	const SKP_int16						in[],	    /* I:	Input signal				*/
	SKP_int32							inLen	    /* I:	Number of input samples		*/
)
{
	/* Verify that state was initialized and has not been corrupted */
    if( S->magic_number != 123456789 ) {
        SKP_assert( 0 );
        return -1;
    }

#if RESAMPLER_SUPPORT_ABOVE_48KHZ
	if( S->nPreDownsamplers + S->nPostUpsamplers > 0 ) {
		/* The input and/or output sampling rate is above 48000 Hz */
        SKP_int32       nSamplesIn, nSamplesOut;
		SKP_int16		in_buf[ 480 ], out_buf[ 480 ];

        while( inLen > 0 ) {
            /* Number of input and output samples to process */
    		nSamplesIn = SKP_min( inLen, S->batchSizePrePost );
            nSamplesOut = SKP_SMULWB( S->ratio_Q16, nSamplesIn );

            SKP_assert( SKP_RSHIFT32( nSamplesIn,  S->nPreDownsamplers ) <= 480 );
            SKP_assert( SKP_RSHIFT32( nSamplesOut, S->nPostUpsamplers  ) <= 480 );

    		if( S->nPreDownsamplers > 0 ) {
                S->down_pre_function( S->sDownPre, in_buf, in, nSamplesIn );
    		    if( S->nPostUpsamplers > 0 ) {
            		S->resampler_function( S, out_buf, in_buf, SKP_RSHIFT32( nSamplesIn, S->nPreDownsamplers ) );
                    S->up_post_function( S->sUpPost, out, out_buf, SKP_RSHIFT32( nSamplesOut, S->nPostUpsamplers ) );
                } else {
            		S->resampler_function( S, out, in_buf, SKP_RSHIFT32( nSamplesIn, S->nPreDownsamplers ) );
                }
            } else {
        		S->resampler_function( S, out_buf, in, SKP_RSHIFT32( nSamplesIn, S->nPreDownsamplers ) );
                S->up_post_function( S->sUpPost, out, out_buf, SKP_RSHIFT32( nSamplesOut, S->nPostUpsamplers ) );
            }

    		in += nSamplesIn;
            out += nSamplesOut;
	    	inLen -= nSamplesIn;
        }
	} else 
#endif
	{
		/* Input and output sampling rate are at most 48000 Hz */
		S->resampler_function( S, out, in, inLen );
	}

	return 0;
}
