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

#ifndef SKP_SILK_DEFINE_H
#define SKP_SILK_DEFINE_H

#include "SKP_Silk_errors.h"
#include "SKP_Silk_typedef.h"

#ifdef __cplusplus
extern "C"
{
#endif


#define MAX_FRAMES_PER_PACKET                   5



/* Limits on bitrate */
#define MIN_TARGET_RATE_BPS                     5000
#define MAX_TARGET_RATE_BPS                     100000

/* Transition bitrates between modes */
#define SWB2WB_BITRATE_BPS                      25000
#define WB2SWB_BITRATE_BPS                      30000
#define WB2MB_BITRATE_BPS                       14000
#define MB2WB_BITRATE_BPS                       18000
#define MB2NB_BITRATE_BPS                       10000
#define NB2MB_BITRATE_BPS                       14000

/* Integration/hysteresis threshold for lowering internal sample frequency */
/* 30000000 -> 6 sec if bitrate is 5000 bps below limit; 3 sec if bitrate is 10000 bps below limit */
#define ACCUM_BITS_DIFF_THRESHOLD               30000000 
#define TARGET_RATE_TAB_SZ                      8

/* DTX settings                                 */
#define NO_SPEECH_FRAMES_BEFORE_DTX             5       /* eq 100 ms */
#define MAX_CONSECUTIVE_DTX                     20      /* eq 400 ms */

#define USE_LBRR                                1

/* Amount of concecutive no FEC packets before telling JB */
#define NO_LBRR_THRES                           10

/* Maximum delay between real packet and LBRR packet */
#define MAX_LBRR_DELAY                          2
#define LBRR_IDX_MASK                           1

#define INBAND_FEC_MIN_RATE_BPS                 18000  /* Dont use inband FEC below this total target rate  */
#define LBRR_LOSS_THRES                         1   /* Start adding LBRR at this loss rate                  */

/* LBRR usage defines */
#define SKP_SILK_NO_LBRR                        0   /* No LBRR information for this packet                  */
#define SKP_SILK_ADD_LBRR_TO_PLUS1              1   /* Add LBRR for this packet to packet n + 1             */
#define SKP_SILK_ADD_LBRR_TO_PLUS2              2   /* Add LBRR for this packet to packet n + 2             */

/* Frame termination indicator defines */
#define SKP_SILK_LAST_FRAME                     0   /* Last frames in packet                                */
#define SKP_SILK_MORE_FRAMES                    1   /* More frames to follow this one                       */
#define SKP_SILK_LBRR_VER1                      2   /* LBRR information from packet n - 1                   */
#define SKP_SILK_LBRR_VER2                      3   /* LBRR information from packet n - 2                   */
#define SKP_SILK_EXT_LAYER                      4   /* Extension layers added                               */

/* Number of Second order Sections for SWB detection HP filter */
#define NB_SOS                                  3
#define HP_8_KHZ_THRES                          10          /* average energy per sample, above 8 kHz       */
#define CONCEC_SWB_SMPLS_THRES                  480 * 15    /* 300 ms                                       */
#define WB_DETECT_ACTIVE_SPEECH_MS_THRES        15000       /* ms of active speech needed for WB detection  */

/* Low complexity setting */
#define LOW_COMPLEXITY_ONLY                     0

/* Activate bandwidth transition filtering for mode switching */
#define SWITCH_TRANSITION_FILTERING             1

/* Decoder Parameters */
#define DEC_HP_ORDER                            2

/* Maximum sampling frequency, should be 16 for some embedded platforms */
#define MAX_FS_KHZ                              24 
#define MAX_API_FS_KHZ                          48

/* Signal Types used by silk */
#define SIG_TYPE_VOICED                         0
#define SIG_TYPE_UNVOICED                       1

/* VAD Types used by silk */
#define NO_VOICE_ACTIVITY                       0
#define VOICE_ACTIVITY                          1

/* Number of samples per frame */ 
#define FRAME_LENGTH_MS                         20
#define MAX_FRAME_LENGTH                        ( FRAME_LENGTH_MS * MAX_FS_KHZ )

/* Milliseconds of lookahead for pitch analysis */
#define LA_PITCH_MS                             2
#define LA_PITCH_MAX                            ( LA_PITCH_MS * MAX_FS_KHZ )

/* Length of LPC window used in find pitch */
#define FIND_PITCH_LPC_WIN_MS                   ( 20 + (LA_PITCH_MS << 1) )
#define FIND_PITCH_LPC_WIN_MAX                  ( FIND_PITCH_LPC_WIN_MS * MAX_FS_KHZ )

/* Order of LPC used in find pitch */
#define MAX_FIND_PITCH_LPC_ORDER                16

#define PITCH_EST_COMPLEXITY_HC_MODE            SKP_Silk_PITCH_EST_MAX_COMPLEX
#define PITCH_EST_COMPLEXITY_MC_MODE            SKP_Silk_PITCH_EST_MID_COMPLEX
#define PITCH_EST_COMPLEXITY_LC_MODE            SKP_Silk_PITCH_EST_MIN_COMPLEX

/* Milliseconds of lookahead for noise shape analysis */
#define LA_SHAPE_MS                             5
#define LA_SHAPE_MAX                            ( LA_SHAPE_MS * MAX_FS_KHZ )

/* Max length of LPC window used in noise shape analysis */
#define SHAPE_LPC_WIN_MAX                       ( 15 * MAX_FS_KHZ )

/* Max number of bytes in payload output buffer (may contain multiple frames) */
#define MAX_ARITHM_BYTES                        1024

#define RANGE_CODER_WRITE_BEYOND_BUFFER         -1
#define RANGE_CODER_CDF_OUT_OF_RANGE            -2
#define RANGE_CODER_NORMALIZATION_FAILED        -3
#define RANGE_CODER_ZERO_INTERVAL_WIDTH         -4
#define RANGE_CODER_DECODER_CHECK_FAILED        -5
#define RANGE_CODER_READ_BEYOND_BUFFER          -6
#define RANGE_CODER_ILLEGAL_SAMPLING_RATE       -7
#define RANGE_CODER_DEC_PAYLOAD_TOO_LONG        -8

/* dB level of lowest gain quantization level */
#define MIN_QGAIN_DB                            6
/* dB level of highest gain quantization level */
#define MAX_QGAIN_DB                            86
/* Number of gain quantization levels */
#define N_LEVELS_QGAIN                          64
/* Max increase in gain quantization index */
#define MAX_DELTA_GAIN_QUANT                    40
/* Max decrease in gain quantization index */
#define MIN_DELTA_GAIN_QUANT                    -4

/* Quantization offsets (multiples of 4) */
#define OFFSET_VL_Q10                           32
#define OFFSET_VH_Q10                           100
#define OFFSET_UVL_Q10                          100
#define OFFSET_UVH_Q10                          256

/* Maximum numbers of iterations used to stabilize a LPC vector */
#define MAX_LPC_STABILIZE_ITERATIONS            20

#define MAX_LPC_ORDER                           16
#define MIN_LPC_ORDER                           10

/* Find Pred Coef defines */
#define LTP_ORDER                               5

/* LTP quantization settings */
#define NB_LTP_CBKS                             3

/* Number of subframes */
#define NB_SUBFR                                4

/* Flag to use harmonic noise shaping */
#define USE_HARM_SHAPING                        1

/* Max LPC order of noise shaping filters */
#define MAX_SHAPE_LPC_ORDER                     16

#define HARM_SHAPE_FIR_TAPS                     3

/* Maximum number of delayed decision states */
#define MAX_DEL_DEC_STATES                      4

#define LTP_BUF_LENGTH                          512
#define LTP_MASK                                (LTP_BUF_LENGTH - 1)

#define DECISION_DELAY                          32
#define DECISION_DELAY_MASK                     (DECISION_DELAY - 1)

/* number of subframes for excitation entropy coding */
#define SHELL_CODEC_FRAME_LENGTH                16
#define MAX_NB_SHELL_BLOCKS                     (MAX_FRAME_LENGTH / SHELL_CODEC_FRAME_LENGTH)

/* number of rate levels, for entropy coding of excitation */
#define N_RATE_LEVELS                           10

/* maximum sum of pulses per shell coding frame */
#define MAX_PULSES                              18

#define MAX_MATRIX_SIZE                         MAX_LPC_ORDER /* Max of LPC Order and LTP order */

#if( MAX_LPC_ORDER > DECISION_DELAY )
# define NSQ_LPC_BUF_LENGTH                     MAX_LPC_ORDER
#else
# define NSQ_LPC_BUF_LENGTH                     DECISION_DELAY
#endif

/***********************/
/* High pass filtering */
/***********************/
#define HIGH_PASS_INPUT                         1

/***************************/
/* Voice activity detector */
/***************************/
#define VAD_N_BANDS                             4

#define VAD_INTERNAL_SUBFRAMES_LOG2             2
#define VAD_INTERNAL_SUBFRAMES                  (1 << VAD_INTERNAL_SUBFRAMES_LOG2)
    
#define VAD_NOISE_LEVEL_SMOOTH_COEF_Q16         1024    /* Must be < 4096                                   */
#define VAD_NOISE_LEVELS_BIAS                   50 

/* Sigmoid settings */
#define VAD_NEGATIVE_OFFSET_Q5                  128     /* sigmoid is 0 at -128                             */
#define VAD_SNR_FACTOR_Q16                      45000 

/* smoothing for SNR measurement */
#define VAD_SNR_SMOOTH_COEF_Q18                 4096

/******************/
/* NLSF quantizer */
/******************/
#   define NLSF_MSVQ_MAX_CB_STAGES                      10  /* Update manually when changing codebooks      */
#   define NLSF_MSVQ_MAX_VECTORS_IN_STAGE               128 /* Update manually when changing codebooks      */
#   define NLSF_MSVQ_MAX_VECTORS_IN_STAGE_TWO_TO_END    16  /* Update manually when changing codebooks      */

#define NLSF_MSVQ_FLUCTUATION_REDUCTION         1
#define MAX_NLSF_MSVQ_SURVIVORS                 16
#define MAX_NLSF_MSVQ_SURVIVORS_LC_MODE         2
#define MAX_NLSF_MSVQ_SURVIVORS_MC_MODE         4

/* Based on above defines, calculate how much memory is necessary to allocate */
#if( NLSF_MSVQ_MAX_VECTORS_IN_STAGE > ( MAX_NLSF_MSVQ_SURVIVORS_LC_MODE * NLSF_MSVQ_MAX_VECTORS_IN_STAGE_TWO_TO_END ) )
#   define NLSF_MSVQ_TREE_SEARCH_MAX_VECTORS_EVALUATED_LC_MODE  NLSF_MSVQ_MAX_VECTORS_IN_STAGE
#else
#   define NLSF_MSVQ_TREE_SEARCH_MAX_VECTORS_EVALUATED_LC_MODE  MAX_NLSF_MSVQ_SURVIVORS_LC_MODE * NLSF_MSVQ_MAX_VECTORS_IN_STAGE_TWO_TO_END
#endif

#if( NLSF_MSVQ_MAX_VECTORS_IN_STAGE > ( MAX_NLSF_MSVQ_SURVIVORS * NLSF_MSVQ_MAX_VECTORS_IN_STAGE_TWO_TO_END ) )
#   define NLSF_MSVQ_TREE_SEARCH_MAX_VECTORS_EVALUATED  NLSF_MSVQ_MAX_VECTORS_IN_STAGE
#else
#   define NLSF_MSVQ_TREE_SEARCH_MAX_VECTORS_EVALUATED  MAX_NLSF_MSVQ_SURVIVORS * NLSF_MSVQ_MAX_VECTORS_IN_STAGE_TWO_TO_END
#endif

#define NLSF_MSVQ_SURV_MAX_REL_RD               0.1f    /* Must be < 0.5                                    */

/* Transition filtering for mode switching */
#if SWITCH_TRANSITION_FILTERING
#  define TRANSITION_TIME_UP_MS                 5120 // 5120 = 64 * FRAME_LENGTH_MS * ( TRANSITION_INT_NUM - 1 ) = 64*(20*4)
#  define TRANSITION_TIME_DOWN_MS               2560 // 2560 = 32 * FRAME_LENGTH_MS * ( TRANSITION_INT_NUM - 1 ) = 32*(20*4)
#  define TRANSITION_NB                         3 /* Hardcoded in tables */
#  define TRANSITION_NA                         2 /* Hardcoded in tables */
#  define TRANSITION_INT_NUM                    5 /* Hardcoded in tables */
#  define TRANSITION_FRAMES_UP                  ( TRANSITION_TIME_UP_MS   / FRAME_LENGTH_MS )
#  define TRANSITION_FRAMES_DOWN                ( TRANSITION_TIME_DOWN_MS / FRAME_LENGTH_MS )
#  define TRANSITION_INT_STEPS_UP               ( TRANSITION_FRAMES_UP    / ( TRANSITION_INT_NUM - 1 )  )
#  define TRANSITION_INT_STEPS_DOWN             ( TRANSITION_FRAMES_DOWN  / ( TRANSITION_INT_NUM - 1 )  )
#endif

/* Row based */
#define matrix_ptr(Matrix_base_adr, row, column, N)         *(Matrix_base_adr + ((row)*(N)+(column)))
#define matrix_adr(Matrix_base_adr, row, column, N)          (Matrix_base_adr + ((row)*(N)+(column)))

/* Column based */
#ifndef matrix_c_ptr
#   define matrix_c_ptr(Matrix_base_adr, row, column, M)    *(Matrix_base_adr + ((row)+(M)*(column)))
#endif
#define matrix_c_adr(Matrix_base_adr, row, column, M)        (Matrix_base_adr + ((row)+(M)*(column)))

/* BWE factors to apply after packet loss */
#define BWE_AFTER_LOSS_Q16                      63570

/* Defines for CN generation */
#define CNG_BUF_MASK_MAX                        255             /* 2^floor(log2(MAX_FRAME_LENGTH))-1    */
#define CNG_GAIN_SMTH_Q16                       4634            /* 0.25^(1/4)                           */
#define CNG_NLSF_SMTH_Q16                       16348           /* 0.25                                 */

#ifdef __cplusplus
}
#endif

#endif
