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

#include "SKP_Silk_main.h"

/* Range encoder for one symbol */
void SKP_Silk_range_encoder(
    SKP_Silk_range_coder_state      *psRC,              /* I/O  compressor data structure                   */
    const SKP_int                   data,               /* I    uncompressed data                           */
    const SKP_uint16                prob[]              /* I    cumulative density functions                */
)
{
    SKP_uint32 low_Q16, high_Q16;
    SKP_uint32 base_tmp, range_Q32;

    /* Copy structure data */
    SKP_uint32 base_Q32  = psRC->base_Q32;
    SKP_uint32 range_Q16 = psRC->range_Q16;
    SKP_int32  bufferIx  = psRC->bufferIx;
    SKP_uint8  *buffer   = psRC->buffer;

    if( psRC->error ) {
        return;
    }

    /* Update interval */
    low_Q16  = prob[ data ];
    high_Q16 = prob[ data + 1 ];
    base_tmp = base_Q32; /* save current base, to test for carry */
    base_Q32 += SKP_MUL_uint( range_Q16, low_Q16 );
    range_Q32 = SKP_MUL_uint( range_Q16, high_Q16 - low_Q16 );

    /* Check for carry */
    if( base_Q32 < base_tmp ) {
        /* Propagate carry in buffer */
        SKP_int bufferIx_tmp = bufferIx;
        while( ( ++buffer[ --bufferIx_tmp ] ) == 0 );
    }

    /* Check normalization */
    if( range_Q32 & 0xFF000000 ) {
        /* No normalization */
        range_Q16 = SKP_RSHIFT_uint( range_Q32, 16 );
    } else {
        if( range_Q32 & 0xFFFF0000 ) {
            /* Normalization of 8 bits shift */
            range_Q16 = SKP_RSHIFT_uint( range_Q32, 8 );
        } else {
            /* Normalization of 16 bits shift */
            range_Q16 = range_Q32;
            /* Make sure not to write beyond buffer */
            if( bufferIx >= psRC->bufferLength ) {
                psRC->error = RANGE_CODER_WRITE_BEYOND_BUFFER;
                return;
            }
            /* Write one byte to buffer */
            buffer[ bufferIx++ ] = (SKP_uint8)( SKP_RSHIFT_uint( base_Q32, 24 ) );
            base_Q32 = SKP_LSHIFT_ovflw( base_Q32, 8 );
        }
        /* Make sure not to write beyond buffer */
        if( bufferIx >= psRC->bufferLength ) {
            psRC->error = RANGE_CODER_WRITE_BEYOND_BUFFER;
            return;
        }
        /* Write one byte to buffer */
        buffer[ bufferIx++ ] = (SKP_uint8)( SKP_RSHIFT_uint( base_Q32, 24 ) );
        base_Q32 = SKP_LSHIFT_ovflw( base_Q32, 8 );
    }

    /* Copy structure data back */
    psRC->base_Q32  = base_Q32;
    psRC->range_Q16 = range_Q16;
    psRC->bufferIx  = bufferIx;
}

/* Range encoder for multiple symbols */
void SKP_Silk_range_encoder_multi(
    SKP_Silk_range_coder_state      *psRC,              /* I/O  compressor data structure                   */
    const SKP_int                   data[],             /* I    uncompressed data    [nSymbols]             */
    const SKP_uint16 * const        prob[],             /* I    cumulative density functions                */
    const SKP_int                   nSymbols            /* I    number of data symbols                      */
)
{
    SKP_int k;
    for( k = 0; k < nSymbols; k++ ) {
        SKP_Silk_range_encoder( psRC, data[ k ], prob[ k ] );
    }
}

