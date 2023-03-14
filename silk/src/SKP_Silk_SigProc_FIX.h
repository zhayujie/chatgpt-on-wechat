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

#ifndef _SKP_SILK_SIGPROC_FIX_H_
#define _SKP_SILK_SIGPROC_FIX_H_

#ifdef  __cplusplus
extern "C"
{
#endif

#define SKP_Silk_MAX_ORDER_LPC            16                    /* max order of the LPC analysis in schur() and k2a()    */
#define SKP_Silk_MAX_CORRELATION_LENGTH   640                   /* max input length to the correlation                    */
#include "SKP_Silk_typedef.h"
#include <string.h>
#include <stdlib.h>                                            /* for abs() */
#include "SKP_Silk_resampler_structs.h"

#ifndef NO_ASM
#	if defined (__ARM_ARCH_4__) || defined (__ARM_ARCH_4T__) || defined (__ARM_ARCH_5__) || defined (__ARM_ARCH_5T__)
#		define EMBEDDED_ARM 4
#		define EMBEDDED_ARMv4
#		include "SKP_Silk_macros_arm.h"
#	elif defined (__ARM_ARCH_5TE__) || defined (__ARM_ARCH_5TEJ__)
#		define EMBEDDED_ARM 5
#		define EMBEDDED_ARMv5
#		include "SKP_Silk_macros_arm.h"	
#	elif defined (__ARM_ARCH_6__) ||defined (__ARM_ARCH_6J__) || defined (__ARM_ARCH_6Z__) || defined (__ARM_ARCH_6K__) || defined(__ARM_ARCH_6ZK__) || defined(__ARM_ARCH_6T2__)
#		define EMBEDDED_ARM 6
#		define EMBEDDED_ARMv6
#		include "SKP_Silk_macros_arm.h"
#	elif defined (__ARM_ARCH_7A__) && defined (__ARM_NEON__)
#		define EMBEDDED_ARM 7
#		define EMBEDDED_ARMv6
#		include "SKP_Silk_macros_arm.h"
#	elif defined (__ARM_ARCH_7A__)
#		define EMBEDDED_ARM 6
#		define EMBEDDED_ARMv6
#		include "SKP_Silk_macros_arm.h"
#	else
#		include "SKP_Silk_macros.h"
#	endif
#else
#	include "SKP_Silk_macros.h"
#endif



/********************************************************************/
/*                    SIGNAL PROCESSING FUNCTIONS                   */
/********************************************************************/

/*!
 * Initialize/reset the resampler state for a given pair of input/output sampling rates 
*/
SKP_int SKP_Silk_resampler_init( 
	SKP_Silk_resampler_state_struct	*S,		    /* I/O: Resampler state 			*/
	SKP_int32							Fs_Hz_in,	/* I:	Input sampling rate (Hz)	*/
	SKP_int32							Fs_Hz_out	/* I:	Output sampling rate (Hz)	*/
);


/*!
 * Clear the states of all resampling filters, without resetting sampling rate ratio 
 */
SKP_int SKP_Silk_resampler_clear( 
	SKP_Silk_resampler_state_struct	*S		    /* I/O: Resampler state 			*/
);

/*!
 * Resampler: convert from one sampling rate to another
 */
SKP_int SKP_Silk_resampler( 
	SKP_Silk_resampler_state_struct	*S,		    /* I/O: Resampler state 			*/
	SKP_int16							out[],	    /* O:	Output signal 				*/
	const SKP_int16						in[],	    /* I:	Input signal				*/
	SKP_int32							inLen	    /* I:	Number of input samples		*/
);

/*!
 Upsample 2x, low quality 
 */
void SKP_Silk_resampler_up2(
    SKP_int32                           *S,         /* I/O: State vector [ 2 ]                  */
    SKP_int16                           *out,       /* O:   Output signal [ 2 * len ]           */
    const SKP_int16                     *in,        /* I:   Input signal [ len ]                */
    SKP_int32                           len         /* I:   Number of input samples             */
);

/*!
* Downsample 2x, mediocre quality 
*/
void SKP_Silk_resampler_down2(
    SKP_int32                           *S,         /* I/O: State vector [ 2 ]                  */
    SKP_int16                           *out,       /* O:   Output signal [ len ]               */
    const SKP_int16                     *in,        /* I:   Input signal [ floor(len/2) ]       */
    SKP_int32                           inLen       /* I:   Number of input samples             */
);


/*!
 * Downsample by a factor 2/3, low quality
*/
void SKP_Silk_resampler_down2_3(
    SKP_int32                           *S,         /* I/O: State vector [ 6 ]                  */
    SKP_int16                           *out,       /* O:   Output signal [ floor(2*inLen/3) ]  */
    const SKP_int16                     *in,        /* I:   Input signal [ inLen ]              */
    SKP_int32                           inLen       /* I:   Number of input samples             */
);

/*!
 * Downsample by a factor 3, low quality
*/
void SKP_Silk_resampler_down3(
    SKP_int32                           *S,         /* I/O: State vector [ 8 ]                  */
    SKP_int16                           *out,       /* O:   Output signal [ floor(inLen/3) ]    */
    const SKP_int16                     *in,        /* I:   Input signal [ inLen ]              */
    SKP_int32                           inLen       /* I:   Number of input samples             */
);

/*! 
 * second order ARMA filter
 * can handle (slowly) varying coefficients 
 */
void SKP_Silk_biquad(
    const SKP_int16      *in,          /* I:   input signal                */
    const SKP_int16      *B,           /* I:   MA coefficients, Q13 [3]    */
    const SKP_int16      *A,           /* I:   AR coefficients, Q13 [2]    */
          SKP_int32      *S,           /* I/O: state vector [2]            */
          SKP_int16      *out,         /* O:   output signal               */
    const SKP_int32      len           /* I:   signal length               */
);
/*!
 * Second order ARMA filter; 
 * slower than biquad() but uses more precise coefficients
 * can handle (slowly) varying coefficients 
 */
void SKP_Silk_biquad_alt(
    const SKP_int16     *in,           /* I:    Input signal                 */
    const SKP_int32     *B_Q28,        /* I:    MA coefficients [3]          */
    const SKP_int32     *A_Q28,        /* I:    AR coefficients [2]          */
    SKP_int32           *S,            /* I/O:  State vector [2]             */
    SKP_int16           *out,          /* O:    Output signal                */
    const SKP_int32     len            /* I:    Signal length (must be even) */
);

/*! 
 * variable order MA filter. Prediction error filter implementation. Coeficients negated and starting with coef to x[n - 1]
 */
void SKP_Silk_MA_Prediction(
    const SKP_int16      *in,          /* I:   Input signal                                */
    const SKP_int16      *B,           /* I:   MA prediction coefficients, Q12 [order]     */
    SKP_int32            *S,           /* I/O: State vector [order]                        */
    SKP_int16            *out,         /* O:   Output signal                               */
    const SKP_int32      len,          /* I:   Signal length                               */
    const SKP_int32      order         /* I:   Filter order                                */
);

/*!
 * 16th order AR filter for LPC synthesis, coefficients are in Q12
 */
void SKP_Silk_LPC_synthesis_order16(
    const SKP_int16      *in,          /* I:   excitation signal                            */
    const SKP_int16      *A_Q12,       /* I:   AR coefficients [16], between -8_Q0 and 8_Q0 */
    const SKP_int32      Gain_Q26,     /* I:   gain                                         */
          SKP_int32      *S,           /* I/O: state vector [16]                            */
          SKP_int16      *out,         /* O:   output signal                                */
    const SKP_int32      len           /* I:   signal length, must be multiple of 16        */
);

/* variable order MA prediction error filter. */
/* Inverse filter of SKP_Silk_LPC_synthesis_filter */
void SKP_Silk_LPC_analysis_filter(
    const SKP_int16      *in,          /* I:   Input signal                                */
    const SKP_int16      *B,           /* I:   MA prediction coefficients, Q12 [order]     */
    SKP_int16            *S,           /* I/O: State vector [order]                        */
    SKP_int16            *out,         /* O:   Output signal                               */
    const SKP_int32      len,          /* I:   Signal length                               */
    const SKP_int32      Order         /* I:   Filter order                                */
);

/* even order AR filter */
void SKP_Silk_LPC_synthesis_filter(
    const SKP_int16      *in,          /* I:   excitation signal                               */
    const SKP_int16      *A_Q12,       /* I:   AR coefficients [Order], between -8_Q0 and 8_Q0 */
    const SKP_int32      Gain_Q26,     /* I:   gain                                            */
    SKP_int32            *S,           /* I/O: state vector [Order]                            */
    SKP_int16            *out,         /* O:   output signal                                   */
    const SKP_int32      len,          /* I:   signal length                                   */
    const SKP_int        Order         /* I:   filter order, must be even                      */
);

/* Chirp (bandwidth expand) LP AR filter */
void SKP_Silk_bwexpander( 
    SKP_int16            *ar,          /* I/O  AR filter to be expanded (without leading 1)    */
    const SKP_int        d,            /* I    Length of ar                                    */
    SKP_int32            chirp_Q16     /* I    Chirp factor (typically in the range 0 to 1)    */
);

/* Chirp (bandwidth expand) LP AR filter */
void SKP_Silk_bwexpander_32( 
    SKP_int32            *ar,          /* I/O  AR filter to be expanded (without leading 1)    */
    const SKP_int        d,            /* I    Length of ar                                    */
    SKP_int32            chirp_Q16     /* I    Chirp factor in Q16                             */
);

/* Compute inverse of LPC prediction gain, and                           */
/* test if LPC coefficients are stable (all poles within unit circle)    */
SKP_int SKP_Silk_LPC_inverse_pred_gain( /* O:  Returns 1 if unstable, otherwise 0          */
    SKP_int32            *invGain_Q30,  /* O:  Inverse prediction gain, Q30 energy domain  */
    const SKP_int16      *A_Q12,        /* I:  Prediction coefficients, Q12 [order]        */
    const SKP_int        order          /* I:  Prediction order                            */
);

SKP_int SKP_Silk_LPC_inverse_pred_gain_Q24( /* O:   Returns 1 if unstable, otherwise 0      */
    SKP_int32           *invGain_Q30,   /* O:   Inverse prediction gain, Q30 energy domain  */
    const SKP_int32     *A_Q24,         /* I:   Prediction coefficients, Q24 [order]        */
    const SKP_int       order           /* I:   Prediction order                            */
);

/* split signal in two decimated bands using first-order allpass filters */
void SKP_Silk_ana_filt_bank_1(
    const SKP_int16      *in,           /* I:   Input signal [N]        */
    SKP_int32            *S,            /* I/O: State vector [2]        */
    SKP_int16            *outL,         /* O:   Low band [N/2]          */
    SKP_int16            *outH,         /* O:   High band [N/2]         */
    SKP_int32            *scratch,      /* I:   Scratch memory [3*N/2]  */
    const SKP_int32      N              /* I:   Number of input samples */
);

/********************************************************************/
/*                        SCALAR FUNCTIONS                          */
/********************************************************************/

/* Approximation of 128 * log2() (very close inverse of approx 2^() below) */
/* Convert input to a log scale    */
SKP_int32 SKP_Silk_lin2log(const SKP_int32 inLin);        /* I: Input in linear scale        */

/* Approximation of a sigmoid function */
SKP_int SKP_Silk_sigm_Q15(SKP_int in_Q5);

/* approximation of 2^() (exact inverse of approx log2() above) */
/* convert input to a linear scale    */ 
SKP_int32 SKP_Silk_log2lin(const SKP_int32 inLog_Q7);    /* I: input on log scale */ 

/* Function that returns the maximum absolut value of the input vector */
SKP_int16 SKP_Silk_int16_array_maxabs(  /* O   Maximum absolute value, max: 2^15-1   */
    const SKP_int16     *vec,           /* I   Input vector  [len]                   */ 
    const SKP_int32     len             /* I   Length of input vector                */
);

/* Compute number of bits to right shift the sum of squares of a vector    */
/* of int16s to make it fit in an int32                                    */
void SKP_Silk_sum_sqr_shift(
    SKP_int32           *energy,        /* O   Energy of x, after shifting to the right            */
    SKP_int             *shift,         /* O   Number of bits right shift applied to energy        */
    const SKP_int16     *x,             /* I   Input vector                                        */
    SKP_int             len             /* I   Length of input vector                              */
);

/* Calculates the reflection coefficients from the correlation sequence    */
/* Faster than schur64(), but much less accurate.                          */
/* Uses SMLAWB(), requiring armv5E and higher.                             */ 
SKP_int32 SKP_Silk_schur(               /* O:    Returns residual energy                   */
    SKP_int16            *rc_Q15,       /* O:    reflection coefficients [order] Q15       */
    const SKP_int32      *c,            /* I:    correlations [order+1]                    */
    const SKP_int32      order          /* I:    prediction order                          */
);

/* Calculates the reflection coefficients from the correlation sequence    */
/* Slower than schur(), but more accurate.                                 */
/* Uses SMULL(), available on armv4                                        */
SKP_int32 SKP_Silk_schur64(             /* O:  returns residual energy                     */
    SKP_int32           rc_Q16[],       /* O:  Reflection coefficients [order] Q16         */
    const SKP_int32     c[],            /* I:  Correlations [order+1]                      */
    SKP_int32           order           /* I:  Prediction order                            */
);

/* Step up function, converts reflection coefficients to prediction coefficients */
void SKP_Silk_k2a(
    SKP_int32           *A_Q24,         /* O:  Prediction coefficients [order] Q24         */
    const SKP_int16     *rc_Q15,        /* I:  Reflection coefficients [order] Q15         */
    const SKP_int32     order           /* I:  Prediction order                            */
);

/* Step up function, converts reflection coefficients to prediction coefficients */
void SKP_Silk_k2a_Q16(
    SKP_int32           *A_Q24,         /* O:  Prediction coefficients [order] Q24         */
    const SKP_int32     *rc_Q16,        /* I:  Reflection coefficients [order] Q16         */
    const SKP_int32     order           /* I:  Prediction order                            */
);

/* Apply sine window to signal vector.                                      */
/* Window types:                                                            */
/*    1 -> sine window from 0 to pi/2                                       */
/*    2 -> sine window from pi/2 to pi                                      */
/* Every other sample is linearly interpolated, for speed.                  */
void SKP_Silk_apply_sine_window(
    SKP_int16                        px_win[],            /* O    Pointer to windowed signal                  */
    const SKP_int16                  px[],                /* I    Pointer to input signal                     */
    const SKP_int                    win_type,            /* I    Selects a window type                       */
    const SKP_int                    length               /* I    Window length, multiple of 4                */
);

/* Compute autocorrelation */
void SKP_Silk_autocorr( 
    SKP_int32           *results,       /* O  Result (length correlationCount)            */
    SKP_int             *scale,         /* O  Scaling of the correlation vector           */
    const SKP_int16     *inputData,     /* I  Input data to correlate                     */
    const SKP_int       inputDataSize,  /* I  Length of input                             */
    const SKP_int       correlationCount /* I  Number of correlation taps to compute      */
);

/* Pitch estimator */
#define SKP_Silk_PITCH_EST_MIN_COMPLEX        0
#define SKP_Silk_PITCH_EST_MID_COMPLEX        1
#define SKP_Silk_PITCH_EST_MAX_COMPLEX        2

void SKP_Silk_decode_pitch(
    SKP_int            lagIndex,        /* I                                              */
    SKP_int            contourIndex,    /* O                                              */
    SKP_int            pitch_lags[],    /* O 4 pitch values                               */
    SKP_int            Fs_kHz           /* I sampling frequency (kHz)                     */
);

SKP_int SKP_Silk_pitch_analysis_core(    /* O    Voicing estimate: 0 voiced, 1 unvoiced                      */
    const SKP_int16  *signal,            /* I    Signal of length PITCH_EST_FRAME_LENGTH_MS*Fs_kHz           */
    SKP_int          *pitch_out,         /* O    4 pitch lag values                                          */
    SKP_int          *lagIndex,          /* O    Lag Index                                                   */
    SKP_int          *contourIndex,      /* O    Pitch contour Index                                         */
    SKP_int          *LTPCorr_Q15,       /* I/O  Normalized correlation; input: value from previous frame    */
    SKP_int          prevLag,            /* I    Last lag of previous frame; set to zero is unvoiced         */
    const SKP_int32  search_thres1_Q16,  /* I    First stage threshold for lag candidates 0 - 1              */
    const SKP_int    search_thres2_Q15,  /* I    Final threshold for lag candidates 0 - 1                    */
    const SKP_int    Fs_kHz,             /* I    Sample frequency (kHz)                                      */
    const SKP_int    complexity,         /* I    Complexity setting, 0-2, where 2 is highest                 */
	const SKP_int	 forLJC			     /* I	 1 if this function is called from LJC code, 0 otherwise.    */
);

/* parameter defining the size and accuracy of the piecewise linear    */
/* cosine approximatin table.                                        */

#define LSF_COS_TAB_SZ_FIX      128
/* rom table with cosine values */
extern const SKP_int SKP_Silk_LSFCosTab_FIX_Q12[ LSF_COS_TAB_SZ_FIX + 1 ];

/* Compute Normalized Line Spectral Frequencies (NLSFs) from whitening filter coefficients        */
/* If not all roots are found, the a_Q16 coefficients are bandwidth expanded until convergence.    */
void SKP_Silk_A2NLSF(
    SKP_int            *NLSF,            /* O    Normalized Line Spectral Frequencies, Q15 (0 - (2^15-1)), [d] */
    SKP_int32          *a_Q16,           /* I/O  Monic whitening filter coefficients in Q16 [d]                */
    const SKP_int      d                 /* I    Filter order (must be even)                                   */
);

/* compute whitening filter coefficients from normalized line spectral frequencies */
void SKP_Silk_NLSF2A(
    SKP_int16          *a,               /* o    monic whitening filter coefficients in Q12,  [d]    */
    const SKP_int      *NLSF,            /* i    normalized line spectral frequencies in Q15, [d]    */
    const SKP_int      d                 /* i    filter order (should be even)                       */
);

void SKP_Silk_insertion_sort_increasing(
    SKP_int32            *a,            /* I/O   Unsorted / Sorted vector                */
    SKP_int              *index,        /* O:    Index vector for the sorted elements    */
    const SKP_int        L,             /* I:    Vector length                           */
    const SKP_int        K              /* I:    Number of correctly sorted positions    */
);

void SKP_Silk_insertion_sort_decreasing_int16(
    SKP_int16            *a,            /* I/O:  Unsorted / Sorted vector                */
    SKP_int              *index,        /* O:    Index vector for the sorted elements    */
    const SKP_int        L,             /* I:    Vector length                           */
    const SKP_int        K              /* I:    Number of correctly sorted positions    */
);

void SKP_Silk_insertion_sort_increasing_all_values(
     SKP_int             *a,            /* I/O:  Unsorted / Sorted vector                */
     const SKP_int       L              /* I:    Vector length                           */
);

/* NLSF stabilizer, for a single input data vector */
void SKP_Silk_NLSF_stabilize(
          SKP_int        *NLSF_Q15,      /* I/O:  Unstable/stabilized normalized LSF vector in Q15 [L]                    */
    const SKP_int        *NDeltaMin_Q15, /* I:    Normalized delta min vector in Q15, NDeltaMin_Q15[L] must be >= 1 [L+1] */
    const SKP_int        L               /* I:    Number of NLSF parameters in the input vector                           */
);

/* Laroia low complexity NLSF weights */
void SKP_Silk_NLSF_VQ_weights_laroia(
    SKP_int              *pNLSFW_Q6,     /* O:    Pointer to input vector weights            [D x 1]       */
    const SKP_int        *pNLSF_Q15,     /* I:    Pointer to input vector                    [D x 1]       */
    const SKP_int        D               /* I:    Input vector dimension (even)                            */
);

/* Compute reflection coefficients from input signal */
void SKP_Silk_burg_modified(        
    SKP_int32            *res_nrg,           /* O   residual energy                                                 */
    SKP_int              *res_nrgQ,          /* O   residual energy Q value                                         */
    SKP_int32            A_Q16[],            /* O   prediction coefficients (length order)                          */
    const SKP_int16      x[],                /* I   input signal, length: nb_subfr * ( D + subfr_length )           */
    const SKP_int        subfr_length,       /* I   input signal subframe length (including D preceeding samples)   */
    const SKP_int        nb_subfr,           /* I   number of subframes stacked in x                                */
    const SKP_int32      WhiteNoiseFrac_Q32, /* I   fraction added to zero-lag autocorrelation                      */
    const SKP_int        D                   /* I   order                                                           */
);

/* Copy and multiply a vector by a constant */
void SKP_Silk_scale_copy_vector16( 
    SKP_int16            *data_out, 
    const SKP_int16      *data_in, 
    SKP_int32            gain_Q16,           /* I:   gain in Q16   */
    const SKP_int        dataSize            /* I:   length        */
);

/* Some for the LTP related function requires Q26 to work.*/
void SKP_Silk_scale_vector32_Q26_lshift_18( 
    SKP_int32            *data1,             /* I/O: Q0/Q18        */
    SKP_int32            gain_Q26,           /* I:   Q26           */
    SKP_int              dataSize            /* I:   length        */
);

/********************************************************************/
/*                        INLINE ARM MATH                             */
/********************************************************************/

/*    return sum(inVec1[i]*inVec2[i])    */
/*    inVec1 and inVec2 should be increasing ordered, and starting address should be 4 byte aligned. (a factor of 4)*/
SKP_int32 SKP_Silk_inner_prod_aligned(
    const SKP_int16* const inVec1,           /* I   input vector 1    */ 
    const SKP_int16* const inVec2,           /* I   input vector 2    */
    const SKP_int          len               /* I   vector lengths    */
);

SKP_int64 SKP_Silk_inner_prod16_aligned_64(
    const SKP_int16        *inVec1,          /* I   input vector 1    */
    const SKP_int16        *inVec2,          /* I   input vector 2    */
    const SKP_int          len               /* I   vector lengths    */
);
/********************************************************************/
/*                                MACROS                            */
/********************************************************************/

/* Rotate a32 right by 'rot' bits. Negative rot values result in rotating
   left. Output is 32bit int.
   Note: contemporary compilers recognize the C expressions below and
   compile them into 'ror' instructions if available. No need for inline ASM! */
#if defined(EMBEDDED_MIPS)
/* For MIPS (and most likely for ARM! and >=i486) we don't have to handle
   negative rot's as only 5 bits of rot are encoded into ROR instructions. */
SKP_INLINE SKP_int32 SKP_ROR32(SKP_int32 a32, SKP_int rot)
{
    SKP_uint32 _x = (SKP_uint32) a32;
    SKP_uint32 _r = (SKP_uint32) rot;
    return (SKP_int32) ((_x << (32 - _r)) | (_x >> _r));
}
#else
/* PPC must use this generic implementation. */
SKP_INLINE SKP_int32 SKP_ROR32( SKP_int32 a32, SKP_int rot )
{
    SKP_uint32 x = (SKP_uint32) a32;
    SKP_uint32 r = (SKP_uint32) rot;
    SKP_uint32 m = (SKP_uint32) -rot;
    if(rot <= 0)
        return (SKP_int32) ((x << m) | (x >> (32 - m)));
    else
        return (SKP_int32) ((x << (32 - r)) | (x >> r));
}
#endif

/* Allocate SKP_int16 alligned to 4-byte memory address */
#if EMBEDDED_ARM
#if defined(_WIN32) && defined(_M_ARM)
#define SKP_DWORD_ALIGN __declspec(align(4))
#else
#define SKP_DWORD_ALIGN __attribute__((aligned(4)))
#endif
#else
#define SKP_DWORD_ALIGN
#endif

/* Useful Macros that can be adjusted to other platforms */
#define SKP_memcpy(a, b, c)                memcpy((a), (b), (c))    /* Dest, Src, ByteCount */
#define SKP_memset(a, b, c)                memset((a), (b), (c))    /* Dest, value, ByteCount */
#define SKP_memmove(a, b, c)               memmove((a), (b), (c))    /* Dest, Src, ByteCount */
/* fixed point macros */

// (a32 * b32) output have to be 32bit int
#define SKP_MUL(a32, b32)                  ((a32) * (b32))

// (a32 * b32) output have to be 32bit uint
#define SKP_MUL_uint(a32, b32)             SKP_MUL(a32, b32)

// a32 + (b32 * c32) output have to be 32bit int
#define SKP_MLA(a32, b32, c32)             SKP_ADD32((a32),((b32) * (c32)))

/* ((a32 >> 16)  * (b32 >> 16)) output have to be 32bit int */
#define SKP_SMULTT(a32, b32)			(((a32) >> 16) * ((b32) >> 16))

/* a32 + ((a32 >> 16)  * (b32 >> 16)) output have to be 32bit int */
#define SKP_SMLATT(a32, b32, c32)          SKP_ADD32((a32),((b32) >> 16) * ((c32) >> 16))

#define SKP_SMLALBB(a64, b16, c16)         SKP_ADD64((a64),(SKP_int64)((SKP_int32)(b16) * (SKP_int32)(c16)))

// (a32 * b32)
#define SKP_SMULL(a32, b32)                ((SKP_int64)(a32) * /*(SKP_int64)*/(b32))

/* Adds two signed 32-bit values in a way that can overflow, while not relying on undefined behaviour
   (just standard two's complement implementation-specific behaviour) */
#define SKP_ADD32_ovflw(a, b)               ((SKP_int32)((SKP_uint32)(a) + (SKP_uint32)(b)))
/* Subtractss two signed 32-bit values in a way that can overflow, while not relying on undefined behaviour
   (just standard two's complement implementation-specific behaviour) */
#define SKP_SUB32_ovflw(a, b)               ((SKP_int32)((SKP_uint32)(a) - (SKP_uint32)(b)))

/* Multiply-accumulate macros that allow overflow in the addition (ie, no asserts in debug mode) */
#define SKP_MLA_ovflw(a32, b32, c32)        SKP_ADD32_ovflw((a32), (SKP_uint32)(b32) * (SKP_uint32)(c32))
#ifndef SKP_SMLABB_ovflw
 #define SKP_SMLABB_ovflw(a32, b32, c32)    SKP_ADD32_ovflw((a32), SKP_SMULBB((b32),(c32)))
#endif
#define SKP_SMLATT_ovflw(a32, b32, c32) 	SKP_ADD32_ovflw((a32), SKP_SMULTT((b32),(c32)))
#define SKP_SMLAWB_ovflw(a32, b32, c32)	    SKP_ADD32_ovflw((a32), SKP_SMULWB((b32),(c32)))
#define SKP_SMLAWT_ovflw(a32, b32, c32)	    SKP_ADD32_ovflw((a32), SKP_SMULWT((b32),(c32)))
#define SKP_DIV32_16(a32, b16)             ((SKP_int32)((a32) / (b16)))
#define SKP_DIV32(a32, b32)                ((SKP_int32)((a32) / (b32)))

#define SKP_ADD32(a, b)                    ((a) + (b))
#define SKP_ADD64(a, b)                    ((a) + (b))

#define SKP_SUB32(a, b)                    ((a) - (b))

#define SKP_SAT16(a)                       ((a) > SKP_int16_MAX ? SKP_int16_MAX : \
                                           ((a) < SKP_int16_MIN ? SKP_int16_MIN : (a)))
