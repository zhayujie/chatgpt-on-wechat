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
 * SKP_Silk_LPC_synthesis_order16.c                                   *
 * Coefficients are in Q12                                              *
 *                                                                      *
 * 16th order AR filter                                                 *
 *                                                                      */
#include "SKP_Silk_SigProc_FIX.h"

/* 16th order AR filter */
void SKP_Silk_LPC_synthesis_order16(const SKP_int16 *in,          /* I:   excitation signal */
                                      const SKP_int16 *A_Q12,       /* I:   AR coefficients [16], between -8_Q0 and 8_Q0 */
                                      const SKP_int32 Gain_Q26,     /* I:   gain */
                                      SKP_int32 *S,                 /* I/O: state vector [16] */
                                      SKP_int16 *out,               /* O:   output signal */
                                      const SKP_int32 len           /* I:   signal length, must be multiple of 16 */
)
{
    SKP_int   k;
    SKP_int32 SA, SB, out32_Q10, out32;
#if !defined(_SYSTEM_IS_BIG_ENDIAN)
    SKP_int32 Atmp, A_align_Q12[ 8 ];
    /* combine two A_Q12 values and ensure 32-bit alignment */
    for( k = 0; k < 8; k++ ) {
        A_align_Q12[ k ] = ( ( ( SKP_int32 )A_Q12[ 2 * k ] ) & 0x0000ffff ) | SKP_LSHIFT( ( SKP_int32 )A_Q12[ 2 * k + 1 ], 16 );
    }
    /* S[] values are in Q14 */
    /* NOTE: the code below loads two int16 values in an int32, and multiplies each using the   */
    /* SMLAWB and SMLAWT instructions. On a big-endian CPU the two int16 variables would be     */
    /* loaded in reverse order and the code will give the wrong result. In that case swapping   */
    /* the SMLAWB and SMLAWT instructions should solve the problem.                             */
    for( k = 0; k < len; k++ ) {
        /* unrolled loop: prolog */
        /* multiply-add two prediction coefficients per iteration */
        SA = S[ 15 ];
        Atmp = A_align_Q12[ 0 ];
        SB = S[ 14 ];
        S[ 14 ] = SA;
        out32_Q10 = SKP_SMULWB(                  SA, Atmp );
        out32_Q10 = SKP_SMLAWT_ovflw( out32_Q10, SB, Atmp );
        SA = S[ 13 ];
        S[ 13 ] = SB;

        /* unrolled loop: main loop */
        Atmp = A_align_Q12[ 1 ];
        SB = S[ 12 ];
        S[ 12 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, Atmp );
        out32_Q10 = SKP_SMLAWT_ovflw( out32_Q10, SB, Atmp );
        SA = S[ 11 ];
        S[ 11 ] = SB;

        Atmp = A_align_Q12[ 2 ];
        SB = S[ 10 ];
        S[ 10 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, Atmp );
        out32_Q10 = SKP_SMLAWT_ovflw( out32_Q10, SB, Atmp );
        SA = S[ 9 ];
        S[ 9 ] = SB;

        Atmp = A_align_Q12[ 3 ];
        SB = S[ 8 ];
        S[ 8 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, Atmp );
        out32_Q10 = SKP_SMLAWT_ovflw( out32_Q10, SB, Atmp );
        SA = S[ 7 ];
        S[ 7 ] = SB;

        Atmp = A_align_Q12[ 4 ];
        SB = S[ 6 ];
        S[ 6 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, Atmp );
        out32_Q10 = SKP_SMLAWT_ovflw( out32_Q10, SB, Atmp );
        SA = S[ 5 ];
        S[ 5 ] = SB;

        Atmp = A_align_Q12[ 5 ];
        SB = S[ 4 ];
        S[ 4 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, Atmp );
        out32_Q10 = SKP_SMLAWT_ovflw( out32_Q10, SB, Atmp );
        SA = S[ 3 ];
        S[ 3 ] = SB;

        Atmp = A_align_Q12[ 6 ];
        SB = S[ 2 ];
        S[ 2 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, Atmp );
        out32_Q10 = SKP_SMLAWT_ovflw( out32_Q10, SB, Atmp );
        SA = S[ 1 ];
        S[ 1 ] = SB;

        /* unrolled loop: epilog */
        Atmp = A_align_Q12[ 7 ];
        SB = S[ 0 ];
        S[ 0 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, Atmp );
        out32_Q10 = SKP_SMLAWT_ovflw( out32_Q10, SB, Atmp );

        /* unrolled loop: end */
        /* apply gain to excitation signal and add to prediction */
        out32_Q10 = SKP_ADD_SAT32( out32_Q10, SKP_SMULWB( Gain_Q26, in[ k ] ) );

        /* scale to Q0 */
        out32 = SKP_RSHIFT_ROUND( out32_Q10, 10 );

        /* saturate output */
        out[ k ] = ( SKP_int16 )SKP_SAT16( out32 );

        /* move result into delay line */
        S[ 15 ] = SKP_LSHIFT_SAT32( out32_Q10, 4 );
    }
#else
    for( k = 0; k < len; k++ ) {
        /* unrolled loop: prolog */
        /* multiply-add two prediction coefficients per iteration */
        SA = S[ 15 ];
        SB = S[ 14 ];
        S[ 14 ] = SA;
        out32_Q10 = SKP_SMULWB(                  SA, A_Q12[ 0 ] );
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SB, A_Q12[ 1 ] );
        SA = S[ 13 ];
        S[ 13 ] = SB;

        /* unrolled loop: main loop */
        SB = S[ 12 ];
        S[ 12 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, A_Q12[ 2 ] );
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SB, A_Q12[ 3 ] );
        SA = S[ 11 ];
        S[ 11 ] = SB;

        SB = S[ 10 ];
        S[ 10 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, A_Q12[ 4 ] );
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SB, A_Q12[ 5 ] );
        SA = S[ 9 ];
        S[ 9 ] = SB;

        SB = S[ 8 ];
        S[ 8 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, A_Q12[ 6 ] );
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SB, A_Q12[ 7 ] );
        SA = S[ 7 ];
        S[ 7 ] = SB;

        SB = S[ 6 ];
        S[ 6 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, A_Q12[ 8 ] );
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SB, A_Q12[ 9 ] );
        SA = S[ 5 ];
        S[ 5 ] = SB;

        SB = S[ 4 ];
        S[ 4 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, A_Q12[ 10 ] );
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SB, A_Q12[ 11 ] );
        SA = S[ 3 ];
        S[ 3 ] = SB;

        SB = S[ 2 ];
        S[ 2 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, A_Q12[ 12 ] );
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SB, A_Q12[ 13 ] );
        SA = S[ 1 ];
        S[ 1 ] = SB;

        /* unrolled loop: epilog */
        SB = S[ 0 ];
        S[ 0 ] = SA;
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SA, A_Q12[ 14 ] );
        out32_Q10 = SKP_SMLAWB_ovflw( out32_Q10, SB, A_Q12[ 15 ] );

        /* unrolled loop: end */
        /* apply gain to excitation signal and add to prediction */
        out32_Q10 = SKP_ADD_SAT32( out32_Q10, SKP_SMULWB( Gain_Q26, in[ k ] ) );

        /* scale to Q0 */
        out32 = SKP_RSHIFT_ROUND( out32_Q10, 10 );

        /* saturate output */
        out[ k ] = ( SKP_int16 )SKP_SAT16( out32 );

        /* move result into delay line */
        S[ 15 ] = SKP_LSHIFT_SAT32( out32_Q10, 4 );
    }
#endif
}


