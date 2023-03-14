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

/* Interpolate two vectors */
void SKP_Silk_interpolate(
    SKP_int                         xi[ MAX_LPC_ORDER ],    /* O    interpolated vector                     */
    const SKP_int                   x0[ MAX_LPC_ORDER ],    /* I    first vector                            */
    const SKP_int                   x1[ MAX_LPC_ORDER ],    /* I    second vector                           */
    const SKP_int                   ifact_Q2,               /* I    interp. factor, weight on 2nd vector    */
    const SKP_int                   d                       /* I    number of parameters                    */
)
{
    SKP_int i;

    SKP_assert( ifact_Q2 >= 0 );
    SKP_assert( ifact_Q2 <= ( 1 << 2 ) );

    for( i = 0; i < d; i++ ) {
        xi[ i ] = ( SKP_int )( ( SKP_int32 )x0[ i ] + SKP_RSHIFT( SKP_MUL( ( SKP_int32 )x1[ i ] - ( SKP_int32 )x0[ i ], ifact_Q2 ), 2 ) );
    }
}
