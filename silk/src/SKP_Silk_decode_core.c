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


void SKP_Silk_decode_short_term_prediction(
SKP_int32	*vec_Q10,
SKP_int32	*pres_Q10,
SKP_int32	*sLPC_Q14,
SKP_int16	*A_Q12_tmp, 
SKP_int		LPC_order,
SKP_int		subfr_length
);


/**********************************************************/
/* Core decoder. Performs inverse NSQ operation LTP + LPC */
/**********************************************************/
void SKP_Silk_decode_core(
    SKP_Silk_decoder_state      *psDec,                             /* I/O  Decoder state               */
    SKP_Silk_decoder_control    *psDecCtrl,                         /* I    Decoder control             */
    SKP_int16                   xq[],                               /* O    Decoded speech              */
    const SKP_int               q[ MAX_FRAME_LENGTH ]               /* I    Pulse signal                */
)
{
    SKP_int   i, k, lag = 0, start_idx, sLTP_buf_idx, NLSF_interpolation_flag, sigtype;
    SKP_int16 *A_Q12, *B_Q14, *pxq, A_Q12_tmp[ MAX_LPC_ORDER ];
    SKP_int16 sLTP[ MAX_FRAME_LENGTH ];
    SKP_int32 LTP_pred_Q14, Gain_Q16, inv_gain_Q16, inv_gain_Q32, gain_adj_Q16, rand_seed, offset_Q10, dither;
    SKP_int32 *pred_lag_ptr, *pexc_Q10, *pres_Q10;
    SKP_int32 vec_Q10[ MAX_FRAME_LENGTH / NB_SUBFR ];
    SKP_int32 FiltState[ MAX_LPC_ORDER ];

    SKP_assert( psDec->prev_inv_gain_Q16 != 0 );
    
    offset_Q10 = SKP_Silk_Quantization_Offsets_Q10[ psDecCtrl->sigtype ][ psDecCtrl->QuantOffsetType ];

    if( psDecCtrl->NLSFInterpCoef_Q2 < ( 1 << 2 ) ) {
        NLSF_interpolation_flag = 1;
    } else {
        NLSF_interpolation_flag = 0;
    }


    /* Decode excitation */
    rand_seed = psDecCtrl->Seed;
    for( i = 0; i < psDec->frame_length; i++ ) {
        rand_seed = SKP_RAND( rand_seed );
        /* dither = rand_seed < 0 ? 0xFFFFFFFF : 0; */
        dither = SKP_RSHIFT( rand_seed, 31 );

        psDec->exc_Q10[ i ] = SKP_LSHIFT( ( SKP_int32 )q[ i ], 10 ) + offset_Q10;
        psDec->exc_Q10[ i ] = ( psDec->exc_Q10[ i ] ^ dither ) - dither;

        rand_seed += q[ i ];
    }


    pexc_Q10 = psDec->exc_Q10;
    pres_Q10 = psDec->res_Q10;
    pxq      = &psDec->outBuf[ psDec->frame_length ];
    sLTP_buf_idx = psDec->frame_length;
    /* Loop over subframes */
    for( k = 0; k < NB_SUBFR; k++ ) {
        A_Q12 = psDecCtrl->PredCoef_Q12[ k >> 1 ];

        /* Preload LPC coeficients to array on stack. Gives small performance gain */        
        SKP_memcpy( A_Q12_tmp, A_Q12, psDec->LPC_order * sizeof( SKP_int16 ) ); 
        B_Q14         = &psDecCtrl->LTPCoef_Q14[ k * LTP_ORDER ];
        Gain_Q16      = psDecCtrl->Gains_Q16[ k ];
        sigtype       = psDecCtrl->sigtype;

        inv_gain_Q16 = SKP_INVERSE32_varQ( SKP_max( Gain_Q16, 1 ), 32 );
        inv_gain_Q16 = SKP_min( inv_gain_Q16, SKP_int16_MAX );

        /* Calculate Gain adjustment factor */
        gain_adj_Q16 = ( SKP_int32 )1 << 16;
        if( inv_gain_Q16 != psDec->prev_inv_gain_Q16 ) {
            gain_adj_Q16 =  SKP_DIV32_varQ( inv_gain_Q16, psDec->prev_inv_gain_Q16, 16 );
        }

        /* Avoid abrupt transition from voiced PLC to unvoiced normal decoding */
        if( psDec->lossCnt && psDec->prev_sigtype == SIG_TYPE_VOICED &&
            psDecCtrl->sigtype == SIG_TYPE_UNVOICED && k < ( NB_SUBFR >> 1 ) ) {
            
            SKP_memset( B_Q14, 0, LTP_ORDER * sizeof( SKP_int16 ) );
            B_Q14[ LTP_ORDER/2 ] = ( SKP_int16 )1 << 12; /* 0.25 */
        
            sigtype = SIG_TYPE_VOICED;
            psDecCtrl->pitchL[ k ] = psDec->lagPrev;
        }

        if( sigtype == SIG_TYPE_VOICED ) {
            /* Voiced */
            
            lag = psDecCtrl->pitchL[ k ];
            /* Re-whitening */
            if( ( k & ( 3 - SKP_LSHIFT( NLSF_interpolation_flag, 1 ) ) ) == 0 ) {
                /* Rewhiten with new A coefs */
                start_idx = psDec->frame_length - lag - psDec->LPC_order - LTP_ORDER / 2;
                SKP_assert( start_idx >= 0 );
                SKP_assert( start_idx <= psDec->frame_length - psDec->LPC_order );

                SKP_memset( FiltState, 0, psDec->LPC_order * sizeof( SKP_int32 ) ); /* Not really necessary, but Valgrind and Coverity will complain otherwise */
                SKP_Silk_MA_Prediction( &psDec->outBuf[ start_idx + k * ( psDec->frame_length >> 2 ) ], 
                    A_Q12, FiltState, sLTP + start_idx, psDec->frame_length - start_idx, psDec->LPC_order );

                /* After rewhitening the LTP state is unscaled */
                inv_gain_Q32 = SKP_LSHIFT( inv_gain_Q16, 16 );
                if( k == 0 ) {
                    /* Do LTP downscaling */
                    inv_gain_Q32 = SKP_LSHIFT( SKP_SMULWB( inv_gain_Q32, psDecCtrl->LTP_scale_Q14 ), 2 );
                }
                for( i = 0; i < (lag + LTP_ORDER/2); i++ ) {
                    psDec->sLTP_Q16[ sLTP_buf_idx - i - 1 ] = SKP_SMULWB( inv_gain_Q32, sLTP[ psDec->frame_length - i - 1 ] );
                }
            } else {
                /* Update LTP state when Gain changes */
                if( gain_adj_Q16 != ( SKP_int32 )1 << 16 ) {
                    for( i = 0; i < ( lag + LTP_ORDER / 2 ); i++ ) {
                        psDec->sLTP_Q16[ sLTP_buf_idx - i - 1 ] = SKP_SMULWW( gain_adj_Q16, psDec->sLTP_Q16[ sLTP_buf_idx - i - 1 ] );
                    }
                }
            }
        }
        
        /* Scale short term state */
        for( i = 0; i < MAX_LPC_ORDER; i++ ) {
            psDec->sLPC_Q14[ i ] = SKP_SMULWW( gain_adj_Q16, psDec->sLPC_Q14[ i ] );
        }

        /* Save inv_gain */
        SKP_assert( inv_gain_Q16 != 0 );
        psDec->prev_inv_gain_Q16 = inv_gain_Q16;

        /* Long-term prediction */
        if( sigtype == SIG_TYPE_VOICED ) {
            /* Setup pointer */
            pred_lag_ptr = &psDec->sLTP_Q16[ sLTP_buf_idx - lag + LTP_ORDER / 2 ];
            for( i = 0; i < psDec->subfr_length; i++ ) {
                /* Unrolled loop */
                LTP_pred_Q14 = SKP_SMULWB(               pred_lag_ptr[  0 ], B_Q14[ 0 ] );
                LTP_pred_Q14 = SKP_SMLAWB( LTP_pred_Q14, pred_lag_ptr[ -1 ], B_Q14[ 1 ] );
                LTP_pred_Q14 = SKP_SMLAWB( LTP_pred_Q14, pred_lag_ptr[ -2 ], B_Q14[ 2 ] );
                LTP_pred_Q14 = SKP_SMLAWB( LTP_pred_Q14, pred_lag_ptr[ -3 ], B_Q14[ 3 ] );
                LTP_pred_Q14 = SKP_SMLAWB( LTP_pred_Q14, pred_lag_ptr[ -4 ], B_Q14[ 4 ] );
                pred_lag_ptr++;
            
                /* Generate LPC residual */ 
                pres_Q10[ i ] = SKP_ADD32( pexc_Q10[ i ], SKP_RSHIFT_ROUND( LTP_pred_Q14, 4 ) );
            
                /* Update states */
                psDec->sLTP_Q16[ sLTP_buf_idx ] = SKP_LSHIFT( pres_Q10[ i ], 6 );
                sLTP_buf_idx++;
            }
        } else {
            SKP_memcpy( pres_Q10, pexc_Q10, psDec->subfr_length * sizeof( SKP_int32 ) );
        }

	SKP_Silk_decode_short_term_prediction(vec_Q10, pres_Q10, psDec->sLPC_Q14,A_Q12_tmp,psDec->LPC_order,psDec->subfr_length);

        /* Scale with Gain */
        for( i = 0; i < psDec->subfr_length; i++ ) {
            pxq[ i ] = ( SKP_int16 )SKP_SAT16( SKP_RSHIFT_ROUND( SKP_SMULWW( vec_Q10[ i ], Gain_Q16 ), 10 ) );
        }

        /* Update LPC filter state */
        SKP_memcpy( psDec->sLPC_Q14, &psDec->sLPC_Q14[ psDec->subfr_length ], MAX_LPC_ORDER * sizeof( SKP_int32 ) );
        pexc_Q10 += psDec->subfr_length;
        pres_Q10 += psDec->subfr_length;
        pxq      += psDec->subfr_length;
    }
    
    /* Copy to output */
    SKP_memcpy( xq, &psDec->outBuf[ psDec->frame_length ], psDec->frame_length * sizeof( SKP_int16 ) );

}

