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

/* NLSF vector decoder */
void SKP_Silk_NLSF_MSVQ_decode(
    SKP_int                         *pNLSF_Q15,     /* O    Pointer to decoded output vector [LPC_ORDER x 1]    */
    const SKP_Silk_NLSF_CB_struct   *psNLSF_CB,     /* I    Pointer to NLSF codebook struct                     */
    const SKP_int                   *NLSFIndices,   /* I    Pointer to NLSF indices          [nStages x 1]      */
    const SKP_int                   LPC_order       /* I    LPC order used                                      */
) 
{
    const SKP_int16 *pCB_element;
          SKP_int    s;
          SKP_int    i;

    /* Check that each index is within valid range */
    SKP_assert( 0 <= NLSFIndices[ 0 ] && NLSFIndices[ 0 ] < psNLSF_CB->CBStages[ 0 ].nVectors );

    /* Point to the first vector element */
    pCB_element = &psNLSF_CB->CBStages[ 0 ].CB_NLSF_Q15[ SKP_MUL( NLSFIndices[ 0 ], LPC_order ) ];

    /* Initialize with the codebook vector from stage 0 */
    for( i = 0; i < LPC_order; i++ ) {
        pNLSF_Q15[ i ] = ( SKP_int )pCB_element[ i ];
    }
          
    for( s = 1; s < psNLSF_CB->nStages; s++ ) {
        /* Check that each index is within valid range */
        SKP_assert( 0 <= NLSFIndices[ s ] && NLSFIndices[ s ] < psNLSF_CB->CBStages[ s ].nVectors );

        if( LPC_order == 16 ) {
            /* Point to the first vector element */
            pCB_element = &psNLSF_CB->CBStages[ s ].CB_NLSF_Q15[ SKP_LSHIFT( NLSFIndices[ s ], 4 ) ];

            /* Add the codebook vector from the current stage */
            pNLSF_Q15[  0 ] += pCB_element[  0 ];
            pNLSF_Q15[  1 ] += pCB_element[  1 ];
            pNLSF_Q15[  2 ] += pCB_element[  2 ];
            pNLSF_Q15[  3 ] += pCB_element[  3 ];
            pNLSF_Q15[  4 ] += pCB_element[  4 ];
            pNLSF_Q15[  5 ] += pCB_element[  5 ];
            pNLSF_Q15[  6 ] += pCB_element[  6 ];
            pNLSF_Q15[  7 ] += pCB_element[  7 ];
            pNLSF_Q15[  8 ] += pCB_element[  8 ];
            pNLSF_Q15[  9 ] += pCB_element[  9 ];
            pNLSF_Q15[ 10 ] += pCB_element[ 10 ];
            pNLSF_Q15[ 11 ] += pCB_element[ 11 ];
            pNLSF_Q15[ 12 ] += pCB_element[ 12 ];
            pNLSF_Q15[ 13 ] += pCB_element[ 13 ];
            pNLSF_Q15[ 14 ] += pCB_element[ 14 ];
            pNLSF_Q15[ 15 ] += pCB_element[ 15 ];
        } else {
            /* Point to the first vector element */
            pCB_element = &psNLSF_CB->CBStages[ s ].CB_NLSF_Q15[ SKP_SMULBB( NLSFIndices[ s ], LPC_order ) ];

            /* Add the codebook vector from the current stage */
            for( i = 0; i < LPC_order; i++ ) {
                pNLSF_Q15[ i ] += pCB_element[ i ];
            }
        }
    }

    /* NLSF stabilization */
    SKP_Silk_NLSF_stabilize( pNLSF_Q15, psNLSF_CB->NDeltaMin_Q15, LPC_order );
}
