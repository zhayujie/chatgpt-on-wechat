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

/* 

    Elliptic/Cauer filters designed with 0.1 dB passband ripple, 
        80 dB minimum stopband attenuation, and
        [0.95 : 0.15 : 0.35] normalized cut off frequencies.

*/
#include "SKP_Silk_main.h"

#if SWITCH_TRANSITION_FILTERING

/* Helper function, that interpolates the filter taps */
SKP_INLINE void SKP_Silk_LP_interpolate_filter_taps( 
    SKP_int32           B_Q28[ TRANSITION_NB ], 
    SKP_int32           A_Q28[ TRANSITION_NA ],
    const SKP_int       ind,
    const SKP_int32     fac_Q16
)
{
    SKP_int nb, na;

    if( ind < TRANSITION_INT_NUM - 1 ) {
        if( fac_Q16 > 0 ) {
            if( fac_Q16 == SKP_SAT16( fac_Q16 ) ) { /* fac_Q16 is in range of a 16-bit int */
                /* Piece-wise linear interpolation of B and A */
                for( nb = 0; nb < TRANSITION_NB; nb++ ) {
                    B_Q28[ nb ] = SKP_SMLAWB(
                        SKP_Silk_Transition_LP_B_Q28[ ind     ][ nb ],
                        SKP_Silk_Transition_LP_B_Q28[ ind + 1 ][ nb ] -
                        SKP_Silk_Transition_LP_B_Q28[ ind     ][ nb ],
                        fac_Q16 );
                }
                for( na = 0; na < TRANSITION_NA; na++ ) {
                    A_Q28[ na ] = SKP_SMLAWB(
                        SKP_Silk_Transition_LP_A_Q28[ ind     ][ na ],
                        SKP_Silk_Transition_LP_A_Q28[ ind + 1 ][ na ] -
                        SKP_Silk_Transition_LP_A_Q28[ ind     ][ na ],
                        fac_Q16 );
                }
            } else if( fac_Q16 == ( 1 << 15 ) ) { /* Neither fac_Q16 nor ( ( 1 << 16 ) - fac_Q16 ) is in range of a 16-bit int */

                /* Piece-wise linear interpolation of B and A */
                for( nb = 0; nb < TRANSITION_NB; nb++ ) {
                    B_Q28[ nb ] = SKP_RSHIFT( 
                        SKP_Silk_Transition_LP_B_Q28[ ind     ][ nb ] +
                        SKP_Silk_Transition_LP_B_Q28[ ind + 1 ][ nb ],
                        1 );
                }
                for( na = 0; na < TRANSITION_NA; na++ ) {
                    A_Q28[ na ] = SKP_RSHIFT( 
                        SKP_Silk_Transition_LP_A_Q28[ ind     ][ na ] + 
                        SKP_Silk_Transition_LP_A_Q28[ ind + 1 ][ na ], 
                        1 );
                }
            } else { /* ( ( 1 << 16 ) - fac_Q16 ) is in range of a 16-bit int */
                
                SKP_assert( ( ( 1 << 16 ) - fac_Q16 ) == SKP_SAT16( ( ( 1 << 16 ) - fac_Q16) ) );
                /* Piece-wise linear interpolation of B and A */
                for( nb = 0; nb < TRANSITION_NB; nb++ ) {
                    B_Q28[ nb ] = SKP_SMLAWB(
                        SKP_Silk_Transition_LP_B_Q28[ ind + 1 ][ nb ],
                        SKP_Silk_Transition_LP_B_Q28[ ind     ][ nb ] -
                        SKP_Silk_Transition_LP_B_Q28[ ind + 1 ][ nb ],
                        ( 1 << 16 ) - fac_Q16 );
                }
                for( na = 0; na < TRANSITION_NA; na++ ) {
                    A_Q28[ na ] = SKP_SMLAWB(
                        SKP_Silk_Transition_LP_A_Q28[ ind + 1 ][ na ],
                        SKP_Silk_Transition_LP_A_Q28[ ind     ][ na ] -
                        SKP_Silk_Transition_LP_A_Q28[ ind + 1 ][ na ],
                        ( 1 << 16 ) - fac_Q16 );
                }
            }
        } else {
            SKP_memcpy( B_Q28, SKP_Silk_Transition_LP_B_Q28[ ind ], TRANSITION_NB * sizeof( SKP_int32 ) );
            SKP_memcpy( A_Q28, SKP_Silk_Transition_LP_A_Q28[ ind ], TRANSITION_NA * sizeof( SKP_int32 ) );
        }
    } else {
        SKP_memcpy( B_Q28, SKP_Silk_Transition_LP_B_Q28[ TRANSITION_INT_NUM - 1 ], TRANSITION_NB * sizeof( SKP_int32 ) );
        SKP_memcpy( A_Q28, SKP_Silk_Transition_LP_A_Q28[ TRANSITION_INT_NUM - 1 ], TRANSITION_NA * sizeof( SKP_int32 ) );
    }
}

