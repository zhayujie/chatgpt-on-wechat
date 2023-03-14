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

/* Decode parameters from payload */
void SKP_Silk_decode_parameters(
    SKP_Silk_decoder_state      *psDec,             /* I/O  State                                       */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I/O  Decoder control                             */
    SKP_int                     q[],                /* O    Excitation signal                           */
    const SKP_int               fullDecoding        /* I    Flag to tell if only arithmetic decoding    */
)
{
    SKP_int   i, k, Ix, fs_kHz_dec, nBytesUsed;
    SKP_int   Ixs[ NB_SUBFR ];
    SKP_int   GainsIndices[ NB_SUBFR ];
    SKP_int   NLSFIndices[ NLSF_MSVQ_MAX_CB_STAGES ];
    SKP_int   pNLSF_Q15[ MAX_LPC_ORDER ], pNLSF0_Q15[ MAX_LPC_ORDER ];
    const SKP_int16 *cbk_ptr_Q14;
    const SKP_Silk_NLSF_CB_struct *psNLSF_CB = NULL;
    SKP_Silk_range_coder_state  *psRC = &psDec->sRC;

    /************************/
    /* Decode sampling rate */
    /************************/
    /* only done for first frame of packet */
    if( psDec->nFramesDecoded == 0 ) {
        SKP_Silk_range_decoder( &Ix, psRC, SKP_Silk_SamplingRates_CDF, SKP_Silk_SamplingRates_offset );

        /* check that sampling rate is supported */
        if( Ix < 0 || Ix > 3 ) {
            psRC->error = RANGE_CODER_ILLEGAL_SAMPLING_RATE;
            return;
        }
        fs_kHz_dec = SKP_Silk_SamplingRates_table[ Ix ];
        SKP_Silk_decoder_set_fs( psDec, fs_kHz_dec );
    }

    /*******************************************/
    /* Decode signal type and quantizer offset */
    /*******************************************/
    if( psDec->nFramesDecoded == 0 ) {
        /* first frame in packet: independent coding */
        SKP_Silk_range_decoder( &Ix, psRC, SKP_Silk_type_offset_CDF, SKP_Silk_type_offset_CDF_offset );
    } else {
        /* condidtional coding */
        SKP_Silk_range_decoder( &Ix, psRC, SKP_Silk_type_offset_joint_CDF[ psDec->typeOffsetPrev ], 
                SKP_Silk_type_offset_CDF_offset );
    }
    psDecCtrl->sigtype         = SKP_RSHIFT( Ix, 1 );
    psDecCtrl->QuantOffsetType = Ix & 1;
    psDec->typeOffsetPrev      = Ix;

    /****************/
    /* Decode gains */
    /****************/
    /* first subframe */    
    if( psDec->nFramesDecoded == 0 ) {
        /* first frame in packet: independent coding */
        SKP_Silk_range_decoder( &GainsIndices[ 0 ], psRC, SKP_Silk_gain_CDF[ psDecCtrl->sigtype ], SKP_Silk_gain_CDF_offset );
    } else {
        /* condidtional coding */
        SKP_Silk_range_decoder( &GainsIndices[ 0 ], psRC, SKP_Silk_delta_gain_CDF, SKP_Silk_delta_gain_CDF_offset );
    }

    /* remaining subframes */
    for( i = 1; i < NB_SUBFR; i++ ) {
        SKP_Silk_range_decoder( &GainsIndices[ i ], psRC, SKP_Silk_delta_gain_CDF, SKP_Silk_delta_gain_CDF_offset );
    }
    
    /* Dequant Gains */
    SKP_Silk_gains_dequant( psDecCtrl->Gains_Q16, GainsIndices, &psDec->LastGainIndex, psDec->nFramesDecoded );
    /****************/
    /* Decode NLSFs */
    /****************/
    /* Set pointer to NLSF VQ CB for the current signal type */
    psNLSF_CB = psDec->psNLSF_CB[ psDecCtrl->sigtype ];

    /* Range decode NLSF path */
    SKP_Silk_range_decoder_multi( NLSFIndices, psRC, psNLSF_CB->StartPtr, psNLSF_CB->MiddleIx, psNLSF_CB->nStages );

    /* From the NLSF path, decode an NLSF vector */
    SKP_Silk_NLSF_MSVQ_decode( pNLSF_Q15, psNLSF_CB, NLSFIndices, psDec->LPC_order );

    /************************************/
    /* Decode NLSF interpolation factor */
    /************************************/
    SKP_Silk_range_decoder( &psDecCtrl->NLSFInterpCoef_Q2, psRC, SKP_Silk_NLSF_interpolation_factor_CDF, 
        SKP_Silk_NLSF_interpolation_factor_offset );
    
    /* If just reset, e.g., because internal Fs changed, do not allow interpolation */
    /* improves the case of packet loss in the first frame after a switch           */
    if( psDec->first_frame_after_reset == 1 ) {
        psDecCtrl->NLSFInterpCoef_Q2 = 4;
    }

    if( fullDecoding ) {
        /* Convert NLSF parameters to AR prediction filter coefficients */
        SKP_Silk_NLSF2A_stable( psDecCtrl->PredCoef_Q12[ 1 ], pNLSF_Q15, psDec->LPC_order );

        if( psDecCtrl->NLSFInterpCoef_Q2 < 4 ) {
            /* Calculation of the interpolated NLSF0 vector from the interpolation factor, */ 
            /* the previous NLSF1, and the current NLSF1                                   */
            for( i = 0; i < psDec->LPC_order; i++ ) {
                pNLSF0_Q15[ i ] = psDec->prevNLSF_Q15[ i ] + SKP_RSHIFT( SKP_MUL( psDecCtrl->NLSFInterpCoef_Q2, 
                    ( pNLSF_Q15[ i ] - psDec->prevNLSF_Q15[ i ] ) ), 2 );
            }

            /* Convert NLSF parameters to AR prediction filter coefficients */
            SKP_Silk_NLSF2A_stable( psDecCtrl->PredCoef_Q12[ 0 ], pNLSF0_Q15, psDec->LPC_order );
        } else {
            /* Copy LPC coefficients for first half from second half */
            SKP_memcpy( psDecCtrl->PredCoef_Q12[ 0 ], psDecCtrl->PredCoef_Q12[ 1 ], 
                psDec->LPC_order * sizeof( SKP_int16 ) );
        }
    }

    SKP_memcpy( psDec->prevNLSF_Q15, pNLSF_Q15, psDec->LPC_order * sizeof( SKP_int ) );

    /* After a packet loss do BWE of LPC coefs */
    if( psDec->lossCnt ) {
        SKP_Silk_bwexpander( psDecCtrl->PredCoef_Q12[ 0 ], psDec->LPC_order, BWE_AFTER_LOSS_Q16 );
        SKP_Silk_bwexpander( psDecCtrl->PredCoef_Q12[ 1 ], psDec->LPC_order, BWE_AFTER_LOSS_Q16 );
    }

    if( psDecCtrl->sigtype == SIG_TYPE_VOICED ) {
        /*********************/
        /* Decode pitch lags */
        /*********************/
        /* Get lag index */
        if( psDec->fs_kHz == 8 ) {
            SKP_Silk_range_decoder( &Ixs[ 0 ], psRC, SKP_Silk_pitch_lag_NB_CDF,  SKP_Silk_pitch_lag_NB_CDF_offset );
        } else if( psDec->fs_kHz == 12 ) {
            SKP_Silk_range_decoder( &Ixs[ 0 ], psRC, SKP_Silk_pitch_lag_MB_CDF,  SKP_Silk_pitch_lag_MB_CDF_offset );
        } else if( psDec->fs_kHz == 16 ) {
            SKP_Silk_range_decoder( &Ixs[ 0 ], psRC, SKP_Silk_pitch_lag_WB_CDF,  SKP_Silk_pitch_lag_WB_CDF_offset );
        } else {
            SKP_Silk_range_decoder( &Ixs[ 0 ], psRC, SKP_Silk_pitch_lag_SWB_CDF, SKP_Silk_pitch_lag_SWB_CDF_offset );
        }
        
        /* Get countour index */
        if( psDec->fs_kHz == 8 ) {
            /* Less codevectors used in 8 khz mode */
            SKP_Silk_range_decoder( &Ixs[ 1 ], psRC, SKP_Silk_pitch_contour_NB_CDF, SKP_Silk_pitch_contour_NB_CDF_offset );
        } else {
            /* Joint for 12, 16, and 24 khz */
            SKP_Silk_range_decoder( &Ixs[ 1 ], psRC, SKP_Silk_pitch_contour_CDF, SKP_Silk_pitch_contour_CDF_offset );
        }
        
        /* Decode pitch values */
        SKP_Silk_decode_pitch( Ixs[ 0 ], Ixs[ 1 ], psDecCtrl->pitchL, psDec->fs_kHz );

        /********************/
        /* Decode LTP gains */
        /********************/
        /* Decode PERIndex value */
        SKP_Silk_range_decoder( &psDecCtrl->PERIndex, psRC, SKP_Silk_LTP_per_index_CDF, 
                SKP_Silk_LTP_per_index_CDF_offset );

        /* Decode Codebook Index */
        cbk_ptr_Q14 = SKP_Silk_LTP_vq_ptrs_Q14[ psDecCtrl->PERIndex ]; /* set pointer to start of codebook */

        for( k = 0; k < NB_SUBFR; k++ ) {
            SKP_Silk_range_decoder( &Ix, psRC, SKP_Silk_LTP_gain_CDF_ptrs[ psDecCtrl->PERIndex ], 
                SKP_Silk_LTP_gain_CDF_offsets[ psDecCtrl->PERIndex ] );

            for( i = 0; i < LTP_ORDER; i++ ) {
                psDecCtrl->LTPCoef_Q14[ k * LTP_ORDER + i ] = cbk_ptr_Q14[ Ix * LTP_ORDER + i ];
            }
        }

        /**********************/
        /* Decode LTP scaling */
        /**********************/
        SKP_Silk_range_decoder( &Ix, psRC, SKP_Silk_LTPscale_CDF, SKP_Silk_LTPscale_offset );
        psDecCtrl->LTP_scale_Q14 = SKP_Silk_LTPScales_table_Q14[ Ix ];
    } else {
        SKP_assert( psDecCtrl->sigtype == SIG_TYPE_UNVOICED );
        SKP_memset( psDecCtrl->pitchL,      0,             NB_SUBFR * sizeof( SKP_int   ) );
        SKP_memset( psDecCtrl->LTPCoef_Q14, 0, LTP_ORDER * NB_SUBFR * sizeof( SKP_int16 ) );
        psDecCtrl->PERIndex      = 0;
        psDecCtrl->LTP_scale_Q14 = 0;
    }

    /***************/
    /* Decode seed */
    /***************/
    SKP_Silk_range_decoder( &Ix, psRC, SKP_Silk_Seed_CDF, SKP_Silk_Seed_offset );
    psDecCtrl->Seed = ( SKP_int32 )Ix;
    /*********************************************/
    /* Decode quantization indices of excitation */
    /*********************************************/
    SKP_Silk_decode_pulses( psRC, psDecCtrl, q, psDec->frame_length );

    /*********************************************/
    /* Decode VAD flag                           */
    /*********************************************/
    SKP_Silk_range_decoder( &psDec->vadFlag, psRC, SKP_Silk_vadflag_CDF, SKP_Silk_vadflag_offset );

    /**************************************/
    /* Decode Frame termination indicator */
    /**************************************/
    SKP_Silk_range_decoder( &psDec->FrameTermination, psRC, SKP_Silk_FrameTermination_CDF, SKP_Silk_FrameTermination_offset );

    /****************************************/
    /* get number of bytes used so far      */
    /****************************************/
    SKP_Silk_range_coder_get_length( psRC, &nBytesUsed );
    psDec->nBytesLeft = psRC->bufferLength - nBytesUsed;
    if( psDec->nBytesLeft < 0 ) {
        psRC->error = RANGE_CODER_READ_BEYOND_BUFFER;
    }

    /****************************************/
    /* check remaining bits in last byte    */
    /****************************************/
    if( psDec->nBytesLeft == 0 ) {
        SKP_Silk_range_coder_check_after_decoding( psRC );
    }
}