#define SKP_SAT32(a)                       ((a) > SKP_int32_MAX ? SKP_int32_MAX : \
                                           ((a) < SKP_int32_MIN ? SKP_int32_MIN : (a)))

#define SKP_CHECK_FIT16(a)                 (a)
#define SKP_CHECK_FIT32(a)                 (a)

#define SKP_ADD_SAT16(a, b)                (SKP_int16)SKP_SAT16( SKP_ADD32( (SKP_int32)(a), (b) ) )

/* Add with saturation for positive input values */ 
#define SKP_ADD_POS_SAT32(a, b)            ((((a)+(b)) & 0x80000000)           ? SKP_int32_MAX : ((a)+(b)))

#define SKP_LSHIFT32(a, shift)             ((a)<<(shift))                // shift >= 0, shift < 32
#define SKP_LSHIFT64(a, shift)             ((a)<<(shift))                // shift >= 0, shift < 64
#define SKP_LSHIFT(a, shift)               SKP_LSHIFT32(a, shift)        // shift >= 0, shift < 32

#define SKP_RSHIFT32(a, shift)             ((a)>>(shift))                // shift >= 0, shift < 32
#define SKP_RSHIFT64(a, shift)             ((a)>>(shift))                // shift >= 0, shift < 64
#define SKP_RSHIFT(a, shift)               SKP_RSHIFT32(a, shift)        // shift >= 0, shift < 32

