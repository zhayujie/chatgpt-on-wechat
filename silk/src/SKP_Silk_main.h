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

#ifndef SKP_SILK_MAIN_H
#define SKP_SILK_MAIN_H

#include "SKP_Silk_SigProc_FIX.h"

#ifdef __cplusplus
extern "C"
{
#endif

#include "SKP_Silk_define.h"
#include "SKP_Silk_structs.h"
#include "SKP_Silk_tables.h"
#include "SKP_Silk_PLC.h"


/* Encodes signs of excitation */
void SKP_Silk_encode_signs(
    SKP_Silk_range_coder_state  *psRC,              /* I/O  Range coder state                           */
    const SKP_int8              q[],                /* I    pulse signal                                */
    const SKP_int               length,             /* I    length of input                             */
    const SKP_int               sigtype,            /* I    Signal type                                 */
    const SKP_int               QuantOffsetType,    /* I    Quantization offset type                    */
    const SKP_int               RateLevelIndex      /* I    Rate Level Index                            */
);

/* Decodes signs of excitation */
void SKP_Silk_decode_signs(
    SKP_Silk_range_coder_state  *psRC,              /* I/O  Range coder state                           */
    SKP_int                     q[],                /* I/O  pulse signal                                */
    const SKP_int               length,             /* I    length of output                            */
    const SKP_int               sigtype,            /* I    Signal type                                 */
    const SKP_int               QuantOffsetType,    /* I    Quantization offset type                    */
    const SKP_int               RateLevelIndex      /* I    Rate Level Index                            */
);

/* Control internal sampling rate */
SKP_int SKP_Silk_control_audio_bandwidth(
    SKP_Silk_encoder_state      *psEncC,            /* I/O  Pointer to Silk encoder state               */
    const SKP_int32             TargetRate_bps      /* I    Target max bitrate (bps)                    */
);

/***************/
/* Shell coder */
/***************/

/* Encode quantization indices of excitation */
void SKP_Silk_encode_pulses(
    SKP_Silk_range_coder_state  *psRC,              /* I/O  Range coder state                           */
    const SKP_int               sigtype,            /* I    Sigtype                                     */
    const SKP_int               QuantOffsetType,    /* I    QuantOffsetType                             */
    const SKP_int8              q[],                /* I    quantization indices                        */
    const SKP_int               frame_length        /* I    Frame length                                */
);

/* Shell encoder, operates on one shell code frame of 16 pulses */
void SKP_Silk_shell_encoder(
    SKP_Silk_range_coder_state  *psRC,              /* I/O  compressor data structure                   */
    const SKP_int               *pulses0            /* I    data: nonnegative pulse amplitudes          */
);

/* Shell decoder, operates on one shell code frame of 16 pulses */
void SKP_Silk_shell_decoder(
    SKP_int                     *pulses0,           /* O    data: nonnegative pulse amplitudes          */
    SKP_Silk_range_coder_state  *psRC,              /* I/O  compressor data structure                   */
    const SKP_int               pulses4             /* I    number of pulses per pulse-subframe         */
);

/***************/
/* Range coder */
/***************/
/* Range encoder for one symbol */
void SKP_Silk_range_encoder(
    SKP_Silk_range_coder_state  *psRC,              /* I/O  compressor data structure                   */
    const SKP_int               data,               /* I    uncompressed data                           */
    const SKP_uint16            prob[]              /* I    cumulative density functions                */
);
    
/* Range encoder for multiple symbols */
void SKP_Silk_range_encoder_multi(
    SKP_Silk_range_coder_state  *psRC,              /* I/O  compressor data structure                   */
    const SKP_int               data[],             /* I    uncompressed data    [nSymbols]             */
    const SKP_uint16 * const    prob[],             /* I    cumulative density functions                */
    const SKP_int               nSymbols            /* I    number of data symbols                      */
);

/* Range decoder for one symbol */
void SKP_Silk_range_decoder(
    SKP_int                     data[],             /* O    uncompressed data                           */
    SKP_Silk_range_coder_state  *psRC,              /* I/O  compressor data structure                   */
    const SKP_uint16            prob[],             /* I    cumulative density function                 */
    SKP_int                     probIx              /* I    initial (middle) entry of cdf               */
);

/* Range decoder for multiple symbols */
void SKP_Silk_range_decoder_multi(
    SKP_int                     data[],             /* O    uncompressed data                [nSymbols] */
    SKP_Silk_range_coder_state  *psRC,              /* I/O  compressor data structure                   */
    const SKP_uint16 * const    prob[],             /* I    cumulative density functions                */
    const SKP_int               probStartIx[],      /* I    initial (middle) entries of cdfs [nSymbols] */
    const SKP_int               nSymbols            /* I    number of data symbols                      */
);

/* Initialize range coder structure for encoder */
void SKP_Silk_range_enc_init(
    SKP_Silk_range_coder_state  *psRC               /* O    compressor data structure                   */
);

/* Initialize range coder structure for decoder */
void SKP_Silk_range_dec_init(
    SKP_Silk_range_coder_state  *psRC,              /* O    compressor data structure                   */
    const SKP_uint8             buffer[],           /* I    buffer for compressed data [bufferLength]   */
    const SKP_int32             bufferLength        /* I    buffer length (in bytes)                    */
);

/* Determine length of bitstream */
SKP_int SKP_Silk_range_coder_get_length(            /* O    returns number of BITS in stream            */
    const SKP_Silk_range_coder_state    *psRC,      /* I    compressed data structure                   */
    SKP_int                             *nBytes     /* O    number of BYTES in stream                   */
);

/* Write decodable stream to buffer, and determine its length */
void SKP_Silk_range_enc_wrap_up(
    SKP_Silk_range_coder_state  *psRC               /* I/O  compressed data structure                   */
);

/* Check that any remaining bits in the last byte are set to 1 */
void SKP_Silk_range_coder_check_after_decoding(
    SKP_Silk_range_coder_state  *psRC               /* I/O  compressed data structure                   */
);

/* Gain scalar quantization with hysteresis, uniform on log scale */
void SKP_Silk_gains_quant(
    SKP_int                     ind[ NB_SUBFR ],        /* O    gain indices                            */
    SKP_int32                   gain_Q16[ NB_SUBFR ],   /* I/O  gains (quantized out)                   */
    SKP_int                     *prev_ind,              /* I/O  last index in previous frame            */
    const SKP_int               conditional             /* I    first gain is delta coded if 1          */
);

/* Gains scalar dequantization, uniform on log scale */
void SKP_Silk_gains_dequant(
    SKP_int32                   gain_Q16[ NB_SUBFR ],   /* O    quantized gains                         */
    const SKP_int               ind[ NB_SUBFR ],        /* I    gain indices                            */
    SKP_int                     *prev_ind,              /* I/O  last index in previous frame            */
    const SKP_int               conditional             /* I    first gain is delta coded if 1          */
);

/* Convert NLSF parameters to stable AR prediction filter coefficients */
void SKP_Silk_NLSF2A_stable(
    SKP_int16                   pAR_Q12[ MAX_LPC_ORDER ],   /* O    Stabilized AR coefs [LPC_order]     */ 
    const SKP_int               pNLSF[ MAX_LPC_ORDER ],     /* I    NLSF vector         [LPC_order]     */
    const SKP_int               LPC_order                   /* I    LPC/LSF order                       */
);

/* Interpolate two vectors */
void SKP_Silk_interpolate(
    SKP_int                     xi[ MAX_LPC_ORDER ],    /* O    interpolated vector                     */
    const SKP_int               x0[ MAX_LPC_ORDER ],    /* I    first vector                            */
    const SKP_int               x1[ MAX_LPC_ORDER ],    /* I    second vector                           */
    const SKP_int               ifact_Q2,               /* I    interp. factor, weight on 2nd vector    */
    const SKP_int               d                       /* I    number of parameters                    */
);

/***********************************/
/* Noise shaping quantization (NSQ)*/
/***********************************/
void SKP_Silk_NSQ(
    SKP_Silk_encoder_state          *psEncC,                                    /* I/O  Encoder State                       */
    SKP_Silk_encoder_control        *psEncCtrlC,                                /* I    Encoder Control                     */
    SKP_Silk_nsq_state              *NSQ,                                       /* I/O  NSQ state                           */
    const SKP_int16                 x[],                                        /* I    prefiltered input signal            */
    SKP_int8                        q[],                                        /* O    quantized qulse signal              */
    const SKP_int                   LSFInterpFactor_Q2,                         /* I    LSF interpolation factor in Q2      */
    const SKP_int16                 PredCoef_Q12[ 2 * MAX_LPC_ORDER ],          /* I    Short term prediction coefficients  */
    const SKP_int16                 LTPCoef_Q14[ LTP_ORDER * NB_SUBFR ],        /* I    Long term prediction coefficients   */
    const SKP_int16                 AR2_Q13[ NB_SUBFR * MAX_SHAPE_LPC_ORDER ],  /* I                                        */
    const SKP_int                   HarmShapeGain_Q14[ NB_SUBFR ],              /* I                                        */
    const SKP_int                   Tilt_Q14[ NB_SUBFR ],                       /* I    Spectral tilt                       */
    const SKP_int32                 LF_shp_Q14[ NB_SUBFR ],                     /* I                                        */
    const SKP_int32                 Gains_Q16[ NB_SUBFR ],                      /* I                                        */
    const SKP_int                   Lambda_Q10,                                 /* I                                        */
    const SKP_int                   LTP_scale_Q14                               /* I    LTP state scaling                   */
);

/* Noise shaping using delayed decision */
void SKP_Silk_NSQ_del_dec(
    SKP_Silk_encoder_state          *psEncC,                                    /* I/O  Encoder State                       */
    SKP_Silk_encoder_control        *psEncCtrlC,                                /* I    Encoder Control                     */
    SKP_Silk_nsq_state              *NSQ,                                       /* I/O  NSQ state                           */
    const SKP_int16                 x[],                                        /* I    Prefiltered input signal            */
    SKP_int8                        q[],                                        /* O    Quantized pulse signal              */
    const SKP_int                   LSFInterpFactor_Q2,                         /* I    LSF interpolation factor in Q2      */
    const SKP_int16                 PredCoef_Q12[ 2 * MAX_LPC_ORDER ],          /* I    Prediction coefs                    */
    const SKP_int16                 LTPCoef_Q14[ LTP_ORDER * NB_SUBFR ],        /* I    LT prediction coefs                 */
    const SKP_int16                 AR2_Q13[ NB_SUBFR * MAX_SHAPE_LPC_ORDER ],  /* I                                        */
    const SKP_int                   HarmShapeGain_Q14[ NB_SUBFR ],              /* I                                        */
    const SKP_int                   Tilt_Q14[ NB_SUBFR ],                       /* I    Spectral tilt                       */
    const SKP_int32                 LF_shp_Q14[ NB_SUBFR ],                     /* I                                        */
    const SKP_int32                 Gains_Q16[ NB_SUBFR ],                      /* I                                        */
    const SKP_int                   Lambda_Q10,                                 /* I                                        */
    const SKP_int                   LTP_scale_Q14                               /* I    LTP state scaling                   */
);

/************/
/* Silk VAD */
/************/
/* Initialize the Silk VAD */
SKP_int SKP_Silk_VAD_Init(                          /* O    Return value, 0 if success                  */ 
    SKP_Silk_VAD_state          *psSilk_VAD         /* I/O  Pointer to Silk VAD state                   */ 
); 

/* Silk VAD noise level estimation */
void SKP_Silk_VAD_GetNoiseLevels(
    const SKP_int32             pX[ VAD_N_BANDS ],  /* I    subband energies                            */
    SKP_Silk_VAD_state          *psSilk_VAD         /* I/O  Pointer to Silk VAD state                   */ 
);

/* Get speech activity level in Q8 */
SKP_int SKP_Silk_VAD_GetSA_Q8(                                  /* O    Return value, 0 if success      */
    SKP_Silk_VAD_state          *psSilk_VAD,                    /* I/O  Silk VAD state                  */
    SKP_int                     *pSA_Q8,                        /* O    Speech activity level in Q8     */
    SKP_int                     *pSNR_dB_Q7,                    /* O    SNR for current frame in Q7     */
    SKP_int                     pQuality_Q15[ VAD_N_BANDS ],    /* O    Smoothed SNR for each band      */
    SKP_int                     *pTilt_Q15,                     /* O    current frame's frequency tilt  */
    const SKP_int16             pIn[],                          /* I    PCM input       [framelength]   */
    const SKP_int               framelength                     /* I    Input frame length              */
);

/* Detect signal in 8 - 12 khz range */
void SKP_Silk_detect_SWB_input(
    SKP_Silk_detect_SWB_state   *psSWBdetect,       /* I/O  Encoder state                               */
    const SKP_int16             samplesIn[],        /* I    Input to encoder                            */
    SKP_int                     nSamplesIn          /* I    Length of input                             */
);

#if SWITCH_TRANSITION_FILTERING
/* Low-pass filter with variable cutoff frequency based on  */
/* piece-wise linear interpolation between elliptic filters */
/* Start by setting transition_frame_no = 1;                */
void SKP_Silk_LP_variable_cutoff(
    SKP_Silk_LP_state           *psLP,              /* I/O  LP filter state                             */
    SKP_int16                   *out,               /* O    Low-pass filtered output signal             */
    const SKP_int16             *in,                /* I    Input signal                                */
    const SKP_int               frame_length        /* I    Frame length                                */
);
#endif

/****************************************************/
/* Decoder Functions                                */
/****************************************************/
SKP_int SKP_Silk_create_decoder(
    SKP_Silk_decoder_state      **ppsDec            /* I/O  Decoder state pointer pointer               */
);

SKP_int SKP_Silk_free_decoder(
    SKP_Silk_decoder_state      *psDec              /* I/O  Decoder state pointer                       */
);

SKP_int SKP_Silk_init_decoder(
    SKP_Silk_decoder_state      *psDec              /* I/O  Decoder state pointer                       */
);

/* Set decoder sampling rate */
void SKP_Silk_decoder_set_fs(
    SKP_Silk_decoder_state      *psDec,             /* I/O  Decoder state pointer                       */
    SKP_int                     fs_kHz              /* I    Sampling frequency (kHz)                    */
);

/****************/
/* Decode frame */
/****************/
SKP_int SKP_Silk_decode_frame(
    SKP_Silk_decoder_state      *psDec,             /* I/O  Pointer to Silk decoder state               */
    SKP_int16                   pOut[],             /* O    Pointer to output speech frame              */
    SKP_int16                   *pN,                /* O    Pointer to size of output frame             */
    const SKP_uint8             pCode[],            /* I    Pointer to payload                          */
    const SKP_int               nBytes,             /* I    Payload length                              */
    SKP_int                     action,             /* I    Action from Jitter Buffer                   */
    SKP_int                     *decBytes           /* O    Used bytes to decode this frame             */
);

/* Decode parameters from payload */
void SKP_Silk_decode_parameters(
    SKP_Silk_decoder_state      *psDec,             /* I/O  State                                       */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I/O  Decoder control                             */
    SKP_int                     q[],                /* O    Excitation signal                           */
    const SKP_int               fullDecoding        /* I    Flag to tell if only arithmetic decoding    */
);

/* Core decoder. Performs inverse NSQ operation LTP + LPC */
void SKP_Silk_decode_core(
    SKP_Silk_decoder_state      *psDec,                             /* I/O  Decoder state               */
    SKP_Silk_decoder_control    *psDecCtrl,                         /* I    Decoder control             */
    SKP_int16                   xq[],                               /* O    Decoded speech              */
    const SKP_int               q[ MAX_FRAME_LENGTH ]               /* I    Pulse signal                */
);

/* NLSF vector decoder */
void SKP_Silk_NLSF_MSVQ_decode(
    SKP_int                         *pNLSF_Q15,     /* O    Pointer to decoded output [LPC_ORDER x 1]   */
    const SKP_Silk_NLSF_CB_struct   *psNLSF_CB,     /* I    Pointer to NLSF codebook struct             */
    const SKP_int                   *NLSFIndices,   /* I    Pointer to NLSF indices [nStages x 1]       */
    const SKP_int                   LPC_order       /* I    LPC order                                   */
);

/**********************/
/* Arithmetic coding */
/*********************/

/* Decode quantization indices of excitation (Shell coding) */
void SKP_Silk_decode_pulses(
    SKP_Silk_range_coder_state  *psRC,              /* I/O  Range coder state                           */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I/O  Decoder control                             */
    SKP_int                     q[],                /* O    Excitation signal                           */
    const SKP_int               frame_length        /* I    Frame length (preliminary)                  */
);

/******************/
/* CNG */
/******************/

/* Reset CNG */
void SKP_Silk_CNG_Reset(
    SKP_Silk_decoder_state      *psDec              /* I/O  Decoder state                               */
);

/* Updates CNG estimate, and applies the CNG when packet was lost   */
void SKP_Silk_CNG(
    SKP_Silk_decoder_state      *psDec,             /* I/O  Decoder state                               */
    SKP_Silk_decoder_control    *psDecCtrl,         /* I/O  Decoder control                             */
    SKP_int16                   signal[],           /* I/O  Signal                                      */
    SKP_int                     length              /* I    Length of residual                          */
);

/* Encoding of various parameters */
void SKP_Silk_encode_parameters(
    SKP_Silk_encoder_state      *psEncC,            /* I/O  Encoder state                               */
    SKP_Silk_encoder_control    *psEncCtrlC,        /* I/O  Encoder control                             */
    SKP_Silk_range_coder_state  *psRC,              /* I/O  Range coder state                           */
    const SKP_int8               *q                 /* I    Quantization indices                        */
);

/* Extract lowest layer encoding */
void SKP_Silk_get_low_layer_internal(
    const SKP_uint8             *indata,            /* I:   Encoded input vector                        */
    const SKP_int16             nBytesIn,           /* I:   Number of input Bytes                       */
    SKP_uint8                   *Layer0data,        /* O:   Layer0 payload                              */
    SKP_int16                   *nLayer0Bytes       /* O:   Number of FEC Bytes                         */
);

/* Resets LBRR buffer, used if packet size changes */
void SKP_Silk_LBRR_reset( 
    SKP_Silk_encoder_state      *psEncC             /* I/O  Pointer to Silk encoder state               */
);


#ifdef __cplusplus
}
#endif

#endif
