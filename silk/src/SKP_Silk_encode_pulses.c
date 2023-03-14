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
/* Encode quantization indices of excitation */
/*********************************************/

SKP_INLINE SKP_int combine_and_check(       /* return ok */
    SKP_int         *pulses_comb,           /* O */
    const SKP_int   *pulses_in,             /* I */
    SKP_int         max_pulses,             /* I    max value for sum of pulses */
    SKP_int         len                     /* I    number of output values */
) 
{
    SKP_int k, sum;

    for( k = 0; k < len; k++ ) {
        sum = pulses_in[ 2 * k ] + pulses_in[ 2 * k + 1 ];
        if( sum > max_pulses ) {
            return 1;
        }
        pulses_comb[ k ] = sum;
    }

    return 0;
}

/* Encode quantization indices of excitation */
void SKP_Silk_encode_pulses(
    SKP_Silk_range_coder_state      *psRC,          /* I/O  Range coder state               */
    const SKP_int                   sigtype,        /* I    Sigtype                         */
    const SKP_int                   QuantOffsetType,/* I    QuantOffsetType                 */
    const SKP_int8                  q[],            /* I    quantization indices            */
    const SKP_int                   frame_length    /* I    Frame length                    */
)
{
    SKP_int   i, k, j, iter, bit, nLS, scale_down, RateLevelIndex = 0;
    SKP_int32 abs_q, minSumBits_Q6, sumBits_Q6;
    SKP_int   abs_pulses[ MAX_FRAME_LENGTH ];
    SKP_int   sum_pulses[ MAX_NB_SHELL_BLOCKS ];
    SKP_int   nRshifts[   MAX_NB_SHELL_BLOCKS ];
    SKP_int   pulses_comb[ 8 ];
    SKP_int   *abs_pulses_ptr;
    const SKP_int8 *pulses_ptr;
    const SKP_uint16 *cdf_ptr;
    const SKP_int16 *nBits_ptr;

    SKP_memset( pulses_comb, 0, 8 * sizeof( SKP_int ) ); // Fixing Valgrind reported problem

    /****************************/
    /* Prepare for shell coding */
    /****************************/
    /* Calculate number of shell blocks */
    iter = frame_length / SHELL_CODEC_FRAME_LENGTH;
    
    /* Take the absolute value of the pulses */
    for( i = 0; i < frame_length; i+=4 ) {
        abs_pulses[i+0] = ( SKP_int )SKP_abs( q[ i + 0 ] );
        abs_pulses[i+1] = ( SKP_int )SKP_abs( q[ i + 1 ] );
        abs_pulses[i+2] = ( SKP_int )SKP_abs( q[ i + 2 ] );
        abs_pulses[i+3] = ( SKP_int )SKP_abs( q[ i + 3 ] );
    }

    /* Calc sum pulses per shell code frame */
    abs_pulses_ptr = abs_pulses;
    for( i = 0; i < iter; i++ ) {
        nRshifts[ i ] = 0;

        while( 1 ) {
            /* 1+1 -> 2 */
            scale_down = combine_and_check( pulses_comb, abs_pulses_ptr, SKP_Silk_max_pulses_table[ 0 ], 8 );

            /* 2+2 -> 4 */
            scale_down += combine_and_check( pulses_comb, pulses_comb, SKP_Silk_max_pulses_table[ 1 ], 4 );

            /* 4+4 -> 8 */
            scale_down += combine_and_check( pulses_comb, pulses_comb, SKP_Silk_max_pulses_table[ 2 ], 2 );

            /* 8+8 -> 16 */
            sum_pulses[ i ] = pulses_comb[ 0 ] + pulses_comb[ 1 ];
            if( sum_pulses[ i ] > SKP_Silk_max_pulses_table[ 3 ] ) {
                scale_down++;
            }

            if( scale_down ) {
                /* We need to down scale the quantization signal */
                nRshifts[ i ]++;                
                for( k = 0; k < SHELL_CODEC_FRAME_LENGTH; k++ ) {
                    abs_pulses_ptr[ k ] = SKP_RSHIFT( abs_pulses_ptr[ k ], 1 );
                }
            } else {
                /* Jump out of while(1) loop and go to next shell coding frame */
                break;
            }
        }
        abs_pulses_ptr += SHELL_CODEC_FRAME_LENGTH;
    }

    /**************/
    /* Rate level */
    /**************/
    /* find rate level that leads to fewest bits for coding of pulses per block info */
    minSumBits_Q6 = SKP_int32_MAX;
    for( k = 0; k < N_RATE_LEVELS - 1; k++ ) {
        nBits_ptr  = SKP_Silk_pulses_per_block_BITS_Q6[ k ];
        sumBits_Q6 = SKP_Silk_rate_levels_BITS_Q6[sigtype][ k ];
        for( i = 0; i < iter; i++ ) {
            if( nRshifts[ i ] > 0 ) {
                sumBits_Q6 += nBits_ptr[ MAX_PULSES + 1 ];
            } else {
                sumBits_Q6 += nBits_ptr[ sum_pulses[ i ] ];
            }
        }
        if( sumBits_Q6 < minSumBits_Q6 ) {
            minSumBits_Q6 = sumBits_Q6;
            RateLevelIndex = k;
        }
    }
    SKP_Silk_range_encoder( psRC, RateLevelIndex, SKP_Silk_rate_levels_CDF[ sigtype ] );

    /***************************************************/
    /* Sum-Weighted-Pulses Encoding                    */
    /***************************************************/
    cdf_ptr = SKP_Silk_pulses_per_block_CDF[ RateLevelIndex ];
    for( i = 0; i < iter; i++ ) {
        if( nRshifts[ i ] == 0 ) {
            SKP_Silk_range_encoder( psRC, sum_pulses[ i ], cdf_ptr );
        } else {
            SKP_Silk_range_encoder( psRC, MAX_PULSES + 1, cdf_ptr );
            for( k = 0; k < nRshifts[ i ] - 1; k++ ) {
                SKP_Silk_range_encoder( psRC, MAX_PULSES + 1, SKP_Silk_pulses_per_block_CDF[ N_RATE_LEVELS - 1 ] );
            }
            SKP_Silk_range_encoder( psRC, sum_pulses[ i ], SKP_Silk_pulses_per_block_CDF[ N_RATE_LEVELS - 1 ] );
        }
    }

    /******************/
    /* Shell Encoding */
    /******************/
    for( i = 0; i < iter; i++ ) {
        if( sum_pulses[ i ] > 0 ) {
            SKP_Silk_shell_encoder( psRC, &abs_pulses[ i * SHELL_CODEC_FRAME_LENGTH ] );
        }
    }

    /****************/
    /* LSB Encoding */
    /****************/
    for( i = 0; i < iter; i++ ) {
        if( nRshifts[ i ] > 0 ) {
            pulses_ptr = &q[ i * SHELL_CODEC_FRAME_LENGTH ];
            nLS = nRshifts[ i ] - 1;
            for( k = 0; k < SHELL_CODEC_FRAME_LENGTH; k++ ) {
                abs_q = (SKP_int8)SKP_abs( pulses_ptr[ k ] );
                for( j = nLS; j > 0; j-- ) {
                    bit = SKP_RSHIFT( abs_q, j ) & 1;
                    SKP_Silk_range_encoder( psRC, bit, SKP_Silk_lsb_CDF );
                }
                bit = abs_q & 1;
                SKP_Silk_range_encoder( psRC, bit, SKP_Silk_lsb_CDF );
            }
        }
    }

    /****************/
    /* Encode signs */
    /****************/
    SKP_Silk_encode_signs( psRC, q, frame_length, sigtype, QuantOffsetType, RateLevelIndex );
}