/* saturates before shifting */
#define SKP_LSHIFT_SAT32(a, shift)         (SKP_LSHIFT32( SKP_LIMIT_32( (a), SKP_RSHIFT32( SKP_int32_MIN, (shift) ),    \
                                                                          SKP_RSHIFT32( SKP_int32_MAX, (shift) ) ), (shift) ))

#define SKP_LSHIFT_ovflw(a, shift)        ((a)<<(shift))        // shift >= 0, allowed to overflow
#define SKP_LSHIFT_uint(a, shift)         ((a)<<(shift))        // shift >= 0
#define SKP_RSHIFT_uint(a, shift)         ((a)>>(shift))        // shift >= 0

#define SKP_ADD_LSHIFT(a, b, shift)       ((a) + SKP_LSHIFT((b), (shift)))            // shift >= 0
#define SKP_ADD_LSHIFT32(a, b, shift)     SKP_ADD32((a), SKP_LSHIFT32((b), (shift)))    // shift >= 0
#define SKP_ADD_RSHIFT(a, b, shift)       ((a) + SKP_RSHIFT((b), (shift)))            // shift >= 0
#define SKP_ADD_RSHIFT32(a, b, shift)     SKP_ADD32((a), SKP_RSHIFT32((b), (shift)))    // shift >= 0
#define SKP_ADD_RSHIFT_uint(a, b, shift)  ((a) + SKP_RSHIFT_uint((b), (shift)))        // shift >= 0
#define SKP_SUB_LSHIFT32(a, b, shift)     SKP_SUB32((a), SKP_LSHIFT32((b), (shift)))    // shift >= 0
#define SKP_SUB_RSHIFT32(a, b, shift)     SKP_SUB32((a), SKP_RSHIFT32((b), (shift)))    // shift >= 0

