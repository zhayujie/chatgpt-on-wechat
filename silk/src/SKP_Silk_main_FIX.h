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

#ifndef SKP_SILK_MAIN_FIX_H
#define SKP_SILK_MAIN_FIX_H

#include <stdlib.h>
#include "SKP_Silk_SigProc_FIX.h"
#include "SKP_Silk_structs_FIX.h"
#include "SKP_Silk_main.h"
#include "SKP_Silk_PLC.h"
#define TIC(TAG_NAME)
#define TOC(TAG_NAME)

#ifndef FORCE_CPP_BUILD
#ifdef __cplusplus
extern "C"
{
#endif
#endif

/*********************/
/* Encoder Functions */
/*********************/

/* Initializes the Silk encoder state */
SKP_int SKP_Silk_init_encoder_FIX(
    SKP_Silk_encoder_state_FIX  *psEnc                  /* I/O  Pointer to Silk FIX encoder state       */
);

/* Control the Silk encoder */
SKP_int SKP_Silk_control_encoder_FIX( 
    SKP_Silk_encoder_state_FIX  *psEnc,                 /* I/O  Pointer to Silk encoder state           */
    const SKP_int               PacketSize_ms,          /* I    Packet length (ms)                      */
    const SKP_int32             TargetRate_bps,         /* I    Target max bitrate (bps)                */
    const SKP_int               PacketLoss_perc,        /* I    Packet loss rate (in percent)           */
    const SKP_int               DTX_enabled,            /* I    Enable / disable DTX                    */
    const SKP_int               Complexity              /* I    Complexity (0->low; 1->medium; 2->high) */
);

/* Encoder main function */
SKP_int SKP_Silk_encode_frame_FIX( 
    SKP_Silk_encoder_state_FIX      *psEnc,             /* I/O  Pointer to Silk FIX encoder state           */
    SKP_uint8                       *pCode,             /* O    Pointer to payload                          */
    SKP_int16                       *pnBytesOut,        /* I/O  Pointer to number of payload bytes;         */
                                                        /*      input: max length; output: used             */
    const SKP_int16                 *pIn                /* I    Pointer to input speech frame               */
);

/* Low BitRate Redundancy encoding functionality. Reuse all parameters but encode with lower bitrate */
void SKP_Silk_LBRR_encode_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,         /* I/O  Pointer to Silk FIX encoder state           */
    SKP_Silk_encoder_control_FIX    *psEncCtrl,     /* I/O  Pointer to Silk FIX encoder control struct  */
    SKP_uint8                       *pCode,         /* O    Pointer to payload                          */
    SKP_int16                       *pnBytesOut,    /* I/O  Pointer to number of payload bytes          */
    SKP_int16                       xfw[]           /* I    Input signal                                */
);

/* High-pass filter with cutoff frequency adaptation based on pitch lag statistics */
void SKP_Silk_HP_variable_cutoff_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,         /* I/O  Encoder state                               */
    SKP_Silk_encoder_control_FIX    *psEncCtrl,     /* I/O  Encoder control                             */
    SKP_int16                       *out,           /* O    high-pass filtered output signal            */
    const SKP_int16                 *in             /* I    input signal                                */
);

/****************/
/* Prefiltering */
/****************/
void SKP_Silk_prefilter_FIX(
    SKP_Silk_encoder_state_FIX          *psEnc,         /* I/O  Encoder state                               */
    const SKP_Silk_encoder_control_FIX  *psEncCtrl,     /* I    Encoder control                             */
    SKP_int16                           xw[],           /* O    Weighted signal                             */
    const SKP_int16                     x[]             /* I    Speech signal                               */
);

/**************************************************************/
/* Compute noise shaping coefficients and initial gain values */
/**************************************************************/
void SKP_Silk_noise_shape_analysis_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,         /* I/O  Encoder state FIX                           */
    SKP_Silk_encoder_control_FIX    *psEncCtrl,     /* I/O  Encoder control FIX                         */
    const SKP_int16                 *pitch_res,     /* I    LPC residual from pitch analysis            */
    const SKP_int16                 *x              /* I    Input signal [ frame_length + la_shape ]    */
);

/* Autocorrelations for a warped frequency axis */
void SKP_Silk_warped_autocorrelation_FIX(
          SKP_int32                 *corr,              /* O    Result [order + 1]                      */
          SKP_int                   *scale,             /* O    Scaling of the correlation vector       */
    const SKP_int16                 *input,             /* I    Input data to correlate                 */
    const SKP_int16                 warping_Q16,        /* I    Warping coefficient                     */
    const SKP_int                   length,             /* I    Length of input                         */
    const SKP_int                   order               /* I    Correlation order (even)                */
);

