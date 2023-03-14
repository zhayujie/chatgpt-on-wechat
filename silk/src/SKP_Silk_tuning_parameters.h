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

#ifndef SKP_SILK_TUNING_PARAMETERS_H
#define SKP_SILK_TUNING_PARAMETERS_H

#ifdef __cplusplus
extern "C"
{
#endif

/*******************/
/* Pitch estimator */
/*******************/

/* Level of noise floor for whitening filter LPC analysis in pitch analysis */
#define FIND_PITCH_WHITE_NOISE_FRACTION                 1e-3f

/* Bandwidth expansion for whitening filter in pitch analysis */
#define FIND_PITCH_BANDWITH_EXPANSION                   0.99f

/* Threshold used by pitch estimator for early escape */
#define FIND_PITCH_CORRELATION_THRESHOLD_HC_MODE        0.7f
#define FIND_PITCH_CORRELATION_THRESHOLD_MC_MODE        0.75f
#define FIND_PITCH_CORRELATION_THRESHOLD_LC_MODE        0.8f

/*********************/
/* Linear prediction */
/*********************/

/* LPC analysis defines: regularization and bandwidth expansion */
#define FIND_LPC_COND_FAC                               2.5e-5f
#define FIND_LPC_CHIRP                                  0.99995f

/* LTP analysis defines */
#define FIND_LTP_COND_FAC                               1e-5f
#define LTP_DAMPING                                     0.01f
#define LTP_SMOOTHING                                   0.1f

/* LTP quantization settings */
#define MU_LTP_QUANT_NB                                 0.03f
#define MU_LTP_QUANT_MB                                 0.025f
#define MU_LTP_QUANT_WB                                 0.02f
#define MU_LTP_QUANT_SWB                                0.016f

/***********************/
/* High pass filtering */
/***********************/

/* Smoothing parameters for low end of pitch frequency range estimation */
#define VARIABLE_HP_SMTH_COEF1                          0.1f
#define VARIABLE_HP_SMTH_COEF2                          0.015f

/* Min and max values for low end of pitch frequency range estimation */
#define VARIABLE_HP_MIN_FREQ                            80.0f
#define VARIABLE_HP_MAX_FREQ                            150.0f

/* Max absolute difference between log2 of pitch frequency and smoother state, to enter the smoother */
#define VARIABLE_HP_MAX_DELTA_FREQ                      0.4f

/***********/
/* Various */
/***********/

/* Required speech activity for counting frame as active */
#define WB_DETECT_ACTIVE_SPEECH_LEVEL_THRES             0.7f        

#define SPEECH_ACTIVITY_DTX_THRES                       0.1f

/* Speech Activity LBRR enable threshold (needs tuning) */
#define LBRR_SPEECH_ACTIVITY_THRES                      0.5f        

/*************************/
/* Perceptual parameters */
/*************************/

/* reduction in coding SNR during low speech activity */
#define BG_SNR_DECR_dB                                  4.0f

/* factor for reducing quantization noise during voiced speech */
#define HARM_SNR_INCR_dB                                2.0f

/* factor for reducing quantization noise for unvoiced sparse signals */
#define SPARSE_SNR_INCR_dB                              2.0f

/* threshold for sparseness measure above which to use lower quantization offset during unvoiced */
#define SPARSENESS_THRESHOLD_QNT_OFFSET                 0.75f

/* warping control */
#define WARPING_MULTIPLIER                              0.015f

/* fraction added to first autocorrelation value */
#define SHAPE_WHITE_NOISE_FRACTION                      1e-5f

/* noise shaping filter chirp factor */
#define BANDWIDTH_EXPANSION                             0.95f

/* difference between chirp factors for analysis and synthesis noise shaping filters at low bitrates */
#define LOW_RATE_BANDWIDTH_EXPANSION_DELTA              0.01f

/* gain reduction for fricatives */
#define DE_ESSER_COEF_SWB_dB                            2.0f
#define DE_ESSER_COEF_WB_dB                             1.0f

/* extra harmonic boosting (signal shaping) at low bitrates */
#define LOW_RATE_HARMONIC_BOOST                         0.1f

/* extra harmonic boosting (signal shaping) for noisy input signals */
#define LOW_INPUT_QUALITY_HARMONIC_BOOST                0.1f

/* harmonic noise shaping */
#define HARMONIC_SHAPING                                0.3f

/* extra harmonic noise shaping for high bitrates or noisy input */
#define HIGH_RATE_OR_LOW_QUALITY_HARMONIC_SHAPING       0.2f

/* parameter for shaping noise towards higher frequencies */
#define HP_NOISE_COEF                                   0.3f

/* parameter for shaping noise even more towards higher frequencies during voiced speech */
#define HARM_HP_NOISE_COEF                              0.35f

/* parameter for applying a high-pass tilt to the input signal */
#define INPUT_TILT                                      0.05f

/* parameter for extra high-pass tilt to the input signal at high rates */
#define HIGH_RATE_INPUT_TILT                            0.1f

/* parameter for reducing noise at the very low frequencies */
#define LOW_FREQ_SHAPING                                3.0f

/* less reduction of noise at the very low frequencies for signals with low SNR at low frequencies */
#define LOW_QUALITY_LOW_FREQ_SHAPING_DECR               0.5f

/* noise floor to put a lower limit on the quantization step size */
#define NOISE_FLOOR_dB                                  4.0f

/* noise floor relative to active speech gain level */
#define RELATIVE_MIN_GAIN_dB                            -50.0f

/* subframe smoothing coefficient for determining active speech gain level (lower -> more smoothing) */
#define GAIN_SMOOTHING_COEF                             1e-3f

/* subframe smoothing coefficient for HarmBoost, HarmShapeGain, Tilt (lower -> more smoothing) */
#define SUBFR_SMTH_COEF                                 0.4f

/* parameters defining the R/D tradeoff in the residual quantizer */
#define LAMBDA_OFFSET                                   1.2f
#define LAMBDA_SPEECH_ACT                               -0.3f
#define LAMBDA_DELAYED_DECISIONS                        -0.05f
#define LAMBDA_INPUT_QUALITY                            -0.2f
#define LAMBDA_CODING_QUALITY                           -0.1f
#define LAMBDA_QUANT_OFFSET                             1.5f

#ifdef __cplusplus
}
#endif

#endif // SKP_SILK_TUNING_PARAMETERS_H
