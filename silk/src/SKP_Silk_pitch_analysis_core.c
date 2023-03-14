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

/***********************************************************
* Pitch analyser function
********************************************************** */
#include "SKP_Silk_SigProc_FIX.h"
#include "SKP_Silk_pitch_est_defines.h"
#include "SKP_Silk_common_pitch_est_defines.h"

#define SCRATCH_SIZE    22

/************************************************************/
/* Internally used functions                                */
/************************************************************/
void SKP_FIX_P_Ana_calc_corr_st3(
    SKP_int32        cross_corr_st3[PITCH_EST_NB_SUBFR][PITCH_EST_NB_CBKS_STAGE3_MAX][PITCH_EST_NB_STAGE3_LAGS],/* (O) 3 DIM correlation array */
    const SKP_int16  signal[],                        /* I vector to correlate         */
    SKP_int          start_lag,                       /* I lag offset to search around */
    SKP_int          sf_length,                       /* I length of a 5 ms subframe   */
    SKP_int          complexity                       /* I Complexity setting          */
);

void SKP_FIX_P_Ana_calc_energy_st3(
    SKP_int32        energies_st3[PITCH_EST_NB_SUBFR][PITCH_EST_NB_CBKS_STAGE3_MAX][PITCH_EST_NB_STAGE3_LAGS],/* (O) 3 DIM energy array */
    const SKP_int16  signal[],                        /* I vector to calc energy in    */
    SKP_int          start_lag,                       /* I lag offset to search around */
    SKP_int          sf_length,                       /* I length of one 5 ms subframe */
    SKP_int          complexity                       /* I Complexity setting          */
);

SKP_int32 SKP_FIX_P_Ana_find_scaling(
    const SKP_int16  *signal,
    const SKP_int    signal_length, 
    const SKP_int    sum_sqr_len
);