/* Requires that shift > 0 */
#define SKP_RSHIFT_ROUND(a, shift)        ((shift) == 1 ? ((a) >> 1) + ((a) & 1) : (((a) >> ((shift) - 1)) + 1) >> 1)
#define SKP_RSHIFT_ROUND64(a, shift)      ((shift) == 1 ? ((a) >> 1) + ((a) & 1) : (((a) >> ((shift) - 1)) + 1) >> 1)

/* Number of rightshift required to fit the multiplication */
#define SKP_NSHIFT_MUL_32_32(a, b)        ( -(31- (32-SKP_Silk_CLZ32(SKP_abs(a)) + (32-SKP_Silk_CLZ32(SKP_abs(b))))) )

#define SKP_min(a, b)                     (((a) < (b)) ? (a) : (b)) 
#define SKP_max(a, b)                     (((a) > (b)) ? (a) : (b))

/* Macro to convert floating-point constants to fixed-point */
#define SKP_FIX_CONST( C, Q )           ((SKP_int32)((C) * ((SKP_int64)1 << (Q)) + 0.5))

/* SKP_min() versions with typecast in the function call */
SKP_INLINE SKP_int SKP_min_int(SKP_int a, SKP_int b)
{
    return (((a) < (b)) ? (a) : (b));
}

