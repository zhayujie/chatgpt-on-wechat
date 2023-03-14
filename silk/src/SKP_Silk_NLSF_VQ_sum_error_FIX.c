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

#if (!defined(__mips__)) && (EMBEDDED_ARM < 6)

/* Compute weighted quantization errors for an LPC_order element input vector, over one codebook stage */
void SKP_Silk_NLSF_VQ_sum_error_FIX(
    SKP_int32                       *err_Q20,           /* O    Weighted quantization errors  [N*K]         */
    const SKP_int                   *in_Q15,            /* I    Input vectors to be quantized [N*LPC_order] */
    const SKP_int                   *w_Q6,              /* I    Weighting vectors             [N*LPC_order] */
    const SKP_int16                 *pCB_Q15,           /* I    Codebook vectors              [K*LPC_order] */
    const SKP_int                   N,                  /* I    Number of input vectors                     */
    const SKP_int                   K,                  /* I    Number of codebook vectors                  */
    const SKP_int                   LPC_order           /* I    Number of LPCs                              */
)
{
    SKP_int         i, n, m;
    SKP_int32       diff_Q15, sum_error, Wtmp_Q6;
    SKP_int32       Wcpy_Q6[ MAX_LPC_ORDER / 2 ];
    const SKP_int16 *cb_vec_Q15;

    SKP_assert( LPC_order <= 16 );
    SKP_assert( ( LPC_order & 1 ) == 0 );

    /* Copy to local stack and pack two weights per int32 */
    for( m = 0; m < SKP_RSHIFT( LPC_order, 1 ); m++ ) {
        Wcpy_Q6[ m ] = w_Q6[ 2 * m ] | SKP_LSHIFT( ( SKP_int32 )w_Q6[ 2 * m + 1 ], 16 );
    }

    /* Loop over input vectors */
    for( n = 0; n < N; n++ ) {
        /* Loop over codebook */
        cb_vec_Q15 = pCB_Q15;
        for( i = 0; i < K; i++ ) {
            sum_error = 0;
            for( m = 0; m < LPC_order; m += 2 ) {
                /* Get two weights packed in an int32 */
                Wtmp_Q6 = Wcpy_Q6[ SKP_RSHIFT( m, 1 ) ];

                /* Compute weighted squared quantization error for index m */
                diff_Q15 = in_Q15[ m ] - *cb_vec_Q15++; // range: [ -32767 : 32767 ]
                sum_error = SKP_SMLAWB( sum_error, SKP_SMULBB( diff_Q15, diff_Q15 ), Wtmp_Q6 );

                /* Compute weighted squared quantization error for index m + 1 */
                diff_Q15 = in_Q15[m + 1] - *cb_vec_Q15++; // range: [ -32767 : 32767 ]
                sum_error = SKP_SMLAWT( sum_error, SKP_SMULBB( diff_Q15, diff_Q15 ), Wtmp_Q6 );
            }
            SKP_assert( sum_error >= 0 );
            err_Q20[ i ] = sum_error;
        }
        err_Q20 += K;
        in_Q15 += LPC_order;
    }
}

#endif