/*************************************************************/
/*      FIXED POINT CORE PITCH ANALYSIS FUNCTION             */
/*************************************************************/
SKP_int SKP_Silk_pitch_analysis_core(  /* O    Voicing estimate: 0 voiced, 1 unvoiced                      */
    const SKP_int16  *signal,            /* I    Signal of length PITCH_EST_FRAME_LENGTH_MS*Fs_kHz           */
    SKP_int          *pitch_out,         /* O    4 pitch lag values                                          */
    SKP_int          *lagIndex,          /* O    Lag Index                                                   */
    SKP_int          *contourIndex,      /* O    Pitch contour Index                                         */
    SKP_int          *LTPCorr_Q15,       /* I/O  Normalized correlation; input: value from previous frame    */
    SKP_int          prevLag,            /* I    Last lag of previous frame; set to zero is unvoiced         */
    const SKP_int32  search_thres1_Q16,  /* I    First stage threshold for lag candidates 0 - 1              */
    const SKP_int    search_thres2_Q15,  /* I    Final threshold for lag candidates 0 - 1                    */
    const SKP_int    Fs_kHz,             /* I    Sample frequency (kHz)                                      */
    const SKP_int    complexity,         /* I   Complexity setting, 0-2, where 2 is highest                 */
	const SKP_int	 forLJC			     /* I	 1 if this function is called from LJC code, 0 otherwise.  */
)
{
    SKP_int16 signal_8kHz[ PITCH_EST_MAX_FRAME_LENGTH_ST_2 ];
    SKP_int16 signal_4kHz[ PITCH_EST_MAX_FRAME_LENGTH_ST_1 ];
    SKP_int32 scratch_mem[ 3 * PITCH_EST_MAX_FRAME_LENGTH ];
    SKP_int16 *input_signal_ptr;
    SKP_int32 filt_state[ PITCH_EST_MAX_DECIMATE_STATE_LENGTH ];
    SKP_int   i, k, d, j;
    SKP_int16 C[ PITCH_EST_NB_SUBFR ][ ( PITCH_EST_MAX_LAG >> 1 ) + 5 ];
    const SKP_int16 *target_ptr, *basis_ptr;
    SKP_int32 cross_corr, normalizer, energy, shift, energy_basis, energy_target;
    SKP_int   d_srch[ PITCH_EST_D_SRCH_LENGTH ];
    SKP_int16 d_comp[ ( PITCH_EST_MAX_LAG >> 1 ) + 5 ];
    SKP_int   Cmax, length_d_srch, length_d_comp;
    SKP_int32 sum, threshold, temp32;
    SKP_int   CBimax, CBimax_new, CBimax_old, lag, start_lag, end_lag, lag_new;
    SKP_int32 CC[ PITCH_EST_NB_CBKS_STAGE2_EXT ], CCmax, CCmax_b, CCmax_new_b, CCmax_new;
    SKP_int32 energies_st3[  PITCH_EST_NB_SUBFR ][ PITCH_EST_NB_CBKS_STAGE3_MAX ][ PITCH_EST_NB_STAGE3_LAGS ];
    SKP_int32 crosscorr_st3[ PITCH_EST_NB_SUBFR ][ PITCH_EST_NB_CBKS_STAGE3_MAX ][ PITCH_EST_NB_STAGE3_LAGS ];
    SKP_int32 lag_counter;
    SKP_int   frame_length, frame_length_8kHz, frame_length_4kHz, max_sum_sq_length;
    SKP_int   sf_length, sf_length_8kHz;
    SKP_int   min_lag, min_lag_8kHz, min_lag_4kHz;
    SKP_int   max_lag, max_lag_8kHz, max_lag_4kHz;
    SKP_int32 contour_bias, diff;
    SKP_int32 lz, lshift;
    SKP_int   cbk_offset, cbk_size, nb_cbks_stage2;
    SKP_int32 delta_lag_log2_sqr_Q7, lag_log2_Q7, prevLag_log2_Q7, prev_lag_bias_Q15, corr_thres_Q15;

    /* Check for valid sampling frequency */
    SKP_assert( Fs_kHz == 8 || Fs_kHz == 12 || Fs_kHz == 16 || Fs_kHz == 24 );

    /* Check for valid complexity setting */
    SKP_assert( complexity >= SKP_Silk_PITCH_EST_MIN_COMPLEX );
    SKP_assert( complexity <= SKP_Silk_PITCH_EST_MAX_COMPLEX );

    SKP_assert( search_thres1_Q16 >= 0 && search_thres1_Q16 <= (1<<16) );
    SKP_assert( search_thres2_Q15 >= 0 && search_thres2_Q15 <= (1<<15) );

    /* Setup frame lengths max / min lag for the sampling frequency */
    frame_length      = PITCH_EST_FRAME_LENGTH_MS * Fs_kHz;
    frame_length_4kHz = PITCH_EST_FRAME_LENGTH_MS * 4;
    frame_length_8kHz = PITCH_EST_FRAME_LENGTH_MS * 8;
    sf_length         = SKP_RSHIFT( frame_length,      3 );
    sf_length_8kHz    = SKP_RSHIFT( frame_length_8kHz, 3 );
    min_lag           = PITCH_EST_MIN_LAG_MS * Fs_kHz;
    min_lag_4kHz      = PITCH_EST_MIN_LAG_MS * 4;
    min_lag_8kHz      = PITCH_EST_MIN_LAG_MS * 8;
    max_lag           = PITCH_EST_MAX_LAG_MS * Fs_kHz;
    max_lag_4kHz      = PITCH_EST_MAX_LAG_MS * 4;
    max_lag_8kHz      = PITCH_EST_MAX_LAG_MS * 8;

    SKP_memset( C, 0, sizeof( SKP_int16 ) * PITCH_EST_NB_SUBFR * ( ( PITCH_EST_MAX_LAG >> 1 ) + 5) );
    
    /* Resample from input sampled at Fs_kHz to 8 kHz */
    if( Fs_kHz == 16 ) {
        SKP_memset( filt_state, 0, 2 * sizeof( SKP_int32 ) );
        SKP_Silk_resampler_down2( filt_state, signal_8kHz, signal, frame_length );
    } else if ( Fs_kHz == 12 ) {
        SKP_int32 R23[ 6 ];
        SKP_memset( R23, 0, 6 * sizeof( SKP_int32 ) );
        SKP_Silk_resampler_down2_3( R23, signal_8kHz, signal, PITCH_EST_FRAME_LENGTH_MS * 12 );
    } else if( Fs_kHz == 24 ) {
        SKP_int32 filt_state_fix[ 8 ];
        SKP_memset( filt_state_fix, 0, 8 * sizeof(SKP_int32) );
        SKP_Silk_resampler_down3( filt_state_fix, signal_8kHz, signal, 24 * PITCH_EST_FRAME_LENGTH_MS );
    } else {
        SKP_assert( Fs_kHz == 8 );
        SKP_memcpy( signal_8kHz, signal, frame_length_8kHz * sizeof(SKP_int16) );
    }
    /* Decimate again to 4 kHz */
    SKP_memset( filt_state, 0, 2 * sizeof( SKP_int32 ) );/* Set state to zero */
    SKP_Silk_resampler_down2( filt_state, signal_4kHz, signal_8kHz, frame_length_8kHz );

    /* Low-pass filter */
    for( i = frame_length_4kHz - 1; i > 0; i-- ) {
        signal_4kHz[ i ] = SKP_ADD_SAT16( signal_4kHz[ i ], signal_4kHz[ i - 1 ] );
    }

    /*******************************************************************************
    ** Scale 4 kHz signal down to prevent correlations measures from overflowing
    ** find scaling as max scaling for each 8kHz(?) subframe
    *******************************************************************************/
    
    /* Inner product is calculated with different lengths, so scale for the worst case */
    max_sum_sq_length = SKP_max_32( sf_length_8kHz, SKP_RSHIFT( frame_length_4kHz, 1 ) );
    shift = SKP_FIX_P_Ana_find_scaling( signal_4kHz, frame_length_4kHz, max_sum_sq_length );
    if( shift > 0 ) {
        for( i = 0; i < frame_length_4kHz; i++ ) {
            signal_4kHz[ i ] = SKP_RSHIFT( signal_4kHz[ i ], shift );
        }
    }

    /******************************************************************************
    * FIRST STAGE, operating in 4 khz
    ******************************************************************************/
    target_ptr = &signal_4kHz[ SKP_RSHIFT( frame_length_4kHz, 1 ) ];
    for( k = 0; k < 2; k++ ) {
        /* Check that we are within range of the array */
        SKP_assert( target_ptr >= signal_4kHz );
        SKP_assert( target_ptr + sf_length_8kHz <= signal_4kHz + frame_length_4kHz );

        basis_ptr = target_ptr - min_lag_4kHz;

        /* Check that we are within range of the array */
        SKP_assert( basis_ptr >= signal_4kHz );
        SKP_assert( basis_ptr + sf_length_8kHz <= signal_4kHz + frame_length_4kHz );

        normalizer = 0;
        cross_corr = 0;
        /* Calculate first vector products before loop */
        cross_corr = SKP_Silk_inner_prod_aligned( target_ptr, basis_ptr, sf_length_8kHz );
        normalizer = SKP_Silk_inner_prod_aligned( basis_ptr,  basis_ptr, sf_length_8kHz );
        normalizer = SKP_ADD_SAT32( normalizer, SKP_SMULBB( sf_length_8kHz, 4000 ) );

        temp32 = SKP_DIV32( cross_corr, SKP_Silk_SQRT_APPROX( normalizer ) + 1 );
        C[ k ][ min_lag_4kHz ] = (SKP_int16)SKP_SAT16( temp32 );        /* Q0 */

        /* From now on normalizer is computed recursively */
        for( d = min_lag_4kHz + 1; d <= max_lag_4kHz; d++ ) {
            basis_ptr--;

            /* Check that we are within range of the array */
            SKP_assert( basis_ptr >= signal_4kHz );
            SKP_assert( basis_ptr + sf_length_8kHz <= signal_4kHz + frame_length_4kHz );

            cross_corr = SKP_Silk_inner_prod_aligned( target_ptr, basis_ptr, sf_length_8kHz );

            /* Add contribution of new sample and remove contribution from oldest sample */
            normalizer +=
                SKP_SMULBB( basis_ptr[ 0 ], basis_ptr[ 0 ] ) - 
                SKP_SMULBB( basis_ptr[ sf_length_8kHz ], basis_ptr[ sf_length_8kHz ] ); 
    
            temp32 = SKP_DIV32( cross_corr, SKP_Silk_SQRT_APPROX( normalizer ) + 1 );
            C[ k ][ d ] = (SKP_int16)SKP_SAT16( temp32 );                        /* Q0 */
        }
        /* Update target pointer */
        target_ptr += sf_length_8kHz;
    }

    /* Combine two subframes into single correlation measure and apply short-lag bias */
    for( i = max_lag_4kHz; i >= min_lag_4kHz; i-- ) {
        sum = (SKP_int32)C[ 0 ][ i ] + (SKP_int32)C[ 1 ][ i ];                /* Q0 */
        SKP_assert( SKP_RSHIFT( sum, 1 ) == SKP_SAT16( SKP_RSHIFT( sum, 1 ) ) );
        sum = SKP_RSHIFT( sum, 1 );                                           /* Q-1 */
        SKP_assert( SKP_LSHIFT( (SKP_int32)-i, 4 ) == SKP_SAT16( SKP_LSHIFT( (SKP_int32)-i, 4 ) ) );
        sum = SKP_SMLAWB( sum, sum, SKP_LSHIFT( -i, 4 ) );                    /* Q-1 */
        SKP_assert( sum == SKP_SAT16( sum ) );
        C[ 0 ][ i ] = (SKP_int16)sum;                                         /* Q-1 */
    }

    /* Sort */
    length_d_srch = 4 + 2 * complexity;
    SKP_assert( 3 * length_d_srch <= PITCH_EST_D_SRCH_LENGTH );
    SKP_Silk_insertion_sort_decreasing_int16( &C[ 0 ][ min_lag_4kHz ], d_srch, max_lag_4kHz - min_lag_4kHz + 1, length_d_srch );

    /* Escape if correlation is very low already here */
    target_ptr = &signal_4kHz[ SKP_RSHIFT( frame_length_4kHz, 1 ) ];
    energy = SKP_Silk_inner_prod_aligned( target_ptr, target_ptr, SKP_RSHIFT( frame_length_4kHz, 1 ) );
    energy = SKP_ADD_POS_SAT32( energy, 1000 );                              /* Q0 */
    Cmax = (SKP_int)C[ 0 ][ min_lag_4kHz ];                                  /* Q-1 */
    threshold = SKP_SMULBB( Cmax, Cmax );                                    /* Q-2 */
    /* Compare in Q-2 domain */
    if( SKP_RSHIFT( energy, 4 + 2 ) > threshold ) {                            
        SKP_memset( pitch_out, 0, PITCH_EST_NB_SUBFR * sizeof( SKP_int ) );
        *LTPCorr_Q15  = 0;
        *lagIndex     = 0;
        *contourIndex = 0;
        return 1;
    }

    threshold = SKP_SMULWB( search_thres1_Q16, Cmax );
    for( i = 0; i < length_d_srch; i++ ) {
        /* Convert to 8 kHz indices for the sorted correlation that exceeds the threshold */
        if( C[ 0 ][ min_lag_4kHz + i ] > threshold ) {
            d_srch[ i ] = ( d_srch[ i ] + min_lag_4kHz ) << 1;
        } else {
            length_d_srch = i;
            break;
        }
    }
    SKP_assert( length_d_srch > 0 );

    for( i = min_lag_8kHz - 5; i < max_lag_8kHz + 5; i++ ) {
        d_comp[ i ] = 0;
    }
    for( i = 0; i < length_d_srch; i++ ) {
        d_comp[ d_srch[ i ] ] = 1;
    }

    /* Convolution */
    for( i = max_lag_8kHz + 3; i >= min_lag_8kHz; i-- ) {
        d_comp[ i ] += d_comp[ i - 1 ] + d_comp[ i - 2 ];
    }

    length_d_srch = 0;
    for( i = min_lag_8kHz; i < max_lag_8kHz + 1; i++ ) {    
        if( d_comp[ i + 1 ] > 0 ) {
            d_srch[ length_d_srch ] = i;
            length_d_srch++;
        }
    }

    /* Convolution */
    for( i = max_lag_8kHz + 3; i >= min_lag_8kHz; i-- ) {
        d_comp[ i ] += d_comp[ i - 1 ] + d_comp[ i - 2 ] + d_comp[ i - 3 ];
    }

    length_d_comp = 0;
    for( i = min_lag_8kHz; i < max_lag_8kHz + 4; i++ ) {    
        if( d_comp[ i ] > 0 ) {
            d_comp[ length_d_comp ] = i - 2;
            length_d_comp++;
        }
    }

    /**********************************************************************************
    ** SECOND STAGE, operating at 8 kHz, on lag sections with high correlation
    *************************************************************************************/

    /******************************************************************************
    ** Scale signal down to avoid correlations measures from overflowing
    *******************************************************************************/
    /* find scaling as max scaling for each subframe */
    shift = SKP_FIX_P_Ana_find_scaling( signal_8kHz, frame_length_8kHz, sf_length_8kHz );
    if( shift > 0 ) {
        for( i = 0; i < frame_length_8kHz; i++ ) {
            signal_8kHz[ i ] = SKP_RSHIFT( signal_8kHz[ i ], shift );
        }
    }

    /********************************************************************************* 
    * Find energy of each subframe projected onto its history, for a range of delays
    *********************************************************************************/
    SKP_memset( C, 0, PITCH_EST_NB_SUBFR * ( ( PITCH_EST_MAX_LAG >> 1 ) + 5 ) * sizeof( SKP_int16 ) );
    
    target_ptr = &signal_8kHz[ frame_length_4kHz ]; /* point to middle of frame */
    for( k = 0; k < PITCH_EST_NB_SUBFR; k++ ) {

        /* Check that we are within range of the array */
        SKP_assert( target_ptr >= signal_8kHz );
        SKP_assert( target_ptr + sf_length_8kHz <= signal_8kHz + frame_length_8kHz );

        energy_target = SKP_Silk_inner_prod_aligned( target_ptr, target_ptr, sf_length_8kHz );
        // ToDo: Calculate 1 / energy_target here and save one division inside next for loop
        for( j = 0; j < length_d_comp; j++ ) {
            d = d_comp[ j ];
            basis_ptr = target_ptr - d;

            /* Check that we are within range of the array */
            SKP_assert( basis_ptr >= signal_8kHz );
            SKP_assert( basis_ptr + sf_length_8kHz <= signal_8kHz + frame_length_8kHz );
        
            cross_corr   = SKP_Silk_inner_prod_aligned( target_ptr, basis_ptr, sf_length_8kHz );
            energy_basis = SKP_Silk_inner_prod_aligned( basis_ptr,  basis_ptr, sf_length_8kHz );
            if( cross_corr > 0 ) {
                energy = SKP_max( energy_target, energy_basis ); /* Find max to make sure first division < 1.0 */
                lz = SKP_Silk_CLZ32( cross_corr );
                lshift = SKP_LIMIT_32( lz - 1, 0, 15 );
                temp32 = SKP_DIV32( SKP_LSHIFT( cross_corr, lshift ), SKP_RSHIFT( energy, 15 - lshift ) + 1 ); /* Q15 */
                SKP_assert( temp32 == SKP_SAT16( temp32 ) );
                temp32 = SKP_SMULWB( cross_corr, temp32 ); /* Q(-1), cc * ( cc / max(b, t) ) */
                temp32 = SKP_ADD_SAT32( temp32, temp32 );  /* Q(0) */
                lz = SKP_Silk_CLZ32( temp32 );
                lshift = SKP_LIMIT_32( lz - 1, 0, 15 );
                energy = SKP_min( energy_target, energy_basis );
                C[ k ][ d ] = SKP_DIV32( SKP_LSHIFT( temp32, lshift ), SKP_RSHIFT( energy, 15 - lshift ) + 1 ); // Q15
            } else {
                C[ k ][ d ] = 0;
            }
        }
        target_ptr += sf_length_8kHz;
    }

    /* search over lag range and lags codebook */
    /* scale factor for lag codebook, as a function of center lag */

    CCmax   = SKP_int32_MIN;
    CCmax_b = SKP_int32_MIN;

    CBimax = 0; /* To avoid returning undefined lag values */
    lag = -1;   /* To check if lag with strong enough correlation has been found */

    if( prevLag > 0 ) {
        if( Fs_kHz == 12 ) {
            prevLag = SKP_DIV32_16( SKP_LSHIFT( prevLag, 1 ), 3 );
        } else if( Fs_kHz == 16 ) {
            prevLag = SKP_RSHIFT( prevLag, 1 );
        } else if( Fs_kHz == 24 ) {
            prevLag = SKP_DIV32_16( prevLag, 3 );
        }
        prevLag_log2_Q7 = SKP_Silk_lin2log( (SKP_int32)prevLag );
    } else {
        prevLag_log2_Q7 = 0;
    }
    SKP_assert( search_thres2_Q15 == SKP_SAT16( search_thres2_Q15 ) );
    corr_thres_Q15 = SKP_RSHIFT( SKP_SMULBB( search_thres2_Q15, search_thres2_Q15 ), 13 );

    /* If input is 8 khz use a larger codebook here because it is last stage */
    if( Fs_kHz == 8 && complexity > SKP_Silk_PITCH_EST_MIN_COMPLEX ) {
        nb_cbks_stage2 = PITCH_EST_NB_CBKS_STAGE2_EXT;    
    } else {
        nb_cbks_stage2 = PITCH_EST_NB_CBKS_STAGE2;
    }

    for( k = 0; k < length_d_srch; k++ ) {
        d = d_srch[ k ];
        for( j = 0; j < nb_cbks_stage2; j++ ) {
            CC[ j ] = 0;
            for( i = 0; i < PITCH_EST_NB_SUBFR; i++ ) {
                /* Try all codebooks */
                CC[ j ] = CC[ j ] + (SKP_int32)C[ i ][ d + SKP_Silk_CB_lags_stage2[ i ][ j ] ];
            }
        }
        /* Find best codebook */
        CCmax_new = SKP_int32_MIN;
        CBimax_new = 0;
        for( i = 0; i < nb_cbks_stage2; i++ ) {
            if( CC[ i ] > CCmax_new ) {
                CCmax_new = CC[ i ];
                CBimax_new = i;
            }
        }

        /* Bias towards shorter lags */
        lag_log2_Q7 = SKP_Silk_lin2log( (SKP_int32)d ); /* Q7 */
	    SKP_assert( lag_log2_Q7 == SKP_SAT16( lag_log2_Q7 ) );
		SKP_assert( PITCH_EST_NB_SUBFR * PITCH_EST_SHORTLAG_BIAS_Q15 == SKP_SAT16( PITCH_EST_NB_SUBFR * PITCH_EST_SHORTLAG_BIAS_Q15 ) );

		if (forLJC) {
			CCmax_new_b = CCmax_new;
		} else {
			CCmax_new_b = CCmax_new - SKP_RSHIFT( SKP_SMULBB( PITCH_EST_NB_SUBFR * PITCH_EST_SHORTLAG_BIAS_Q15, lag_log2_Q7 ), 7 ); /* Q15 */
		}
		
        /* Bias towards previous lag */
        SKP_assert( PITCH_EST_NB_SUBFR * PITCH_EST_PREVLAG_BIAS_Q15 == SKP_SAT16( PITCH_EST_NB_SUBFR * PITCH_EST_PREVLAG_BIAS_Q15 ) );
        if( prevLag > 0 ) {
            delta_lag_log2_sqr_Q7 = lag_log2_Q7 - prevLag_log2_Q7;
            SKP_assert( delta_lag_log2_sqr_Q7 == SKP_SAT16( delta_lag_log2_sqr_Q7 ) );
            delta_lag_log2_sqr_Q7 = SKP_RSHIFT( SKP_SMULBB( delta_lag_log2_sqr_Q7, delta_lag_log2_sqr_Q7 ), 7 );
            prev_lag_bias_Q15 = SKP_RSHIFT( SKP_SMULBB( PITCH_EST_NB_SUBFR * PITCH_EST_PREVLAG_BIAS_Q15, ( *LTPCorr_Q15 ) ), 15 ); /* Q15 */
            prev_lag_bias_Q15 = SKP_DIV32( SKP_MUL( prev_lag_bias_Q15, delta_lag_log2_sqr_Q7 ), delta_lag_log2_sqr_Q7 + ( 1 << 6 ) );
            CCmax_new_b -= prev_lag_bias_Q15; /* Q15 */
        }

        if ( CCmax_new_b > CCmax_b                                          &&              /* Find maximum biased correlation                  */
              CCmax_new > corr_thres_Q15                                    &&              /* Correlation needs to be high enough to be voiced */
             SKP_Silk_CB_lags_stage2[ 0 ][ CBimax_new ] <= min_lag_8kHz                   /* Lag must be in range                             */
            ) {
            CCmax_b = CCmax_new_b;
            CCmax   = CCmax_new;
            lag     = d;
            CBimax  = CBimax_new;
        }
    }

    if( lag == -1 ) {
        /* No suitable candidate found */
        SKP_memset( pitch_out, 0, PITCH_EST_NB_SUBFR * sizeof( SKP_int ) );
        *LTPCorr_Q15  = 0;
        *lagIndex     = 0;
        *contourIndex = 0;
        return 1;
    }

    if( Fs_kHz > 8 ) {

        /******************************************************************************
        ** Scale input signal down to avoid correlations measures from overflowing
        *******************************************************************************/
        /* find scaling as max scaling for each subframe */
        shift = SKP_FIX_P_Ana_find_scaling( signal, frame_length, sf_length );
        if( shift > 0 ) {
            /* Move signal to scratch mem because the input signal should be unchanged */
            /* Reuse the 32 bit scratch mem vector, use a 16 bit pointer from now */
            input_signal_ptr = (SKP_int16*)scratch_mem;
            for( i = 0; i < frame_length; i++ ) {
                input_signal_ptr[ i ] = SKP_RSHIFT( signal[ i ], shift );
            }
        } else {
            input_signal_ptr = (SKP_int16*)signal;
        }
        /*********************************************************************************/

        /* Search in original signal */
                    
        CBimax_old = CBimax;
        /* Compensate for decimation */
        SKP_assert( lag == SKP_SAT16( lag ) );
        if( Fs_kHz == 12 ) {
            lag = SKP_RSHIFT( SKP_SMULBB( lag, 3 ), 1 );
        } else if( Fs_kHz == 16 ) {
            lag = SKP_LSHIFT( lag, 1 );
        } else {
            lag = SKP_SMULBB( lag, 3 );
        }

        lag = SKP_LIMIT_int( lag, min_lag, max_lag );
        start_lag = SKP_max_int( lag - 2, min_lag );
        end_lag   = SKP_min_int( lag + 2, max_lag );
        lag_new   = lag;                                    /* to avoid undefined lag */
        CBimax    = 0;                                        /* to avoid undefined lag */
        SKP_assert( SKP_LSHIFT( CCmax, 13 ) >= 0 ); 
        *LTPCorr_Q15 = (SKP_int)SKP_Silk_SQRT_APPROX( SKP_LSHIFT( CCmax, 13 ) ); /* Output normalized correlation */

        CCmax = SKP_int32_MIN;
        /* pitch lags according to second stage */
        for( k = 0; k < PITCH_EST_NB_SUBFR; k++ ) {
            pitch_out[ k ] = lag + 2 * SKP_Silk_CB_lags_stage2[ k ][ CBimax_old ];
        }
        /* Calculate the correlations and energies needed in stage 3 */
        SKP_FIX_P_Ana_calc_corr_st3(  crosscorr_st3, input_signal_ptr, start_lag, sf_length, complexity );
        SKP_FIX_P_Ana_calc_energy_st3( energies_st3, input_signal_ptr, start_lag, sf_length, complexity );

        lag_counter = 0;
        SKP_assert( lag == SKP_SAT16( lag ) );
        contour_bias = SKP_DIV32_16( PITCH_EST_FLATCONTOUR_BIAS_Q20, lag );

        /* Setup cbk parameters acording to complexity setting */
        cbk_size   = (SKP_int)SKP_Silk_cbk_sizes_stage3[   complexity ];
        cbk_offset = (SKP_int)SKP_Silk_cbk_offsets_stage3[ complexity ];

        for( d = start_lag; d <= end_lag; d++ ) {
            for( j = cbk_offset; j < ( cbk_offset + cbk_size ); j++ ) {
                cross_corr = 0;
                energy     = 0;
                for( k = 0; k < PITCH_EST_NB_SUBFR; k++ ) {
                    SKP_assert( PITCH_EST_NB_SUBFR == 4 );
                    energy     += SKP_RSHIFT( energies_st3[  k ][ j ][ lag_counter ], 2 ); /* use mean, to avoid overflow */
                    SKP_assert( energy >= 0 );
                    cross_corr += SKP_RSHIFT( crosscorr_st3[ k ][ j ][ lag_counter ], 2 ); /* use mean, to avoid overflow */
                }
                if( cross_corr > 0 ) {
                    /* Divide cross_corr / energy and get result in Q15 */
                    lz = SKP_Silk_CLZ32( cross_corr );
                    /* Divide with result in Q13, cross_corr could be larger than energy */
                    lshift = SKP_LIMIT_32( lz - 1, 0, 13 );
                    CCmax_new = SKP_DIV32( SKP_LSHIFT( cross_corr, lshift ), SKP_RSHIFT( energy, 13 - lshift ) + 1 );
                    CCmax_new = SKP_SAT16( CCmax_new );
                    CCmax_new = SKP_SMULWB( cross_corr, CCmax_new );
                    /* Saturate */
                    if( CCmax_new > SKP_RSHIFT( SKP_int32_MAX, 3 ) ) {
                        CCmax_new = SKP_int32_MAX;
                    } else {
                        CCmax_new = SKP_LSHIFT( CCmax_new, 3 );
                    }
                    /* Reduce depending on flatness of contour */
                    diff = j - SKP_RSHIFT( PITCH_EST_NB_CBKS_STAGE3_MAX, 1 );
                    diff = SKP_MUL( diff, diff );
                    diff = SKP_int16_MAX - SKP_RSHIFT( SKP_MUL( contour_bias, diff ), 5 ); /* Q20 -> Q15 */
                    SKP_assert( diff == SKP_SAT16( diff ) );
                    CCmax_new = SKP_LSHIFT( SKP_SMULWB( CCmax_new, diff ), 1 );
                } else {
                    CCmax_new = 0;
                }

                if( CCmax_new > CCmax                                               && 
                   ( d + (SKP_int)SKP_Silk_CB_lags_stage3[ 0 ][ j ] ) <= max_lag  
                   ) {
                    CCmax   = CCmax_new;
                    lag_new = d;
                    CBimax  = j;
                }
            }
            lag_counter++;
        }

        for( k = 0; k < PITCH_EST_NB_SUBFR; k++ ) {
            pitch_out[ k ] = lag_new + SKP_Silk_CB_lags_stage3[ k ][ CBimax ];
        }
        *lagIndex = lag_new - min_lag;
        *contourIndex = CBimax;
    } else {
        /* Save Lags and correlation */
        CCmax = SKP_max( CCmax, 0 );
        *LTPCorr_Q15 = (SKP_int)SKP_Silk_SQRT_APPROX( SKP_LSHIFT( CCmax, 13 ) ); /* Output normalized correlation */
        for( k = 0; k < PITCH_EST_NB_SUBFR; k++ ) {
            pitch_out[ k ] = lag + SKP_Silk_CB_lags_stage2[ k ][ CBimax ];
        }
        *lagIndex = lag - min_lag_8kHz;
        *contourIndex = CBimax;
    }
    SKP_assert( *lagIndex >= 0 );
    /* return as voiced */
    return 0;
}

