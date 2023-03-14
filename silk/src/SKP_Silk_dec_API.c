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

#include "SKP_Silk_SDK_API.h"
#include "SKP_Silk_main.h"

/*********************/
/* Decoder functions */
/*********************/

SKP_int SKP_Silk_SDK_Get_Decoder_Size( SKP_int32 *decSizeBytes ) 
{
    SKP_int ret = 0;

    *decSizeBytes = sizeof( SKP_Silk_decoder_state );

    return ret;
}

/* Reset decoder state */
SKP_int SKP_Silk_SDK_InitDecoder(
    void* decState                                      /* I/O: State                                          */
)
{
    SKP_int ret = 0;
    SKP_Silk_decoder_state *struc;

    struc = (SKP_Silk_decoder_state *)decState;

    ret  = SKP_Silk_init_decoder( struc );

    return ret;
}

/* Decode a frame */
SKP_int SKP_Silk_SDK_Decode(
    void*                               decState,       /* I/O: State                                           */
    SKP_SILK_SDK_DecControlStruct*      decControl,     /* I/O: Control structure                               */
    SKP_int                             lostFlag,       /* I:   0: no loss, 1 loss                              */
    const SKP_uint8                     *inData,        /* I:   Encoded input vector                            */
    const SKP_int                       nBytesIn,       /* I:   Number of input Bytes                           */
    SKP_int16                           *samplesOut,    /* O:   Decoded output speech vector                    */
    SKP_int16                           *nSamplesOut    /* I/O: Number of samples (vector/decoded)              */
)
{
    SKP_int ret = 0, used_bytes, prev_fs_kHz;
    SKP_Silk_decoder_state *psDec;
    SKP_int16 samplesOutInternal[ MAX_API_FS_KHZ * FRAME_LENGTH_MS ];
    SKP_int16 *pSamplesOutInternal;

    psDec = (SKP_Silk_decoder_state *)decState;

    /* We need this buffer to have room for an internal frame */
    pSamplesOutInternal = samplesOut;
    if( psDec->fs_kHz * 1000 > decControl->API_sampleRate ) {
        pSamplesOutInternal = samplesOutInternal;
    }

    /**********************************/
    /* Test if first frame in payload */
    /**********************************/
    if( psDec->moreInternalDecoderFrames == 0 ) {
        /* First Frame in Payload */
        psDec->nFramesDecoded = 0;  /* Used to count frames in packet */
    }

    if( psDec->moreInternalDecoderFrames == 0 &&    /* First frame in packet    */
        lostFlag == 0 &&                            /* Not packet loss          */
        nBytesIn > MAX_ARITHM_BYTES ) {             /* Too long payload         */
            /* Avoid trying to decode a too large packet */
            lostFlag = 1;
            ret = SKP_SILK_DEC_PAYLOAD_TOO_LARGE;
    }
            
    /* Save previous sample frequency */
    prev_fs_kHz = psDec->fs_kHz;
    
    /* Call decoder for one frame */
    ret += SKP_Silk_decode_frame( psDec, pSamplesOutInternal, nSamplesOut, inData, nBytesIn, 
            lostFlag, &used_bytes );
    
    if( used_bytes ) { /* Only Call if not a packet loss */
        if( psDec->nBytesLeft > 0 && psDec->FrameTermination == SKP_SILK_MORE_FRAMES && psDec->nFramesDecoded < 5 ) {
            /* We have more frames in the Payload */
            psDec->moreInternalDecoderFrames = 1;
        } else {
            /* Last frame in Payload */
            psDec->moreInternalDecoderFrames = 0;
            psDec->nFramesInPacket = psDec->nFramesDecoded;
        
            /* Track inband FEC usage */
            if( psDec->vadFlag == VOICE_ACTIVITY ) {
                if( psDec->FrameTermination == SKP_SILK_LAST_FRAME ) {
                    psDec->no_FEC_counter++;
                    if( psDec->no_FEC_counter > NO_LBRR_THRES ) {
                        psDec->inband_FEC_offset = 0;
                    }
                } else if( psDec->FrameTermination == SKP_SILK_LBRR_VER1 ) {
                    psDec->inband_FEC_offset = 1; /* FEC info with 1 packet delay */
                    psDec->no_FEC_counter    = 0;
                } else if( psDec->FrameTermination == SKP_SILK_LBRR_VER2 ) {
                    psDec->inband_FEC_offset = 2; /* FEC info with 2 packets delay */
                    psDec->no_FEC_counter    = 0;
                }
            }
        }
    }

    if( MAX_API_FS_KHZ * 1000 < decControl->API_sampleRate ||
        8000       > decControl->API_sampleRate ) {
        ret = SKP_SILK_DEC_INVALID_SAMPLING_FREQUENCY;
        return( ret );
    }

    /* Resample if needed */
    if( psDec->fs_kHz * 1000 != decControl->API_sampleRate ) { 
        SKP_int16 samplesOut_tmp[ MAX_API_FS_KHZ * FRAME_LENGTH_MS ];
        SKP_assert( psDec->fs_kHz <= MAX_API_FS_KHZ );

        /* Copy to a tmp buffer as the resampling writes to samplesOut */
        SKP_memcpy( samplesOut_tmp, pSamplesOutInternal, *nSamplesOut * sizeof( SKP_int16 ) );

        /* (Re-)initialize resampler state when switching internal sampling frequency */
        if( prev_fs_kHz != psDec->fs_kHz || psDec->prev_API_sampleRate != decControl->API_sampleRate ) {
            ret = SKP_Silk_resampler_init( &psDec->resampler_state, SKP_SMULBB( psDec->fs_kHz, 1000 ), decControl->API_sampleRate );
        }

        /* Resample the output to API_sampleRate */
        ret += SKP_Silk_resampler( &psDec->resampler_state, samplesOut, samplesOut_tmp, *nSamplesOut );

        /* Update the number of output samples */
        *nSamplesOut = SKP_DIV32( ( SKP_int32 )*nSamplesOut * decControl->API_sampleRate, psDec->fs_kHz * 1000 );
    } else if( prev_fs_kHz * 1000 > decControl->API_sampleRate ) { 
        SKP_memcpy( samplesOut, pSamplesOutInternal, *nSamplesOut * sizeof( SKP_int16 ) );
    }

    psDec->prev_API_sampleRate = decControl->API_sampleRate;

    /* Copy all parameters that are needed out of internal structure to the control stucture */
    decControl->frameSize                 = (SKP_uint16)( decControl->API_sampleRate / 50 ) ;
    decControl->framesPerPacket           = ( SKP_int )psDec->nFramesInPacket;
    decControl->inBandFECOffset           = ( SKP_int )psDec->inband_FEC_offset;
    decControl->moreInternalDecoderFrames = ( SKP_int )psDec->moreInternalDecoderFrames;

    return ret;
}

