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


/*****************************/
/* Silk encoder test program */
/*****************************/

#ifdef _WIN32
#define _CRT_SECURE_NO_DEPRECATE    1
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "SKP_Silk_SDK_API.h"

/* Define codec specific settings */
#define MAX_BYTES_PER_FRAME     250 // Equals peak bitrate of 100 kbps 
#define MAX_INPUT_FRAMES        5
#define FRAME_LENGTH_MS         20
#define MAX_API_FS_KHZ          48

#ifdef _SYSTEM_IS_BIG_ENDIAN
/* Function to convert a little endian int16 to a */
/* big endian int16 or vica verca                 */
void swap_endian(
    SKP_int16       vec[],              /*  I/O array of */
    SKP_int         len                 /*  I   length      */
)
{
    SKP_int i;
    SKP_int16 tmp;
    SKP_uint8 *p1, *p2;

    for( i = 0; i < len; i++ ){
        tmp = vec[ i ];
        p1 = (SKP_uint8 *)&vec[ i ]; p2 = (SKP_uint8 *)&tmp;
        p1[ 0 ] = p2[ 1 ]; p1[ 1 ] = p2[ 0 ];
    }
}
#endif

#if (defined(_WIN32) || defined(_WINCE)) 
#include <windows.h>	/* timer */
#else    // Linux or Mac
#include <sys/time.h>
#endif

#ifdef _WIN32

unsigned long GetHighResolutionTime() /* O: time in usec*/
{
    /* Returns a time counter in microsec	*/
    /* the resolution is platform dependent */
    /* but is typically 1.62 us resolution  */
    LARGE_INTEGER lpPerformanceCount;
    LARGE_INTEGER lpFrequency;
    QueryPerformanceCounter(&lpPerformanceCount);
    QueryPerformanceFrequency(&lpFrequency);
    return (unsigned long)((1000000*(lpPerformanceCount.QuadPart)) / lpFrequency.QuadPart);
}
#else    // Linux or Mac
unsigned long GetHighResolutionTime() /* O: time in usec*/
{
    struct timeval tv;
    gettimeofday(&tv, 0);
    return((tv.tv_sec*1000000)+(tv.tv_usec));
}
#endif // _WIN32

static void print_usage( char* argv[] ) {
    printf( "\nVersion:20160922    Build By kn007 (kn007.net)");
    printf( "\nGithub: https://github.com/kn007/silk-v3-decoder\n");
    printf( "\nusage: %s in.pcm out.bit [settings]\n", argv[ 0 ] );
    printf( "\nin.pcm               : Speech input to encoder" );
    printf( "\nout.bit              : Bitstream output from encoder" );
    printf( "\n   settings:" );
    printf( "\n-Fs_API <Hz>         : API sampling rate in Hz, default: 24000" );
    printf( "\n-Fs_maxInternal <Hz> : Maximum internal sampling rate in Hz, default: 24000" ); 
    printf( "\n-packetlength <ms>   : Packet interval in ms, default: 20" );
    printf( "\n-rate <bps>          : Target bitrate; default: 25000" );
    printf( "\n-loss <perc>         : Uplink loss estimate, in percent (0-100); default: 0" );
    printf( "\n-inbandFEC <flag>    : Enable inband FEC usage (0/1); default: 0" );
    printf( "\n-complexity <comp>   : Set complexity, 0: low, 1: medium, 2: high; default: 2" );
    printf( "\n-DTX <flag>          : Enable DTX (0/1); default: 0" );
    printf( "\n-quiet               : Print only some basic values" );
    printf( "\n-tencent             : Compatible with QQ/Wechat" );
    printf( "\n");
}

