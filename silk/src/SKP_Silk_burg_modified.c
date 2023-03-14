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

/*                                                                      *
 * SKP_Silk_burg_modified.c                                           *
 *                                                                      *
 * Calculates the reflection coefficients from the input vector         *
 * Input vector contains nb_subfr sub vectors of length L_sub + D       *
 *                                                                      *
 * Copyright 2009 (c), Skype Limited                                    *
 * Date: 100105                                                         *
 */

#include "SKP_Silk_SigProc_FIX.h"

#define MAX_FRAME_SIZE              544 // subfr_length * nb_subfr = ( 0.005 * 24000 + 16 ) * 4 = 544
#define MAX_NB_SUBFR                4

#define QA                          25
#define N_BITS_HEAD_ROOM            2
#define MIN_RSHIFTS                 -16
#define MAX_RSHIFTS                 (32 - QA)

/* Compute reflection coefficients from input signal */
void SKP_Silk_burg_modified(
    SKP_int32       *res_nrg,           /* O    residual energy                                                 */
    SKP_int         *res_nrg_Q,         /* O    residual energy Q value                                         */
    SKP_int32       A_Q16[],            /* O    prediction coefficients (length order)                          */
    const SKP_int16 x[],                /* I    input signal, length: nb_subfr * ( D + subfr_length )           */
    const SKP_int   subfr_length,       /* I    input signal subframe length (including D preceeding samples)   */
    const SKP_int   nb_subfr,           /* I    number of subframes stacked in x                                */
    const SKP_int32 WhiteNoiseFrac_Q32, /* I    fraction added to zero-lag autocorrelation                      */
    const SKP_int   D                   /* I    order                                                           */
)
{
    SKP_int         k, n, s, lz, rshifts, rshifts_extra;
    SKP_int32       C0, num, nrg, rc_Q31, Atmp_QA, Atmp1, tmp1, tmp2, x1, x2;
    const SKP_int16 *x_ptr;

    SKP_int32       C_first_row[ SKP_Silk_MAX_ORDER_LPC ];
    SKP_int32       C_last_row[  SKP_Silk_MAX_ORDER_LPC ];
    SKP_int32       Af_QA[       SKP_Silk_MAX_ORDER_LPC ];

    SKP_int32       CAf[ SKP_Silk_MAX_ORDER_LPC + 1 ];
    SKP_int32       CAb[ SKP_Silk_MAX_ORDER_LPC + 1 ];

    SKP_assert( subfr_length * nb_subfr <= MAX_FRAME_SIZE );
    SKP_assert( nb_subfr <= MAX_NB_SUBFR );


    /* Compute autocorrelations, added over subframes */
    SKP_Silk_sum_sqr_shift( &C0, &rshifts, x, nb_subfr * subfr_length );
    if( rshifts > MAX_RSHIFTS ) {
        C0 = SKP_LSHIFT32( C0, rshifts - MAX_RSHIFTS );
        SKP_assert( C0 > 0 );
        rshifts = MAX_RSHIFTS;
    } else {
        lz = SKP_Silk_CLZ32( C0 ) - 1;
        rshifts_extra = N_BITS_HEAD_ROOM - lz;
        if( rshifts_extra > 0 ) {
            rshifts_extra = SKP_min( rshifts_extra, MAX_RSHIFTS - rshifts );
            C0 = SKP_RSHIFT32( C0, rshifts_extra );
        } else {
            rshifts_extra = SKP_max( rshifts_extra, MIN_RSHIFTS - rshifts );
            C0 = SKP_LSHIFT32( C0, -rshifts_extra );
        }
        rshifts += rshifts_extra;
    }
    SKP_memset( C_first_row, 0, SKP_Silk_MAX_ORDER_LPC * sizeof( SKP_int32 ) );
    if( rshifts > 0 ) {
        for( s = 0; s < nb_subfr; s++ ) {
            x_ptr = x + s * subfr_length;
            for( n = 1; n < D + 1; n++ ) {
                C_first_row[ n - 1 ] += (SKP_int32)SKP_RSHIFT64( 
                    SKP_Silk_inner_prod16_aligned_64( x_ptr, x_ptr + n, subfr_length - n ), rshifts );
            }
        }
    } else {
        for( s = 0; s < nb_subfr; s++ ) {
            x_ptr = x + s * subfr_length;
            for( n = 1; n < D + 1; n++ ) {
                C_first_row[ n - 1 ] += SKP_LSHIFT32( 
                    SKP_Silk_inner_prod_aligned( x_ptr, x_ptr + n, subfr_length - n ), -rshifts );
            }
        }
    }
    SKP_memcpy( C_last_row, C_first_row, SKP_Silk_MAX_ORDER_LPC * sizeof( SKP_int32 ) );
    
    /* Initialize */
    CAb[ 0 ] = CAf[ 0 ] = C0 + SKP_SMMUL( WhiteNoiseFrac_Q32, C0 ) + 1;         // Q(-rshifts)

    for( n = 0; n < D; n++ ) {
        /* Update first row of correlation matrix (without first element) */
        /* Update last row of correlation matrix (without last element, stored in reversed order) */
        /* Update C * Af */
        /* Update C * flipud(Af) (stored in reversed order) */
        if( rshifts > -2 ) {
            for( s = 0; s < nb_subfr; s++ ) {
                x_ptr = x + s * subfr_length;
                x1  = -SKP_LSHIFT32( (SKP_int32)x_ptr[ n ],                    16 - rshifts );      // Q(16-rshifts)
                x2  = -SKP_LSHIFT32( (SKP_int32)x_ptr[ subfr_length - n - 1 ], 16 - rshifts );      // Q(16-rshifts)
                tmp1 = SKP_LSHIFT32( (SKP_int32)x_ptr[ n ],                    QA - 16 );           // Q(QA-16)
                tmp2 = SKP_LSHIFT32( (SKP_int32)x_ptr[ subfr_length - n - 1 ], QA - 16 );           // Q(QA-16)
                for( k = 0; k < n; k++ ) {
                    C_first_row[ k ] = SKP_SMLAWB( C_first_row[ k ], x1, x_ptr[ n - k - 1 ]            ); // Q( -rshifts )
                    C_last_row[ k ]  = SKP_SMLAWB( C_last_row[ k ],  x2, x_ptr[ subfr_length - n + k ] ); // Q( -rshifts )
                    Atmp_QA = Af_QA[ k ];
                    tmp1 = SKP_SMLAWB( tmp1, Atmp_QA, x_ptr[ n - k - 1 ]            );              // Q(QA-16)
                    tmp2 = SKP_SMLAWB( tmp2, Atmp_QA, x_ptr[ subfr_length - n + k ] );              // Q(QA-16)
                }
                tmp1 = SKP_LSHIFT32( -tmp1, 32 - QA - rshifts );                                    // Q(16-rshifts)
                tmp2 = SKP_LSHIFT32( -tmp2, 32 - QA - rshifts );                                    // Q(16-rshifts)
                for( k = 0; k <= n; k++ ) {
                    CAf[ k ] = SKP_SMLAWB( CAf[ k ], tmp1, x_ptr[ n - k ]                    );     // Q( -rshift )
                    CAb[ k ] = SKP_SMLAWB( CAb[ k ], tmp2, x_ptr[ subfr_length - n + k - 1 ] );     // Q( -rshift )
                }
            }
        } else {
            for( s = 0; s < nb_subfr; s++ ) {
                x_ptr = x + s * subfr_length;
                x1  = -SKP_LSHIFT32( (SKP_int32)x_ptr[ n ],                    -rshifts );          // Q( -rshifts )
                x2  = -SKP_LSHIFT32( (SKP_int32)x_ptr[ subfr_length - n - 1 ], -rshifts );          // Q( -rshifts )
                tmp1 = SKP_LSHIFT32( (SKP_int32)x_ptr[ n ],                    17 );                // Q17
                tmp2 = SKP_LSHIFT32( (SKP_int32)x_ptr[ subfr_length - n - 1 ], 17 );                // Q17
                for( k = 0; k < n; k++ ) {
                    C_first_row[ k ] = SKP_MLA( C_first_row[ k ], x1, x_ptr[ n - k - 1 ]            ); // Q( -rshifts )
                    C_last_row[ k ]  = SKP_MLA( C_last_row[ k ],  x2, x_ptr[ subfr_length - n + k ] ); // Q( -rshifts )
                    Atmp1 = SKP_RSHIFT_ROUND( Af_QA[ k ], QA - 17 );                                // Q17
                    tmp1 = SKP_MLA( tmp1, x_ptr[ n - k - 1 ],            Atmp1 );                   // Q17
                    tmp2 = SKP_MLA( tmp2, x_ptr[ subfr_length - n + k ], Atmp1 );                   // Q17
                }
                tmp1 = -tmp1;                                                                       // Q17
                tmp2 = -tmp2;                                                                       // Q17
                for( k = 0; k <= n; k++ ) {
                    CAf[ k ] = SKP_SMLAWW( CAf[ k ], tmp1, 
                        SKP_LSHIFT32( (SKP_int32)x_ptr[ n - k ], -rshifts - 1 ) );                  // Q( -rshift )
                    CAb[ k ] = SKP_SMLAWW( CAb[ k ], tmp2, 
                        SKP_LSHIFT32( (SKP_int32)x_ptr[ subfr_length - n + k - 1 ], -rshifts - 1 ) );// Q( -rshift )
                }
            }
        }

        /* Calculate nominator and denominator for the next order reflection (parcor) coefficient */
        tmp1 = C_first_row[ n ];                                                            // Q( -rshifts )
        tmp2 = C_last_row[ n ];                                                             // Q( -rshifts )
        num  = 0;                                                                           // Q( -rshifts )
        nrg  = SKP_ADD32( CAb[ 0 ], CAf[ 0 ] );                                             // Q( 1-rshifts )
        for( k = 0; k < n; k++ ) {
            Atmp_QA = Af_QA[ k ];
            lz = SKP_Silk_CLZ32( SKP_abs( Atmp_QA ) ) - 1;
            lz = SKP_min( 32 - QA, lz );
            Atmp1 = SKP_LSHIFT32( Atmp_QA, lz );                                            // Q( QA + lz )

            tmp1 = SKP_ADD_LSHIFT32( tmp1, SKP_SMMUL( C_last_row[  n - k - 1 ], Atmp1 ), 32 - QA - lz );    // Q( -rshifts )
            tmp2 = SKP_ADD_LSHIFT32( tmp2, SKP_SMMUL( C_first_row[ n - k - 1 ], Atmp1 ), 32 - QA - lz );    // Q( -rshifts )
            num  = SKP_ADD_LSHIFT32( num,  SKP_SMMUL( CAb[ n - k ],             Atmp1 ), 32 - QA - lz );    // Q( -rshifts )
            nrg  = SKP_ADD_LSHIFT32( nrg,  SKP_SMMUL( SKP_ADD32( CAb[ k + 1 ], CAf[ k + 1 ] ), 
                                                                                Atmp1 ), 32 - QA - lz );    // Q( 1-rshifts )
        }
        CAf[ n + 1 ] = tmp1;                                                                // Q( -rshifts )
        CAb[ n + 1 ] = tmp2;                                                                // Q( -rshifts )
        num = SKP_ADD32( num, tmp2 );                                                       // Q( -rshifts )
        num = SKP_LSHIFT32( -num, 1 );                                                      // Q( 1-rshifts )

        /* Calculate the next order reflection (parcor) coefficient */
        if( SKP_abs( num ) < nrg ) {
            rc_Q31 = SKP_DIV32_varQ( num, nrg, 31 );
        } else {
            /* Negative energy or ratio too high; set remaining coefficients to zero and exit loop */
            SKP_memset( &Af_QA[ n ], 0, ( D - n ) * sizeof( SKP_int32 ) );
            SKP_assert( 0 );
            break;
        }

        /* Update the AR coefficients */
        for( k = 0; k < (n + 1) >> 1; k++ ) {
            tmp1 = Af_QA[ k ];                                                              // QA
            tmp2 = Af_QA[ n - k - 1 ];                                                      // QA
            Af_QA[ k ]         = SKP_ADD_LSHIFT32( tmp1, SKP_SMMUL( tmp2, rc_Q31 ), 1 );    // QA
            Af_QA[ n - k - 1 ] = SKP_ADD_LSHIFT32( tmp2, SKP_SMMUL( tmp1, rc_Q31 ), 1 );    // QA
        }
        Af_QA[ n ] = SKP_RSHIFT32( rc_Q31, 31 - QA );                                       // QA

        /* Update C * Af and C * Ab */
        for( k = 0; k <= n + 1; k++ ) {
            tmp1 = CAf[ k ];                                                                // Q( -rshifts )
            tmp2 = CAb[ n - k + 1 ];                                                        // Q( -rshifts )
            CAf[ k ]         = SKP_ADD_LSHIFT32( tmp1, SKP_SMMUL( tmp2, rc_Q31 ), 1 );      // Q( -rshifts )
            CAb[ n - k + 1 ] = SKP_ADD_LSHIFT32( tmp2, SKP_SMMUL( tmp1, rc_Q31 ), 1 );      // Q( -rshifts )
        }
    }

    /* Return residual energy */
    nrg  = CAf[ 0 ];                                                                        // Q( -rshifts )
    tmp1 = 1 << 16;                                                                         // Q16
    for( k = 0; k < D; k++ ) {
        Atmp1 = SKP_RSHIFT_ROUND( Af_QA[ k ], QA - 16 );                                    // Q16
        nrg  = SKP_SMLAWW( nrg, CAf[ k + 1 ], Atmp1 );                                      // Q( -rshifts )
        tmp1 = SKP_SMLAWW( tmp1, Atmp1, Atmp1 );                                            // Q16
        A_Q16[ k ] = -Atmp1;
    }
    *res_nrg = SKP_SMLAWW( nrg, SKP_SMMUL( WhiteNoiseFrac_Q32, C0 ), -tmp1 );               // Q( -rshifts )
    *res_nrg_Q = -rshifts;
}
