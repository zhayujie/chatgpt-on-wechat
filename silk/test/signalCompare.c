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

/*
* Compare two audio signals and compute weighted SNR difference
*/

#ifdef _WIN32
#define _CRT_SECURE_NO_DEPRECATE    1
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "SKP_Silk_SigProc_FIX.h"

#define FRAME_LENGTH_MS         10
#define WIN_LENGTH_MS           20
#define BW_EXPANSION            0.7f

#define MAX_FS_KHZ              48
#define LPC_ORDER               10
#define SNR_THRESHOLD           15.0

#ifdef  __cplusplus
extern "C"
{
#endif
/* Internally used functions */
void Autocorrelation( 
    SKP_float *results,                 /* o    result (length correlationCount)            */
    const SKP_float *inputData,         /* i    input data to correlate                     */
    SKP_int inputDataSize,              /* i    length of input                             */
    SKP_int correlationCount            /* i    number of correlation taps to compute       */
);

/* inner product of two SKP_float arrays, with result as double */
double Inner_product( 
    const SKP_float     *data1, 
    const SKP_float     *data2, 
    SKP_int             dataSize
);
/* Solve the normal equations using the Levinson-Durbin recursion */
SKP_float Levinsondurbin(               /* O    prediction error energy                     */
    SKP_float       A[],                /* O    prediction coefficients [order]             */
    const SKP_float corr[],             /* I    input auto-correlations [order + 1]         */
    const SKP_int   order               /* I    prediction order                            */
);

/* Chirp (bw expand) LP AR filter */
void Bwexpander( 
    SKP_float *ar,                      /* io   AR filter to be expanded (without leading 1)    */
    const SKP_int d,                    /* i    length of ar                                    */
    const SKP_float chirp               /* i    chirp factor (typically in range (0..1) )       */
);

#ifdef  __cplusplus
}
#endif

static void print_usage(char* argv[]) {
    printf("\nusage: %s ref.pcm test.pcm [settings]\n", argv[ 0 ]);
    printf("\nref.pcm       : Reference file");
    printf("\ntest.pcm      : File to be tested, should be of same length as ref.pcm");
    printf("\n   settings:");
    printf("\n-diff         : Only determine bit-exactness");
    printf("\n-fs <Hz>      : Sampling rate in Hz, max: %d; default: 48000", MAX_FS_KHZ * 1000 );
    printf("\n");
}