SKP_INLINE SKP_int32 SKP_min_32(SKP_int32 a, SKP_int32 b)
{
    return (((a) < (b)) ? (a) : (b));
}

/* SKP_min() versions with typecast in the function call */
SKP_INLINE SKP_int SKP_max_int(SKP_int a, SKP_int b)
{
    return (((a) > (b)) ? (a) : (b));
}
SKP_INLINE SKP_int16 SKP_max_16(SKP_int16 a, SKP_int16 b)
{
    return (((a) > (b)) ? (a) : (b));
}
SKP_INLINE SKP_int32 SKP_max_32(SKP_int32 a, SKP_int32 b)
{
    return (((a) > (b)) ? (a) : (b));
}

#define SKP_LIMIT( a, limit1, limit2)    ((limit1) > (limit2) ? ((a) > (limit1) ? (limit1) : ((a) < (limit2) ? (limit2) : (a))) \
                                                             : ((a) > (limit2) ? (limit2) : ((a) < (limit1) ? (limit1) : (a))))

#define SKP_LIMIT_int SKP_LIMIT
#define SKP_LIMIT_32 SKP_LIMIT

//#define SKP_non_neg(a)                 ((a) & ((-(a)) >> (8 * sizeof(a) - 1)))   /* doesn't seem faster than SKP_max(0, a);

