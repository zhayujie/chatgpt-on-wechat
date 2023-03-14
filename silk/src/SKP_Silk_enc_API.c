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


#include "SKP_Silk_define.h"
#include "SKP_Silk_main_FIX.h"
#include "SKP_Silk_SDK_API.h"
#include "SKP_Silk_control.h"
#include "SKP_Silk_typedef.h"
#include "SKP_Silk_structs.h"
#define SKP_Silk_EncodeControlStruct SKP_SILK_SDK_EncControlStruct

/****************************************/
/* Encoder functions                    */
/****************************************/

SKP_int SKP_Silk_SDK_Get_Encoder_Size( SKP_int32 *encSizeBytes )
{
    SKP_int ret = 0;
    
    *encSizeBytes = sizeof( SKP_Silk_encoder_state_FIX );
    
    return ret;
}


/***************************************/
/* Read control structure from encoder */
/***************************************/
SKP_int SKP_Silk_SDK_QueryEncoder(
    const void *encState,                       /* I:   State Vector                                    */
    SKP_Silk_EncodeControlStruct *encStatus     /* O:   Control Structure                               */
)
{
    SKP_Silk_encoder_state_FIX *psEnc;
    SKP_int ret = 0;

    psEnc = ( SKP_Silk_encoder_state_FIX* )encState;

    encStatus->API_sampleRate        = psEnc->sCmn.API_fs_Hz;
    encStatus->maxInternalSampleRate = SKP_SMULBB( psEnc->sCmn.maxInternal_fs_kHz, 1000 );
    encStatus->packetSize            = ( SKP_int )SKP_DIV32_16( psEnc->sCmn.API_fs_Hz * psEnc->sCmn.PacketSize_ms, 1000 );  /* convert samples -> ms */
    encStatus->bitRate               = psEnc->sCmn.TargetRate_bps;
    encStatus->packetLossPercentage  = psEnc->sCmn.PacketLoss_perc;
    encStatus->complexity            = psEnc->sCmn.Complexity;
    encStatus->useInBandFEC          = psEnc->sCmn.useInBandFEC;
    encStatus->useDTX                = psEnc->sCmn.useDTX;
    return ret;
}

/*************************/
/* Init or Reset encoder */
/*************************/
SKP_int SKP_Silk_SDK_InitEncoder(
    void                            *encState,          /* I/O: State                                           */
    SKP_Silk_EncodeControlStruct    *encStatus          /* O:   Control structure                               */
)
{
    SKP_Silk_encoder_state_FIX *psEnc;
    SKP_int ret = 0;

        
    psEnc = ( SKP_Silk_encoder_state_FIX* )encState;

    /* Reset Encoder */
    if( ret += SKP_Silk_init_encoder_FIX( psEnc ) ) {
        SKP_assert( 0 );
    }

    /* Read control structure */
    if( ret += SKP_Silk_SDK_QueryEncoder( encState, encStatus ) ) {
        SKP_assert( 0 );
    }


    return ret;
}

