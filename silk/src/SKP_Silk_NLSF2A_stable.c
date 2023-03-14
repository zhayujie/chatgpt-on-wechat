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

#include "SKP_Silk_main.h"

/* Convert NLSF parameters to stable AR prediction filter coefficients */
void SKP_Silk_NLSF2A_stable(
    SKP_int16                       pAR_Q12[ MAX_LPC_ORDER ],   /* O    Stabilized AR coefs [LPC_order]     */ 
    const SKP_int                   pNLSF[ MAX_LPC_ORDER ],     /* I    NLSF vector         [LPC_order]     */
    const SKP_int                   LPC_order                   /* I    LPC/LSF order                       */
)
{
    SKP_int   i;
    SKP_int32 invGain_Q30;

    SKP_Silk_NLSF2A( pAR_Q12, pNLSF, LPC_order );

    /* Ensure stable LPCs */
    for( i = 0; i < MAX_LPC_STABILIZE_ITERATIONS; i++ ) {
        if( SKP_Silk_LPC_inverse_pred_gain( &invGain_Q30, pAR_Q12, LPC_order ) == 1 ) {
            SKP_Silk_bwexpander( pAR_Q12, LPC_order, 65536 - SKP_SMULBB( 10 + i, i ) );		/* 10_Q16 = 0.00015 */
        } else {
            break;
        }
    }

    /* Reached the last iteration */
    if( i == MAX_LPC_STABILIZE_ITERATIONS ) {
        SKP_assert( 0 );
        for( i = 0; i < LPC_order; i++ ) {
            pAR_Q12[ i ] = 0;
        }
    }
}