/* Processing of gains */
void SKP_Silk_process_gains_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,         /* I/O  Encoder state                               */
    SKP_Silk_encoder_control_FIX    *psEncCtrl      /* I/O  Encoder control                             */
);

/* Control low bitrate redundancy usage */
void SKP_Silk_LBRR_ctrl_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,         /* I/O  encoder state                               */
    SKP_Silk_encoder_control        *psEncCtrlC     /* I/O  encoder control                             */
);

/* Calculation of LTP state scaling */
void SKP_Silk_LTP_scale_ctrl_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,         /* I/O  encoder state                               */
    SKP_Silk_encoder_control_FIX    *psEncCtrl      /* I/O  encoder control                             */
);

/**********************************************/
/* Prediction Analysis                        */
/**********************************************/

/* Find pitch lags */
void SKP_Silk_find_pitch_lags_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,         /* I/O  encoder state                               */
    SKP_Silk_encoder_control_FIX    *psEncCtrl,     /* I/O  encoder control                             */
    SKP_int16                       res[],          /* O    residual                                    */
    const SKP_int16                 x[]             /* I    Speech signal                               */
);

void SKP_Silk_find_pred_coefs_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,         /* I/O  encoder state                               */
    SKP_Silk_encoder_control_FIX    *psEncCtrl,     /* I/O  encoder control                             */
    const SKP_int16                 res_pitch[]     /* I    Residual from pitch analysis                */
);

void SKP_Silk_find_LPC_FIX(
    SKP_int             NLSF_Q15[],             /* O    NLSFs                                                                       */
    SKP_int             *interpIndex,           /* O    NLSF interpolation index, only used for NLSF interpolation                  */
    const SKP_int       prev_NLSFq_Q15[],       /* I    previous NLSFs, only used for NLSF interpolation                            */
    const SKP_int       useInterpolatedLSFs,    /* I    Flag                                                                        */
    const SKP_int       LPC_order,              /* I    LPC order                                                                   */
    const SKP_int16     x[],                    /* I    Input signal                                                                */
    const SKP_int       subfr_length            /* I    Input signal subframe length including preceeding samples                   */
);

void SKP_Silk_warped_LPC_analysis_filter_FIX(
          SKP_int32                 state[],            /* I/O  State [order + 1]                       */
          SKP_int16                 res[],              /* O    Residual signal [length]                */
    const SKP_int16                 coef_Q13[],         /* I    Coefficients [order]                    */
    const SKP_int16                 input[],            /* I    Input signal [length]                   */
    const SKP_int16                 lambda_Q16,         /* I    Warping factor                          */
    const SKP_int                   length,             /* I    Length of input signal                  */
    const SKP_int                   order               /* I    Filter order (even)                     */
);

void SKP_Silk_LTP_analysis_filter_FIX(
    SKP_int16       *LTP_res,                           /* O:   LTP residual signal of length NB_SUBFR * ( pre_length + subfr_length )  */
    const SKP_int16 *x,                                 /* I:   Pointer to input signal with at least max( pitchL ) preceeding samples  */
    const SKP_int16 LTPCoef_Q14[ LTP_ORDER * NB_SUBFR ],/* I:   LTP_ORDER LTP coefficients for each NB_SUBFR subframe                   */
    const SKP_int   pitchL[ NB_SUBFR ],                 /* I:   Pitch lag, one for each subframe                                        */
    const SKP_int32 invGains_Q16[ NB_SUBFR ],           /* I:   Inverse quantization gains, one for each subframe                       */
    const SKP_int   subfr_length,                       /* I:   Length of each subframe                                                 */
    const SKP_int   pre_length                          /* I:   Length of the preceeding samples starting at &x[0] for each subframe    */
);

/* Finds LTP vector from correlations */
void SKP_Silk_find_LTP_FIX(
    SKP_int16           b_Q14[ NB_SUBFR * LTP_ORDER ],              /* O    LTP coefs                                                   */
    SKP_int32           WLTP[ NB_SUBFR * LTP_ORDER * LTP_ORDER ],   /* O    Weight for LTP quantization                                 */
    SKP_int             *LTPredCodGain_Q7,                          /* O    LTP coding gain                                             */
    const SKP_int16     r_first[],                                  /* I    residual signal after LPC signal + state for first 10 ms    */
    const SKP_int16     r_last[],                                   /* I    residual signal after LPC signal + state for last 10 ms     */
    const SKP_int       lag[ NB_SUBFR ],                            /* I    LTP lags                                                    */
    const SKP_int32     Wght_Q15[ NB_SUBFR ],                       /* I    weights                                                     */
    const SKP_int       subfr_length,                               /* I    subframe length                                             */
    const SKP_int       mem_offset,                                 /* I    number of samples in LTP memory                             */
    SKP_int             corr_rshifts[ NB_SUBFR ]                    /* O    right shifts applied to correlations                        */
);