int main(int argc, char* argv[])
{
    SKP_int   args, n, i, counterRef, counterTest;
    char      testInFileName[150], refInFileName[150];
    FILE      *refInFile, *testInFile;
    SKP_int   nFrames = 0, isUnequal = 0;
    SKP_int   diff = 0, Fs_kHz;
    SKP_int32 Fs_Hz = 24000;
    SKP_float c, refWhtnd, testWhtnd, refNrg, diffNrg;
    double    SNR = 0.0;
    SKP_int16 refIn[WIN_LENGTH_MS * MAX_FS_KHZ], testIn[WIN_LENGTH_MS * MAX_FS_KHZ];
    SKP_float refWin[WIN_LENGTH_MS * MAX_FS_KHZ];
    SKP_float autoCorr[LPC_ORDER + 1], LPC_Coef[LPC_ORDER];

    if (argc < 3) {
        print_usage(argv);
        exit(0);
    }

    /* get arguments */
    args = 1;
    strcpy(refInFileName, argv[args]);
    args++;
    strcpy(testInFileName, argv[args]);
    args++;
    while(args < argc ) {
        if (SKP_STR_CASEINSENSITIVE_COMPARE(argv[args], "-diff") == 0) {
            diff = 1;
            args++;
        }else if (SKP_STR_CASEINSENSITIVE_COMPARE(argv[args], "-fs") == 0) {
            sscanf(argv[args+1], "%d", &Fs_Hz);
            args += 2;
        } else {
            printf("Error: unrecognized setting: %s\n\n", argv[args]);
            print_usage(argv);
            exit(0);
        }
    }

    Fs_kHz = SKP_DIV32_16( Fs_Hz, 1000 );

    if( Fs_kHz > MAX_FS_KHZ ) {
        printf("Error: sampling rate too high: %d\n\n", Fs_kHz);
        print_usage(argv);
        exit(0);
    }

    printf("Reference:  %s\n", refInFileName);
    //printf("Test:       %s\n", testInFileName);

    /* open files */
    refInFile = fopen(refInFileName, "rb");
    if (refInFile==NULL) {
        printf("Error: could not open input file %s\n", refInFileName);
        exit(0);
    } 
    testInFile = fopen(testInFileName, "rb");
    if (testInFile==NULL) {
        printf("Error: could not open input file %s\n", testInFileName);
        exit(0);
    }

    SKP_memset( refIn,  0, sizeof(refIn) );
    SKP_memset( testIn, 0, sizeof(testIn) );

    while(1) {
        /* Read inputs */
        counterRef  = (SKP_int)fread(&refIn[(WIN_LENGTH_MS - FRAME_LENGTH_MS) * Fs_kHz], 
            sizeof(SKP_int16), FRAME_LENGTH_MS * Fs_kHz, refInFile);
        counterTest = (SKP_int)fread(&testIn[(WIN_LENGTH_MS - FRAME_LENGTH_MS) * Fs_kHz], 
            sizeof(SKP_int16), FRAME_LENGTH_MS * Fs_kHz, testInFile);
        if(counterRef != FRAME_LENGTH_MS * Fs_kHz || counterTest != FRAME_LENGTH_MS * Fs_kHz){
            break;
        }

        /* test for bit-exactness */
        for( n = 0; n < FRAME_LENGTH_MS * Fs_kHz; n++ ) {
            if( refIn[(WIN_LENGTH_MS - FRAME_LENGTH_MS) * Fs_kHz + n] != 
                testIn[(WIN_LENGTH_MS - FRAME_LENGTH_MS) * Fs_kHz + n] ) {
                    isUnequal = 1;
                    break;
            }
        }

        /* apply sine window */
        for( n = 0; n < WIN_LENGTH_MS * Fs_kHz; n++ ) {
            c = (SKP_float)sin( 3.14159265 * (n + 1) / (WIN_LENGTH_MS * Fs_kHz + 1) );
            refWin[n]  = refIn[n]  * c;
        }

        /* LPC analysis on reference signal */

        /* Calculate auto correlation */
        Autocorrelation(autoCorr, refWin, WIN_LENGTH_MS * Fs_kHz, LPC_ORDER + 1);

        /* Add white noise */
        autoCorr[ 0 ] += autoCorr[ 0 ] * 1e-6f + 1.0f; 

        /* Convert correlations to prediction coefficients */
        Levinsondurbin(LPC_Coef, autoCorr, LPC_ORDER);

        /* Bandwdith expansion */
        Bwexpander(LPC_Coef, LPC_ORDER, BW_EXPANSION);

        /* Filter both signals */
        refNrg = 1.0f;
        diffNrg = 1e-10f;
        for( n = (WIN_LENGTH_MS - FRAME_LENGTH_MS) / 2 * Fs_kHz; 
             n < (WIN_LENGTH_MS + FRAME_LENGTH_MS) / 2 * Fs_kHz; n++ ) {
                refWhtnd = refIn[n];
                testWhtnd = testIn[n];
                for( i = 0; i < LPC_ORDER; i++ ) {
                    refWhtnd  -= LPC_Coef[ i ] * refIn[n - i - 1];
                    testWhtnd -= LPC_Coef[ i ] * testIn[n - i - 1];
                }
                refNrg += refWhtnd * refWhtnd;
                diffNrg += (refWhtnd - testWhtnd) * (refWhtnd - testWhtnd);
        }

        /* weighted SNR */
        if( refNrg > FRAME_LENGTH_MS * Fs_kHz ) {
            SNR += 10.0 * log10( refNrg / diffNrg );
            nFrames++;
        }

        /* Update Buffer */
        SKP_memmove( refIn,  &refIn[FRAME_LENGTH_MS * Fs_kHz],  (WIN_LENGTH_MS - FRAME_LENGTH_MS) * Fs_kHz * sizeof(SKP_int16));
        SKP_memmove( testIn, &testIn[FRAME_LENGTH_MS * Fs_kHz], (WIN_LENGTH_MS - FRAME_LENGTH_MS) * Fs_kHz * sizeof(SKP_int16));
    }

    if( diff ) {
        if( isUnequal ) {
            printf("Signals differ\n");
        } else {
            if(counterRef != counterTest){
                printf("Warning: signals differ in length\n");
            }
            printf("Signals are bit-exact          PASS\n");
        }
    } else {
        if( nFrames == 0 ) {
            printf("At least one signal too short or not loud enough\n");
            exit(0);
        }
        if(counterRef != counterTest){
            printf("Warning: signals differ in length\n");
        }
        if( isUnequal == 0 ) {
            printf("Signals are bit-exact          PASS\n");
        } else {
            printf("Average weighted SNR: %4.1f dB  ", SNR / nFrames);
            if( SNR / nFrames < SNR_THRESHOLD ) {
                printf("FAIL\n");
            } else {
                printf("PASS\n");
            }
        }
    }
    printf("\n");

    /* Close Files */
    fclose(refInFile);
    fclose(testInFile);

    return 0;
}

