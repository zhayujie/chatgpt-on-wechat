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
 * SKP_Silk_autocorr.c                                                *
 *                                                                      *
 * Calculates the autocorrelation                                       *
 * The result has 29 non-zero bits for the first correlation, to leave  *
 * some    room for adding white noise fractions etc.                   *
 *                                                                      *
 * Copyright 2008 (c), Skype Limited                                    *
 *                                                                      */
#include "SKP_Silk_SigProc_FIX.h"

/* Compute autocorrelation */
void SKP_Silk_autocorr( 
    SKP_int32        *results,                   /* O    Result (length correlationCount)            */
    SKP_int          *scale,                     /* O    Scaling of the correlation vector           */
    const SKP_int16  *inputData,                 /* I    Input data to correlate                     */
    const SKP_int    inputDataSize,              /* I    Length of input                             */
    const SKP_int    correlationCount            /* I    Number of correlation taps to compute       */
)
{
    SKP_int   i, lz, nRightShifts, corrCount;
    SKP_int64 corr64;

    corrCount = SKP_min_int( inputDataSize, correlationCount );

    /* compute energy (zero-lag correlation) */
    corr64 = SKP_Silk_inner_prod16_aligned_64( inputData, inputData, inputDataSize );

    /* deal with all-zero input data */
    corr64 += 1;

    /* number of leading zeros */
    lz = SKP_Silk_CLZ64( corr64 );

    /* scaling: number of right shifts applied to correlations */
    nRightShifts = 35 - lz;
    *scale = nRightShifts;

    if( nRightShifts <= 0 ) {
        results[ 0 ] = SKP_LSHIFT( (SKP_int32)SKP_CHECK_FIT32( corr64 ), -nRightShifts );

        /* compute remaining correlations based on int32 inner product */
          for( i = 1; i < corrCount; i++ ) {
            results[ i ] = SKP_LSHIFT( SKP_Silk_inner_prod_aligned( inputData, inputData + i, inputDataSize - i ), -nRightShifts );
        }
    } else {
        results[ 0 ] = (SKP_int32)SKP_CHECK_FIT32( SKP_RSHIFT64( corr64, nRightShifts ) );

        /* compute remaining correlations based on int64 inner product */
          for( i = 1; i < corrCount; i++ ) {
            results[ i ] =  (SKP_int32)SKP_CHECK_FIT32( SKP_RSHIFT64( SKP_Silk_inner_prod16_aligned_64( inputData, inputData + i, inputDataSize - i ), nRightShifts ) );
        }
    }
}
