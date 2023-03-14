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

#ifndef SKP_SILK_ERRORS_H
#define SKP_SILK_ERRORS_H

#ifdef __cplusplus
extern "C"
{
#endif

/******************/
/* Error messages */
/******************/
#define SKP_SILK_NO_ERROR                               0

/**************************/
/* Encoder error messages */
/**************************/

/* Input length is not a multiplum of 10 ms, or length is longer than the packet length */
#define SKP_SILK_ENC_INPUT_INVALID_NO_OF_SAMPLES        -1

/* Sampling frequency not 8000, 12000, 16000 or 24000 Hertz */
#define SKP_SILK_ENC_FS_NOT_SUPPORTED                   -2

/* Packet size not 20, 40, 60, 80 or 100 ms */
#define SKP_SILK_ENC_PACKET_SIZE_NOT_SUPPORTED          -3

/* Allocated payload buffer too short */
#define SKP_SILK_ENC_PAYLOAD_BUF_TOO_SHORT              -4

/* Loss rate not between 0 and 100 percent */
#define SKP_SILK_ENC_INVALID_LOSS_RATE                  -5

/* Complexity setting not valid, use 0, 1 or 2 */
#define SKP_SILK_ENC_INVALID_COMPLEXITY_SETTING         -6

/* Inband FEC setting not valid, use 0 or 1 */
#define SKP_SILK_ENC_INVALID_INBAND_FEC_SETTING         -7

/* DTX setting not valid, use 0 or 1 */
#define SKP_SILK_ENC_INVALID_DTX_SETTING                -8

/* Internal encoder error */
#define SKP_SILK_ENC_INTERNAL_ERROR                     -9

/**************************/
/* Decoder error messages */
/**************************/

/* Output sampling frequency lower than internal decoded sampling frequency */
#define SKP_SILK_DEC_INVALID_SAMPLING_FREQUENCY         -10

/* Payload size exceeded the maximum allowed 1024 bytes */
#define SKP_SILK_DEC_PAYLOAD_TOO_LARGE                  -11

/* Payload has bit errors */
#define SKP_SILK_DEC_PAYLOAD_ERROR                      -12

#ifdef __cplusplus
}
#endif

#endif
