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

/* Chirp (bandwidth expand) LP AR filter */
void SKP_Silk_bwexpander( 
    SKP_int16            *ar,        /* I/O  AR filter to be expanded (without leading 1)    */
    const SKP_int        d,          /* I    Length of ar                                    */
    SKP_int32            chirp_Q16   /* I    Chirp factor (typically in the range 0 to 1)    */
)
{
    SKP_int   i;
    SKP_int32 chirp_minus_one_Q16;

    chirp_minus_one_Q16 = chirp_Q16 - 65536;

    /* NB: Dont use SKP_SMULWB, instead of SKP_RSHIFT_ROUND( SKP_MUL() , 16 ), below. */
    /* Bias in SKP_SMULWB can lead to unstable filters                                */
    for( i = 0; i < d - 1; i++ ) {
        ar[ i ]    = (SKP_int16)SKP_RSHIFT_ROUND( SKP_MUL( chirp_Q16, ar[ i ]             ), 16 );
        chirp_Q16 +=            SKP_RSHIFT_ROUND( SKP_MUL( chirp_Q16, chirp_minus_one_Q16 ), 16 );
    }
    ar[ d - 1 ] = (SKP_int16)SKP_RSHIFT_ROUND( SKP_MUL( chirp_Q16, ar[ d - 1 ] ), 16 );
}
