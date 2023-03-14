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
 * SKP_Silk_int16_array_maxabs.c                                      *
 *                                                                      *
 * Function that returns the maximum absolut value of                   *
 * the input vector                                                     *
 *                                                                      *
 * Copyright 2006 (c), Skype Limited                                    *
 * Date: 060221                                                         *
 *                                                                      */
#include "SKP_Silk_SigProc_FIX.h"

/* Function that returns the maximum absolut value of the input vector */
#if (EMBEDDED_ARM<4)  
SKP_int16 SKP_Silk_int16_array_maxabs(    /* O    Maximum absolute value, max: 2^15-1   */
    const SKP_int16        *vec,            /* I    Input vector  [len]                   */
    const SKP_int32        len              /* I    Length of input vector                */
)                    
{
    SKP_int32 max = 0, i, lvl = 0, ind;
	if( len == 0 ) return 0;

    ind = len - 1;
    max = SKP_SMULBB( vec[ ind ], vec[ ind ] );
    for( i = len - 2; i >= 0; i-- ) {
        lvl = SKP_SMULBB( vec[ i ], vec[ i ] );
        if( lvl > max ) {
            max = lvl;
            ind = i;
        }
    }

    /* Do not return 32768, as it will not fit in an int16 so may lead to problems later on */
    if( max >= 1073676289 ) { // (2^15-1)^2 = 1073676289
        return( SKP_int16_MAX );
    } else {
        if( vec[ ind ] < 0 ) {
            return( -vec[ ind ] );
        } else {
            return(  vec[ ind ] );
        }
    }
}
#endif