/* Range decoder for one symbol */
void SKP_Silk_range_decoder(
    SKP_int                         data[],             /* O    uncompressed data                           */
    SKP_Silk_range_coder_state      *psRC,              /* I/O  compressor data structure                   */
    const SKP_uint16                prob[],             /* I    cumulative density function                 */
    SKP_int                         probIx              /* I    initial (middle) entry of cdf               */
)
{
    SKP_uint32 low_Q16, high_Q16;
    SKP_uint32 base_tmp, range_Q32;

    /* Copy structure data */
    SKP_uint32 base_Q32  = psRC->base_Q32;
    SKP_uint32 range_Q16 = psRC->range_Q16;
    SKP_int32  bufferIx  = psRC->bufferIx;
    SKP_uint8  *buffer   = &psRC->buffer[ 4 ];

    if( psRC->error ) {
        /* Set output to zero */
        *data = 0;
        return;
    }

    high_Q16 = prob[ probIx ];
    base_tmp = SKP_MUL_uint( range_Q16, high_Q16 );
    if( base_tmp > base_Q32 ) {
        while( 1 ) {
            low_Q16 = prob[ --probIx ];
            base_tmp = SKP_MUL_uint( range_Q16, low_Q16 );
            if( base_tmp <= base_Q32 ) {
                break;
            }
            high_Q16 = low_Q16;
            /* Test for out of range */
            if( high_Q16 == 0 ) {
                psRC->error = RANGE_CODER_CDF_OUT_OF_RANGE;
                /* Set output to zero */
                *data = 0;
                return;
            }
        }
    } else {
        while( 1 ) {
            low_Q16  = high_Q16;
            high_Q16 = prob[ ++probIx ];
            base_tmp = SKP_MUL_uint( range_Q16, high_Q16 );
            if( base_tmp > base_Q32 ) {
                probIx--;
                break;
            }
            /* Test for out of range */
            if( high_Q16 == 0xFFFF ) {
                psRC->error = RANGE_CODER_CDF_OUT_OF_RANGE;
                /* Set output to zero */
                *data = 0;
                return;
            }
        }
    }
    *data = probIx;
    base_Q32 -= SKP_MUL_uint( range_Q16, low_Q16 );
    range_Q32 = SKP_MUL_uint( range_Q16, high_Q16 - low_Q16 );

    /* Check normalization */
    if( range_Q32 & 0xFF000000 ) {
        /* No normalization */
        range_Q16 = SKP_RSHIFT_uint( range_Q32, 16 );
    } else {
        if( range_Q32 & 0xFFFF0000 ) {
            /* Normalization of 8 bits shift */
            range_Q16 = SKP_RSHIFT_uint( range_Q32, 8 );
            /* Check for errors */
            if( SKP_RSHIFT_uint( base_Q32, 24 ) ) {
                psRC->error = RANGE_CODER_NORMALIZATION_FAILED;
                /* Set output to zero */
                *data = 0;
                return;
            }
        } else {
            /* Normalization of 16 bits shift */
            range_Q16 = range_Q32;
            /* Check for errors */
            if( SKP_RSHIFT( base_Q32, 16 ) ) {
                psRC->error = RANGE_CODER_NORMALIZATION_FAILED;
                /* Set output to zero */
                *data = 0;
                return;
            }
            /* Update base */
            base_Q32 = SKP_LSHIFT_uint( base_Q32, 8 );
            /* Make sure not to read beyond buffer */
            if( bufferIx < psRC->bufferLength ) {
                /* Read one byte from buffer */
                base_Q32 |= (SKP_uint32)buffer[ bufferIx++ ];
            }
        }
        /* Update base */
        base_Q32 = SKP_LSHIFT_uint( base_Q32, 8 );
        /* Make sure not to read beyond buffer */
        if( bufferIx < psRC->bufferLength ) {
            /* Read one byte from buffer */
            base_Q32 |= (SKP_uint32)buffer[ bufferIx++ ];
        }
    }

    /* Check for zero interval length */
    if( range_Q16 == 0 ) {
        psRC->error = RANGE_CODER_ZERO_INTERVAL_WIDTH;
        /* Set output to zero */
        *data = 0;
        return;
    }

    /* Copy structure data back */
    psRC->base_Q32  = base_Q32;
    psRC->range_Q16 = range_Q16;
    psRC->bufferIx  = bufferIx;
}

/* Range decoder for multiple symbols */
void SKP_Silk_range_decoder_multi(
    SKP_int                         data[],             /* O    uncompressed data                [nSymbols] */
    SKP_Silk_range_coder_state      *psRC,              /* I/O  compressor data structure                   */
    const SKP_uint16 * const        prob[],             /* I    cumulative density functions                */
    const SKP_int                   probStartIx[],      /* I    initial (middle) entries of cdfs [nSymbols] */
    const SKP_int                   nSymbols            /* I    number of data symbols                      */
)
{
    SKP_int k;
    for( k = 0; k < nSymbols; k++ ) {
        SKP_Silk_range_decoder( &data[ k ], psRC, prob[ k ], probStartIx[ k ] );
    }
}

/* Initialize range encoder */
void SKP_Silk_range_enc_init(
    SKP_Silk_range_coder_state      *psRC               /* O    compressor data structure                   */
)
{
    /* Initialize structure */
    psRC->bufferLength = MAX_ARITHM_BYTES;
    psRC->range_Q16    = 0x0000FFFF;
    psRC->bufferIx     = 0;
    psRC->base_Q32     = 0;
    psRC->error        = 0;
}

