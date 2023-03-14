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
#include "SKP_Silk_tuning_parameters.h"

/*****************************/
/* Internal function headers */
/*****************************/

typedef struct {
    SKP_int32 Q36_part;
    SKP_int32 Q48_part;
} inv_D_t;

/* Factorize square matrix A into LDL form */
SKP_INLINE void SKP_Silk_LDL_factorize_FIX(
    SKP_int32           *A,         /* I/O Pointer to Symetric Square Matrix */
    SKP_int             M,          /* I   Size of Matrix */
    SKP_int32           *L_Q16,     /* I/O Pointer to Square Upper triangular Matrix */
    inv_D_t             *inv_D      /* I/O Pointer to vector holding inverted diagonal elements of D */
);

/* Solve Lx = b, when L is lower triangular and has ones on the diagonal */
SKP_INLINE void SKP_Silk_LS_SolveFirst_FIX(
    const SKP_int32     *L_Q16,     /* I Pointer to Lower Triangular Matrix */
    SKP_int             M,          /* I Dim of Matrix equation */
    const SKP_int32     *b,         /* I b Vector */
    SKP_int32           *x_Q16      /* O x Vector */  
);

/* Solve L^t*x = b, where L is lower triangular with ones on the diagonal */
SKP_INLINE void SKP_Silk_LS_SolveLast_FIX(
    const SKP_int32     *L_Q16,     /* I Pointer to Lower Triangular Matrix */
    const SKP_int       M,          /* I Dim of Matrix equation */
    const SKP_int32     *b,         /* I b Vector */
    SKP_int32           *x_Q16      /* O x Vector */  
);

SKP_INLINE void SKP_Silk_LS_divide_Q16_FIX(
    SKP_int32           T[],    /* I/O Numenator vector */
    inv_D_t             *inv_D, /* I   1 / D vector     */
    SKP_int             M       /* I   dimension        */
);

/* Solves Ax = b, assuming A is symmetric */
void SKP_Silk_solve_LDL_FIX(
    SKP_int32                       *A,                 /* I    Pointer to symetric square matrix A         */
    SKP_int                         M,                  /* I    Size of matrix                              */
    const SKP_int32                 *b,                 /* I    Pointer to b vector                         */
    SKP_int32                       *x_Q16              /* O    Pointer to x solution vector                */
)
{
    SKP_int32 L_Q16[  MAX_MATRIX_SIZE * MAX_MATRIX_SIZE ]; 
    SKP_int32 Y[      MAX_MATRIX_SIZE ];
    inv_D_t   inv_D[  MAX_MATRIX_SIZE ];

    SKP_assert( M <= MAX_MATRIX_SIZE );

    /***************************************************
    Factorize A by LDL such that A = L*D*L',
    where L is lower triangular with ones on diagonal
    ****************************************************/
    SKP_Silk_LDL_factorize_FIX( A, M, L_Q16, inv_D );
        
    /****************************************************
    * substitute D*L'*x = Y. ie:
    L*D*L'*x = b => L*Y = b <=> Y = inv(L)*b
    ******************************************************/
    SKP_Silk_LS_SolveFirst_FIX( L_Q16, M, b, Y );

    /****************************************************
    D*L'*x = Y <=> L'*x = inv(D)*Y, because D is 
    diagonal just multiply with 1/d_i
    ****************************************************/
    SKP_Silk_LS_divide_Q16_FIX( Y, inv_D, M );

    /****************************************************
    x = inv(L') * inv(D) * Y
    *****************************************************/
    SKP_Silk_LS_SolveLast_FIX( L_Q16, M, Y, x_Q16 );
}