/* Low-pass filter with variable cutoff frequency based on  */
/* piece-wise linear interpolation between elliptic filters */
/* Start by setting psEncC->transition_frame_no = 1;            */
/* Deactivate by setting psEncC->transition_frame_no = 0;   */
void SKP_Silk_LP_variable_cutoff(
    SKP_Silk_LP_state               *psLP,          /* I/O  LP filter state                     */
    SKP_int16                       *out,           /* O    Low-pass filtered output signal     */
    const SKP_int16                 *in,            /* I    Input signal                        */
    const SKP_int                   frame_length    /* I    Frame length                        */
)
{
    SKP_int32   B_Q28[ TRANSITION_NB ], A_Q28[ TRANSITION_NA ], fac_Q16 = 0;
    SKP_int     ind = 0;

    SKP_assert( psLP->transition_frame_no >= 0 );
    SKP_assert( ( ( ( psLP->transition_frame_no <= TRANSITION_FRAMES_DOWN ) && ( psLP->mode == 0 ) ) || 
                  ( ( psLP->transition_frame_no <= TRANSITION_FRAMES_UP   ) && ( psLP->mode == 1 ) ) ) );

    /* Interpolate filter coefficients if needed */
    if( psLP->transition_frame_no > 0 ) {
        if( psLP->mode == 0 ) {
            if( psLP->transition_frame_no < TRANSITION_FRAMES_DOWN ) {
                /* Calculate index and interpolation factor for interpolation */
#if( TRANSITION_INT_STEPS_DOWN == 32 )
                fac_Q16 = SKP_LSHIFT( psLP->transition_frame_no, 16 - 5 );
#else
                fac_Q16 = SKP_DIV32_16( SKP_LSHIFT( psLP->transition_frame_no, 16 ), TRANSITION_INT_STEPS_DOWN );
#endif
                ind      = SKP_RSHIFT( fac_Q16, 16 );
                fac_Q16 -= SKP_LSHIFT( ind, 16 );

                SKP_assert( ind >= 0 );
                SKP_assert( ind < TRANSITION_INT_NUM );

                /* Interpolate filter coefficients */
                SKP_Silk_LP_interpolate_filter_taps( B_Q28, A_Q28, ind, fac_Q16 );

                /* Increment transition frame number for next frame */
                psLP->transition_frame_no++;

            } else {
                SKP_assert( psLP->transition_frame_no == TRANSITION_FRAMES_DOWN );
                /* End of transition phase */
                SKP_Silk_LP_interpolate_filter_taps( B_Q28, A_Q28, TRANSITION_INT_NUM - 1, 0 );
            }
        } else {
            SKP_assert( psLP->mode == 1 );
            if( psLP->transition_frame_no < TRANSITION_FRAMES_UP ) {
                /* Calculate index and interpolation factor for interpolation */
#if( TRANSITION_INT_STEPS_UP == 64 )
                fac_Q16 = SKP_LSHIFT( TRANSITION_FRAMES_UP - psLP->transition_frame_no, 16 - 6 );
#else
                fac_Q16 = SKP_DIV32_16( SKP_LSHIFT( TRANSITION_FRAMES_UP - psLP->transition_frame_no, 16 ), TRANSITION_INT_STEPS_UP );
#endif
                ind      = SKP_RSHIFT( fac_Q16, 16 );
                fac_Q16 -= SKP_LSHIFT( ind, 16 );

                SKP_assert( ind >= 0 );
                SKP_assert( ind < TRANSITION_INT_NUM );

                /* Interpolate filter coefficients */
                SKP_Silk_LP_interpolate_filter_taps( B_Q28, A_Q28, ind, fac_Q16 );

                /* Increment transition frame number for next frame */
                psLP->transition_frame_no++;
            
            } else {
                SKP_assert( psLP->transition_frame_no == TRANSITION_FRAMES_UP );
                /* End of transition phase */
                SKP_Silk_LP_interpolate_filter_taps( B_Q28, A_Q28, 0, 0 );
            }
        }
    } 
    
    if( psLP->transition_frame_no > 0 ) {
        /* ARMA low-pass filtering */
        SKP_assert( TRANSITION_NB == 3 && TRANSITION_NA == 2 );
        SKP_Silk_biquad_alt( in, B_Q28, A_Q28, psLP->In_LP_State, out, frame_length );
    } else {
        /* Instead of using the filter, copy input directly to output */
        SKP_memcpy( out, in, frame_length * sizeof( SKP_int16 ) );
    }
}
#endif
