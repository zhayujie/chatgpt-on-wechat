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

#ifndef SKP_SILK_CONTROL_H
#define SKP_SILK_CONTROL_H

#include "SKP_Silk_typedef.h"

#ifdef __cplusplus
extern "C"
{
#endif

/***********************************************/
/* Structure for controlling encoder operation */
/***********************************************/
typedef struct {
    /* I:   Input signal sampling rate in Hertz; 8000/12000/16000/24000                     */
    SKP_int32 API_sampleRate;

    /* I:   Maximum internal sampling rate in Hertz; 8000/12000/16000/24000                 */
    SKP_int32 maxInternalSampleRate;

    /* I:   Number of samples per packet; must be equivalent of 20, 40, 60, 80 or 100 ms    */
    SKP_int packetSize;

    /* I:   Bitrate during active speech in bits/second; internally limited                 */
    SKP_int32 bitRate;                        

    /* I:   Uplink packet loss in percent (0-100)                                           */
    SKP_int packetLossPercentage;
    
    /* I:   Complexity mode; 0 is lowest; 1 is medium and 2 is highest complexity           */
    SKP_int complexity;

    /* I:   Flag to enable in-band Forward Error Correction (FEC); 0/1                      */
    SKP_int useInBandFEC;

    /* I:   Flag to enable discontinuous transmission (DTX); 0/1                            */
    SKP_int useDTX;
} SKP_SILK_SDK_EncControlStruct;

/**************************************************************************/
/* Structure for controlling decoder operation and reading decoder status */
/**************************************************************************/
typedef struct {
    /* I:   Output signal sampling rate in Hertz; 8000/12000/16000/24000                    */
    SKP_int32 API_sampleRate;

    /* O:   Number of samples per frame                                                     */
    SKP_int frameSize;

    /* O:   Frames per packet 1, 2, 3, 4, 5                                                 */
    SKP_int framesPerPacket;

    /* O:   Flag to indicate that the decoder has remaining payloads internally             */
    SKP_int moreInternalDecoderFrames;

    /* O:   Distance between main payload and redundant payload in packets                  */
    SKP_int inBandFECOffset;
} SKP_SILK_SDK_DecControlStruct;

#ifdef __cplusplus
}
#endif

#endif
