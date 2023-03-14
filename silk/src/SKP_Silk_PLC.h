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

#ifndef SKP_SILK_PLC_FIX_H
#define SKP_SILK_PLC_FIX_H

#include "SKP_Silk_main.h"

#define BWE_COEF_Q16                    64880           /* 0.99 in Q16                      */
#define V_PITCH_GAIN_START_MIN_Q14      11469           /* 0.7 in Q14                       */
#define V_PITCH_GAIN_START_MAX_Q14      15565           /* 0.95 in Q14                      */
#define MAX_PITCH_LAG_MS                18
#define SA_THRES_Q8                     50
#define USE_SINGLE_TAP                  1
#define RAND_BUF_SIZE                   128
#define RAND_BUF_MASK                   (RAND_BUF_SIZE - 1)
#define LOG2_INV_LPC_GAIN_HIGH_THRES    3               /* 2^3 = 8 dB LPC gain              */
#define LOG2_INV_LPC_GAIN_LOW_THRES     8               /* 2^8 = 24 dB LPC gain             */
#define PITCH_DRIFT_FAC_Q16             655             /* 0.01 in Q16                      */

void SKP_Silk_PLC_Reset(
    SKP_Silk_decoder_state      *psDec              /* I/O Decoder state        */
);

void SKP_Silk_PLC(
    SKP_Silk_decoder_state      *psDec,             /* I/O Decoder state        */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I/O Decoder control      */
    SKP_int16                   signal[],           /* I/O  signal              */
    SKP_int                     length,             /* I length of residual     */
    SKP_int                     lost                /* I Loss flag              */
);

void SKP_Silk_PLC_update(
    SKP_Silk_decoder_state      *psDec,             /* I/O Decoder state        */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I/O Decoder control      */
    SKP_int16                   signal[],
    SKP_int                     length
);

void SKP_Silk_PLC_conceal(
    SKP_Silk_decoder_state      *psDec,             /* I/O Decoder state        */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I/O Decoder control      */
    SKP_int16                   signal[],           /* O LPC residual signal    */
    SKP_int                     length              /* I length of signal       */
);

void SKP_Silk_PLC_glue_frames(
    SKP_Silk_decoder_state      *psDec,             /* I/O decoder state        */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I/O Decoder control      */
    SKP_int16                   signal[],           /* I/O signal               */
    SKP_int                     length              /* I length of signal       */
);

#endif

