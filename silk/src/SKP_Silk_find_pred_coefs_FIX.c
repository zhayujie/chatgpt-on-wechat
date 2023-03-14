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


void SKP_Silk_find_pred_coefs_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,         /* I/O  encoder state                               */
    SKP_Silk_encoder_control_FIX    *psEncCtrl,     /* I/O  encoder control                             */
    const SKP_int16                 res_pitch[]     /* I    Residual from pitch analysis                */
)
{
    SKP_int         i;
    SKP_int32       WLTP[ NB_SUBFR * LTP_ORDER * LTP_ORDER ];
    SKP_int32       invGains_Q16[ NB_SUBFR ], local_gains[ NB_SUBFR ], Wght_Q15[ NB_SUBFR ];
    SKP_int         NLSF_Q15[ MAX_LPC_ORDER ];
    const SKP_int16 *x_ptr;
    SKP_int16       *x_pre_ptr, LPC_in_pre[ NB_SUBFR * MAX_LPC_ORDER + MAX_FRAME_LENGTH ];
    SKP_int32       tmp, min_gain_Q16;
    SKP_int         LTP_corrs_rshift[ NB_SUBFR ];


    /* weighting for weighted least squares */
    min_gain_Q16 = SKP_int32_MAX >> 6;
    for( i = 0; i < NB_SUBFR; i++ ) {
        min_gain_Q16 = SKP_min( min_gain_Q16, psEncCtrl->Gains_Q16[ i ] );
    }
    for( i = 0; i < NB_SUBFR; i++ ) {
        /* Divide to Q16 */
        SKP_assert( psEncCtrl->Gains_Q16[ i ] > 0 );
        /* Invert and normalize gains, and ensure that maximum invGains_Q16 is within range of a 16 bit int */
        invGains_Q16[ i ] = SKP_DIV32_varQ( min_gain_Q16, psEncCtrl->Gains_Q16[ i ], 16 - 2 );

        /* Ensure Wght_Q15 a minimum value 1 */
        invGains_Q16[ i ] = SKP_max( invGains_Q16[ i ], 363 ); 
        
        /* Square the inverted gains */
        SKP_assert( invGains_Q16[ i ] == SKP_SAT16( invGains_Q16[ i ] ) );
        tmp = SKP_SMULWB( invGains_Q16[ i ], invGains_Q16[ i ] );
        Wght_Q15[ i ] = SKP_RSHIFT( tmp, 1 );

        /* Invert the inverted and normalized gains */
        local_gains[ i ] = SKP_DIV32( ( 1 << 16 ), invGains_Q16[ i ] );
    }

    if( psEncCtrl->sCmn.sigtype == SIG_TYPE_VOICED ) {
        /**********/
        /* VOICED */
        /**********/
        SKP_assert( psEnc->sCmn.frame_length - psEnc->sCmn.predictLPCOrder >= psEncCtrl->sCmn.pitchL[ 0 ] + LTP_ORDER / 2 );

        /* LTP analysis */
        SKP_Silk_find_LTP_FIX( psEncCtrl->LTPCoef_Q14, WLTP, &psEncCtrl->LTPredCodGain_Q7, res_pitch, 
            res_pitch + SKP_RSHIFT( psEnc->sCmn.frame_length, 1 ), psEncCtrl->sCmn.pitchL, Wght_Q15, 
            psEnc->sCmn.subfr_length, psEnc->sCmn.frame_length, LTP_corrs_rshift );


        /* Quantize LTP gain parameters */
        SKP_Silk_quant_LTP_gains_FIX( psEncCtrl->LTPCoef_Q14, psEncCtrl->sCmn.LTPIndex, &psEncCtrl->sCmn.PERIndex, 
            WLTP, psEnc->mu_LTP_Q8, psEnc->sCmn.LTPQuantLowComplexity );

        /* Control LTP scaling */
        SKP_Silk_LTP_scale_ctrl_FIX( psEnc, psEncCtrl );

        /* Create LTP residual */
        SKP_Silk_LTP_analysis_filter_FIX( LPC_in_pre, psEnc->x_buf + psEnc->sCmn.frame_length - psEnc->sCmn.predictLPCOrder, 
            psEncCtrl->LTPCoef_Q14, psEncCtrl->sCmn.pitchL, invGains_Q16, psEnc->sCmn.subfr_length, psEnc->sCmn.predictLPCOrder );

    } else {
        /************/
        /* UNVOICED */
        /************/
        /* Create signal with prepended subframes, scaled by inverse gains */
        x_ptr     = psEnc->x_buf + psEnc->sCmn.frame_length - psEnc->sCmn.predictLPCOrder;
        x_pre_ptr = LPC_in_pre;
        for( i = 0; i < NB_SUBFR; i++ ) {
            SKP_Silk_scale_copy_vector16( x_pre_ptr, x_ptr, invGains_Q16[ i ], 
                psEnc->sCmn.subfr_length + psEnc->sCmn.predictLPCOrder );
            x_pre_ptr += psEnc->sCmn.subfr_length + psEnc->sCmn.predictLPCOrder;
            x_ptr     += psEnc->sCmn.subfr_length;
        }

        SKP_memset( psEncCtrl->LTPCoef_Q14, 0, NB_SUBFR * LTP_ORDER * sizeof( SKP_int16 ) );
        psEncCtrl->LTPredCodGain_Q7 = 0;
    }

    /* LPC_in_pre contains the LTP-filtered input for voiced, and the unfiltered input for unvoiced */
    TIC(FIND_LPC)
    SKP_Silk_find_LPC_FIX( NLSF_Q15, &psEncCtrl->sCmn.NLSFInterpCoef_Q2, psEnc->sPred.prev_NLSFq_Q15, 
        psEnc->sCmn.useInterpolatedNLSFs * ( 1 - psEnc->sCmn.first_frame_after_reset ), psEnc->sCmn.predictLPCOrder, 
        LPC_in_pre, psEnc->sCmn.subfr_length + psEnc->sCmn.predictLPCOrder );
    TOC(FIND_LPC)


    /* Quantize LSFs */
    TIC(PROCESS_LSFS)
        SKP_Silk_process_NLSFs_FIX( psEnc, psEncCtrl, NLSF_Q15 );
    TOC(PROCESS_LSFS)

    /* Calculate residual energy using quantized LPC coefficients */
    SKP_Silk_residual_energy_FIX( psEncCtrl->ResNrg, psEncCtrl->ResNrgQ, LPC_in_pre, psEncCtrl->PredCoef_Q12, local_gains,
        psEnc->sCmn.subfr_length, psEnc->sCmn.predictLPCOrder );

    /* Copy to prediction struct for use in next frame for fluctuation reduction */
    SKP_memcpy( psEnc->sPred.prev_NLSFq_Q15, NLSF_Q15, psEnc->sCmn.predictLPCOrder * sizeof( SKP_int ) );

}

