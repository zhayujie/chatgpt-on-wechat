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
#include "SKP_Silk_tuning_parameters.h"

/* Finds LPC vector from correlations, and converts to NLSF */
void SKP_Silk_find_LPC_FIX(
    SKP_int             NLSF_Q15[],             /* O    NLSFs                                                                       */
    SKP_int             *interpIndex,           /* O    NLSF interpolation index, only used for NLSF interpolation                  */
    const SKP_int       prev_NLSFq_Q15[],       /* I    previous NLSFs, only used for NLSF interpolation                            */
    const SKP_int       useInterpolatedNLSFs,   /* I    Flag                                                                        */
    const SKP_int       LPC_order,              /* I    LPC order                                                                   */
    const SKP_int16     x[],                    /* I    Input signal                                                                */
    const SKP_int       subfr_length            /* I    Input signal subframe length including preceeding samples                   */
)
{
    SKP_int     k;
    SKP_int32   a_Q16[ MAX_LPC_ORDER ];
    SKP_int     isInterpLower, shift;
    SKP_int16   S[ MAX_LPC_ORDER ];
    SKP_int32   res_nrg0, res_nrg1;
    SKP_int     rshift0, rshift1; 

    /* Used only for LSF interpolation */
    SKP_int32   a_tmp_Q16[ MAX_LPC_ORDER ], res_nrg_interp, res_nrg, res_tmp_nrg;
    SKP_int     res_nrg_interp_Q, res_nrg_Q, res_tmp_nrg_Q;
    SKP_int16   a_tmp_Q12[ MAX_LPC_ORDER ];
    SKP_int     NLSF0_Q15[ MAX_LPC_ORDER ];
    SKP_int16   LPC_res[ ( MAX_FRAME_LENGTH + NB_SUBFR * MAX_LPC_ORDER ) / 2 ];

    /* Default: no interpolation */
    *interpIndex = 4;

    /* Burg AR analysis for the full frame */
    SKP_Silk_burg_modified( &res_nrg, &res_nrg_Q, a_Q16, x, subfr_length, NB_SUBFR, SKP_FIX_CONST( FIND_LPC_COND_FAC, 32 ), LPC_order );

    SKP_Silk_bwexpander_32( a_Q16, LPC_order, SKP_FIX_CONST( FIND_LPC_CHIRP, 16 ) );

    if( useInterpolatedNLSFs == 1 ) {

        /* Optimal solution for last 10 ms */
        SKP_Silk_burg_modified( &res_tmp_nrg, &res_tmp_nrg_Q, a_tmp_Q16, x + ( NB_SUBFR >> 1 ) * subfr_length, 
            subfr_length, ( NB_SUBFR >> 1 ), SKP_FIX_CONST( FIND_LPC_COND_FAC, 32 ), LPC_order );

        SKP_Silk_bwexpander_32( a_tmp_Q16, LPC_order, SKP_FIX_CONST( FIND_LPC_CHIRP, 16 ) );

        /* subtract residual energy here, as that's easier than adding it to the    */
        /* residual energy of the first 10 ms in each iteration of the search below */
        shift = res_tmp_nrg_Q - res_nrg_Q;
        if( shift >= 0 ) {
            if( shift < 32 ) { 
                res_nrg = res_nrg - SKP_RSHIFT( res_tmp_nrg, shift );
            }
        } else {
            SKP_assert( shift > -32 ); 
            res_nrg   = SKP_RSHIFT( res_nrg, -shift ) - res_tmp_nrg;
            res_nrg_Q = res_tmp_nrg_Q; 
        }
        
        /* Convert to NLSFs */
        SKP_Silk_A2NLSF( NLSF_Q15, a_tmp_Q16, LPC_order );

        /* Search over interpolation indices to find the one with lowest residual energy */
        for( k = 3; k >= 0; k-- ) {
            /* Interpolate NLSFs for first half */
            SKP_Silk_interpolate( NLSF0_Q15, prev_NLSFq_Q15, NLSF_Q15, k, LPC_order );

            /* Convert to LPC for residual energy evaluation */
            SKP_Silk_NLSF2A_stable( a_tmp_Q12, NLSF0_Q15, LPC_order );

            /* Calculate residual energy with NLSF interpolation */
            SKP_memset( S, 0, LPC_order * sizeof( SKP_int16 ) );
            SKP_Silk_LPC_analysis_filter( x, a_tmp_Q12, S, LPC_res, 2 * subfr_length, LPC_order );

            SKP_Silk_sum_sqr_shift( &res_nrg0, &rshift0, LPC_res + LPC_order,                subfr_length - LPC_order );
            SKP_Silk_sum_sqr_shift( &res_nrg1, &rshift1, LPC_res + LPC_order + subfr_length, subfr_length - LPC_order );

            /* Add subframe energies from first half frame */
            shift = rshift0 - rshift1;
            if( shift >= 0 ) {
                res_nrg1         = SKP_RSHIFT( res_nrg1, shift );
                res_nrg_interp_Q = -rshift0;
            } else {
                res_nrg0         = SKP_RSHIFT( res_nrg0, -shift );
                res_nrg_interp_Q = -rshift1;
            }
            res_nrg_interp = SKP_ADD32( res_nrg0, res_nrg1 );

            /* Compare with first half energy without NLSF interpolation, or best interpolated value so far */
            shift = res_nrg_interp_Q - res_nrg_Q;
            if( shift >= 0 ) {
                if( SKP_RSHIFT( res_nrg_interp, shift ) < res_nrg ) {
                    isInterpLower = SKP_TRUE;
                } else {
                    isInterpLower = SKP_FALSE;
                }
            } else {
                if( -shift < 32 ) { 
                    if( res_nrg_interp < SKP_RSHIFT( res_nrg, -shift ) ) {
                        isInterpLower = SKP_TRUE;
                    } else {
                        isInterpLower = SKP_FALSE;
                    }
                } else {
                    isInterpLower = SKP_FALSE;
                }
            }

            /* Determine whether current interpolated NLSFs are best so far */
            if( isInterpLower == SKP_TRUE ) {
                /* Interpolation has lower residual energy */
                res_nrg   = res_nrg_interp;
                res_nrg_Q = res_nrg_interp_Q;
                *interpIndex = k;
            }
        }
    }

    if( *interpIndex == 4 ) {
        /* NLSF interpolation is currently inactive, calculate NLSFs from full frame AR coefficients */
        SKP_Silk_A2NLSF( NLSF_Q15, a_Q16, LPC_order );
    }
}
