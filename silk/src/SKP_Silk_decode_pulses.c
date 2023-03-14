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

#include "SKP_Silk_main.h"

/*********************************************/
/* Decode quantization indices of excitation */
/*********************************************/
void SKP_Silk_decode_pulses(
    SKP_Silk_range_coder_state      *psRC,              /* I/O  Range coder state                           */
    SKP_Silk_decoder_control        *psDecCtrl,         /* I/O  Decoder control                             */
    SKP_int                         q[],                /* O    Excitation signal                           */
    const SKP_int                   frame_length        /* I    Frame length (preliminary)                  */
)
{
    SKP_int   i, j, k, iter, abs_q, nLS, bit;
    SKP_int   sum_pulses[ MAX_NB_SHELL_BLOCKS ], nLshifts[ MAX_NB_SHELL_BLOCKS ];
    SKP_int   *pulses_ptr;
    const SKP_uint16 *cdf_ptr;
    
    /*********************/
    /* Decode rate level */
    /*********************/
    SKP_Silk_range_decoder( &psDecCtrl->RateLevelIndex, psRC, 
            SKP_Silk_rate_levels_CDF[ psDecCtrl->sigtype ], SKP_Silk_rate_levels_CDF_offset );

    /* Calculate number of shell blocks */
    iter = frame_length / SHELL_CODEC_FRAME_LENGTH;
    
    /***************************************************/
    /* Sum-Weighted-Pulses Decoding                    */
    /***************************************************/
    cdf_ptr = SKP_Silk_pulses_per_block_CDF[ psDecCtrl->RateLevelIndex ];
    for( i = 0; i < iter; i++ ) {
        nLshifts[ i ] = 0;
        SKP_Silk_range_decoder( &sum_pulses[ i ], psRC, cdf_ptr, SKP_Silk_pulses_per_block_CDF_offset );

        /* LSB indication */
        while( sum_pulses[ i ] == ( MAX_PULSES + 1 ) ) {
            nLshifts[ i ]++;
            SKP_Silk_range_decoder( &sum_pulses[ i ], psRC, 
                    SKP_Silk_pulses_per_block_CDF[ N_RATE_LEVELS - 1 ], SKP_Silk_pulses_per_block_CDF_offset );
        }
    }
    
    /***************************************************/
    /* Shell decoding                                  */
    /***************************************************/
    for( i = 0; i < iter; i++ ) {
        if( sum_pulses[ i ] > 0 ) {
            SKP_Silk_shell_decoder( &q[ SKP_SMULBB( i, SHELL_CODEC_FRAME_LENGTH ) ], psRC, sum_pulses[ i ] );
        } else {
            SKP_memset( &q[ SKP_SMULBB( i, SHELL_CODEC_FRAME_LENGTH ) ], 0, SHELL_CODEC_FRAME_LENGTH * sizeof( SKP_int ) );
        }
    }

    /***************************************************/
    /* LSB Decoding                                    */
    /***************************************************/
    for( i = 0; i < iter; i++ ) {
        if( nLshifts[ i ] > 0 ) {
            nLS = nLshifts[ i ];
            pulses_ptr = &q[ SKP_SMULBB( i, SHELL_CODEC_FRAME_LENGTH ) ];
            for( k = 0; k < SHELL_CODEC_FRAME_LENGTH; k++ ) {
                abs_q = pulses_ptr[ k ];
                for( j = 0; j < nLS; j++ ) {
                    abs_q = SKP_LSHIFT( abs_q, 1 ); 
                    SKP_Silk_range_decoder( &bit, psRC, SKP_Silk_lsb_CDF, 1 );
                    abs_q += bit;
                }
                pulses_ptr[ k ] = abs_q;
            }
        }
    }

    /****************************************/
    /* Decode and add signs to pulse signal */
    /****************************************/
    SKP_Silk_decode_signs( psRC, q, frame_length, psDecCtrl->sigtype, 
        psDecCtrl->QuantOffsetType, psDecCtrl->RateLevelIndex);
}