/* Function to find LBRR information in a packet */
void SKP_Silk_SDK_search_for_LBRR(
    const SKP_uint8                     *inData,        /* I:   Encoded input vector                            */
    const SKP_int                       nBytesIn,       /* I:   Number of input Bytes                           */
    SKP_int                             lost_offset,    /* I:   Offset from lost packet                         */
    SKP_uint8                           *LBRRData,      /* O:   LBRR payload                                    */
    SKP_int16                           *nLBRRBytes     /* O:   Number of LBRR Bytes                            */
)
{
    SKP_Silk_decoder_state   sDec; // Local decoder state to avoid interfering with running decoder */
    SKP_Silk_decoder_control sDecCtrl;
    SKP_int TempQ[ MAX_FRAME_LENGTH ];

    if( lost_offset < 1 || lost_offset > MAX_LBRR_DELAY ) {
        /* No useful FEC in this packet */
        *nLBRRBytes = 0;
        return;
    }

    sDec.nFramesDecoded = 0;
    sDec.fs_kHz         = 0; /* Force update parameters LPC_order etc */
	sDec.lossCnt        = 0; /* Avoid running bw expansion of the LPC parameters when searching for LBRR data */
    SKP_memset( sDec.prevNLSF_Q15, 0, MAX_LPC_ORDER * sizeof( SKP_int ) );
    SKP_Silk_range_dec_init( &sDec.sRC, inData, ( SKP_int32 )nBytesIn );
    
    while(1) {
        SKP_Silk_decode_parameters( &sDec, &sDecCtrl, TempQ, 0 );
    
        if( sDec.sRC.error ) {
            /* Corrupt stream */
            *nLBRRBytes = 0;
            return;
        };
        if( ( sDec.FrameTermination - 1 ) & lost_offset && sDec.FrameTermination > 0 && sDec.nBytesLeft >= 0 ) {
            /* The wanted FEC is present in the packet */
            *nLBRRBytes = sDec.nBytesLeft;
            SKP_memcpy( LBRRData, &inData[ nBytesIn - sDec.nBytesLeft ], sDec.nBytesLeft * sizeof( SKP_uint8 ) );
            break;
        }
        if( sDec.nBytesLeft > 0 && sDec.FrameTermination == SKP_SILK_MORE_FRAMES ) {
            sDec.nFramesDecoded++;
        } else {
            LBRRData = NULL;
            *nLBRRBytes = 0;
            break;
        }
    }
}