/*************************************************************************/
/* Calculates the correlations used in stage 3 search. In order to cover */
/* the whole lag codebook for all the searched offset lags (lag +- 2),   */
/*************************************************************************/
void SKP_FIX_P_Ana_calc_corr_st3(
    SKP_int32        cross_corr_st3[ PITCH_EST_NB_SUBFR ][ PITCH_EST_NB_CBKS_STAGE3_MAX ][ PITCH_EST_NB_STAGE3_LAGS ],/* (O) 3 DIM correlation array */
    const SKP_int16  signal[],                        /* I vector to correlate         */
    SKP_int          start_lag,                       /* I lag offset to search around */
    SKP_int          sf_length,                       /* I length of a 5 ms subframe   */
    SKP_int          complexity                       /* I Complexity setting          */
)
{
    const SKP_int16 *target_ptr, *basis_ptr;
    SKP_int32    cross_corr;
    SKP_int        i, j, k, lag_counter;
    SKP_int        cbk_offset, cbk_size, delta, idx;
    SKP_int32    scratch_mem[ SCRATCH_SIZE ];

    SKP_assert( complexity >= SKP_Silk_PITCH_EST_MIN_COMPLEX );
    SKP_assert( complexity <= SKP_Silk_PITCH_EST_MAX_COMPLEX );

    cbk_offset = SKP_Silk_cbk_offsets_stage3[ complexity ];
    cbk_size   = SKP_Silk_cbk_sizes_stage3[   complexity ];

    target_ptr = &signal[ SKP_LSHIFT( sf_length, 2 ) ]; /* Pointer to middle of frame */
    for( k = 0; k < PITCH_EST_NB_SUBFR; k++ ) {
        lag_counter = 0;

        /* Calculate the correlations for each subframe */
        for( j = SKP_Silk_Lag_range_stage3[ complexity ][ k ][ 0 ]; j <= SKP_Silk_Lag_range_stage3[ complexity ][ k ][ 1 ]; j++ ) {
            basis_ptr = target_ptr - ( start_lag + j );
            cross_corr = SKP_Silk_inner_prod_aligned( (SKP_int16*)target_ptr, (SKP_int16*)basis_ptr, sf_length );
            SKP_assert( lag_counter < SCRATCH_SIZE );
            scratch_mem[ lag_counter ] = cross_corr;
            lag_counter++;
        }

        delta = SKP_Silk_Lag_range_stage3[ complexity ][ k ][ 0 ];
        for( i = cbk_offset; i < ( cbk_offset + cbk_size ); i++ ) { 
            /* Fill out the 3 dim array that stores the correlations for */
            /* each code_book vector for each start lag */
            idx = SKP_Silk_CB_lags_stage3[ k ][ i ] - delta;
            for( j = 0; j < PITCH_EST_NB_STAGE3_LAGS; j++ ) {
                SKP_assert( idx + j < SCRATCH_SIZE );
                SKP_assert( idx + j < lag_counter );
                cross_corr_st3[ k ][ i ][ j ] = scratch_mem[ idx + j ];
            }
        }
        target_ptr += sf_length;
    }
}