SKP_INLINE void SKP_Silk_LDL_factorize_FIX(
    SKP_int32           *A,         /* I   Pointer to Symetric Square Matrix */
    SKP_int             M,          /* I   Size of Matrix */
    SKP_int32           *L_Q16,     /* I/O Pointer to Square Upper triangular Matrix */
    inv_D_t             *inv_D      /* I/O Pointer to vector holding inverted diagonal elements of D */
)
{
    SKP_int   i, j, k, status, loop_count;
    const SKP_int32 *ptr1, *ptr2;
    SKP_int32 diag_min_value, tmp_32, err;
    SKP_int32 v_Q0[ MAX_MATRIX_SIZE ], D_Q0[ MAX_MATRIX_SIZE ];
    SKP_int32 one_div_diag_Q36, one_div_diag_Q40, one_div_diag_Q48;

    SKP_assert( M <= MAX_MATRIX_SIZE );

    status = 1;
    diag_min_value = SKP_max_32( SKP_SMMUL( SKP_ADD_SAT32( A[ 0 ], A[ SKP_SMULBB( M, M ) - 1 ] ), SKP_FIX_CONST( FIND_LTP_COND_FAC, 31 ) ), 1 << 9 );
    for( loop_count = 0; loop_count < M && status == 1; loop_count++ ) {
        status = 0;
        for( j = 0; j < M; j++ ) {
            ptr1 = matrix_adr( L_Q16, j, 0, M );
            tmp_32 = 0;
            for( i = 0; i < j; i++ ) {
                v_Q0[ i ] = SKP_SMULWW(         D_Q0[ i ], ptr1[ i ] ); /* Q0 */
                tmp_32    = SKP_SMLAWW( tmp_32, v_Q0[ i ], ptr1[ i ] ); /* Q0 */
            }
            tmp_32 = SKP_SUB32( matrix_ptr( A, j, j, M ), tmp_32 );

            if( tmp_32 < diag_min_value ) {
                tmp_32 = SKP_SUB32( SKP_SMULBB( loop_count + 1, diag_min_value ), tmp_32 );
                /* Matrix not positive semi-definite, or ill conditioned */
                for( i = 0; i < M; i++ ) {
                    matrix_ptr( A, i, i, M ) = SKP_ADD32( matrix_ptr( A, i, i, M ), tmp_32 );
                }
                status = 1;
                break;
            }
            D_Q0[ j ] = tmp_32;                         /* always < max(Correlation) */
        
            /* two-step division */
            one_div_diag_Q36 = SKP_INVERSE32_varQ( tmp_32, 36 );                    /* Q36 */
            one_div_diag_Q40 = SKP_LSHIFT( one_div_diag_Q36, 4 );                   /* Q40 */
            err = SKP_SUB32( 1 << 24, SKP_SMULWW( tmp_32, one_div_diag_Q40 ) );     /* Q24 */
            one_div_diag_Q48 = SKP_SMULWW( err, one_div_diag_Q40 );                 /* Q48 */

            /* Save 1/Ds */
            inv_D[ j ].Q36_part = one_div_diag_Q36;
            inv_D[ j ].Q48_part = one_div_diag_Q48;

            matrix_ptr( L_Q16, j, j, M ) = 65536; /* 1.0 in Q16 */
            ptr1 = matrix_adr( A, j, 0, M );
            ptr2 = matrix_adr( L_Q16, j + 1, 0, M );
            for( i = j + 1; i < M; i++ ) { 
                tmp_32 = 0;
                for( k = 0; k < j; k++ ) {
                    tmp_32 = SKP_SMLAWW( tmp_32, v_Q0[ k ], ptr2[ k ] ); /* Q0 */
                }
                tmp_32 = SKP_SUB32( ptr1[ i ], tmp_32 ); /* always < max(Correlation) */

                /* tmp_32 / D_Q0[j] : Divide to Q16 */
                matrix_ptr( L_Q16, i, j, M ) = SKP_ADD32( SKP_SMMUL( tmp_32, one_div_diag_Q48 ),
                    SKP_RSHIFT( SKP_SMULWW( tmp_32, one_div_diag_Q36 ), 4 ) );

                /* go to next column */
                ptr2 += M; 
            }
        }
    }

    SKP_assert( status == 0 );
}

SKP_INLINE void SKP_Silk_LS_divide_Q16_FIX(
    SKP_int32 T[],      /* I/O Numenator vector */
    inv_D_t *inv_D,     /* I   1 / D vector     */
    SKP_int M           /* I   Order */
)
{
    SKP_int   i;
    SKP_int32 tmp_32;
    SKP_int32 one_div_diag_Q36, one_div_diag_Q48;

    for( i = 0; i < M; i++ ) {
        one_div_diag_Q36 = inv_D[ i ].Q36_part;
        one_div_diag_Q48 = inv_D[ i ].Q48_part;

        tmp_32 = T[ i ];
        T[ i ] = SKP_ADD32( SKP_SMMUL( tmp_32, one_div_diag_Q48 ), SKP_RSHIFT( SKP_SMULWW( tmp_32, one_div_diag_Q36 ), 4 ) );
    }
}

/* Solve Lx = b, when L is lower triangular and has ones on the diagonal */
SKP_INLINE void SKP_Silk_LS_SolveFirst_FIX(
    const SKP_int32     *L_Q16, /* I Pointer to Lower Triangular Matrix */
    SKP_int             M,      /* I Dim of Matrix equation */
    const SKP_int32     *b,     /* I b Vector */
    SKP_int32           *x_Q16  /* O x Vector */  
)
{
    SKP_int i, j;
    const SKP_int32 *ptr32;
    SKP_int32 tmp_32;

    for( i = 0; i < M; i++ ) {
        ptr32 = matrix_adr( L_Q16, i, 0, M );
        tmp_32 = 0;
        for( j = 0; j < i; j++ ) {
            tmp_32 = SKP_SMLAWW( tmp_32, ptr32[ j ], x_Q16[ j ] );
        }
        x_Q16[ i ] = SKP_SUB32( b[ i ], tmp_32 );
    }
}

/* Solve L^t*x = b, where L is lower triangular with ones on the diagonal */
SKP_INLINE void SKP_Silk_LS_SolveLast_FIX(
    const SKP_int32     *L_Q16,     /* I Pointer to Lower Triangular Matrix */
    const SKP_int       M,          /* I Dim of Matrix equation */
    const SKP_int32     *b,         /* I b Vector */
    SKP_int32           *x_Q16      /* O x Vector */  
)
{
    SKP_int i, j;
    const SKP_int32 *ptr32;
    SKP_int32 tmp_32;

    for( i = M - 1; i >= 0; i-- ) {
        ptr32 = matrix_adr( L_Q16, 0, i, M );
        tmp_32 = 0;
        for( j = M - 1; j > i; j-- ) {
            tmp_32 = SKP_SMLAWW( tmp_32, ptr32[ SKP_SMULBB( j, M ) ], x_Q16[ j ] );
        }
        x_Q16[ i ] = SKP_SUB32( b[ i ], tmp_32 );
    }
}
