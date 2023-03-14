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
#include "SKP_Silk_PLC.h"

#define NB_ATT 2
static const SKP_int16 HARM_ATT_Q15[NB_ATT]              = { 32440, 31130 }; /* 0.99, 0.95 */
static const SKP_int16 PLC_RAND_ATTENUATE_V_Q15[NB_ATT]  = { 31130, 26214 }; /* 0.95, 0.8 */
static const SKP_int16 PLC_RAND_ATTENUATE_UV_Q15[NB_ATT] = { 32440, 29491 }; /* 0.99, 0.9 */

void SKP_Silk_PLC_Reset(
    SKP_Silk_decoder_state      *psDec              /* I/O Decoder state        */
)
{
    psDec->sPLC.pitchL_Q8 = SKP_RSHIFT( psDec->frame_length, 1 );
}

void SKP_Silk_PLC(
    SKP_Silk_decoder_state      *psDec,             /* I Decoder state          */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I Decoder control        */
    SKP_int16                   signal[],           /* O Concealed signal       */
    SKP_int                     length,             /* I length of residual     */
    SKP_int                     lost                /* I Loss flag              */
)
{
    /* PLC control function */
    if( psDec->fs_kHz != psDec->sPLC.fs_kHz ) {
        SKP_Silk_PLC_Reset( psDec );
        psDec->sPLC.fs_kHz = psDec->fs_kHz;
    }

    if( lost ) {
        /****************************/
        /* Generate Signal          */
        /****************************/
        SKP_Silk_PLC_conceal( psDec, psDecCtrl, signal, length );

        psDec->lossCnt++;
    } else {
        /****************************/
        /* Update state             */
        /****************************/
        SKP_Silk_PLC_update( psDec, psDecCtrl, signal, length );
    }
}

/**************************************************/
/* Update state of PLC                            */
/**************************************************/
void SKP_Silk_PLC_update(
    SKP_Silk_decoder_state      *psDec,             /* (I/O) Decoder state          */
    SKP_Silk_decoder_control    *psDecCtrl,         /* (I/O) Decoder control        */
    SKP_int16                   signal[],
    SKP_int                     length
)
{
    SKP_int32 LTP_Gain_Q14, temp_LTP_Gain_Q14;
    SKP_int   i, j;
    SKP_Silk_PLC_struct *psPLC;

    psPLC = &psDec->sPLC;

    /* Update parameters used in case of packet loss */
    psDec->prev_sigtype = psDecCtrl->sigtype;
    LTP_Gain_Q14 = 0;
    if( psDecCtrl->sigtype == SIG_TYPE_VOICED ) {
        /* Find the parameters for the last subframe which contains a pitch pulse */
        for( j = 0; j * psDec->subfr_length  < psDecCtrl->pitchL[ NB_SUBFR - 1 ]; j++ ) {
            temp_LTP_Gain_Q14 = 0;
            for( i = 0; i < LTP_ORDER; i++ ) {
                temp_LTP_Gain_Q14 += psDecCtrl->LTPCoef_Q14[ ( NB_SUBFR - 1 - j ) * LTP_ORDER  + i ];
            }
            if( temp_LTP_Gain_Q14 > LTP_Gain_Q14 ) {
                LTP_Gain_Q14 = temp_LTP_Gain_Q14;
                SKP_memcpy( psPLC->LTPCoef_Q14,
                    &psDecCtrl->LTPCoef_Q14[ SKP_SMULBB( NB_SUBFR - 1 - j, LTP_ORDER ) ],
                    LTP_ORDER * sizeof( SKP_int16 ) );

                psPLC->pitchL_Q8 = SKP_LSHIFT( psDecCtrl->pitchL[ NB_SUBFR - 1 - j ], 8 );
            }
        }

#if USE_SINGLE_TAP
        SKP_memset( psPLC->LTPCoef_Q14, 0, LTP_ORDER * sizeof( SKP_int16 ) );
        psPLC->LTPCoef_Q14[ LTP_ORDER / 2 ] = LTP_Gain_Q14;
#endif

        /* Limit LT coefs */
        if( LTP_Gain_Q14 < V_PITCH_GAIN_START_MIN_Q14 ) {
            SKP_int   scale_Q10;
            SKP_int32 tmp;

            tmp = SKP_LSHIFT( V_PITCH_GAIN_START_MIN_Q14, 10 );
            scale_Q10 = SKP_DIV32( tmp, SKP_max( LTP_Gain_Q14, 1 ) );
            for( i = 0; i < LTP_ORDER; i++ ) {
                psPLC->LTPCoef_Q14[ i ] = SKP_RSHIFT( SKP_SMULBB( psPLC->LTPCoef_Q14[ i ], scale_Q10 ), 10 );
            }
        } else if( LTP_Gain_Q14 > V_PITCH_GAIN_START_MAX_Q14 ) {
            SKP_int   scale_Q14;
            SKP_int32 tmp;

            tmp = SKP_LSHIFT( V_PITCH_GAIN_START_MAX_Q14, 14 );
            scale_Q14 = SKP_DIV32( tmp, SKP_max( LTP_Gain_Q14, 1 ) );
            for( i = 0; i < LTP_ORDER; i++ ) {
                psPLC->LTPCoef_Q14[ i ] = SKP_RSHIFT( SKP_SMULBB( psPLC->LTPCoef_Q14[ i ], scale_Q14 ), 14 );
            }
        }
    } else {
        psPLC->pitchL_Q8 = SKP_LSHIFT( SKP_SMULBB( psDec->fs_kHz, 18 ), 8 );
        SKP_memset( psPLC->LTPCoef_Q14, 0, LTP_ORDER * sizeof( SKP_int16 ));
    }

    /* Save LPC coeficients */
    SKP_memcpy( psPLC->prevLPC_Q12, psDecCtrl->PredCoef_Q12[ 1 ], psDec->LPC_order * sizeof( SKP_int16 ) );
    psPLC->prevLTP_scale_Q14 = psDecCtrl->LTP_scale_Q14;

    /* Save Gains */
    SKP_memcpy( psPLC->prevGain_Q16, psDecCtrl->Gains_Q16, NB_SUBFR * sizeof( SKP_int32 ) );
}

