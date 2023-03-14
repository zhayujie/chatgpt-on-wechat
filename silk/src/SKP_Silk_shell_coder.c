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

/* shell coder; pulse-subframe length is hardcoded */

SKP_INLINE void combine_pulses(
    SKP_int         *out,   /* O:   combined pulses vector [len] */
    const SKP_int   *in,    /* I:   input vector       [2 * len] */
    const SKP_int   len     /* I:   number of OUTPUT samples     */
)
{
    SKP_int k;
    for( k = 0; k < len; k++ ) {
        out[ k ] = in[ 2 * k ] + in[ 2 * k + 1 ];
    }
}

SKP_INLINE void encode_split(
    SKP_Silk_range_coder_state  *sRC,           /* I/O: compressor data structure                   */
    const SKP_int               p_child1,       /* I:   pulse amplitude of first child subframe     */
    const SKP_int               p,              /* I:   pulse amplitude of current subframe         */
    const SKP_uint16            *shell_table    /* I:   table of shell cdfs                         */
)
{
    const SKP_uint16 *cdf;

    if( p > 0 ) {
        cdf = &shell_table[ SKP_Silk_shell_code_table_offsets[ p ] ];
        SKP_Silk_range_encoder( sRC, p_child1, cdf );
    }
}

SKP_INLINE void decode_split(
    SKP_int                     *p_child1,      /* O:   pulse amplitude of first child subframe     */
    SKP_int                     *p_child2,      /* O:   pulse amplitude of second child subframe    */
    SKP_Silk_range_coder_state  *sRC,           /* I/O: compressor data structure                   */
    const SKP_int               p,              /* I:   pulse amplitude of current subframe         */
    const SKP_uint16            *shell_table    /* I:   table of shell cdfs                         */
)
{
    SKP_int cdf_middle;
    const SKP_uint16 *cdf;

    if( p > 0 ) {
        cdf_middle = SKP_RSHIFT( p, 1 );
        cdf = &shell_table[ SKP_Silk_shell_code_table_offsets[ p ] ];
        SKP_Silk_range_decoder( p_child1, sRC, cdf, cdf_middle );
        p_child2[ 0 ] = p - p_child1[ 0 ];
    } else {
        p_child1[ 0 ] = 0;
        p_child2[ 0 ] = 0;
    }
}

/* Shell encoder, operates on one shell code frame of 16 pulses */
void SKP_Silk_shell_encoder(
    SKP_Silk_range_coder_state      *sRC,               /* I/O  compressor data structure                   */
    const SKP_int                   *pulses0            /* I    data: nonnegative pulse amplitudes          */
)
{
    SKP_int pulses1[ 8 ], pulses2[ 4 ], pulses3[ 2 ], pulses4[ 1 ];

    /* this function operates on one shell code frame of 16 pulses */
    SKP_assert( SHELL_CODEC_FRAME_LENGTH == 16 );

    /* tree representation per pulse-subframe */
    combine_pulses( pulses1, pulses0, 8 );
    combine_pulses( pulses2, pulses1, 4 );
    combine_pulses( pulses3, pulses2, 2 );
    combine_pulses( pulses4, pulses3, 1 );

    encode_split( sRC, pulses3[  0 ], pulses4[ 0 ], SKP_Silk_shell_code_table3 );

    encode_split( sRC, pulses2[  0 ], pulses3[ 0 ], SKP_Silk_shell_code_table2 );

    encode_split( sRC, pulses1[  0 ], pulses2[ 0 ], SKP_Silk_shell_code_table1 );
    encode_split( sRC, pulses0[  0 ], pulses1[ 0 ], SKP_Silk_shell_code_table0 );
    encode_split( sRC, pulses0[  2 ], pulses1[ 1 ], SKP_Silk_shell_code_table0 );

    encode_split( sRC, pulses1[  2 ], pulses2[ 1 ], SKP_Silk_shell_code_table1 );
    encode_split( sRC, pulses0[  4 ], pulses1[ 2 ], SKP_Silk_shell_code_table0 );
    encode_split( sRC, pulses0[  6 ], pulses1[ 3 ], SKP_Silk_shell_code_table0 );

    encode_split( sRC, pulses2[  2 ], pulses3[ 1 ], SKP_Silk_shell_code_table2 );

    encode_split( sRC, pulses1[  4 ], pulses2[ 2 ], SKP_Silk_shell_code_table1 );
    encode_split( sRC, pulses0[  8 ], pulses1[ 4 ], SKP_Silk_shell_code_table0 );
    encode_split( sRC, pulses0[ 10 ], pulses1[ 5 ], SKP_Silk_shell_code_table0 );

    encode_split( sRC, pulses1[  6 ], pulses2[ 3 ], SKP_Silk_shell_code_table1 );
    encode_split( sRC, pulses0[ 12 ], pulses1[ 6 ], SKP_Silk_shell_code_table0 );
    encode_split( sRC, pulses0[ 14 ], pulses1[ 7 ], SKP_Silk_shell_code_table0 );
}