/* Initialize range decoder */
void SKP_Silk_range_dec_init(
    SKP_Silk_range_coder_state      *psRC,              /* O    compressor data structure                   */
    const SKP_uint8                 buffer[],           /* I    buffer for compressed data [bufferLength]   */
    const SKP_int32                 bufferLength        /* I    buffer length (in bytes)                    */
)
{
    /* check input */
    if( ( bufferLength > MAX_ARITHM_BYTES ) || ( bufferLength < 0 ) ) {
        psRC->error = RANGE_CODER_DEC_PAYLOAD_TOO_LONG;
        return;
    }
    /* Initialize structure */
    /* Copy to internal buffer */
    SKP_memcpy( psRC->buffer, buffer, bufferLength * sizeof( SKP_uint8 ) ); 
    psRC->bufferLength = bufferLength;
    psRC->bufferIx = 0;
    psRC->base_Q32 = 
        SKP_LSHIFT_uint( (SKP_uint32)buffer[ 0 ], 24 ) | 
        SKP_LSHIFT_uint( (SKP_uint32)buffer[ 1 ], 16 ) | 
        SKP_LSHIFT_uint( (SKP_uint32)buffer[ 2 ],  8 ) | 
                         (SKP_uint32)buffer[ 3 ];
    psRC->range_Q16 = 0x0000FFFF;
    psRC->error     = 0;
}

/* Determine length of bitstream */
SKP_int SKP_Silk_range_coder_get_length(                /* O    returns number of BITS in stream            */
    const SKP_Silk_range_coder_state    *psRC,          /* I    compressed data structure                   */
    SKP_int                             *nBytes         /* O    number of BYTES in stream                   */
)
{
    SKP_int nBits;

    /* Number of bits in stream */
    nBits = SKP_LSHIFT( psRC->bufferIx, 3 ) + SKP_Silk_CLZ32( psRC->range_Q16 - 1 ) - 14;

    *nBytes = SKP_RSHIFT( nBits + 7, 3 );

    /* Return number of bits in bitstream */
    return nBits;
}

/* Write shortest uniquely decodable stream to buffer, and determine its length */
void SKP_Silk_range_enc_wrap_up(
    SKP_Silk_range_coder_state      *psRC               /* I/O  compressed data structure                   */
)
{
    SKP_int bufferIx_tmp, bits_to_store, bits_in_stream, nBytes, mask;
    SKP_uint32 base_Q24;

    /* Lower limit of interval, shifted 8 bits to the right */
    base_Q24 = SKP_RSHIFT_uint( psRC->base_Q32, 8 );

    bits_in_stream = SKP_Silk_range_coder_get_length( psRC, &nBytes );

    /* Number of additional bits (1..9) required to be stored to stream */
    bits_to_store = bits_in_stream - SKP_LSHIFT( psRC->bufferIx, 3 );
    /* Round up to required resolution */
    base_Q24 += SKP_RSHIFT_uint(  0x00800000, bits_to_store - 1 );
    base_Q24 &= SKP_LSHIFT_ovflw( 0xFFFFFFFF, 24 - bits_to_store );

    /* Check for carry */
    if( base_Q24 & 0x01000000 ) {
        /* Propagate carry in buffer */
        bufferIx_tmp = psRC->bufferIx;
        while( ( ++( psRC->buffer[ --bufferIx_tmp ] ) ) == 0 );
    }

    /* Store to stream, making sure not to write beyond buffer */
    if( psRC->bufferIx < psRC->bufferLength ) {
        psRC->buffer[ psRC->bufferIx++ ] = (SKP_uint8)SKP_RSHIFT_uint( base_Q24, 16 );
        if( bits_to_store > 8 ) {
            if( psRC->bufferIx < psRC->bufferLength ) {
                psRC->buffer[ psRC->bufferIx++ ] = (SKP_uint8)SKP_RSHIFT_uint( base_Q24, 8 );
            }
        }
    }

    /* Fill up any remaining bits in the last byte with 1s */
    if( bits_in_stream & 7 ) {
        mask = SKP_RSHIFT( 0xFF, bits_in_stream & 7 );
        if( nBytes - 1 < psRC->bufferLength ) {
            psRC->buffer[ nBytes - 1 ] |= mask;
        }
    }
}

/* Check that any remaining bits in the last byte are set to 1 */
void SKP_Silk_range_coder_check_after_decoding(
    SKP_Silk_range_coder_state      *psRC               /* I/O  compressed data structure                   */
)
{
    SKP_int bits_in_stream, nBytes, mask;

    bits_in_stream = SKP_Silk_range_coder_get_length( psRC, &nBytes );

    /* Make sure not to read beyond buffer */
    if( nBytes - 1 >= psRC->bufferLength ) {
        psRC->error = RANGE_CODER_DECODER_CHECK_FAILED;
        return;
    }

    /* Test any remaining bits in last byte */
    if( bits_in_stream & 7 ) {
        mask = SKP_RSHIFT( 0xFF, bits_in_stream & 7 );
        if( ( psRC->buffer[ nBytes - 1 ] & mask ) != mask ) {
            psRC->error = RANGE_CODER_DECODER_CHECK_FAILED;
            return;
        }
    }
}