int main( int argc, char* argv[] )
{
    unsigned long tottime, starttime;
    double    filetime;
    size_t    counter;
    SKP_int32 k, args, totPackets, totActPackets, ret;
    SKP_int16 nBytes;
    double    sumBytes, sumActBytes, avg_rate, act_rate, nrg;
    SKP_uint8 payload[ MAX_BYTES_PER_FRAME * MAX_INPUT_FRAMES ];
    SKP_int16 in[ FRAME_LENGTH_MS * MAX_API_FS_KHZ * MAX_INPUT_FRAMES ];
    char      speechInFileName[ 150 ], bitOutFileName[ 150 ];
    FILE      *bitOutFile, *speechInFile;
    SKP_int32 encSizeBytes;
    void      *psEnc;
#ifdef _SYSTEM_IS_BIG_ENDIAN
    SKP_int16 nBytes_LE;
#endif

    /* default settings */
    SKP_int32 API_fs_Hz = 24000;
    SKP_int32 max_internal_fs_Hz = 0;
    SKP_int32 targetRate_bps = 25000;
    SKP_int32 smplsSinceLastPacket, packetSize_ms = 20;
    SKP_int32 frameSizeReadFromFile_ms = 20;
    SKP_int32 packetLoss_perc = 0;
#if LOW_COMPLEXITY_ONLY
    SKP_int32 complexity_mode = 0;
#else
    SKP_int32 complexity_mode = 2;
#endif
    SKP_int32 DTX_enabled = 0, INBandFEC_enabled = 0, quiet = 0, tencent = 0;
    SKP_SILK_SDK_EncControlStruct encControl; // Struct for input to encoder
    SKP_SILK_SDK_EncControlStruct encStatus;  // Struct for status of encoder

    if( argc < 3 ) {
        print_usage( argv );
        exit( 0 );
    } 
    
    /* get arguments */
    args = 1;
    strcpy( speechInFileName, argv[ args ] );
    args++;
    strcpy( bitOutFileName,   argv[ args ] );
    args++;
    while( args < argc ) {
        if( SKP_STR_CASEINSENSITIVE_COMPARE( argv[ args ], "-Fs_API" ) == 0 ) {
            sscanf( argv[ args + 1 ], "%d", &API_fs_Hz );
            args += 2;
        } else if( SKP_STR_CASEINSENSITIVE_COMPARE( argv[ args ], "-Fs_maxInternal" ) == 0 ) {
            sscanf( argv[ args + 1 ], "%d", &max_internal_fs_Hz );
            args += 2;
        } else if( SKP_STR_CASEINSENSITIVE_COMPARE( argv[ args ], "-packetlength" ) == 0 ) {
            sscanf( argv[ args + 1 ], "%d", &packetSize_ms );
            args += 2;
        } else if( SKP_STR_CASEINSENSITIVE_COMPARE( argv[ args ], "-rate" ) == 0 ) {
            sscanf( argv[ args + 1 ], "%d", &targetRate_bps );
            args += 2;
        } else if( SKP_STR_CASEINSENSITIVE_COMPARE( argv[ args ], "-loss" ) == 0 ) {
            sscanf( argv[ args + 1 ], "%d", &packetLoss_perc );
            args += 2;
        } else if( SKP_STR_CASEINSENSITIVE_COMPARE( argv[ args ], "-complexity" ) == 0 ) {
            sscanf( argv[ args + 1 ], "%d", &complexity_mode );
            args += 2;
        } else if( SKP_STR_CASEINSENSITIVE_COMPARE( argv[ args ], "-inbandFEC" ) == 0 ) {
            sscanf( argv[ args + 1 ], "%d", &INBandFEC_enabled );
            args += 2;
        } else if( SKP_STR_CASEINSENSITIVE_COMPARE( argv[ args ], "-DTX") == 0 ) {
            sscanf( argv[ args + 1 ], "%d", &DTX_enabled );
            args += 2;
        } else if( SKP_STR_CASEINSENSITIVE_COMPARE( argv[ args ], "-tencent" ) == 0 ) {
            tencent = 1;
            args ++;
        } else if( SKP_STR_CASEINSENSITIVE_COMPARE( argv[ args ], "-quiet" ) == 0 ) {
            quiet = 1;
            args++;
        } else {
            printf( "Error: unrecognized setting: %s\n\n", argv[ args ] );
            print_usage( argv );
            exit( 0 );
        }
    }

    /* If no max internal is specified, set to minimum of API fs and 24 kHz */
    if( max_internal_fs_Hz == 0 ) {
        max_internal_fs_Hz = 24000;
        if( API_fs_Hz < max_internal_fs_Hz ) {
            max_internal_fs_Hz = API_fs_Hz;
        }
    }

    /* Print options */
    if( !quiet ) {
        printf("********** Silk Encoder (Fixed Point) v %s ********************\n", SKP_Silk_SDK_get_version());
        printf("********** Compiled for %d bit cpu ******************************* \n", (int)sizeof(void*) * 8 );
        printf( "Input:                          %s\n",     speechInFileName );
        printf( "Output:                         %s\n",     bitOutFileName );
        printf( "API sampling rate:              %d Hz\n",  API_fs_Hz );
        printf( "Maximum internal sampling rate: %d Hz\n",  max_internal_fs_Hz );
        printf( "Packet interval:                %d ms\n",  packetSize_ms );
        printf( "Inband FEC used:                %d\n",     INBandFEC_enabled );
        printf( "DTX used:                       %d\n",     DTX_enabled );
        printf( "Complexity:                     %d\n",     complexity_mode );
        printf( "Target bitrate:                 %d bps\n", targetRate_bps );
    }

    /* Open files */
    speechInFile = fopen( speechInFileName, "rb" );
    if( speechInFile == NULL ) {
        printf( "Error: could not open input file %s\n", speechInFileName );
        exit( 0 );
    }
    bitOutFile = fopen( bitOutFileName, "wb" );
    if( bitOutFile == NULL ) {
        printf( "Error: could not open output file %s\n", bitOutFileName );
        exit( 0 );
    }

    /* Add Silk header to stream */
    {
        if( tencent ) {
	        static const char Tencent_break[] = "";
            fwrite( Tencent_break, sizeof( char ), strlen( Tencent_break ), bitOutFile );
        }

        static const char Silk_header[] = "#!SILK_V3";
        fwrite( Silk_header, sizeof( char ), strlen( Silk_header ), bitOutFile );
    }

    /* Create Encoder */
    ret = SKP_Silk_SDK_Get_Encoder_Size( &encSizeBytes );
    if( ret ) {
        printf( "\nError: SKP_Silk_create_encoder returned %d\n", ret );
        exit( 0 );
    }

    psEnc = malloc( encSizeBytes );

    /* Reset Encoder */
    ret = SKP_Silk_SDK_InitEncoder( psEnc, &encStatus );
    if( ret ) {
        printf( "\nError: SKP_Silk_reset_encoder returned %d\n", ret );
        exit( 0 );
    }

    /* Set Encoder parameters */
    encControl.API_sampleRate        = API_fs_Hz;
    encControl.maxInternalSampleRate = max_internal_fs_Hz;
    encControl.packetSize            = ( packetSize_ms * API_fs_Hz ) / 1000;
    encControl.packetLossPercentage  = packetLoss_perc;
    encControl.useInBandFEC          = INBandFEC_enabled;
    encControl.useDTX                = DTX_enabled;
    encControl.complexity            = complexity_mode;
    encControl.bitRate               = ( targetRate_bps > 0 ? targetRate_bps : 0 );

    if( API_fs_Hz > MAX_API_FS_KHZ * 1000 || API_fs_Hz < 0 ) {
        printf( "\nError: API sampling rate = %d out of range, valid range 8000 - 48000 \n \n", API_fs_Hz );
        exit( 0 );
    }

    tottime              = 0;
    totPackets           = 0;
    totActPackets        = 0;
    smplsSinceLastPacket = 0;
    sumBytes             = 0.0;
    sumActBytes          = 0.0;
    smplsSinceLastPacket = 0;
    
    while( 1 ) {
        /* Read input from file */
        counter = fread( in, sizeof( SKP_int16 ), ( frameSizeReadFromFile_ms * API_fs_Hz ) / 1000, speechInFile );
#ifdef _SYSTEM_IS_BIG_ENDIAN
        swap_endian( in, counter );
#endif
        if( ( SKP_int )counter < ( ( frameSizeReadFromFile_ms * API_fs_Hz ) / 1000 ) ) {
            break;
        }

        /* max payload size */
        nBytes = MAX_BYTES_PER_FRAME * MAX_INPUT_FRAMES;

        starttime = GetHighResolutionTime();

        /* Silk Encoder */
        ret = SKP_Silk_SDK_Encode( psEnc, &encControl, in, (SKP_int16)counter, payload, &nBytes );
        if( ret ) {
            printf( "\nSKP_Silk_Encode returned %d", ret );
        }

        tottime += GetHighResolutionTime() - starttime;

        /* Get packet size */
        packetSize_ms = ( SKP_int )( ( 1000 * ( SKP_int32 )encControl.packetSize ) / encControl.API_sampleRate );

        smplsSinceLastPacket += ( SKP_int )counter;
        
        if( ( ( 1000 * smplsSinceLastPacket ) / API_fs_Hz ) == packetSize_ms ) {
            /* Sends a dummy zero size packet in case of DTX period  */
            /* to make it work with the decoder test program.        */
            /* In practice should be handled by RTP sequence numbers */
            totPackets++;
            sumBytes  += nBytes;
            nrg = 0.0;
            for( k = 0; k < ( SKP_int )counter; k++ ) {
                nrg += in[ k ] * (double)in[ k ];
            }
            if( ( nrg / ( SKP_int )counter ) > 1e3 ) {
                sumActBytes += nBytes;
                totActPackets++;
            }

            /* Write payload size */
#ifdef _SYSTEM_IS_BIG_ENDIAN
            nBytes_LE = nBytes;
            swap_endian( &nBytes_LE, 1 );
            fwrite( &nBytes_LE, sizeof( SKP_int16 ), 1, bitOutFile );
#else
            fwrite( &nBytes, sizeof( SKP_int16 ), 1, bitOutFile );
#endif

            /* Write payload */
            fwrite( payload, sizeof( SKP_uint8 ), nBytes, bitOutFile );

            smplsSinceLastPacket = 0;
        
            if( !quiet ) {
                fprintf( stderr, "\rPackets encoded:                %d", totPackets );
            }
        }
    }

    /* Write dummy because it can not end with 0 bytes */
    nBytes = -1;

    /* Write payload size */
    if( !tencent ) {
        fwrite( &nBytes, sizeof( SKP_int16 ), 1, bitOutFile );
    }

    /* Free Encoder */
    free( psEnc );

    fclose( speechInFile );
    fclose( bitOutFile );

    filetime  = totPackets * 1e-3 * packetSize_ms;
    avg_rate  = 8.0 / packetSize_ms * sumBytes       / totPackets;
    act_rate  = 8.0 / packetSize_ms * sumActBytes    / totActPackets;
    if( !quiet ) {
        printf( "\nFile length:                    %.3f s", filetime );
        printf( "\nTime for encoding:              %.3f s (%.3f%% of realtime)", 1e-6 * tottime, 1e-4 * tottime / filetime );
        printf( "\nAverage bitrate:                %.3f kbps", avg_rate  );
        printf( "\nActive bitrate:                 %.3f kbps", act_rate  );
        printf( "\n\n" );
    } else {
        /* print time and % of realtime */
        printf("%.3f %.3f %d ", 1e-6 * tottime, 1e-4 * tottime / filetime, totPackets );
        /* print average and active bitrates */
        printf( "%.3f %.3f \n", avg_rate, act_rate );
    }

    return 0;
}