void SKP_Silk_PLC_conceal(
    SKP_Silk_decoder_state      *psDec,             /* I/O Decoder state */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I/O Decoder control */
    SKP_int16                   signal[],           /* O concealed signal */
    SKP_int                     length              /* I length of residual */
)
{
    SKP_int   i, j, k;
    SKP_int16 *B_Q14, exc_buf[ MAX_FRAME_LENGTH ], *exc_buf_ptr;
    SKP_int16 rand_scale_Q14;
    union {
        SKP_int16 as_int16[ MAX_LPC_ORDER ];
        SKP_int32 as_int32[ MAX_LPC_ORDER / 2 ];
    } A_Q12_tmp;
    SKP_int32 rand_seed, harm_Gain_Q15, rand_Gain_Q15;
    SKP_int   lag, idx, sLTP_buf_idx, shift1, shift2;
    SKP_int32 energy1, energy2, *rand_ptr, *pred_lag_ptr;
    SKP_int32 sig_Q10[ MAX_FRAME_LENGTH ], *sig_Q10_ptr, LPC_exc_Q10, LPC_pred_Q10,  LTP_pred_Q14;
    SKP_Silk_PLC_struct *psPLC;
#if !defined(_SYSTEM_IS_BIG_ENDIAN)
    SKP_int32 Atmp;
#endif
    psPLC = &psDec->sPLC;

    /* Update LTP buffer */
    SKP_memcpy( psDec->sLTP_Q16, &psDec->sLTP_Q16[ psDec->frame_length ], psDec->frame_length * sizeof( SKP_int32 ) );

    /* LPC concealment. Apply BWE to previous LPC */
    SKP_Silk_bwexpander( psPLC->prevLPC_Q12, psDec->LPC_order, BWE_COEF_Q16 );

    /* Find random noise component */
    /* Scale previous excitation signal */
    exc_buf_ptr = exc_buf;
    for( k = ( NB_SUBFR >> 1 ); k < NB_SUBFR; k++ ) {
        for( i = 0; i < psDec->subfr_length; i++ ) {
            exc_buf_ptr[ i ] = ( SKP_int16 )SKP_RSHIFT( 
                SKP_SMULWW( psDec->exc_Q10[ i + k * psDec->subfr_length ], psPLC->prevGain_Q16[ k ] ), 10 );
        }
        exc_buf_ptr += psDec->subfr_length;
    }
    /* Find the subframe with lowest energy of the last two and use that as random noise generator */ 
    SKP_Silk_sum_sqr_shift( &energy1, &shift1, exc_buf,                         psDec->subfr_length );
    SKP_Silk_sum_sqr_shift( &energy2, &shift2, &exc_buf[ psDec->subfr_length ], psDec->subfr_length );
        
    if( SKP_RSHIFT( energy1, shift2 ) < SKP_RSHIFT( energy2, shift1 ) ) {
        /* First sub-frame has lowest energy */
        rand_ptr = &psDec->exc_Q10[ SKP_max_int( 0, 3 * psDec->subfr_length - RAND_BUF_SIZE ) ];
    } else {
        /* Second sub-frame has lowest energy */
        rand_ptr = &psDec->exc_Q10[ SKP_max_int( 0, psDec->frame_length - RAND_BUF_SIZE ) ];
    }

    /* Setup Gain to random noise component */ 
    B_Q14          = psPLC->LTPCoef_Q14;
    rand_scale_Q14 = psPLC->randScale_Q14;

    /* Setup attenuation gains */
    harm_Gain_Q15 = HARM_ATT_Q15[ SKP_min_int( NB_ATT - 1, psDec->lossCnt ) ];
    if( psDec->prev_sigtype == SIG_TYPE_VOICED ) {
        rand_Gain_Q15 = PLC_RAND_ATTENUATE_V_Q15[  SKP_min_int( NB_ATT - 1, psDec->lossCnt ) ];
    } else {
        rand_Gain_Q15 = PLC_RAND_ATTENUATE_UV_Q15[ SKP_min_int( NB_ATT - 1, psDec->lossCnt ) ];
    }

    /* First Lost frame */
    if( psDec->lossCnt == 0 ) {
        rand_scale_Q14 = (1 << 14 );
    
        /* Reduce random noise Gain for voiced frames */
        if( psDec->prev_sigtype == SIG_TYPE_VOICED ) {
            for( i = 0; i < LTP_ORDER; i++ ) {
                rand_scale_Q14 -= B_Q14[ i ];
            }
            rand_scale_Q14 = SKP_max_16( 3277, rand_scale_Q14 ); /* 0.2 */
            rand_scale_Q14 = ( SKP_int16 )SKP_RSHIFT( SKP_SMULBB( rand_scale_Q14, psPLC->prevLTP_scale_Q14 ), 14 );
        }

        /* Reduce random noise for unvoiced frames with high LPC gain */
        if( psDec->prev_sigtype == SIG_TYPE_UNVOICED ) {
            SKP_int32 invGain_Q30, down_scale_Q30;
            
            SKP_Silk_LPC_inverse_pred_gain( &invGain_Q30, psPLC->prevLPC_Q12, psDec->LPC_order );
            
            down_scale_Q30 = SKP_min_32( SKP_RSHIFT( ( 1 << 30 ), LOG2_INV_LPC_GAIN_HIGH_THRES ), invGain_Q30 );
            down_scale_Q30 = SKP_max_32( SKP_RSHIFT( ( 1 << 30 ), LOG2_INV_LPC_GAIN_LOW_THRES ), down_scale_Q30 );
            down_scale_Q30 = SKP_LSHIFT( down_scale_Q30, LOG2_INV_LPC_GAIN_HIGH_THRES );
            
            rand_Gain_Q15 = SKP_RSHIFT( SKP_SMULWB( down_scale_Q30, rand_Gain_Q15 ), 14 );
        }
    }

    rand_seed    = psPLC->rand_seed;
    lag          = SKP_RSHIFT_ROUND( psPLC->pitchL_Q8, 8 );
    sLTP_buf_idx = psDec->frame_length;

    /***************************/
    /* LTP synthesis filtering */
    /***************************/
    sig_Q10_ptr = sig_Q10;
    for( k = 0; k < NB_SUBFR; k++ ) {
        /* Setup pointer */
        pred_lag_ptr = &psDec->sLTP_Q16[ sLTP_buf_idx - lag + LTP_ORDER / 2 ];
        for( i = 0; i < psDec->subfr_length; i++ ) {
            rand_seed = SKP_RAND( rand_seed );
            idx = SKP_RSHIFT( rand_seed, 25 ) & RAND_BUF_MASK;

            /* Unrolled loop */
            LTP_pred_Q14 = SKP_SMULWB(               pred_lag_ptr[  0 ], B_Q14[ 0 ] );
            LTP_pred_Q14 = SKP_SMLAWB( LTP_pred_Q14, pred_lag_ptr[ -1 ], B_Q14[ 1 ] );
            LTP_pred_Q14 = SKP_SMLAWB( LTP_pred_Q14, pred_lag_ptr[ -2 ], B_Q14[ 2 ] );
            LTP_pred_Q14 = SKP_SMLAWB( LTP_pred_Q14, pred_lag_ptr[ -3 ], B_Q14[ 3 ] );
            LTP_pred_Q14 = SKP_SMLAWB( LTP_pred_Q14, pred_lag_ptr[ -4 ], B_Q14[ 4 ] );
            pred_lag_ptr++;
            
            /* Generate LPC residual */
            LPC_exc_Q10 = SKP_LSHIFT( SKP_SMULWB( rand_ptr[ idx ], rand_scale_Q14 ), 2 ); /* Random noise part */
            LPC_exc_Q10 = SKP_ADD32( LPC_exc_Q10, SKP_RSHIFT_ROUND( LTP_pred_Q14, 4 ) );  /* Harmonic part */
            
            /* Update states */
            psDec->sLTP_Q16[ sLTP_buf_idx ] = SKP_LSHIFT( LPC_exc_Q10, 6 );
            sLTP_buf_idx++;
                
            /* Save LPC residual */
            sig_Q10_ptr[ i ] = LPC_exc_Q10;
        }
        sig_Q10_ptr += psDec->subfr_length;
        /* Gradually reduce LTP gain */
        for( j = 0; j < LTP_ORDER; j++ ) {
            B_Q14[ j ] = SKP_RSHIFT( SKP_SMULBB( harm_Gain_Q15, B_Q14[ j ] ), 15 );
        }
        /* Gradually reduce excitation gain */
        rand_scale_Q14 = SKP_RSHIFT( SKP_SMULBB( rand_scale_Q14, rand_Gain_Q15 ), 15 );

        /* Slowly increase pitch lag */
        psPLC->pitchL_Q8 += SKP_SMULWB( psPLC->pitchL_Q8, PITCH_DRIFT_FAC_Q16 );
        psPLC->pitchL_Q8 = SKP_min_32( psPLC->pitchL_Q8, SKP_LSHIFT( SKP_SMULBB( MAX_PITCH_LAG_MS, psDec->fs_kHz ), 8 ) );
        lag = SKP_RSHIFT_ROUND( psPLC->pitchL_Q8, 8 );
    }

    /***************************/
    /* LPC synthesis filtering */
    /***************************/
    sig_Q10_ptr = sig_Q10;
    /* Preload LPC coeficients to array on stack. Gives small performance gain */
    SKP_memcpy( A_Q12_tmp.as_int16, psPLC->prevLPC_Q12, psDec->LPC_order * sizeof( SKP_int16 ) );
    SKP_assert( psDec->LPC_order >= 10 ); /* check that unrolling works */
    for( k = 0; k < NB_SUBFR; k++ ) {
        for( i = 0; i < psDec->subfr_length; i++ ){
            /* partly unrolled */
#if !defined(_SYSTEM_IS_BIG_ENDIAN)
            /* NOTE: the code below loads two int16 values in an int32, and multiplies each using the   */
            /* SMLAWB and SMLAWT instructions. On a big-endian CPU the two int16 variables would be     */
            /* loaded in reverse order and the code will give the wrong result. In that case swapping   */
            /* the SMLAWB and SMLAWT instructions should solve the problem.                             */
            Atmp = A_Q12_tmp.as_int32[ 0 ];    /* read two coefficients at once */
            LPC_pred_Q10 = SKP_SMULWB(               psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  1 ], Atmp );
            LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  2 ], Atmp );
            Atmp = A_Q12_tmp.as_int32[ 1 ];
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  3 ], Atmp );
            LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  4 ], Atmp );
            Atmp = A_Q12_tmp.as_int32[ 2 ];
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  5 ], Atmp );
            LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  6 ], Atmp );
            Atmp = A_Q12_tmp.as_int32[ 3 ];
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  7 ], Atmp );
            LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  8 ], Atmp );
            Atmp = A_Q12_tmp.as_int32[ 4 ];
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  9 ], Atmp );
            LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i - 10 ], Atmp );
            for( j = 10 ; j < psDec->LPC_order ; j+=2 ) {
                Atmp = A_Q12_tmp.as_int32[ j / 2 ];
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  1 - j ], Atmp );
                LPC_pred_Q10 = SKP_SMLAWT( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  2 - j ], Atmp );
            }
