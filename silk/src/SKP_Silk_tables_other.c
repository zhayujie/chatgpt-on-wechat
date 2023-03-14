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

#include "SKP_Silk_structs.h"
#include "SKP_Silk_define.h"
#include "SKP_Silk_tables.h"
#ifdef __cplusplus
extern "C"
{
#endif

/* Piece-wise linear mapping from bitrate in kbps to coding quality in dB SNR */
const SKP_int32 TargetRate_table_NB[ TARGET_RATE_TAB_SZ ] = {
    0,      8000,   9000,   11000,  13000,  16000,  22000,  MAX_TARGET_RATE_BPS
};
const SKP_int32 TargetRate_table_MB[ TARGET_RATE_TAB_SZ ] = {
    0,      10000,  12000,  14000,  17000,  21000,  28000,  MAX_TARGET_RATE_BPS
};
const SKP_int32 TargetRate_table_WB[ TARGET_RATE_TAB_SZ ] = {
    0,      11000,  14000,  17000,  21000,  26000,  36000,  MAX_TARGET_RATE_BPS
};
const SKP_int32 TargetRate_table_SWB[ TARGET_RATE_TAB_SZ ] = {
    0,      13000,  16000,  19000,  25000,  32000,  46000,  MAX_TARGET_RATE_BPS
};
const SKP_int32 SNR_table_Q1[ TARGET_RATE_TAB_SZ ] = {
    19,     31,     35,     39,     43,     47,     54,     64
};

const SKP_int32 SNR_table_one_bit_per_sample_Q7[ 4 ] = {
    1984,   2240,   2408,   2708
};

/* Filter coeficicnts for HP filter: 4. Order filter implementad as two biquad filters  */
const SKP_int16 SKP_Silk_SWB_detect_B_HP_Q13[ NB_SOS ][ 3 ] = {
    //{400, -550, 400}, {400, 130, 400}, {400, 390, 400}
    {575, -948, 575}, {575, -221, 575}, {575, 104, 575} 
};
const SKP_int16 SKP_Silk_SWB_detect_A_HP_Q13[ NB_SOS ][ 2 ] = {
    {14613, 6868}, {12883, 7337}, {11586, 7911}
    //{14880, 6900}, {14400, 7300}, {13700, 7800}
};

/* Decoder high-pass filter coefficients for 24 kHz sampling, -6 dB @ 44 Hz */
const SKP_int16 SKP_Silk_Dec_A_HP_24[ DEC_HP_ORDER     ] = {-16220, 8030};              // second order AR coefs, Q13
const SKP_int16 SKP_Silk_Dec_B_HP_24[ DEC_HP_ORDER + 1 ] = {8000, -16000, 8000};        // second order MA coefs, Q13

/* Decoder high-pass filter coefficients for 16 kHz sampling, - 6 dB @ 46 Hz */
const SKP_int16 SKP_Silk_Dec_A_HP_16[ DEC_HP_ORDER     ] = {-16127, 7940};              // second order AR coefs, Q13
const SKP_int16 SKP_Silk_Dec_B_HP_16[ DEC_HP_ORDER + 1 ] = {8000, -16000, 8000};        // second order MA coefs, Q13

/* Decoder high-pass filter coefficients for 12 kHz sampling, -6 dB @ 44 Hz */
const SKP_int16 SKP_Silk_Dec_A_HP_12[ DEC_HP_ORDER     ] = {-16043, 7859};              // second order AR coefs, Q13
const SKP_int16 SKP_Silk_Dec_B_HP_12[ DEC_HP_ORDER + 1 ] = {8000, -16000, 8000};        // second order MA coefs, Q13

/* Decoder high-pass filter coefficients for 8 kHz sampling, -6 dB @ 43 Hz */
const SKP_int16 SKP_Silk_Dec_A_HP_8[ DEC_HP_ORDER     ] = {-15885, 7710};               // second order AR coefs, Q13
const SKP_int16 SKP_Silk_Dec_B_HP_8[ DEC_HP_ORDER + 1 ] = {8000, -16000, 8000};         // second order MA coefs, Q13

/* table for LSB coding */
const SKP_uint16 SKP_Silk_lsb_CDF[ 3 ] = {0,  40000,  65535};

/* tables for LTPScale */
const SKP_uint16 SKP_Silk_LTPscale_CDF[ 4 ] = {0,  32000,  48000,  65535};
const SKP_int    SKP_Silk_LTPscale_offset   = 2;

/* tables for VAD flag */
const SKP_uint16 SKP_Silk_vadflag_CDF[ 3 ] = {0,  22000,  65535}; // 66% for speech, 33% for no speech
const SKP_int    SKP_Silk_vadflag_offset   = 1;

/* tables for sampling rate */
const SKP_int    SKP_Silk_SamplingRates_table[ 4 ] = {8, 12, 16, 24};
const SKP_uint16 SKP_Silk_SamplingRates_CDF[ 5 ]   = {0,  16000,  32000,  48000,  65535};
const SKP_int    SKP_Silk_SamplingRates_offset     = 2;

/* tables for NLSF interpolation factor */
const SKP_uint16 SKP_Silk_NLSF_interpolation_factor_CDF[ 6 ] = {0,   3706,   8703,  19226,  30926,  65535};
const SKP_int    SKP_Silk_NLSF_interpolation_factor_offset   = 4;

/* Table for frame termination indication */
const SKP_uint16 SKP_Silk_FrameTermination_CDF[ 5 ] = {0, 20000, 45000, 56000, 65535};
const SKP_int    SKP_Silk_FrameTermination_offset   = 2;

/* Table for random seed */
const SKP_uint16 SKP_Silk_Seed_CDF[ 5 ] = {0, 16384, 32768, 49152, 65535};
const SKP_int    SKP_Silk_Seed_offset   = 2;

/* Quantization offsets */
const SKP_int16  SKP_Silk_Quantization_Offsets_Q10[ 2 ][ 2 ] = {
    { OFFSET_VL_Q10, OFFSET_VH_Q10 }, { OFFSET_UVL_Q10, OFFSET_UVH_Q10 }
};

/* Table for LTPScale */
const SKP_int16 SKP_Silk_LTPScales_table_Q14[ 3 ] = { 15565, 11469, 8192 };

#if SWITCH_TRANSITION_FILTERING
/*  Elliptic/Cauer filters designed with 0.1 dB passband ripple, 
        80 dB minimum stopband attenuation, and
        [0.95 : 0.15 : 0.35] normalized cut off frequencies. */

/* Interpolation points for filter coefficients used in the bandwidth transition smoother */
const SKP_int32 SKP_Silk_Transition_LP_B_Q28[ TRANSITION_INT_NUM ][ TRANSITION_NB ] = 
{
{    250767114,  501534038,  250767114  },
{    209867381,  419732057,  209867381  },
{    170987846,  341967853,  170987846  },
{    131531482,  263046905,  131531482  },
{     89306658,  178584282,   89306658  }
};

/* Interpolation points for filter coefficients used in the bandwidth transition smoother */
const SKP_int32 SKP_Silk_Transition_LP_A_Q28[ TRANSITION_INT_NUM ][ TRANSITION_NA ] = 
{
{    506393414,  239854379  },
{    411067935,  169683996  },
{    306733530,  116694253  },
{    185807084,   77959395  },
{     35497197,   57401098  }
};
#endif

#ifdef __cplusplus
}
#endif

