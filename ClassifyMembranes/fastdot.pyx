cimport cython
import numpy as np
from cython.parallel import prange, parallel, threadid
import sys

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cdef void _fastdot(unsigned char [:, ::1] D,
                   unsigned int [:, :, ::1] out) nogil:
    cdef int r, i, j, offset
    for r in prange(D.shape[0], schedule='static'):
        offset = threadid()
        for i in range(D.shape[1]):
            if D[r, i]:
                out[offset, i, i] += 1
                for j in range(i):
                    out[offset, i, j] += D[r, j]

def fastdot(D):
    assert (D.dtype == np.bool) or (D.dtype == np.uint8)
    out = np.zeros((8, D.shape[1], D.shape[1]), np.uint32)
    _fastdot(D.view(dtype=np.uint8), out)
    out = out.sum(axis=0)
    out = np.maximum(out, out.T)
    return out
