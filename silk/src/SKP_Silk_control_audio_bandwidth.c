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

/* Control internal sampling rate */
SKP_int SKP_Silk_control_audio_bandwidth(
    SKP_Silk_encoder_state      *psEncC,            /* I/O  Pointer to Silk encoder state               */
    const SKP_int32             TargetRate_bps      /* I    Target max bitrate (bps)                    */
)
{
    SKP_int fs_kHz;

    fs_kHz = psEncC->fs_kHz;
    if( fs_kHz == 0 ) {
        /* Encoder has just been initialized */
        if( TargetRate_bps >= SWB2WB_BITRATE_BPS ) {
            fs_kHz = 24;
        } else if( TargetRate_bps >= WB2MB_BITRATE_BPS ) {
            fs_kHz = 16;
        } else if( TargetRate_bps >= MB2NB_BITRATE_BPS ) {
            fs_kHz = 12;
        } else {
            fs_kHz = 8;
        }
        /* Make sure internal rate is not higher than external rate or maximum allowed, or lower than minimum allowed */
        fs_kHz = SKP_min( fs_kHz, SKP_DIV32_16( psEncC->API_fs_Hz, 1000 ) );
        fs_kHz = SKP_min( fs_kHz, psEncC->maxInternal_fs_kHz );
    } else if( SKP_SMULBB( fs_kHz, 1000 ) > psEncC->API_fs_Hz || fs_kHz > psEncC->maxInternal_fs_kHz ) {
        /* Make sure internal rate is not higher than external rate or maximum allowed */
        fs_kHz = SKP_DIV32_16( psEncC->API_fs_Hz, 1000 );
        fs_kHz = SKP_min( fs_kHz, psEncC->maxInternal_fs_kHz );
    } else {
        /* State machine for the internal sampling rate switching */
        if( psEncC->API_fs_Hz > 8000 ) {
            /* Accumulate the difference between the target rate and limit for switching down */
            psEncC->bitrateDiff += SKP_MUL( psEncC->PacketSize_ms, TargetRate_bps - psEncC->bitrate_threshold_down );
            psEncC->bitrateDiff  = SKP_min( psEncC->bitrateDiff, 0 );

            if( psEncC->vadFlag == NO_VOICE_ACTIVITY ) { /* Low speech activity */
                /* Check if we should switch down */
#if SWITCH_TRANSITION_FILTERING 
                if( ( psEncC->sLP.transition_frame_no == 0 ) &&                         /* Transition phase not active */
                    ( psEncC->bitrateDiff <= -ACCUM_BITS_DIFF_THRESHOLD ||              /* Bitrate threshold is met */
                    ( psEncC->sSWBdetect.WB_detected * psEncC->fs_kHz == 24 ) ) ) {     /* Forced down-switching due to WB input */
                        psEncC->sLP.transition_frame_no = 1;                            /* Begin transition phase */
                        psEncC->sLP.mode                = 0;                            /* Switch down */
                } else if( 
                    ( psEncC->sLP.transition_frame_no >= TRANSITION_FRAMES_DOWN ) &&    /* Transition phase complete */
                    ( psEncC->sLP.mode == 0 ) ) {                                       /* Ready to switch down */
                        psEncC->sLP.transition_frame_no = 0;                            /* Ready for new transition phase */
#else
                if( psEncC->bitrateDiff <= -ACCUM_BITS_DIFF_THRESHOLD ) {               /* Bitrate threshold is met */ 
#endif            
                    psEncC->bitrateDiff = 0;

                    /* Switch to a lower sample frequency */
                    if( psEncC->fs_kHz == 24 ) {
                        fs_kHz = 16;
                    } else if( psEncC->fs_kHz == 16 ) {
                        fs_kHz = 12;
                    } else {
                        SKP_assert( psEncC->fs_kHz == 12 );
                        fs_kHz = 8;
                    }
                }

                /* Check if we should switch up */
                if( ( ( psEncC->fs_kHz * 1000 < psEncC->API_fs_Hz ) &&
                    ( TargetRate_bps >= psEncC->bitrate_threshold_up ) && 
                    ( psEncC->sSWBdetect.WB_detected * psEncC->fs_kHz < 16 ) ) && 
                    ( ( ( psEncC->fs_kHz == 16 ) && ( psEncC->maxInternal_fs_kHz >= 24 ) ) || 
                    (   ( psEncC->fs_kHz == 12 ) && ( psEncC->maxInternal_fs_kHz >= 16 ) ) ||
                    (   ( psEncC->fs_kHz ==  8 ) && ( psEncC->maxInternal_fs_kHz >= 12 ) ) ) 
#if SWITCH_TRANSITION_FILTERING
                    && ( psEncC->sLP.transition_frame_no == 0 ) ) { /* No transition phase running, ready to switch */
                        psEncC->sLP.mode = 1; /* Switch up */
#else
                    ) {
#endif
                    psEncC->bitrateDiff = 0;

                    /* Switch to a higher sample frequency */
                    if( psEncC->fs_kHz == 8 ) {
                        fs_kHz = 12;
                    } else if( psEncC->fs_kHz == 12 ) {
                        fs_kHz = 16;
                    } else {
                        SKP_assert( psEncC->fs_kHz == 16 );
                        fs_kHz = 24;
                    }
                }
            }
        }

#if SWITCH_TRANSITION_FILTERING
        /* After switching up, stop transition filter during speech inactivity */
        if( ( psEncC->sLP.mode == 1 ) &&
            ( psEncC->sLP.transition_frame_no >= TRANSITION_FRAMES_UP ) && 
            ( psEncC->vadFlag == NO_VOICE_ACTIVITY ) ) {

                psEncC->sLP.transition_frame_no = 0;

                /* Reset transition filter state */
                SKP_memset( psEncC->sLP.In_LP_State, 0, 2 * sizeof( SKP_int32 ) );
        }
#endif
    }



    return fs_kHz;
}