/* LTP tap quantizer */
void SKP_Silk_quant_LTP_gains_FIX(
    SKP_int16               B_Q14[],                /* I/O  (un)quantized LTP gains     */
    SKP_int                 cbk_index[],            /* O    Codebook Index              */
    SKP_int                 *periodicity_index,     /* O    Periodicity Index           */
    const SKP_int32         W_Q18[],                /* I    Error Weights in Q18        */
    SKP_int                 mu_Q8,                  /* I    Mu value (R/D tradeoff)     */
    SKP_int                 lowComplexity           /* I    Flag for low complexity     */
);

/******************/
/* NLSF Quantizer */
/******************/

/* Limit, stabilize, convert and quantize NLSFs.    */ 
void SKP_Silk_process_NLSFs_FIX(
    SKP_Silk_encoder_state_FIX      *psEnc,     /* I/O  encoder state                               */
    SKP_Silk_encoder_control_FIX    *psEncCtrl, /* I/O  encoder control                             */
    SKP_int                         *pNLSF_Q15  /* I/O  Normalized LSFs (quant out) (0 - (2^15-1))  */
);

/* NLSF vector encoder */
void SKP_Silk_NLSF_MSVQ_encode_FIX(
          SKP_int                   *NLSFIndices,           /* O    Codebook path vector [ CB_STAGES ]      */
          SKP_int                   *pNLSF_Q15,             /* I/O  Quantized NLSF vector [ LPC_ORDER ]     */
    const SKP_Silk_NLSF_CB_struct   *psNLSF_CB,             /* I    Codebook object                         */
    const SKP_int                   *pNLSF_q_Q15_prev,      /* I    Prev. quantized NLSF vector [LPC_ORDER] */
    const SKP_int                   *pW_Q6,                 /* I    NLSF weight vector [ LPC_ORDER ]        */
    const SKP_int                   NLSF_mu_Q15,            /* I    Rate weight for the RD optimization     */
    const SKP_int                   NLSF_mu_fluc_red_Q16,   /* I    Fluctuation reduction error weight      */
    const SKP_int                   NLSF_MSVQ_Survivors,    /* I    Max survivors from each stage           */
    const SKP_int                   LPC_order,              /* I    LPC order                               */
    const SKP_int                   deactivate_fluc_red     /* I    Deactivate fluctuation reduction        */
);

/* Rate-Distortion calculations for multiple input data vectors */
void SKP_Silk_NLSF_VQ_rate_distortion_FIX(
    SKP_int32                       *pRD_Q20,           /* O    Rate-distortion values [psNLSF_CBS->nVectors*N] */
    const SKP_Silk_NLSF_CBS         *psNLSF_CBS,        /* I    NLSF codebook stage struct                      */
    const SKP_int                   *in_Q15,            /* I    Input vectors to be quantized                   */
    const SKP_int                   *w_Q6,              /* I    Weight vector                                   */
    const SKP_int32                 *rate_acc_Q5,       /* I    Accumulated rates from previous stage           */
    const SKP_int                   mu_Q15,             /* I    Weight between weighted error and rate          */
    const SKP_int                   N,                  /* I    Number of input vectors to be quantized         */
    const SKP_int                   LPC_order           /* I    LPC order                                       */
);

/* Compute weighted quantization errors for an LPC_order element input vector, over one codebook stage */
void SKP_Silk_NLSF_VQ_sum_error_FIX(
    SKP_int32                       *err_Q20,           /* O    Weighted quantization errors  [N*K]         */
    const SKP_int                   *in_Q15,            /* I    Input vectors to be quantized [N*LPC_order] */
    const SKP_int                   *w_Q6,              /* I    Weighting vectors             [N*LPC_order] */
    const SKP_int16                 *pCB_Q15,           /* I    Codebook vectors              [K*LPC_order] */
    const SKP_int                   N,                  /* I    Number of input vectors                     */
    const SKP_int                   K,                  /* I    Number of codebook vectors                  */
    const SKP_int                   LPC_order           /* I    Number of LPCs                              */
);

