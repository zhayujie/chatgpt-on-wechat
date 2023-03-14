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

/* Calculates residual energies of input subframes where all subframes have LPC_order   */
/* of preceeding samples                                                                */
void SKP_Silk_residual_energy_FIX(
          SKP_int32 nrgs[ NB_SUBFR ],           /* O    Residual energy per subframe    */
          SKP_int   nrgsQ[ NB_SUBFR ],          /* O    Q value per subframe            */
    const SKP_int16 x[],                        /* I    Input signal                    */
          SKP_int16 a_Q12[ 2 ][ MAX_LPC_ORDER ],/* I    AR coefs for each frame half    */
    const SKP_int32 gains[ NB_SUBFR ],          /* I    Quantization gains              */
    const SKP_int   subfr_length,               /* I    Subframe length                 */
    const SKP_int   LPC_order                   /* I    LPC order                       */
)
{
    SKP_int         offset, i, j, rshift, lz1, lz2;
    SKP_int16       *LPC_res_ptr, LPC_res[ ( MAX_FRAME_LENGTH + NB_SUBFR * MAX_LPC_ORDER ) / 2 ];
    const SKP_int16 *x_ptr;
    SKP_int16       S[ MAX_LPC_ORDER ];
    SKP_int32       tmp32;

    x_ptr  = x;
    offset = LPC_order + subfr_length;
    
    /* Filter input to create the LPC residual for each frame half, and measure subframe energies */
    for( i = 0; i < 2; i++ ) {
        /* Calculate half frame LPC residual signal including preceeding samples */
        SKP_memset( S, 0, LPC_order * sizeof( SKP_int16 ) );
        SKP_Silk_LPC_analysis_filter( x_ptr, a_Q12[ i ], S, LPC_res, ( NB_SUBFR >> 1 ) * offset, LPC_order );

        /* Point to first subframe of the just calculated LPC residual signal */
        LPC_res_ptr = LPC_res + LPC_order;
        for( j = 0; j < ( NB_SUBFR >> 1 ); j++ ) {
            /* Measure subframe energy */
            SKP_Silk_sum_sqr_shift( &nrgs[ i * ( NB_SUBFR >> 1 ) + j ], &rshift, LPC_res_ptr, subfr_length ); 
            
            /* Set Q values for the measured energy */
            nrgsQ[ i * ( NB_SUBFR >> 1 ) + j ] = -rshift;
            
            /* Move to next subframe */
            LPC_res_ptr += offset;
        }
        /* Move to next frame half */
        x_ptr += ( NB_SUBFR >> 1 ) * offset;
    }

    /* Apply the squared subframe gains */
    for( i = 0; i < NB_SUBFR; i++ ) {
        /* Fully upscale gains and energies */
        lz1 = SKP_Silk_CLZ32( nrgs[  i ] ) - 1; 
        lz2 = SKP_Silk_CLZ32( gains[ i ] ) - 1; 
        
        tmp32 = SKP_LSHIFT32( gains[ i ], lz2 );

        /* Find squared gains */
        tmp32 = SKP_SMMUL( tmp32, tmp32 ); // Q( 2 * lz2 - 32 )

        /* Scale energies */
        nrgs[ i ] = SKP_SMMUL( tmp32, SKP_LSHIFT32( nrgs[ i ], lz1 ) ); // Q( nrgsQ[ i ] + lz1 + 2 * lz2 - 32 - 32 )
        nrgsQ[ i ] += lz1 + 2 * lz2 - 32 - 32;
    }
}
