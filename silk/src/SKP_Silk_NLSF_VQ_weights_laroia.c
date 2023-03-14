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

#include "SKP_Silk_SigProc_FIX.h"

/* 
R. Laroia, N. Phamdo and N. Farvardin, "Robust and Efficient Quantization of Speech LSP
Parameters Using Structured Vector Quantization", Proc. IEEE Int. Conf. Acoust., Speech,
Signal Processing, pp. 641-644, 1991.
*/

#define Q_OUT                       6
#define MIN_NDELTA                  3

/* Laroia low complexity NLSF weights */
void SKP_Silk_NLSF_VQ_weights_laroia(
    SKP_int             *pNLSFW_Q6,         /* O: Pointer to input vector weights           [D x 1]     */
    const SKP_int       *pNLSF_Q15,         /* I: Pointer to input vector                   [D x 1]     */ 
    const SKP_int       D                   /* I: Input vector dimension (even)                         */
)
{
    SKP_int   k;
    SKP_int32 tmp1_int, tmp2_int;
    
    /* Check that we are guaranteed to end up within the required range */
    SKP_assert( D > 0 );
    SKP_assert( ( D & 1 ) == 0 );
    
    /* First value */
    tmp1_int = SKP_max_int( pNLSF_Q15[ 0 ], MIN_NDELTA );
    tmp1_int = SKP_DIV32_16( 1 << ( 15 + Q_OUT ), tmp1_int );
    tmp2_int = SKP_max_int( pNLSF_Q15[ 1 ] - pNLSF_Q15[ 0 ], MIN_NDELTA );
    tmp2_int = SKP_DIV32_16( 1 << ( 15 + Q_OUT ), tmp2_int );
    pNLSFW_Q6[ 0 ] = (SKP_int)SKP_min_int( tmp1_int + tmp2_int, SKP_int16_MAX );
    SKP_assert( pNLSFW_Q6[ 0 ] > 0 );
    
    /* Main loop */
    for( k = 1; k < D - 1; k += 2 ) {
        tmp1_int = SKP_max_int( pNLSF_Q15[ k + 1 ] - pNLSF_Q15[ k ], MIN_NDELTA );
        tmp1_int = SKP_DIV32_16( 1 << ( 15 + Q_OUT ), tmp1_int );
        pNLSFW_Q6[ k ] = (SKP_int)SKP_min_int( tmp1_int + tmp2_int, SKP_int16_MAX );
        SKP_assert( pNLSFW_Q6[ k ] > 0 );

        tmp2_int = SKP_max_int( pNLSF_Q15[ k + 2 ] - pNLSF_Q15[ k + 1 ], MIN_NDELTA );
        tmp2_int = SKP_DIV32_16( 1 << ( 15 + Q_OUT ), tmp2_int );
        pNLSFW_Q6[ k + 1 ] = (SKP_int)SKP_min_int( tmp1_int + tmp2_int, SKP_int16_MAX );
        SKP_assert( pNLSFW_Q6[ k + 1 ] > 0 );
    }
    
    /* Last value */
    tmp1_int = SKP_max_int( ( 1 << 15 ) - pNLSF_Q15[ D - 1 ], MIN_NDELTA );
    tmp1_int = SKP_DIV32_16( 1 << ( 15 + Q_OUT ), tmp1_int );
    pNLSFW_Q6[ D - 1 ] = (SKP_int)SKP_min_int( tmp1_int + tmp2_int, SKP_int16_MAX );
    SKP_assert( pNLSFW_Q6[ D - 1 ] > 0 );
}
