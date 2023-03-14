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

/*********************************/
/* Initialize Silk Encoder state */
/*********************************/
SKP_int SKP_Silk_init_encoder_FIX(
    SKP_Silk_encoder_state_FIX  *psEnc                  /* I/O  Pointer to Silk FIX encoder state       */
) {
    SKP_int ret = 0;
    /* Clear the entire encoder state */
    SKP_memset( psEnc, 0, sizeof( SKP_Silk_encoder_state_FIX ) );

#if HIGH_PASS_INPUT
    psEnc->variable_HP_smth1_Q15 = 200844; /* = SKP_Silk_log2(70)_Q0; */
    psEnc->variable_HP_smth2_Q15 = 200844; /* = SKP_Silk_log2(70)_Q0; */
#endif

    /* Used to deactivate e.g. LSF interpolation and fluctuation reduction */
    psEnc->sCmn.first_frame_after_reset = 1;

    /* Initialize Silk VAD */
    ret += SKP_Silk_VAD_Init( &psEnc->sCmn.sVAD );

    /* Initialize NSQ */
    psEnc->sCmn.sNSQ.prev_inv_gain_Q16      = 65536;
    psEnc->sCmn.sNSQ_LBRR.prev_inv_gain_Q16 = 65536;

    return( ret );
}
