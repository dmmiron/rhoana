#include <stdio.h>

__global__ void
thresh(float *raw, unsigned int *labels, int rawsize,
       unsigned int *packed, int packedsize,
       float thresh, unsigned int offset,
       unsigned int *labelsums)
{
    int bitidx, rawidx;
    int idx = threadIdx.x + blockIdx.x * blockDim.x;
    if (idx < packedsize) {
        unsigned int temp, ls;

        temp = 0;
        ls = 0;
        
        for (bitidx = 0; bitidx < sizeof(unsigned int) * 8; bitidx++) {
            rawidx = idx * sizeof(unsigned int) * 8 + bitidx;
            if (rawidx < rawsize) {
                if (raw[rawidx] > thresh) {
                    temp |= (1 << bitidx);
                    ls += labels[rawidx];
                }
            }
        }
        packed[idx + offset] = temp;
        labelsums[idx] = ls;
    }
}

__global__ void
outerprod(unsigned int *packed, int packedsize,
          int N, int sub_x, int sub_y,
          unsigned int *prod)
{
    unsigned int tid = threadIdx.x;
    extern __shared__ unsigned int sdata[];
    int bx = blockIdx.x + sub_x;
    int by = blockIdx.y + sub_y;
    
    if (blockIdx.x < blockIdx.y) {
        if (tid == 0) prod[(bx * N + by)] = 0;
        return;
    }

    unsigned int i = tid + packedsize * bx;
    unsigned int j = tid + packedsize * by;
    unsigned int upper = packedsize * (bx + 1);
    unsigned int mySum = 0;

    while (i < upper)
    {
        mySum += __popc(packed[i] & packed[j]);
        i += 512;
        j += 512;
    }

    // do reduction in shared mem
    sdata[tid] = mySum;
    __syncthreads();

    if (tid < 256) {
        sdata[tid] = mySum = mySum + sdata[tid + 256];
    }
    __syncthreads();

    if (tid < 128) {
        sdata[tid] = mySum = mySum + sdata[tid + 128];
    }
    __syncthreads();

    if (tid <  64) {
        sdata[tid] = mySum = mySum + sdata[tid +  64];
    }
    __syncthreads();

    if (tid < 32)
    {
        // now that we are using warp-synchronous programming (below)
        // we need to declare our shared memory volatile so that the compiler
        // doesn't reorder stores to it and induce incorrect behavior.
        volatile unsigned int *smem = sdata;

        smem[tid] = mySum = mySum + smem[tid + 32];
        smem[tid] = mySum = mySum + smem[tid + 16];
        smem[tid] = mySum = mySum + smem[tid +  8];
        smem[tid] = mySum = mySum + smem[tid +  4];
        smem[tid] = mySum = mySum + smem[tid +  2];
        smem[tid] = mySum = mySum + smem[tid +  1];
    }

    // write result for this block to outer product
    if (tid == 0) {
        prod[bx * N + by] = mySum;
    }
}