#if EMBEDDED_ARM<5 
void SKP_Silk_decode_short_term_prediction(
SKP_int32	*vec_Q10,
SKP_int32	*pres_Q10,
SKP_int32	*sLPC_Q14,
SKP_int16	*A_Q12_tmp, 
SKP_int		LPC_order,
SKP_int		subfr_length
)
{
  SKP_int	i;
  SKP_int32	LPC_pred_Q10;
  #if !defined(_SYSTEM_IS_BIG_ENDIAN)
  SKP_int32	Atmp;
        /* Short term prediction */
        /* NOTE: the code below loads two int16 values in an int32, and multiplies each using the   */
        /* SMLAWB and SMLAWT instructions. On a big-endian CPU the two int16 variables would be     */
        /* loaded in reverse order and the code will give the wrong result. In that case swapping   */
        /* the SMLAWB and SMLAWT instructions should solve the problem.                             */
        if( LPC_order == 16 ) {
            for( i = 0; i < subfr_length; i++ ) {
                /* unrolled */
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 0 ] );    /* read two coefficients at once */
                LPC_pred_Q10 = SKP_SMULWB(               sLPC_Q14[ MAX_LPC_ORDER + i -  1 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  2 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 2 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  3 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  4 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 4 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  5 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  6 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 6 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  7 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  8 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 8 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  9 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i - 10 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 10 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i - 11 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i - 12 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 12 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i - 13 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i - 14 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 14 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i - 15 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i - 16 ], Atmp );
                
                /* Add prediction to LPC residual */
                vec_Q10[ i ] = SKP_ADD32( pres_Q10[ i ], LPC_pred_Q10 );
                
                /* Update states */
                sLPC_Q14[ MAX_LPC_ORDER + i ] = SKP_LSHIFT_ovflw( vec_Q10[ i ], 4 );
            }
        } else {
            SKP_assert( LPC_order == 10 );
            for( i = 0; i < subfr_length; i++ ) {
                /* unrolled */
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 0 ] );    /* read two coefficients at once */
                LPC_pred_Q10 = SKP_SMULWB(               sLPC_Q14[ MAX_LPC_ORDER + i -  1 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  2 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 2 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  3 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  4 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 4 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  5 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  6 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 6 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  7 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  8 ], Atmp );
                Atmp = *( ( SKP_int32* )&A_Q12_tmp[ 8 ] );
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  9 ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i - 10 ], Atmp );
                
                /* Add prediction to LPC residual */
                vec_Q10[ i ] = SKP_ADD32( pres_Q10[ i ], LPC_pred_Q10 );
                
                /* Update states */
                sLPC_Q14[ MAX_LPC_ORDER + i ] = SKP_LSHIFT_ovflw( vec_Q10[ i ], 4 );
            }
        }