/********************************************************************/
/* Calculate the energies for first two subframes. The energies are */
/* calculated recursively.                                          */
/********************************************************************/
void SKP_FIX_P_Ana_calc_energy_st3(
    SKP_int32        energies_st3[ PITCH_EST_NB_SUBFR ][ PITCH_EST_NB_CBKS_STAGE3_MAX ][ PITCH_EST_NB_STAGE3_LAGS ],/* (O) 3 DIM energy array */
    const SKP_int16  signal[],                        /* I vector to calc energy in    */
    SKP_int          start_lag,                       /* I lag offset to search around */
    SKP_int          sf_length,                       /* I length of one 5 ms subframe */
    SKP_int          complexity                       /* I Complexity setting          */
)
{
    const SKP_int16 *target_ptr, *basis_ptr;
    SKP_int32    energy;
    SKP_int        k, i, j, lag_counter;
    SKP_int        cbk_offset, cbk_size, delta, idx;
    SKP_int32    scratch_mem[ SCRATCH_SIZE ];

    SKP_assert( complexity >= SKP_Silk_PITCH_EST_MIN_COMPLEX );
    SKP_assert( complexity <= SKP_Silk_PITCH_EST_MAX_COMPLEX );

    cbk_offset = SKP_Silk_cbk_offsets_stage3[ complexity ];
    cbk_size   = SKP_Silk_cbk_sizes_stage3[   complexity ];

    target_ptr = &signal[ SKP_LSHIFT( sf_length, 2 ) ];
    for( k = 0; k < PITCH_EST_NB_SUBFR; k++ ) {
        lag_counter = 0;

        /* Calculate the energy for first lag */
        basis_ptr = target_ptr - ( start_lag + SKP_Silk_Lag_range_stage3[ complexity ][ k ][ 0 ] );
        energy = SKP_Silk_inner_prod_aligned( basis_ptr, basis_ptr, sf_length );
        SKP_assert( energy >= 0 );
        scratch_mem[ lag_counter ] = energy;
        lag_counter++;

        for( i = 1; i < ( SKP_Silk_Lag_range_stage3[ complexity ][ k ][ 1 ] - SKP_Silk_Lag_range_stage3[ complexity ][ k ][ 0 ] + 1 ); i++ ) {
            /* remove part outside new window */
            energy -= SKP_SMULBB( basis_ptr[ sf_length - i ], basis_ptr[ sf_length - i ] );
            SKP_assert( energy >= 0 );

            /* add part that comes into window */
            energy = SKP_ADD_SAT32( energy, SKP_SMULBB( basis_ptr[ -i ], basis_ptr[ -i ] ) );
            SKP_assert( energy >= 0 );
            SKP_assert( lag_counter < SCRATCH_SIZE );
            scratch_mem[ lag_counter ] = energy;
            lag_counter++;
        }

        delta = SKP_Silk_Lag_range_stage3[ complexity ][ k ][ 0 ];
        for( i = cbk_offset; i < ( cbk_offset + cbk_size ); i++ ) { 
            /* Fill out the 3 dim array that stores the correlations for    */
            /* each code_book vector for each start lag                        */
            idx = SKP_Silk_CB_lags_stage3[ k ][ i ] - delta;
            for( j = 0; j < PITCH_EST_NB_STAGE3_LAGS; j++ ) {
                SKP_assert( idx + j < SCRATCH_SIZE );
                SKP_assert( idx + j < lag_counter );
                energies_st3[ k ][ i ][ j ] = scratch_mem[ idx + j ];
                SKP_assert( energies_st3[ k ][ i ][ j ] >= 0.0f );
            }
        }
        target_ptr += sf_length;
    }
}

SKP_int32 SKP_FIX_P_Ana_find_scaling(
    const SKP_int16  *signal,
    const SKP_int    signal_length, 
    const SKP_int    sum_sqr_len
)
{
    SKP_int32 nbits, x_max;
    
    x_max = SKP_Silk_int16_array_maxabs( signal, signal_length );

    if( x_max < SKP_int16_MAX ) {
        /* Number of bits needed for the sum of the squares */
        nbits = 32 - SKP_Silk_CLZ32( SKP_SMULBB( x_max, x_max ) ); 
    } else {
        /* Here we don't know if x_max should have been SKP_int16_MAX + 1, so we expect the worst case */
        nbits = 30;
    }
    nbits += 17 - SKP_Silk_CLZ16( sum_sqr_len );

    /* Without a guarantee of saturation, we need to keep the 31st bit free */
    if( nbits < 31 ) {
        return 0;
    } else {
        return( nbits - 30 );
    }
}
