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

/* Entropy constrained MATRIX-weighted VQ, hard-coded to 5-element vectors, for a single input data vector */
void SKP_Silk_VQ_WMat_EC_FIX(
    SKP_int                         *ind,               /* O    index of best codebook vector               */
    SKP_int32                       *rate_dist_Q14,     /* O    best weighted quantization error + mu * rate*/
    const SKP_int16                 *in_Q14,            /* I    input vector to be quantized                */
    const SKP_int32                 *W_Q18,             /* I    weighting matrix                            */
    const SKP_int16                 *cb_Q14,            /* I    codebook                                    */
    const SKP_int16                 *cl_Q6,             /* I    code length for each codebook vector        */
    const SKP_int                   mu_Q8,              /* I    tradeoff between weighted error and rate    */
    SKP_int                         L                   /* I    number of vectors in codebook               */
)
{
    SKP_int   k;
    const SKP_int16 *cb_row_Q14;
#if !defined(_SYSTEM_IS_BIG_ENDIAN)
    SKP_int32 sum1_Q14, sum2_Q16, diff_Q14_01, diff_Q14_23, diff_Q14_4;
#else
    SKP_int16 diff_Q14[ 5 ];
    SKP_int32 sum1_Q14, sum2_Q16;
#endif

    /* Loop over codebook */
    *rate_dist_Q14 = SKP_int32_MAX;
    cb_row_Q14 = cb_Q14;
    for( k = 0; k < L; k++ ) {
#if !defined(_SYSTEM_IS_BIG_ENDIAN)
        /* Pack pairs of int16 values per int32 */
        diff_Q14_01 = ( SKP_uint16 )( in_Q14[ 0 ] - cb_row_Q14[ 0 ] ) | SKP_LSHIFT( ( SKP_int32 )in_Q14[ 1 ] - cb_row_Q14[ 1 ], 16 );
        diff_Q14_23 = ( SKP_uint16 )( in_Q14[ 2 ] - cb_row_Q14[ 2 ] ) | SKP_LSHIFT( ( SKP_int32 )in_Q14[ 3 ] - cb_row_Q14[ 3 ], 16 );
        diff_Q14_4  = in_Q14[ 4 ] - cb_row_Q14[ 4 ];
#else
        diff_Q14[ 0 ] = in_Q14[ 0 ] - cb_row_Q14[ 0 ];
        diff_Q14[ 1 ] = in_Q14[ 1 ] - cb_row_Q14[ 1 ];
        diff_Q14[ 2 ] = in_Q14[ 2 ] - cb_row_Q14[ 2 ];
        diff_Q14[ 3 ] = in_Q14[ 3 ] - cb_row_Q14[ 3 ];
        diff_Q14[ 4 ] = in_Q14[ 4 ] - cb_row_Q14[ 4 ];
#endif

        /* Weighted rate */
        sum1_Q14 = SKP_SMULBB( mu_Q8, cl_Q6[ k ] );

        SKP_assert( sum1_Q14 >= 0 );

#if !defined(_SYSTEM_IS_BIG_ENDIAN)
        /* Add weighted quantization error, assuming W_Q18 is symmetric */
        /* NOTE: the code below loads two int16 values as one int32, and multiplies each using the  */
        /* SMLAWB and SMLAWT instructions. On a big-endian CPU the two int16 variables would be     */
        /* loaded in reverse order and the code will give the wrong result. In that case swapping   */
        /* the SMLAWB and SMLAWT instructions should solve the problem.                             */
        /* first row of W_Q18 */
        sum2_Q16 = SKP_SMULWT(           W_Q18[ 1 ], diff_Q14_01 );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[ 2 ], diff_Q14_23 );
        sum2_Q16 = SKP_SMLAWT( sum2_Q16, W_Q18[ 3 ], diff_Q14_23 );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[ 4 ], diff_Q14_4  );
        sum2_Q16 = SKP_LSHIFT( sum2_Q16, 1 );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[ 0 ], diff_Q14_01 );
        sum1_Q14 = SKP_SMLAWB( sum1_Q14, sum2_Q16,   diff_Q14_01 );

        /* second row of W_Q18 */
        sum2_Q16 = SKP_SMULWB(           W_Q18[ 7 ], diff_Q14_23 );
        sum2_Q16 = SKP_SMLAWT( sum2_Q16, W_Q18[ 8 ], diff_Q14_23 );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[ 9 ], diff_Q14_4  );
        sum2_Q16 = SKP_LSHIFT( sum2_Q16, 1 );
        sum2_Q16 = SKP_SMLAWT( sum2_Q16, W_Q18[ 6 ], diff_Q14_01 );
        sum1_Q14 = SKP_SMLAWT( sum1_Q14, sum2_Q16,   diff_Q14_01 );

        /* third row of W_Q18 */
        sum2_Q16 = SKP_SMULWT(           W_Q18[ 13 ], diff_Q14_23 );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[ 14 ], diff_Q14_4  );
        sum2_Q16 = SKP_LSHIFT( sum2_Q16, 1 );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[ 12 ], diff_Q14_23 );
        sum1_Q14 = SKP_SMLAWB( sum1_Q14, sum2_Q16,    diff_Q14_23 );

        /* fourth row of W_Q18 */
        sum2_Q16 = SKP_SMULWB(           W_Q18[ 19 ], diff_Q14_4  );
        sum2_Q16 = SKP_LSHIFT( sum2_Q16, 1 );
        sum2_Q16 = SKP_SMLAWT( sum2_Q16, W_Q18[ 18 ], diff_Q14_23 );
        sum1_Q14 = SKP_SMLAWT( sum1_Q14, sum2_Q16,    diff_Q14_23 );

        /* last row of W_Q18 */
        sum2_Q16 = SKP_SMULWB(           W_Q18[ 24 ], diff_Q14_4  );
        sum1_Q14 = SKP_SMLAWB( sum1_Q14, sum2_Q16,    diff_Q14_4  );