/* Getting type of content for a packet */
void SKP_Silk_SDK_get_TOC(
    const SKP_uint8                     *inData,        /* I:   Encoded input vector                            */
    const SKP_int                       nBytesIn,       /* I:   Number of input bytes                           */
    SKP_Silk_TOC_struct                 *Silk_TOC       /* O:   Type of content                                 */
)
{
    SKP_Silk_decoder_state      sDec; // Local Decoder state to avoid interfering with running decoder */
    SKP_Silk_decoder_control    sDecCtrl;
    SKP_int TempQ[ MAX_FRAME_LENGTH ];

    sDec.nFramesDecoded = 0;
    sDec.fs_kHz         = 0; /* Force update parameters LPC_order etc */
    SKP_Silk_range_dec_init( &sDec.sRC, inData, ( SKP_int32 )nBytesIn );

    Silk_TOC->corrupt = 0;
    while( 1 ) {
        SKP_Silk_decode_parameters( &sDec, &sDecCtrl, TempQ, 0 );
        
        Silk_TOC->vadFlags[     sDec.nFramesDecoded ] = sDec.vadFlag;
        Silk_TOC->sigtypeFlags[ sDec.nFramesDecoded ] = sDecCtrl.sigtype;
    
        if( sDec.sRC.error ) {
            /* Corrupt stream */
            Silk_TOC->corrupt = 1;
            break;
        };
    
        if( sDec.nBytesLeft > 0 && sDec.FrameTermination == SKP_SILK_MORE_FRAMES ) {
            sDec.nFramesDecoded++;
        } else {
            break;
        }
    }
    if( Silk_TOC->corrupt || sDec.FrameTermination == SKP_SILK_MORE_FRAMES || 
        sDec.nFramesInPacket > SILK_MAX_FRAMES_PER_PACKET ) {
        /* Corrupt packet */
        SKP_memset( Silk_TOC, 0, sizeof( SKP_Silk_TOC_struct ) );
        Silk_TOC->corrupt = 1;
    } else {
        Silk_TOC->framesInPacket = sDec.nFramesDecoded + 1;
        Silk_TOC->fs_kHz         = sDec.fs_kHz;
        if( sDec.FrameTermination == SKP_SILK_LAST_FRAME ) {
            Silk_TOC->inbandLBRR = sDec.FrameTermination;
        } else {
            Silk_TOC->inbandLBRR = sDec.FrameTermination - 1;
        }
    }
}

/**************************/
/* Get the version number */
/**************************/
/* Return a pointer to string specifying the version */ 
const char *SKP_Silk_SDK_get_version()
{
    static const char version[] = "1.0.9.6";
    return version;
}
