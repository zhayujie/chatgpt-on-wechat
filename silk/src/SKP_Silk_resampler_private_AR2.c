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

/*																		*
 * SKP_Silk_resampler_private_AR2. c                                  *
 *																		*
 * Second order AR filter with single delay elements                	*
 *                                                                      *
 * Copyright 2010 (c), Skype Limited                                    *
 *                                                                      */

#include "SKP_Silk_SigProc_FIX.h"
#include "SKP_Silk_resampler_private.h"

#if (EMBEDDED_ARM<5)  
/* Second order AR filter with single delay elements */
void SKP_Silk_resampler_private_AR2(
	SKP_int32					    S[],		    /* I/O: State vector [ 2 ]			    	    */
	SKP_int32					    out_Q8[],		/* O:	Output signal				    	    */
	const SKP_int16				    in[],			/* I:	Input signal				    	    */
	const SKP_int16				    A_Q14[],		/* I:	AR coefficients, Q14 	                */
	SKP_int32				        len				/* I:	Signal length				        	*/
)
{
	SKP_int32	k;
	SKP_int32	out32;

	for( k = 0; k < len; k++ ) {
		out32       = SKP_ADD_LSHIFT32( S[ 0 ], (SKP_int32)in[ k ], 8 );
		out_Q8[ k ] = out32;
		out32       = SKP_LSHIFT( out32, 2 );
		S[ 0 ]      = SKP_SMLAWB( S[ 1 ], out32, A_Q14[ 0 ] );
		S[ 1 ]      = SKP_SMULWB( out32, A_Q14[ 1 ] );
	}
}
#endif