/* Shell decoder, operates on one shell code frame of 16 pulses */
void SKP_Silk_shell_decoder(
    SKP_int                         *pulses0,           /* O    data: nonnegative pulse amplitudes          */
    SKP_Silk_range_coder_state      *sRC,               /* I/O  compressor data structure                   */
    const SKP_int                   pulses4             /* I    number of pulses per pulse-subframe         */
)
{
    SKP_int pulses3[ 2 ], pulses2[ 4 ], pulses1[ 8 ];

    /* this function operates on one shell code frame of 16 pulses */
    SKP_assert( SHELL_CODEC_FRAME_LENGTH == 16 );

    decode_split( &pulses3[  0 ], &pulses3[  1 ], sRC, pulses4,      SKP_Silk_shell_code_table3 );

    decode_split( &pulses2[  0 ], &pulses2[  1 ], sRC, pulses3[ 0 ], SKP_Silk_shell_code_table2 );

    decode_split( &pulses1[  0 ], &pulses1[  1 ], sRC, pulses2[ 0 ], SKP_Silk_shell_code_table1 );
    decode_split( &pulses0[  0 ], &pulses0[  1 ], sRC, pulses1[ 0 ], SKP_Silk_shell_code_table0 );
    decode_split( &pulses0[  2 ], &pulses0[  3 ], sRC, pulses1[ 1 ], SKP_Silk_shell_code_table0 );

    decode_split( &pulses1[  2 ], &pulses1[  3 ], sRC, pulses2[ 1 ], SKP_Silk_shell_code_table1 );
    decode_split( &pulses0[  4 ], &pulses0[  5 ], sRC, pulses1[ 2 ], SKP_Silk_shell_code_table0 );
    decode_split( &pulses0[  6 ], &pulses0[  7 ], sRC, pulses1[ 3 ], SKP_Silk_shell_code_table0 );

    decode_split( &pulses2[  2 ], &pulses2[  3 ], sRC, pulses3[ 1 ], SKP_Silk_shell_code_table2 );

    decode_split( &pulses1[  4 ], &pulses1[  5 ], sRC, pulses2[ 2 ], SKP_Silk_shell_code_table1 );
    decode_split( &pulses0[  8 ], &pulses0[  9 ], sRC, pulses1[ 4 ], SKP_Silk_shell_code_table0 );
    decode_split( &pulses0[ 10 ], &pulses0[ 11 ], sRC, pulses1[ 5 ], SKP_Silk_shell_code_table0 );

    decode_split( &pulses1[  6 ], &pulses1[  7 ], sRC, pulses2[ 3 ], SKP_Silk_shell_code_table1 );
    decode_split( &pulses0[ 12 ], &pulses0[ 13 ], sRC, pulses1[ 6 ], SKP_Silk_shell_code_table0 );
    decode_split( &pulses0[ 14 ], &pulses0[ 15 ], sRC, pulses1[ 7 ], SKP_Silk_shell_code_table0 );
}
