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

/* Set decoder sampling rate */
void SKP_Silk_decoder_set_fs(
    SKP_Silk_decoder_state          *psDec,             /* I/O  Decoder state pointer                       */
    SKP_int                         fs_kHz              /* I    Sampling frequency (kHz)                    */
)
{
    if( psDec->fs_kHz != fs_kHz ) {
        psDec->fs_kHz  = fs_kHz;
        psDec->frame_length = SKP_SMULBB( FRAME_LENGTH_MS, fs_kHz );
        psDec->subfr_length = SKP_SMULBB( FRAME_LENGTH_MS / NB_SUBFR, fs_kHz );
        if( psDec->fs_kHz == 8 ) {
            psDec->LPC_order = MIN_LPC_ORDER;
            psDec->psNLSF_CB[ 0 ] = &SKP_Silk_NLSF_CB0_10;
            psDec->psNLSF_CB[ 1 ] = &SKP_Silk_NLSF_CB1_10;
        } else {
            psDec->LPC_order = MAX_LPC_ORDER;
            psDec->psNLSF_CB[ 0 ] = &SKP_Silk_NLSF_CB0_16;
            psDec->psNLSF_CB[ 1 ] = &SKP_Silk_NLSF_CB1_16;
        }
        /* Reset part of the decoder state */
        SKP_memset( psDec->sLPC_Q14,     0, MAX_LPC_ORDER    * sizeof( SKP_int32 ) );
        SKP_memset( psDec->outBuf,       0, MAX_FRAME_LENGTH * sizeof( SKP_int16 ) );
        SKP_memset( psDec->prevNLSF_Q15, 0, MAX_LPC_ORDER    * sizeof( SKP_int )   );

        psDec->lagPrev                 = 100;
        psDec->LastGainIndex           = 1;
        psDec->prev_sigtype            = 0;
        psDec->first_frame_after_reset = 1;

        if( fs_kHz == 24 ) {
            psDec->HP_A = SKP_Silk_Dec_A_HP_24;
            psDec->HP_B = SKP_Silk_Dec_B_HP_24;
        } else if( fs_kHz == 16 ) {
            psDec->HP_A = SKP_Silk_Dec_A_HP_16;
            psDec->HP_B = SKP_Silk_Dec_B_HP_16;
        } else if( fs_kHz == 12 ) {
            psDec->HP_A = SKP_Silk_Dec_A_HP_12;
            psDec->HP_B = SKP_Silk_Dec_B_HP_12;
        } else if( fs_kHz == 8 ) {
            psDec->HP_A = SKP_Silk_Dec_A_HP_8;
            psDec->HP_B = SKP_Silk_Dec_B_HP_8;
        } else {
            /* unsupported sampling rate */
            SKP_assert( 0 );
        }
    } 

    /* Check that settings are valid */
    SKP_assert( psDec->frame_length > 0 && psDec->frame_length <= MAX_FRAME_LENGTH );
}