/* compute autocorrelation */
void Autocorrelation( 
    SKP_float *results,                 /* o    result (length correlationCount)            */
    const SKP_float *inputData,         /* i    input data to correlate                     */
    SKP_int inputDataSize,              /* i    length of input                             */
    SKP_int correlationCount            /* i    number of correlation taps to compute       */
)
{
    SKP_int i;

    if (correlationCount > inputDataSize) {
        correlationCount = inputDataSize;
    }

    for( i = 0; i < correlationCount; i++ ) {
        results[ i ] =  (SKP_float)Inner_product( inputData, inputData + i, inputDataSize - i );
    }
}

/* inner product of two SKP_float arrays, with result as double */
double Inner_product( 
    const SKP_float     *data1, 
    const SKP_float     *data2, 
    SKP_int             dataSize
)
{
    SKP_int  i, dataSize4;
    double   result;

    /* 4x unrolled loop */
    result = 0.0f;
    dataSize4 = dataSize & 0xFFFC;
    for( i = 0; i < dataSize4; i += 4 ) {
        result += data1[ i + 0 ] * data2[ i + 0 ] + 
                  data1[ i + 1 ] * data2[ i + 1 ] +
                  data1[ i + 2 ] * data2[ i + 2 ] +
                  data1[ i + 3 ] * data2[ i + 3 ];
    }

    /* add any remaining products */
    for( ; i < dataSize; i++ ) {
        result += data1[ i ] * data2[ i ];
    }

    return result;
}

/* Solve the normal equations using the Levinson-Durbin recursion */
SKP_float Levinsondurbin(               /* O    prediction error energy                     */
    SKP_float       A[],                /* O    prediction coefficients [order]             */
    const SKP_float corr[],             /* I    input auto-correlations [order + 1]         */
    const SKP_int   order               /* I    prediction order                            */
)
{
    SKP_int   i, mHalf, m;
    SKP_float min_nrg, nrg, t, km, Atmp1, Atmp2;
    
    min_nrg = 1e-12f * corr[ 0 ] + 1e-9f;
    nrg = corr[ 0 ];
    nrg = SKP_max(min_nrg, nrg);
    A[ 0 ] = corr[ 1 ] / nrg;
    nrg -= A[ 0 ] * corr[ 1 ];
    nrg = SKP_max(min_nrg, nrg);

    for( m = 1; m < order; m++ )
    {
        t = corr[ m + 1 ];
        for( i = 0; i < m; i++ ) {
            t -= A[ i ] * corr[ m - i ];
        }

        /* reflection coefficient */
        km = t / nrg;

        /* residual energy */
        nrg -= km * t;
        nrg = SKP_max(min_nrg, nrg);

        mHalf = m >> 1;
        for( i = 0; i < mHalf; i++ ) {
            Atmp1 = A[ i ];
            Atmp2 = A[ m - i - 1 ];
            A[ m - i - 1 ] -= km * Atmp1;
            A[ i ]         -= km * Atmp2;
        }
        if( m & 1 ) {
            A[ mHalf ]     -= km * A[ mHalf ];
        }
        A[ m ] = km;
    }

    /* return the residual energy */
    return nrg;
}

/* Chirp (bw expand) LP AR filter */
void Bwexpander( 
    SKP_float *ar,                      /* io   AR filter to be expanded (without leading 1)    */
    const SKP_int d,                    /* i    length of ar                                    */
    const SKP_float chirp               /* i    chirp factor (typically in range (0..1) )       */
)
{
    SKP_int   i;
    SKP_float cfac = chirp;

    for( i = 0; i < d - 1; i++ ) {
        ar[ i ] *=  cfac;
        cfac    *=  chirp;
    }
    ar[ d - 1 ] *=  cfac;
}
