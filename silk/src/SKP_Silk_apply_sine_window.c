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

/* Apply sine window to signal vector.                                      */
/* Window types:                                                            */
/*    1 -> sine window from 0 to pi/2                                       */
/*    2 -> sine window from pi/2 to pi                                      */
/* Every other sample is linearly interpolated, for speed.                  */
/* Window length must be between 16 and 120 (incl) and a multiple of 4.     */

/* Matlab code for table: 
   for k=16:9*4:16+2*9*4, fprintf(' %7.d,', -round(65536*pi ./ (k:4:k+8*4))); fprintf('\n'); end
*/
static SKP_int16 freq_table_Q16[ 27 ] = {
   12111,    9804,    8235,    7100,    6239,    5565,    5022,    4575,    4202,
    3885,    3612,    3375,    3167,    2984,    2820,    2674,    2542,    2422,
    2313,    2214,    2123,    2038,    1961,    1889,    1822,    1760,    1702,
};

//#if EMBEDDED_ARM<6
void SKP_Silk_apply_sine_window(
    SKP_int16                        px_win[],            /* O    Pointer to windowed signal                  */
    const SKP_int16                  px[],                /* I    Pointer to input signal                     */
    const SKP_int                    win_type,            /* I    Selects a window type                       */
    const SKP_int                    length               /* I    Window length, multiple of 4                */
)
{
    SKP_int   k, f_Q16, c_Q16;
    SKP_int32 S0_Q16, S1_Q16;
#if !defined(_SYSTEM_IS_BIG_ENDIAN)
    SKP_int32 px32;
#endif
    SKP_assert( win_type == 1 || win_type == 2 );

    /* Length must be in a range from 16 to 120 and a multiple of 4 */
    SKP_assert( length >= 16 && length <= 120 );
    SKP_assert( ( length & 3 ) == 0 );

    /* Input pointer must be 4-byte aligned */
    SKP_assert( ( ( SKP_int64 )( ( SKP_int8* )px - ( SKP_int8* )0 ) & 3 ) == 0 );

    /* Frequency */
    k = ( length >> 2 ) - 4;
    SKP_assert( k >= 0 && k <= 26 );
    f_Q16 = (SKP_int)freq_table_Q16[ k ];

    /* Factor used for cosine approximation */
    c_Q16 = SKP_SMULWB( f_Q16, -f_Q16 );
    SKP_assert( c_Q16 >= -32768 );

    /* initialize state */
    if( win_type == 1 ) {
        /* start from 0 */
        S0_Q16 = 0;
        /* approximation of sin(f) */
        S1_Q16 = f_Q16 + SKP_RSHIFT( length, 3 );
    } else {
        /* start from 1 */
        S0_Q16 = ( 1 << 16 );
        /* approximation of cos(f) */
        S1_Q16 = ( 1 << 16 ) + SKP_RSHIFT( c_Q16, 1 ) + SKP_RSHIFT( length, 4 );
    }

    /* Uses the recursive equation:   sin(n*f) = 2 * cos(f) * sin((n-1)*f) - sin((n-2)*f)    */
    /* 4 samples at a time */
#if !defined(_SYSTEM_IS_BIG_ENDIAN)
    for( k = 0; k < length; k += 4 ) {
        px32 = *( (SKP_int32 *)&px[ k ] );                        /* load two values at once */
        px_win[ k ]     = (SKP_int16)SKP_SMULWB( SKP_RSHIFT( S0_Q16 + S1_Q16, 1 ), px32 );
        px_win[ k + 1 ] = (SKP_int16)SKP_SMULWT( S1_Q16, px32 );
        S0_Q16 = SKP_SMULWB( S1_Q16, c_Q16 ) + SKP_LSHIFT( S1_Q16, 1 ) - S0_Q16 + 1;
        S0_Q16 = SKP_min( S0_Q16, ( 1 << 16 ) );

        px32 = *( (SKP_int32 *)&px[k + 2] );                      /* load two values at once */
        px_win[ k + 2 ] = (SKP_int16)SKP_SMULWB( SKP_RSHIFT( S0_Q16 + S1_Q16, 1 ), px32 );
        px_win[ k + 3 ] = (SKP_int16)SKP_SMULWT( S0_Q16, px32 );
        S1_Q16 = SKP_SMULWB( S0_Q16, c_Q16 ) + SKP_LSHIFT( S0_Q16, 1 ) - S1_Q16;
        S1_Q16 = SKP_min( S1_Q16, ( 1 << 16 ) );
    }
#else
    for( k = 0; k < length; k += 4 ) {
        px_win[ k ]     = (SKP_int16)SKP_SMULWB( SKP_RSHIFT( S0_Q16 + S1_Q16, 1 ), px[ k ] );
        px_win[ k + 1 ] = (SKP_int16)SKP_SMULWB( S1_Q16, px[ k + 1] );
        S0_Q16 = SKP_SMULWB( S1_Q16, c_Q16 ) + SKP_LSHIFT( S1_Q16, 1 ) - S0_Q16 + 1;
        S0_Q16 = SKP_min( S0_Q16, ( 1 << 16 ) );

        px_win[ k + 2 ] = (SKP_int16)SKP_SMULWB( SKP_RSHIFT( S0_Q16 + S1_Q16, 1 ), px[ k + 2] );
        px_win[ k + 3 ] = (SKP_int16)SKP_SMULWB( S0_Q16, px[ k + 3 ] );
        S1_Q16 = SKP_SMULWB( S0_Q16, c_Q16 ) + SKP_LSHIFT( S0_Q16, 1 ) - S1_Q16;
        S1_Q16 = SKP_min( S1_Q16, ( 1 << 16 ) );
    }
#endif
}
//#endif
