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
 * File Name:	SKP_Silk_resampler_private_IIR_FIR.c  			    *
 *																		*
 * Description: Hybrid IIR/FIR polyphase implementation of resampling	*
 *                                                                      *
 * Copyright 2010 (c), Skype Limited                                    *
 * All rights reserved.													*
 *                                                                      */

#include "SKP_Silk_SigProc_FIX.h"
#include "SKP_Silk_resampler_private.h"
#if EMBEDDED_ARM<5
SKP_INLINE SKP_int16 *SKP_Silk_resampler_private_IIR_FIR_INTERPOL( 
			SKP_int16 * out, SKP_int16 * buf, SKP_int32 max_index_Q16 , SKP_int32 index_increment_Q16 ){
	SKP_int32 index_Q16, res_Q15;
	SKP_int16 *buf_ptr;
	SKP_int32 table_index;
	/* Interpolate upsampled signal and store in output array */
	for( index_Q16 = 0; index_Q16 < max_index_Q16; index_Q16 += index_increment_Q16 ) {
        table_index = SKP_SMULWB( index_Q16 & 0xFFFF, 144 );
        buf_ptr = &buf[ index_Q16 >> 16 ];
            
        res_Q15 = SKP_SMULBB(          buf_ptr[ 0 ], SKP_Silk_resampler_frac_FIR_144[       table_index ][ 0 ] );
        res_Q15 = SKP_SMLABB( res_Q15, buf_ptr[ 1 ], SKP_Silk_resampler_frac_FIR_144[       table_index ][ 1 ] );
        res_Q15 = SKP_SMLABB( res_Q15, buf_ptr[ 2 ], SKP_Silk_resampler_frac_FIR_144[       table_index ][ 2 ] );
        res_Q15 = SKP_SMLABB( res_Q15, buf_ptr[ 3 ], SKP_Silk_resampler_frac_FIR_144[ 143 - table_index ][ 2 ] );
        res_Q15 = SKP_SMLABB( res_Q15, buf_ptr[ 4 ], SKP_Silk_resampler_frac_FIR_144[ 143 - table_index ][ 1 ] );
        res_Q15 = SKP_SMLABB( res_Q15, buf_ptr[ 5 ], SKP_Silk_resampler_frac_FIR_144[ 143 - table_index ][ 0 ] );          
		*out++ = (SKP_int16)SKP_SAT16( SKP_RSHIFT_ROUND( res_Q15, 15 ) );
	}
	return out;	
}
#else
extern SKP_int16 *SKP_Silk_resampler_private_IIR_FIR_INTERPOL( 
			SKP_int16 * out, SKP_int16 * buf, SKP_int32 max_index_Q16 , SKP_int32 index_increment_Q16 );
#endif
/* Upsample using a combination of allpass-based 2x upsampling and FIR interpolation */
void SKP_Silk_resampler_private_IIR_FIR(
	void	                        *SS,		    /* I/O: Resampler state 						*/
	SKP_int16						out[],		    /* O:	Output signal 							*/
	const SKP_int16					in[],		    /* I:	Input signal							*/
	SKP_int32					    inLen		    /* I:	Number of input samples					*/
)
{
    SKP_Silk_resampler_state_struct *S = (SKP_Silk_resampler_state_struct *)SS;
	SKP_int32 nSamplesIn;
	SKP_int32 max_index_Q16, index_increment_Q16;
	SKP_int16 buf[ 2 * RESAMPLER_MAX_BATCH_SIZE_IN + RESAMPLER_ORDER_FIR_144 ];
    

	/* Copy buffered samples to start of buffer */	
	SKP_memcpy( buf, S->sFIR, RESAMPLER_ORDER_FIR_144 * sizeof( SKP_int32 ) );

	/* Iterate over blocks of frameSizeIn input samples */
    index_increment_Q16 = S->invRatio_Q16;
	while( 1 ) {
		nSamplesIn = SKP_min( inLen, S->batchSize );

        if( S->input2x == 1 ) {
		    /* Upsample 2x */
            S->up2_function( S->sIIR, &buf[ RESAMPLER_ORDER_FIR_144 ], in, nSamplesIn );
        } else {
		    /* Fourth-order ARMA filter */
            SKP_Silk_resampler_private_ARMA4( S->sIIR, &buf[ RESAMPLER_ORDER_FIR_144 ], in, S->Coefs, nSamplesIn );
        }

        max_index_Q16 = SKP_LSHIFT32( nSamplesIn, 16 + S->input2x );         /* +1 if 2x upsampling */
		out = SKP_Silk_resampler_private_IIR_FIR_INTERPOL(out, buf, max_index_Q16, index_increment_Q16);    
		in += nSamplesIn;
		inLen -= nSamplesIn;

		if( inLen > 0 ) {
			/* More iterations to do; copy last part of filtered signal to beginning of buffer */
			SKP_memcpy( buf, &buf[ nSamplesIn << S->input2x ], RESAMPLER_ORDER_FIR_144 * sizeof( SKP_int32 ) );
		} else {
			break;
		}
	}

	/* Copy last part of filtered signal to the state for the next call */
	SKP_memcpy( S->sFIR, &buf[nSamplesIn << S->input2x ], RESAMPLER_ORDER_FIR_144 * sizeof( SKP_int32 ) );
}