/* Entropy constrained MATRIX-weighted VQ, for a single input data vector */
void SKP_Silk_VQ_WMat_EC_FIX(
    SKP_int                         *ind,               /* O    index of best codebook vector               */
    SKP_int32                       *rate_dist_Q14,     /* O    best weighted quantization error + mu * rate*/
    const SKP_int16                 *in_Q14,            /* I    input vector to be quantized                */
    const SKP_int32                 *W_Q18,             /* I    weighting matrix                            */
    const SKP_int16                 *cb_Q14,            /* I    codebook                                    */
    const SKP_int16                 *cl_Q6,             /* I    code length for each codebook vector        */
    const SKP_int                   mu_Q8,              /* I    tradeoff between weighted error and rate    */
    SKP_int                         L                   /* I    number of vectors in codebook               */
);

/******************/
/* Linear Algebra */
/******************/

/* Calculates correlation matrix X'*X */
void SKP_Silk_corrMatrix_FIX(
    const SKP_int16                 *x,         /* I    x vector [L + order - 1] used to form data matrix X */
    const SKP_int                   L,          /* I    Length of vectors                                   */
    const SKP_int                   order,      /* I    Max lag for correlation                             */
    const SKP_int                   head_room,  /* I    Desired headroom                                    */
    SKP_int32                       *XX,        /* O    Pointer to X'*X correlation matrix [ order x order ]*/
    SKP_int                         *rshifts    /* I/O  Right shifts of correlations                        */
);

/* Calculates correlation vector X'*t */
void SKP_Silk_corrVector_FIX(
    const SKP_int16                 *x,         /* I    x vector [L + order - 1] used to form data matrix X */
    const SKP_int16                 *t,         /* I    Target vector [L]                                   */
    const SKP_int                   L,          /* I    Length of vectors                                   */
    const SKP_int                   order,      /* I    Max lag for correlation                             */
    SKP_int32                       *Xt,        /* O    Pointer to X'*t correlation vector [order]          */
    const SKP_int                   rshifts     /* I    Right shifts of correlations                        */
);

/* Add noise to matrix diagonal */
void SKP_Silk_regularize_correlations_FIX(
    SKP_int32                       *XX,                /* I/O  Correlation matrices                        */
    SKP_int32                       *xx,                /* I/O  Correlation values                          */
    SKP_int32                       noise,              /* I    Noise to add                                */
    SKP_int                         D                   /* I    Dimension of XX                             */
);

/* Solves Ax = b, assuming A is symmetric */
void SKP_Silk_solve_LDL_FIX(
    SKP_int32                       *A,                 /* I    Pointer to symetric square matrix A         */
    SKP_int                         M,                  /* I    Size of matrix                              */
    const SKP_int32                 *b,                 /* I    Pointer to b vector                         */
    SKP_int32                       *x_Q16              /* O    Pointer to x solution vector                */
);

/* Residual energy: nrg = wxx - 2 * wXx * c + c' * wXX * c */
SKP_int32 SKP_Silk_residual_energy16_covar_FIX(
    const SKP_int16                 *c,                 /* I    Prediction vector                           */
    const SKP_int32                 *wXX,               /* I    Correlation matrix                          */
    const SKP_int32                 *wXx,               /* I    Correlation vector                          */
    SKP_int32                       wxx,                /* I    Signal energy                               */
    SKP_int                         D,                  /* I    Dimension                                   */
    SKP_int                         cQ                  /* I    Q value for c vector 0 - 15                 */
);

/* Calculates residual energies of input subframes where all subframes have LPC_order   */
/* of preceeding samples                                                                */
void SKP_Silk_residual_energy_FIX(
          SKP_int32 nrgs[ NB_SUBFR ],           /* O    Residual energy per subframe    */
          SKP_int   nrgsQ[ NB_SUBFR ],          /* O    Q value per subframe            */
    const SKP_int16 x[],                        /* I    Input signal                    */
          SKP_int16 a_Q12[ 2 ][ MAX_LPC_ORDER ],/* I    AR coefs for each frame half    */
    const SKP_int32 gains[ NB_SUBFR ],          /* I    Quantization gains              */
    const SKP_int   subfr_length,               /* I    Subframe length                 */
    const SKP_int   LPC_order                   /* I    LPC order                       */
);

#ifndef FORCE_CPP_BUILD
#ifdef __cplusplus
}
#endif /* __cplusplus */
#endif /* FORCE_CPP_BUILD */
#endif /* SKP_SILK_MAIN_FIX_H */