#else
    SKP_int j;
        for( i = 0; i < subfr_length; i++ ) {
            /* Partially unrolled */
            LPC_pred_Q10 = SKP_SMULWB(               sLPC_Q14[ MAX_LPC_ORDER + i -  1 ], A_Q12_tmp[ 0 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  2 ], A_Q12_tmp[ 1 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  3 ], A_Q12_tmp[ 2 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  4 ], A_Q12_tmp[ 3 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  5 ], A_Q12_tmp[ 4 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  6 ], A_Q12_tmp[ 5 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  7 ], A_Q12_tmp[ 6 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  8 ], A_Q12_tmp[ 7 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i -  9 ], A_Q12_tmp[ 8 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i - 10 ], A_Q12_tmp[ 9 ] );

            for( j = 10; j < LPC_order; j ++ ) {
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, sLPC_Q14[ MAX_LPC_ORDER + i - j - 1 ], A_Q12_tmp[ j ] );
            }

            /* Add prediction to LPC residual */
            vec_Q10[ i ] = SKP_ADD32( pres_Q10[ i ], LPC_pred_Q10 );
            
            /* Update states */
            sLPC_Q14[ MAX_LPC_ORDER + i ] = SKP_LSHIFT_ovflw( vec_Q10[ i ], 4 );
        }
#endif
}
#endif



