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
#include "SKP_Silk_common_pitch_est_defines.h"

void SKP_Silk_decode_pitch(
    SKP_int          lagIndex,                        /* I                             */
    SKP_int          contourIndex,                    /* O                             */
    SKP_int          pitch_lags[],                    /* O 4 pitch values              */
    SKP_int          Fs_kHz                           /* I sampling frequency (kHz)    */
)
{
    SKP_int lag, i, min_lag;

    min_lag = SKP_SMULBB( PITCH_EST_MIN_LAG_MS, Fs_kHz );

    /* Only for 24 / 16 kHz version for now */
    lag = min_lag + lagIndex;
    if( Fs_kHz == 8 ) {
        /* Only a small codebook for 8 khz */
        for( i = 0; i < PITCH_EST_NB_SUBFR; i++ ) {
            pitch_lags[ i ] = lag + SKP_Silk_CB_lags_stage2[ i ][ contourIndex ];
        }
    } else {
        for( i = 0; i < PITCH_EST_NB_SUBFR; i++ ) {
            pitch_lags[ i ] = lag + SKP_Silk_CB_lags_stage3[ i ][ contourIndex ];
        }
    }
}