#define SKP_abs(a)                       (((a) >  0)  ? (a) : -(a))            // Be careful, SKP_abs returns wrong when input equals to SKP_intXX_MIN
#define SKP_abs_int32(a)                 (((a) ^ ((a) >> 31)) - ((a) >> 31))

/* PSEUDO-RANDOM GENERATOR                                                          */
/* Make sure to store the result as the seed for the next call (also in between     */
/* frames), otherwise result won't be random at all. When only using some of the    */
/* bits, take the most significant bits by right-shifting. Do not just mask off     */
/* the lowest bits.                                                                 */
#define SKP_RAND(seed)                   (SKP_MLA_ovflw(907633515, (seed), 196314165))

// Add some multiplication functions that can be easily mapped to ARM.

//    SKP_SMMUL: Signed top word multiply. 
//        ARMv6        2 instruction cycles. 
//        ARMv3M+        3 instruction cycles. use SMULL and ignore LSB registers.(except xM) 
//#define SKP_SMMUL(a32, b32)            (SKP_int32)SKP_RSHIFT(SKP_SMLAL(SKP_SMULWB((a32), (b32)), (a32), SKP_RSHIFT_ROUND((b32), 16)), 16)
// the following seems faster on x86
//#define SKP_SMMUL(a32, b32)              (SKP_int32)SKP_RSHIFT64(SKP_SMULL((a32), (b32)), 32)

#include "SKP_Silk_Inlines.h"

#ifdef  __cplusplus
}
#endif

#endif
