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

/*******************************************/
/* Encode parameters to create the payload */
/*******************************************/
void SKP_Silk_encode_parameters(
    SKP_Silk_encoder_state          *psEncC,        /* I/O  Encoder state                   */
    SKP_Silk_encoder_control        *psEncCtrlC,    /* I/O  Encoder control                 */
    SKP_Silk_range_coder_state      *psRC,          /* I/O  Range encoder state             */
    const SKP_int8                  *q              /* I    Quantization indices            */
)
{
    SKP_int   i, k, typeOffset;
    const SKP_Silk_NLSF_CB_struct *psNLSF_CB;


    /************************/
    /* Encode sampling rate */
    /************************/
    /* only done for first frame in packet */
    if( psEncC->nFramesInPayloadBuf == 0 ) {
        /* get sampling rate index */
        for( i = 0; i < 3; i++ ) {
            if( SKP_Silk_SamplingRates_table[ i ] == psEncC->fs_kHz ) {
                break;
            }
        }
        SKP_Silk_range_encoder( psRC, i, SKP_Silk_SamplingRates_CDF );
    }

    /*******************************************/
    /* Encode signal type and quantizer offset */
    /*******************************************/
    typeOffset = 2 * psEncCtrlC->sigtype + psEncCtrlC->QuantOffsetType;
    if( psEncC->nFramesInPayloadBuf == 0 ) {
        /* first frame in packet: independent coding */
        SKP_Silk_range_encoder( psRC, typeOffset, SKP_Silk_type_offset_CDF );
    } else {
        /* condidtional coding */
        SKP_Silk_range_encoder( psRC, typeOffset, SKP_Silk_type_offset_joint_CDF[ psEncC->typeOffsetPrev ] );
    }
    psEncC->typeOffsetPrev = typeOffset;

    /****************/
    /* Encode gains */
    /****************/
    /* first subframe */
    if( psEncC->nFramesInPayloadBuf == 0 ) {
        /* first frame in packet: independent coding */
        SKP_Silk_range_encoder( psRC, psEncCtrlC->GainsIndices[ 0 ], SKP_Silk_gain_CDF[ psEncCtrlC->sigtype ] );
    } else {
        /* condidtional coding */
        SKP_Silk_range_encoder( psRC, psEncCtrlC->GainsIndices[ 0 ], SKP_Silk_delta_gain_CDF );
    }

    /* remaining subframes */
    for( i = 1; i < NB_SUBFR; i++ ) {
        SKP_Silk_range_encoder( psRC, psEncCtrlC->GainsIndices[ i ], SKP_Silk_delta_gain_CDF );
    }


    /****************/
    /* Encode NLSFs */
    /****************/
    /* Range encoding of the NLSF path */
    psNLSF_CB = psEncC->psNLSF_CB[ psEncCtrlC->sigtype ];
    SKP_Silk_range_encoder_multi( psRC, psEncCtrlC->NLSFIndices, psNLSF_CB->StartPtr, psNLSF_CB->nStages );

    /* Encode NLSF interpolation factor */
    SKP_assert( psEncC->useInterpolatedNLSFs == 1 || psEncCtrlC->NLSFInterpCoef_Q2 == ( 1 << 2 ) );
    SKP_Silk_range_encoder( psRC, psEncCtrlC->NLSFInterpCoef_Q2, SKP_Silk_NLSF_interpolation_factor_CDF );


    if( psEncCtrlC->sigtype == SIG_TYPE_VOICED ) {
        /*********************/
        /* Encode pitch lags */
        /*********************/


        /* lag index */
        if( psEncC->fs_kHz == 8 ) {
            SKP_Silk_range_encoder( psRC, psEncCtrlC->lagIndex, SKP_Silk_pitch_lag_NB_CDF );
        } else if( psEncC->fs_kHz == 12 ) {
            SKP_Silk_range_encoder( psRC, psEncCtrlC->lagIndex, SKP_Silk_pitch_lag_MB_CDF );
        } else if( psEncC->fs_kHz == 16 ) {
            SKP_Silk_range_encoder( psRC, psEncCtrlC->lagIndex, SKP_Silk_pitch_lag_WB_CDF );
        } else {
            SKP_Silk_range_encoder( psRC, psEncCtrlC->lagIndex, SKP_Silk_pitch_lag_SWB_CDF );
        }


        /* countour index */
        if( psEncC->fs_kHz == 8 ) {
            /* Less codevectors used in 8 khz mode */
            SKP_Silk_range_encoder( psRC, psEncCtrlC->contourIndex, SKP_Silk_pitch_contour_NB_CDF );
        } else {
            /* Joint for 12, 16, 24 khz */
            SKP_Silk_range_encoder( psRC, psEncCtrlC->contourIndex, SKP_Silk_pitch_contour_CDF );
        }

        /********************/
        /* Encode LTP gains */
        /********************/

        /* PERIndex value */
        SKP_Silk_range_encoder( psRC, psEncCtrlC->PERIndex, SKP_Silk_LTP_per_index_CDF );

        /* Codebook Indices */
        for( k = 0; k < NB_SUBFR; k++ ) {
            SKP_Silk_range_encoder( psRC, psEncCtrlC->LTPIndex[ k ], SKP_Silk_LTP_gain_CDF_ptrs[ psEncCtrlC->PERIndex ] );
        }

        /**********************/
        /* Encode LTP scaling */
        /**********************/
        SKP_Silk_range_encoder( psRC, psEncCtrlC->LTP_scaleIndex, SKP_Silk_LTPscale_CDF );
    }


    /***************/
    /* Encode seed */
    /***************/
    SKP_Silk_range_encoder( psRC, psEncCtrlC->Seed, SKP_Silk_Seed_CDF );

    /*********************************************/
    /* Encode quantization indices of excitation */
    /*********************************************/
    SKP_Silk_encode_pulses( psRC, psEncCtrlC->sigtype, psEncCtrlC->QuantOffsetType, q, psEncC->frame_length );


    /*********************************************/
    /* Encode VAD flag                           */
    /*********************************************/
    SKP_Silk_range_encoder( psRC, psEncC->vadFlag, SKP_Silk_vadflag_CDF );
}
