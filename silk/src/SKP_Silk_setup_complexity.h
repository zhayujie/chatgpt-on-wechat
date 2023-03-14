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
#include "SKP_Silk_tuning_parameters.h"

SKP_INLINE SKP_int SKP_Silk_setup_complexity(
    SKP_Silk_encoder_state          *psEncC,            /* I/O  Pointer to Silk encoder state           */
    SKP_int                         Complexity          /* I    Complexity (0->low; 1->medium; 2->high) */
)
{
    SKP_int ret = SKP_SILK_NO_ERROR;

    /* Check that settings are valid */
    if( LOW_COMPLEXITY_ONLY && Complexity != 0 ) { 
        ret = SKP_SILK_ENC_INVALID_COMPLEXITY_SETTING;
    }

    /* Set encoding complexity */
    if( Complexity == 0 || LOW_COMPLEXITY_ONLY ) {
        /* Low complexity */
        psEncC->Complexity                      = 0;
        psEncC->pitchEstimationComplexity       = PITCH_EST_COMPLEXITY_LC_MODE;
        psEncC->pitchEstimationThreshold_Q16    = SKP_FIX_CONST( FIND_PITCH_CORRELATION_THRESHOLD_LC_MODE, 16 );
        psEncC->pitchEstimationLPCOrder         = 6;
        psEncC->shapingLPCOrder                 = 8;
        psEncC->la_shape                        = 3 * psEncC->fs_kHz;
        psEncC->nStatesDelayedDecision          = 1;
        psEncC->useInterpolatedNLSFs            = 0;
        psEncC->LTPQuantLowComplexity           = 1;
        psEncC->NLSF_MSVQ_Survivors             = MAX_NLSF_MSVQ_SURVIVORS_LC_MODE;
        psEncC->warping_Q16                     = 0;
    } else if( Complexity == 1 ) {
        /* Medium complexity */
        psEncC->Complexity                      = 1;
        psEncC->pitchEstimationComplexity       = PITCH_EST_COMPLEXITY_MC_MODE;
        psEncC->pitchEstimationThreshold_Q16    = SKP_FIX_CONST( FIND_PITCH_CORRELATION_THRESHOLD_MC_MODE, 16 );
        psEncC->pitchEstimationLPCOrder         = 12;
        psEncC->shapingLPCOrder                 = 12;
        psEncC->la_shape                        = 5 * psEncC->fs_kHz;
        psEncC->nStatesDelayedDecision          = 2;
        psEncC->useInterpolatedNLSFs            = 0;
        psEncC->LTPQuantLowComplexity           = 0;
        psEncC->NLSF_MSVQ_Survivors             = MAX_NLSF_MSVQ_SURVIVORS_MC_MODE;
        psEncC->warping_Q16                     = psEncC->fs_kHz * SKP_FIX_CONST( WARPING_MULTIPLIER, 16 );
    } else if( Complexity == 2 ) {
        /* High complexity */
        psEncC->Complexity                      = 2;
        psEncC->pitchEstimationComplexity       = PITCH_EST_COMPLEXITY_HC_MODE;
        psEncC->pitchEstimationThreshold_Q16    = SKP_FIX_CONST( FIND_PITCH_CORRELATION_THRESHOLD_HC_MODE, 16 );
        psEncC->pitchEstimationLPCOrder         = 16;
        psEncC->shapingLPCOrder                 = 16;
        psEncC->la_shape                        = 5 * psEncC->fs_kHz;
        psEncC->nStatesDelayedDecision          = MAX_DEL_DEC_STATES;
        psEncC->useInterpolatedNLSFs            = 1;
        psEncC->LTPQuantLowComplexity           = 0;
        psEncC->NLSF_MSVQ_Survivors             = MAX_NLSF_MSVQ_SURVIVORS;
        psEncC->warping_Q16                     = psEncC->fs_kHz * SKP_FIX_CONST( WARPING_MULTIPLIER, 16 );
    } else {
        ret = SKP_SILK_ENC_INVALID_COMPLEXITY_SETTING;
    }

    /* Do not allow higher pitch estimation LPC order than predict LPC order */
    psEncC->pitchEstimationLPCOrder             = SKP_min_int( psEncC->pitchEstimationLPCOrder, psEncC->predictLPCOrder );
    psEncC->shapeWinLength                      = 5 * psEncC->fs_kHz + 2 * psEncC->la_shape;

    SKP_assert( psEncC->pitchEstimationLPCOrder <= MAX_FIND_PITCH_LPC_ORDER );
    SKP_assert( psEncC->shapingLPCOrder         <= MAX_SHAPE_LPC_ORDER      );
    SKP_assert( psEncC->nStatesDelayedDecision  <= MAX_DEL_DEC_STATES       );
    SKP_assert( psEncC->warping_Q16             <= 32767                    );
    SKP_assert( psEncC->la_shape                <= LA_SHAPE_MAX             );
    SKP_assert( psEncC->shapeWinLength          <= SHAPE_LPC_WIN_MAX        );

    return( ret );
}