#else
            LPC_pred_Q10 = SKP_SMULWB(               psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  1 ], A_Q12_tmp.as_int16[ 0 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  2 ], A_Q12_tmp.as_int16[ 1 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  3 ], A_Q12_tmp.as_int16[ 2 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  4 ], A_Q12_tmp.as_int16[ 3 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  5 ], A_Q12_tmp.as_int16[ 4 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  6 ], A_Q12_tmp.as_int16[ 5 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  7 ], A_Q12_tmp.as_int16[ 6 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  8 ], A_Q12_tmp.as_int16[ 7 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i -  9 ], A_Q12_tmp.as_int16[ 8 ] );
            LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i - 10 ], A_Q12_tmp.as_int16[ 9 ] );

            for( j = 10; j < psDec->LPC_order; j++ ) {
                LPC_pred_Q10 = SKP_SMLAWB( LPC_pred_Q10, psDec->sLPC_Q14[ MAX_LPC_ORDER + i - j - 1 ], A_Q12_tmp.as_int16[ j ] );
            }
#endif
            /* Add prediction to LPC residual */
            sig_Q10_ptr[ i ] = SKP_ADD32( sig_Q10_ptr[ i ], LPC_pred_Q10 );
                
            /* Update states */
            psDec->sLPC_Q14[ MAX_LPC_ORDER + i ] = SKP_LSHIFT( sig_Q10_ptr[ i ], 4 );
        }
        sig_Q10_ptr += psDec->subfr_length;
        /* Update LPC filter state */
        SKP_memcpy( psDec->sLPC_Q14, &psDec->sLPC_Q14[ psDec->subfr_length ], MAX_LPC_ORDER * sizeof( SKP_int32 ) );
    }

    /* Scale with Gain */
    for( i = 0; i < psDec->frame_length; i++ ) {
        signal[ i ] = ( SKP_int16 )SKP_SAT16( SKP_RSHIFT_ROUND( SKP_SMULWW( sig_Q10[ i ], psPLC->prevGain_Q16[ NB_SUBFR - 1 ] ), 10 ) );
    }

    /**************************************/
    /* Update states                      */
    /**************************************/
    psPLC->rand_seed     = rand_seed;
    psPLC->randScale_Q14 = rand_scale_Q14;
    for( i = 0; i < NB_SUBFR; i++ ) {
        psDecCtrl->pitchL[ i ] = lag;
    }
}