#else
        /* first row of W_Q18 */
        sum2_Q16 = SKP_SMULWB(           W_Q18[  1 ], diff_Q14[ 1 ] );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[  2 ], diff_Q14[ 2 ] );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[  3 ], diff_Q14[ 3 ] );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[  4 ], diff_Q14[ 4 ] );
        sum2_Q16 = SKP_LSHIFT( sum2_Q16, 1 );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[  0 ], diff_Q14[ 0 ] );
        sum1_Q14 = SKP_SMLAWB( sum1_Q14, sum2_Q16,    diff_Q14[ 0 ] );

        /* second row of W_Q18 */
        sum2_Q16 = SKP_SMULWB(           W_Q18[  7 ], diff_Q14[ 2 ] ); 
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[  8 ], diff_Q14[ 3 ] );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[  9 ], diff_Q14[ 4 ] );
        sum2_Q16 = SKP_LSHIFT( sum2_Q16, 1 );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[  6 ], diff_Q14[ 1 ] );
        sum1_Q14 = SKP_SMLAWB( sum1_Q14, sum2_Q16,    diff_Q14[ 1 ] );

        /* third row of W_Q18 */
        sum2_Q16 = SKP_SMULWB(           W_Q18[ 13 ], diff_Q14[ 3 ] ); 
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[ 14 ], diff_Q14[ 4 ] );
        sum2_Q16 = SKP_LSHIFT( sum2_Q16, 1 );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[ 12 ], diff_Q14[ 2 ] );
        sum1_Q14 = SKP_SMLAWB( sum1_Q14, sum2_Q16,    diff_Q14[ 2 ] );

        /* fourth row of W_Q18 */
        sum2_Q16 = SKP_SMULWB(           W_Q18[ 19 ], diff_Q14[ 4 ] ); 
        sum2_Q16 = SKP_LSHIFT( sum2_Q16, 1 );
        sum2_Q16 = SKP_SMLAWB( sum2_Q16, W_Q18[ 18 ], diff_Q14[ 3 ] );
        sum1_Q14 = SKP_SMLAWB( sum1_Q14, sum2_Q16,    diff_Q14[ 3 ] );

        /* last row of W_Q18 */
        sum2_Q16 = SKP_SMULWB(           W_Q18[ 24 ], diff_Q14[ 4 ] ); 
        sum1_Q14 = SKP_SMLAWB( sum1_Q14, sum2_Q16,    diff_Q14[ 4 ] );
#endif

        SKP_assert( sum1_Q14 >= 0 );

        /* find best */
        if( sum1_Q14 < *rate_dist_Q14 ) {
            *rate_dist_Q14 = sum1_Q14;
            *ind = k;
        }

        /* Go to next cbk vector */
        cb_row_Q14 += LTP_ORDER;
    }
}
