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

#include "SKP_Silk_main_FIX.h"
#include "SKP_Silk_tuning_parameters.h"

/* Find pitch lags */
void SKP_Silk_find_pitch_lags_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,         /* I/O  encoder state                               */
    SKP_Silk_encoder_control_FIX    *psEncCtrl,     /* I/O  encoder control                             */
    SKP_int16                       res[],          /* O    residual                                    */
    const SKP_int16                 x[]             /* I    Speech signal                               */
)
{
    SKP_Silk_predict_state_FIX *psPredSt = &psEnc->sPred;
    SKP_int   buf_len, i, scale;
    SKP_int32 thrhld_Q15, res_nrg;
    const SKP_int16 *x_buf, *x_buf_ptr;
    SKP_int16 Wsig[      FIND_PITCH_LPC_WIN_MAX ], *Wsig_ptr;
    SKP_int32 auto_corr[ MAX_FIND_PITCH_LPC_ORDER + 1 ];
    SKP_int16 rc_Q15[    MAX_FIND_PITCH_LPC_ORDER ];
    SKP_int32 A_Q24[     MAX_FIND_PITCH_LPC_ORDER ];
    SKP_int32 FiltState[ MAX_FIND_PITCH_LPC_ORDER ];
    SKP_int16 A_Q12[     MAX_FIND_PITCH_LPC_ORDER ];

    /******************************************/
    /* Setup buffer lengths etc based on Fs   */
    /******************************************/
    buf_len = SKP_ADD_LSHIFT( psEnc->sCmn.la_pitch, psEnc->sCmn.frame_length, 1 );

    /* Safty check */
    SKP_assert( buf_len >= psPredSt->pitch_LPC_win_length );

    x_buf = x - psEnc->sCmn.frame_length;

    /*************************************/
    /* Estimate LPC AR coefficients      */
    /*************************************/
    
    /* Calculate windowed signal */
    
    /* First LA_LTP samples */
    x_buf_ptr = x_buf + buf_len - psPredSt->pitch_LPC_win_length;
    Wsig_ptr  = Wsig;
    SKP_Silk_apply_sine_window( Wsig_ptr, x_buf_ptr, 1, psEnc->sCmn.la_pitch );

    /* Middle un - windowed samples */
    Wsig_ptr  += psEnc->sCmn.la_pitch;
    x_buf_ptr += psEnc->sCmn.la_pitch;
    SKP_memcpy( Wsig_ptr, x_buf_ptr, ( psPredSt->pitch_LPC_win_length - SKP_LSHIFT( psEnc->sCmn.la_pitch, 1 ) ) * sizeof( SKP_int16 ) );

    /* Last LA_LTP samples */
    Wsig_ptr  += psPredSt->pitch_LPC_win_length - SKP_LSHIFT( psEnc->sCmn.la_pitch, 1 );
    x_buf_ptr += psPredSt->pitch_LPC_win_length - SKP_LSHIFT( psEnc->sCmn.la_pitch, 1 );
    SKP_Silk_apply_sine_window( Wsig_ptr, x_buf_ptr, 2, psEnc->sCmn.la_pitch );

    /* Calculate autocorrelation sequence */
    SKP_Silk_autocorr( auto_corr, &scale, Wsig, psPredSt->pitch_LPC_win_length, psEnc->sCmn.pitchEstimationLPCOrder + 1 ); 
        
    /* Add white noise, as fraction of energy */
    auto_corr[ 0 ] = SKP_SMLAWB( auto_corr[ 0 ], auto_corr[ 0 ], SKP_FIX_CONST( FIND_PITCH_WHITE_NOISE_FRACTION, 16 ) );

    /* Calculate the reflection coefficients using schur */
    res_nrg = SKP_Silk_schur( rc_Q15, auto_corr, psEnc->sCmn.pitchEstimationLPCOrder );

    /* Prediction gain */
    psEncCtrl->predGain_Q16 = SKP_DIV32_varQ( auto_corr[ 0 ], SKP_max_int( res_nrg, 1 ), 16 );

    /* Convert reflection coefficients to prediction coefficients */
    SKP_Silk_k2a( A_Q24, rc_Q15, psEnc->sCmn.pitchEstimationLPCOrder );
    
    /* Convert From 32 bit Q24 to 16 bit Q12 coefs */
    for( i = 0; i < psEnc->sCmn.pitchEstimationLPCOrder; i++ ) {
        A_Q12[ i ] = ( SKP_int16 )SKP_SAT16( SKP_RSHIFT( A_Q24[ i ], 12 ) );
    }

    /* Do BWE */
    SKP_Silk_bwexpander( A_Q12, psEnc->sCmn.pitchEstimationLPCOrder, SKP_FIX_CONST( FIND_PITCH_BANDWITH_EXPANSION, 16 ) );
    
    /*****************************************/
    /* LPC analysis filtering                */
    /*****************************************/
    SKP_memset( FiltState, 0, psEnc->sCmn.pitchEstimationLPCOrder * sizeof( SKP_int32 ) ); /* Not really necessary, but Valgrind will complain otherwise */
    SKP_Silk_MA_Prediction( x_buf, A_Q12, FiltState, res, buf_len, psEnc->sCmn.pitchEstimationLPCOrder );
    SKP_memset( res, 0, psEnc->sCmn.pitchEstimationLPCOrder * sizeof( SKP_int16 ) );

    /* Threshold for pitch estimator */
    thrhld_Q15 = SKP_FIX_CONST( 0.45, 15 );
    thrhld_Q15 = SKP_SMLABB( thrhld_Q15, SKP_FIX_CONST( -0.004, 15 ), psEnc->sCmn.pitchEstimationLPCOrder );
    thrhld_Q15 = SKP_SMLABB( thrhld_Q15, SKP_FIX_CONST( -0.1,   7  ), psEnc->speech_activity_Q8 );
    thrhld_Q15 = SKP_SMLABB( thrhld_Q15, SKP_FIX_CONST(  0.15,  15 ), psEnc->sCmn.prev_sigtype );
    thrhld_Q15 = SKP_SMLAWB( thrhld_Q15, SKP_FIX_CONST( -0.1,   16 ), psEncCtrl->input_tilt_Q15 );
    thrhld_Q15 = SKP_SAT16(  thrhld_Q15 );

    /*****************************************/
    /* Call pitch estimator                  */
    /*****************************************/
    psEncCtrl->sCmn.sigtype = SKP_Silk_pitch_analysis_core( res, psEncCtrl->sCmn.pitchL, &psEncCtrl->sCmn.lagIndex, 
        &psEncCtrl->sCmn.contourIndex, &psEnc->LTPCorr_Q15, psEnc->sCmn.prevLag, psEnc->sCmn.pitchEstimationThreshold_Q16, 
        ( SKP_int16 )thrhld_Q15, psEnc->sCmn.fs_kHz, psEnc->sCmn.pitchEstimationComplexity, SKP_FALSE );
}
