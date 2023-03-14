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

/*
 * Detect SWB input by measuring energy above 8 kHz.
 */

#include "SKP_Silk_main.h"

void SKP_Silk_detect_SWB_input(
    SKP_Silk_detect_SWB_state   *psSWBdetect,   /* (I/O) encoder state  */
    const SKP_int16             samplesIn[],    /* (I) input to encoder */
    SKP_int                     nSamplesIn      /* (I) length of input */
)
{
    SKP_int     HP_8_kHz_len, i, shift;
    SKP_int16   in_HP_8_kHz[ MAX_FRAME_LENGTH ];
    SKP_int32   energy_32;
    
    /* High pass filter with cutoff at 8 khz */
    HP_8_kHz_len = SKP_min_int( nSamplesIn, MAX_FRAME_LENGTH );
    HP_8_kHz_len = SKP_max_int( HP_8_kHz_len, 0 );

    /* Cutoff around 9 khz */
    /* A = conv(conv([8192,14613, 6868], [8192,12883, 7337]), [8192,11586, 7911]); */
    /* B = conv(conv([575, -948, 575], [575, -221, 575]), [575, 104, 575]); */
    SKP_Silk_biquad( samplesIn, SKP_Silk_SWB_detect_B_HP_Q13[ 0 ], SKP_Silk_SWB_detect_A_HP_Q13[ 0 ], 
        psSWBdetect->S_HP_8_kHz[ 0 ], in_HP_8_kHz, HP_8_kHz_len );
    for( i = 1; i < NB_SOS; i++ ) {
        SKP_Silk_biquad( in_HP_8_kHz, SKP_Silk_SWB_detect_B_HP_Q13[ i ], SKP_Silk_SWB_detect_A_HP_Q13[ i ], 
            psSWBdetect->S_HP_8_kHz[ i ], in_HP_8_kHz, HP_8_kHz_len );
    }

    /* Calculate energy in HP signal */
    SKP_Silk_sum_sqr_shift( &energy_32, &shift, in_HP_8_kHz, HP_8_kHz_len );

    /* Count concecutive samples above threshold, after adjusting threshold for number of input samples and shift */
    if( energy_32 > SKP_RSHIFT( SKP_SMULBB( HP_8_KHZ_THRES, HP_8_kHz_len ), shift ) ) {
        psSWBdetect->ConsecSmplsAboveThres += nSamplesIn;
        if( psSWBdetect->ConsecSmplsAboveThres > CONCEC_SWB_SMPLS_THRES ) {
            psSWBdetect->SWB_detected = 1;
        }
    } else {
        psSWBdetect->ConsecSmplsAboveThres -= nSamplesIn;
        psSWBdetect->ConsecSmplsAboveThres = SKP_max( psSWBdetect->ConsecSmplsAboveThres, 0 );
    }

    /* If sufficient speech activity and no SWB detected, we detect the signal as being WB */
    if( ( psSWBdetect->ActiveSpeech_ms > WB_DETECT_ACTIVE_SPEECH_MS_THRES ) && ( psSWBdetect->SWB_detected == 0 ) ) {
        psSWBdetect->WB_detected = 1;
    }
}
