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
 * File Name:	SKP_Silk_resampler_structs.h							*
 *																		*
 * Description: Structs for IIR/FIR resamplers							*
 *                                                                      *
 * Copyright 2010 (c), Skype Limited                                    *
 * All rights reserved.													*
 *																		*
 *                                                                      */

#ifndef SKP_Silk_RESAMPLER_STRUCTS_H
#define SKP_Silk_RESAMPLER_STRUCTS_H

#ifdef __cplusplus
extern "C" {
#endif

/* Flag to enable support for input/output sampling rates above 48 kHz. Turn off for embedded devices */
#define RESAMPLER_SUPPORT_ABOVE_48KHZ                   1

#define SKP_Silk_RESAMPLER_MAX_FIR_ORDER                 16
#define SKP_Silk_RESAMPLER_MAX_IIR_ORDER                 6


typedef struct _SKP_Silk_resampler_state_struct{
	SKP_int32       sIIR[ SKP_Silk_RESAMPLER_MAX_IIR_ORDER ];        /* this must be the first element of this struct */
	SKP_int32       sFIR[ SKP_Silk_RESAMPLER_MAX_FIR_ORDER ];
	SKP_int32       sDown2[ 2 ];
	void            (*resampler_function)( void *, SKP_int16 *, const SKP_int16 *, SKP_int32 );
	void            (*up2_function)(  SKP_int32 *, SKP_int16 *, const SKP_int16 *, SKP_int32 );
    SKP_int32       batchSize;
	SKP_int32       invRatio_Q16;
	SKP_int32       FIR_Fracs;
    SKP_int32       input2x;
	const SKP_int16	*Coefs;
#if RESAMPLER_SUPPORT_ABOVE_48KHZ
	SKP_int32       sDownPre[ 2 ];
	SKP_int32       sUpPost[ 2 ];
	void            (*down_pre_function)( SKP_int32 *, SKP_int16 *, const SKP_int16 *, SKP_int32 );
	void            (*up_post_function)(  SKP_int32 *, SKP_int16 *, const SKP_int16 *, SKP_int32 );
	SKP_int32       batchSizePrePost;
	SKP_int32       ratio_Q16;
	SKP_int32       nPreDownsamplers;
	SKP_int32       nPostUpsamplers;
#endif
	SKP_int32 magic_number;
} SKP_Silk_resampler_state_struct;

#ifdef __cplusplus
}
#endif
#endif /* SKP_Silk_RESAMPLER_STRUCTS_H */

