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
 * SKP_Silk_sum_sqr_shift.c                                           *
 *                                                                      *
 * compute number of bits to right shift the sum of squares of a vector *
 * of int16s to make it fit in an int32                                 *
 *                                                                      *
 * Copyright 2006-2008 (c), Skype Limited                               *
 *                                                                      */
#include "SKP_Silk_SigProc_FIX.h"
#if (EMBEDDED_ARM<5) 
/* Compute number of bits to right shift the sum of squares of a vector */
/* of int16s to make it fit in an int32                                 */
void SKP_Silk_sum_sqr_shift(
    SKP_int32            *energy,            /* O    Energy of x, after shifting to the right            */
    SKP_int              *shift,             /* O    Number of bits right shift applied to energy        */
    const SKP_int16      *x,                 /* I    Input vector                                        */
    SKP_int              len                 /* I    Length of input vector                              */
)
{
    SKP_int   i, shft;
    SKP_int32 in32, nrg_tmp, nrg;

    if( (SKP_int32)( (SKP_int_ptr_size)x & 2 ) != 0 ) {
        /* Input is not 4-byte aligned */
        nrg = SKP_SMULBB( x[ 0 ], x[ 0 ] );
        i = 1;
    } else {
        nrg = 0;
        i   = 0;
    }
    shft = 0;
    len--;
    while( i < len ) {
        /* Load two values at once */
        in32 = *( (SKP_int32 *)&x[ i ] );
        nrg = SKP_SMLABB_ovflw( nrg, in32, in32 );
        nrg = SKP_SMLATT_ovflw( nrg, in32, in32 );
        i += 2;
        if( nrg < 0 ) {
            /* Scale down */
            nrg = (SKP_int32)SKP_RSHIFT_uint( (SKP_uint32)nrg, 2 );
            shft = 2;
            break;
        }
    }
    for( ; i < len; i += 2 ) {
        /* Load two values at once */
        in32 = *( (SKP_int32 *)&x[ i ] );
        nrg_tmp = SKP_SMULBB( in32, in32 );
        nrg_tmp = SKP_SMLATT_ovflw( nrg_tmp, in32, in32 );
        nrg = (SKP_int32)SKP_ADD_RSHIFT_uint( nrg, (SKP_uint32)nrg_tmp, shft );
        if( nrg < 0 ) {
            /* Scale down */
            nrg = (SKP_int32)SKP_RSHIFT_uint( (SKP_uint32)nrg, 2 );
            shft += 2;
        }
    }
    if( i == len ) {
        /* One sample left to process */
        nrg_tmp = SKP_SMULBB( x[ i ], x[ i ] );
        nrg = (SKP_int32)SKP_ADD_RSHIFT_uint( nrg, nrg_tmp, shft );
    }

    /* Make sure to have at least one extra leading zero (two leading zeros in total) */
    if( nrg & 0xC0000000 ) {
        nrg = SKP_RSHIFT_uint( (SKP_uint32)nrg, 2 );
        shft += 2;
    }

    /* Output arguments */
    *shift  = shft;
    *energy = nrg;
}

#endif
