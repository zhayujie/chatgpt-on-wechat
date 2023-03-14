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

#include "SKP_Silk_main_FIX.h"

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
)
{
    SKP_int   i, n;
    SKP_int32 *pRD_vec_Q20;

    /* Compute weighted quantization errors for all input vectors over one codebook stage */
    SKP_Silk_NLSF_VQ_sum_error_FIX( pRD_Q20, in_Q15, w_Q6, psNLSF_CBS->CB_NLSF_Q15, 
        N, psNLSF_CBS->nVectors, LPC_order );

    /* Loop over input vectors */
    pRD_vec_Q20 = pRD_Q20;
    for( n = 0; n < N; n++ ) {
        /* Add rate cost to error for each codebook vector */
        for( i = 0; i < psNLSF_CBS->nVectors; i++ ) {
            SKP_assert( rate_acc_Q5[ n ] + psNLSF_CBS->Rates_Q5[ i ] >= 0 );
            SKP_assert( rate_acc_Q5[ n ] + psNLSF_CBS->Rates_Q5[ i ] <= SKP_int16_MAX );
            pRD_vec_Q20[ i ] = SKP_SMLABB( pRD_vec_Q20[ i ], rate_acc_Q5[ n ] + psNLSF_CBS->Rates_Q5[ i ], mu_Q15 );
            SKP_assert( pRD_vec_Q20[ i ] >= 0 );
        }
        pRD_vec_Q20 += psNLSF_CBS->nVectors;
    }
}