/* Glues concealed frames with new good recieved frames             */
void SKP_Silk_PLC_glue_frames(
    SKP_Silk_decoder_state      *psDec,             /* I/O decoder state    */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I/O Decoder control  */
    SKP_int16                   signal[],           /* I/O signal           */
    SKP_int                     length              /* I length of residual */
)
{
    SKP_int   i, energy_shift;
    SKP_int32 energy;
    SKP_Silk_PLC_struct *psPLC;
    psPLC = &psDec->sPLC;

    if( psDec->lossCnt ) {
        /* Calculate energy in concealed residual */
        SKP_Silk_sum_sqr_shift( &psPLC->conc_energy, &psPLC->conc_energy_shift, signal, length );
        
        psPLC->last_frame_lost = 1;
    } else {
        if( psDec->sPLC.last_frame_lost ) {
            /* Calculate residual in decoded signal if last frame was lost */
            SKP_Silk_sum_sqr_shift( &energy, &energy_shift, signal, length );

            /* Normalize energies */
            if( energy_shift > psPLC->conc_energy_shift ) {
                psPLC->conc_energy = SKP_RSHIFT( psPLC->conc_energy, energy_shift - psPLC->conc_energy_shift );
            } else if( energy_shift < psPLC->conc_energy_shift ) {
                energy = SKP_RSHIFT( energy, psPLC->conc_energy_shift - energy_shift );
            }

            /* Fade in the energy difference */
            if( energy > psPLC->conc_energy ) {
                SKP_int32 frac_Q24, LZ;
                SKP_int32 gain_Q12, slope_Q12;

                LZ = SKP_Silk_CLZ32( psPLC->conc_energy );
                LZ = LZ - 1;
                psPLC->conc_energy = SKP_LSHIFT( psPLC->conc_energy, LZ );
                energy = SKP_RSHIFT( energy, SKP_max_32( 24 - LZ, 0 ) );
                
                frac_Q24 = SKP_DIV32( psPLC->conc_energy, SKP_max( energy, 1 ) );
                
                gain_Q12 = SKP_Silk_SQRT_APPROX( frac_Q24 );
                slope_Q12 = SKP_DIV32_16( ( 1 << 12 ) - gain_Q12, length );

                for( i = 0; i < length; i++ ) {
                    signal[ i ] = SKP_RSHIFT( SKP_MUL( gain_Q12, signal[ i ] ), 12 );
                    gain_Q12 += slope_Q12;
                    gain_Q12 = SKP_min( gain_Q12, ( 1 << 12 ) );
                }
            }
        }
        psPLC->last_frame_lost = 0;

    }
}

