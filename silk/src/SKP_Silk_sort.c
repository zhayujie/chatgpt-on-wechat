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

/* Insertion sort (fast for already almost sorted arrays):   */
/* Best case:  O(n)   for an already sorted array            */
/* Worst case: O(n^2) for an inversely sorted array          */

#include "SKP_Silk_SigProc_FIX.h"

void SKP_Silk_insertion_sort_increasing(
    SKP_int32           *a,             /* I/O:  Unsorted / Sorted vector               */
    SKP_int             *index,         /* O:    Index vector for the sorted elements   */
    const SKP_int       L,              /* I:    Vector length                          */
    const SKP_int       K               /* I:    Number of correctly sorted output positions   */
)
{
    SKP_int32    value;
    SKP_int        i, j;

    /* Safety checks */
    SKP_assert( K >  0 );
    SKP_assert( L >  0 );
    SKP_assert( L >= K );

    /* Write start indices in index vector */
    for( i = 0; i < K; i++ ) {
        index[ i ] = i;
    }

    /* Sort vector elements by value, increasing order */
    for( i = 1; i < K; i++ ) {
        value = a[ i ];
        for( j = i - 1; ( j >= 0 ) && ( value < a[ j ] ); j-- ) {
            a[ j + 1 ]     = a[ j ];     /* Shift value */
            index[ j + 1 ] = index[ j ]; /* Shift index */
        }
        a[ j + 1 ]     = value; /* Write value */
        index[ j + 1 ] = i;     /* Write index */
    }

    /* If less than L values are asked for, check the remaining values, */
    /* but only spend CPU to ensure that the K first values are correct */
    for( i = K; i < L; i++ ) {
        value = a[ i ];
        if( value < a[ K - 1 ] ) {
            for( j = K - 2; ( j >= 0 ) && ( value < a[ j ] ); j-- ) {
                a[ j + 1 ]     = a[ j ];     /* Shift value */
                index[ j + 1 ] = index[ j ]; /* Shift index */
            }
            a[ j + 1 ]     = value; /* Write value */
            index[ j + 1 ] = i;        /* Write index */
        }
    }
}

void SKP_Silk_insertion_sort_decreasing_int16(
    SKP_int16           *a,             /* I/O: Unsorted / Sorted vector                */
    SKP_int             *index,         /* O:   Index vector for the sorted elements    */
    const SKP_int       L,              /* I:   Vector length                           */
    const SKP_int       K               /* I:   Number of correctly sorted output positions    */
)
{
    SKP_int i, j;
    SKP_int value;

    /* Safety checks */
    SKP_assert( K >  0 );
    SKP_assert( L >  0 );
    SKP_assert( L >= K );

    /* Write start indices in index vector */
    for( i = 0; i < K; i++ ) {
        index[ i ] = i;
    }

    /* Sort vector elements by value, decreasing order */
    for( i = 1; i < K; i++ ) {
        value = a[ i ];
        for( j = i - 1; ( j >= 0 ) && ( value > a[ j ] ); j-- ) {    
            a[ j + 1 ]     = a[ j ];     /* Shift value */
            index[ j + 1 ] = index[ j ]; /* Shift index */
        }
        a[ j + 1 ]     = value; /* Write value */
        index[ j + 1 ] = i;     /* Write index */
    }

    /* If less than L values are asked for, check the remaining values, */
    /* but only spend CPU to ensure that the K first values are correct */
    for( i = K; i < L; i++ ) {
        value = a[ i ];
        if( value > a[ K - 1 ] ) {
            for( j = K - 2; ( j >= 0 ) && ( value > a[ j ] ); j-- ) {    
                a[ j + 1 ]     = a[ j ];     /* Shift value */
                index[ j + 1 ] = index[ j ]; /* Shift index */
            }
            a[ j + 1 ]     = value; /* Write value */
            index[ j + 1 ] = i;     /* Write index */
        }
    }
}

void SKP_Silk_insertion_sort_increasing_all_values(
    SKP_int             *a,             /* I/O: Unsorted / Sorted vector                */
    const SKP_int       L               /* I:   Vector length                           */
)
{
    SKP_int    value;
    SKP_int    i, j;

    /* Safety checks */
    SKP_assert( L >  0 );

    /* Sort vector elements by value, increasing order */
    for( i = 1; i < L; i++ ) {
        value = a[ i ];
        for( j = i - 1; ( j >= 0 ) && ( value < a[ j ] ); j-- ) {
            a[ j + 1 ] = a[ j ]; /* Shift value */
        }
        a[ j + 1 ] = value; /* Write value */
    }
}