/**************************/
/* Encode frame with Silk */
/**************************/
SKP_int SKP_Silk_SDK_Encode( 
    void                                *encState,      /* I/O: State                                           */
    const SKP_Silk_EncodeControlStruct  *encControl,    /* I:   Control structure                               */
    const SKP_int16                     *samplesIn,     /* I:   Speech sample input vector                      */
    SKP_int                             nSamplesIn,     /* I:   Number of samples in input vector               */
    SKP_uint8                           *outData,       /* O:   Encoded output vector                           */
    SKP_int16                           *nBytesOut      /* I/O: Number of bytes in outData (input: Max bytes)   */
)
{
    SKP_int   max_internal_fs_kHz, PacketSize_ms, PacketLoss_perc, UseInBandFEC, UseDTX, ret = 0;
    SKP_int   nSamplesToBuffer, Complexity, input_10ms, nSamplesFromInput = 0;
    SKP_int32 TargetRate_bps, API_fs_Hz;
    SKP_int16 MaxBytesOut;
    SKP_Silk_encoder_state_FIX *psEnc = ( SKP_Silk_encoder_state_FIX* )encState;

    SKP_assert( encControl != NULL );

    /* Check sampling frequency first, to avoid divide by zero later */
    if( ( ( encControl->API_sampleRate        !=  8000 ) &&
          ( encControl->API_sampleRate        != 12000 ) &&
          ( encControl->API_sampleRate        != 16000 ) &&
          ( encControl->API_sampleRate        != 24000 ) && 
          ( encControl->API_sampleRate        != 32000 ) &&
          ( encControl->API_sampleRate        != 44100 ) &&
          ( encControl->API_sampleRate        != 48000 ) ) ||
        ( ( encControl->maxInternalSampleRate !=  8000 ) &&
          ( encControl->maxInternalSampleRate != 12000 ) &&
          ( encControl->maxInternalSampleRate != 16000 ) &&
          ( encControl->maxInternalSampleRate != 24000 ) ) ) {
        ret = SKP_SILK_ENC_FS_NOT_SUPPORTED;
        SKP_assert( 0 );
        return( ret );
    }

    /* Set encoder parameters from control structure */
    API_fs_Hz           =                            encControl->API_sampleRate;
    max_internal_fs_kHz =                 (SKP_int)( encControl->maxInternalSampleRate >> 10 ) + 1;   /* convert Hz -> kHz */
    PacketSize_ms       = SKP_DIV32( 1000 * (SKP_int)encControl->packetSize, API_fs_Hz );
    TargetRate_bps      =                            encControl->bitRate;
    PacketLoss_perc     =                            encControl->packetLossPercentage;
    UseInBandFEC        =                            encControl->useInBandFEC;
    Complexity          =                            encControl->complexity;
    UseDTX              =                            encControl->useDTX;

    /* Save values in state */
    psEnc->sCmn.API_fs_Hz          = API_fs_Hz;
    psEnc->sCmn.maxInternal_fs_kHz = max_internal_fs_kHz;
    psEnc->sCmn.useInBandFEC       = UseInBandFEC;

    /* Only accept input lengths that are a multiple of 10 ms */
    input_10ms = SKP_DIV32( 100 * nSamplesIn, API_fs_Hz );
    if( input_10ms * API_fs_Hz != 100 * nSamplesIn || nSamplesIn < 0 ) {
        ret = SKP_SILK_ENC_INPUT_INVALID_NO_OF_SAMPLES;
        SKP_assert( 0 );
        return( ret );
    }

    TargetRate_bps = SKP_LIMIT( TargetRate_bps, MIN_TARGET_RATE_BPS, MAX_TARGET_RATE_BPS );
    if( ( ret = SKP_Silk_control_encoder_FIX( psEnc, PacketSize_ms, TargetRate_bps, 
                        PacketLoss_perc, UseDTX, Complexity) ) != 0 ) {
        SKP_assert( 0 );
        return( ret );
    }

    /* Make sure no more than one packet can be produced */
    if( 1000 * (SKP_int32)nSamplesIn > psEnc->sCmn.PacketSize_ms * API_fs_Hz ) {
        ret = SKP_SILK_ENC_INPUT_INVALID_NO_OF_SAMPLES;
        SKP_assert( 0 );
        return( ret );
    }

#if MAX_FS_KHZ > 16
    /* Detect energy above 8 kHz */
    if( SKP_min( API_fs_Hz, 1000 * max_internal_fs_kHz ) == 24000 && 
            psEnc->sCmn.sSWBdetect.SWB_detected == 0 && 
            psEnc->sCmn.sSWBdetect.WB_detected == 0 ) {
        SKP_Silk_detect_SWB_input( &psEnc->sCmn.sSWBdetect, samplesIn, ( SKP_int )nSamplesIn );
    }
#endif

    /* Input buffering/resampling and encoding */
    MaxBytesOut = 0;                    /* return 0 output bytes if no encoder called */
    while( 1 ) {
        nSamplesToBuffer = psEnc->sCmn.frame_length - psEnc->sCmn.inputBufIx;
        if( API_fs_Hz == SKP_SMULBB( 1000, psEnc->sCmn.fs_kHz ) ) { 
            nSamplesToBuffer  = SKP_min_int( nSamplesToBuffer, nSamplesIn );
            nSamplesFromInput = nSamplesToBuffer;
            /* Copy to buffer */
            SKP_memcpy( &psEnc->sCmn.inputBuf[ psEnc->sCmn.inputBufIx ], samplesIn, nSamplesFromInput * sizeof( SKP_int16 ) );
        } else {  
            nSamplesToBuffer  = SKP_min( nSamplesToBuffer, 10 * input_10ms * psEnc->sCmn.fs_kHz );
            nSamplesFromInput = SKP_DIV32_16( nSamplesToBuffer * API_fs_Hz, psEnc->sCmn.fs_kHz * 1000 );
            /* Resample and write to buffer */
            ret += SKP_Silk_resampler( &psEnc->sCmn.resampler_state, 
                &psEnc->sCmn.inputBuf[ psEnc->sCmn.inputBufIx ], samplesIn, nSamplesFromInput );
        } 
        samplesIn              += nSamplesFromInput;
        nSamplesIn             -= nSamplesFromInput;
        psEnc->sCmn.inputBufIx += nSamplesToBuffer;

        /* Silk encoder */
        if( psEnc->sCmn.inputBufIx >= psEnc->sCmn.frame_length ) {
            SKP_assert( psEnc->sCmn.inputBufIx == psEnc->sCmn.frame_length );

            /* Enough data in input buffer, so encode */
            if( MaxBytesOut == 0 ) {
                /* No payload obtained so far */
                MaxBytesOut = *nBytesOut;
                if( ( ret = SKP_Silk_encode_frame_FIX( psEnc, outData, &MaxBytesOut, psEnc->sCmn.inputBuf ) ) != 0 ) {
                    SKP_assert( 0 );
                }
            } else {
                /* outData already contains a payload */
                if( ( ret = SKP_Silk_encode_frame_FIX( psEnc, outData, nBytesOut, psEnc->sCmn.inputBuf ) ) != 0 ) {
                    SKP_assert( 0 );
                }
                /* Check that no second payload was created */
                SKP_assert( *nBytesOut == 0 );
            }
            psEnc->sCmn.inputBufIx = 0;
            psEnc->sCmn.controlled_since_last_payload = 0;

            if( nSamplesIn == 0 ) {
                break;
            }
        } else {
            break;
        }
    }

    *nBytesOut = MaxBytesOut;
    if( psEnc->sCmn.useDTX && psEnc->sCmn.inDTX ) {
        /* DTX simulation */
        *nBytesOut = 0;
    }



    return ret;
}


