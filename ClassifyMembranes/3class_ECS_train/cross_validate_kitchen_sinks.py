#!/usr/bin/env Python27epd64

import sys
import threading
import time

from collections import defaultdict

import numpy as np
import random
import cv2
import h5py

import glob
import warnings

import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule
import pycuda.gpuarray

NUM_RANDOM_FEATURES = 2000

cudafuncs = SourceModule(open(r"C:\Users\DanielMiron\rhoana\ClassifyMembranes\3class_ECS_train\thresher.cu").read())

def extract_data(labeled_images, feature_files):
    '''For N labeled pixels with K features, returns:
          - KxN data matrix
          - 1xN label matrix
          - list of K feature names

    '''
    f = h5py.File(feature_files[0], 'r')
    feature_names = sorted(f.keys())
    f.close()
    data = []
    labels = []
    for imn, fn in zip(labeled_images, feature_files):
        print "Extracting data from", imn, "/", fn
        im = cv2.imread(imn)
        assert im is not None
        f = h5py.File(fn, 'r')
        mask0 = im[:, :, 0] > np.maximum(im[:, :, 1], im[:, :, 2])
        mask1 = im[:, :, 1] > np.maximum(im[:, :, 0], im[:, :, 2])
        mask2 = im[:, :, 2] > np.maximum(im[:, :, 0], im[:, :, 1])
        mask_all = (mask0 | mask1 | mask2)
        labels.append((mask1 * 1 + mask2 * 2)[mask_all])
        data.append([f[feature][...][mask_all].astype(np.float32) for feature in feature_names])
        f.close()
    return np.hstack(data), np.hstack(labels).astype(np.int32), feature_names

def featureize(D, num_new_features, labels, indices, thresholds):
    '''For a KxN data matrix with K features, returns:
          - NxZ new 0/1 data matrix
          - Z new feature names of the form "feature > threshold"
    '''

    packed_len = (D.shape[1] + 31) // 32  # one bit per sample, in 32-bit integers
    # make sure we have good alignment
    packed_len += 64 - (packed_len % 64)
    gpu_packed_features = cuda.mem_alloc(num_new_features * packed_len * 4)

    gpu_labels = cuda.mem_alloc(labels.nbytes)
    cuda.memcpy_htod(gpu_labels, labels)
    labelsums = np.zeros(packed_len, np.uint32)
    gpu_labelsums = cuda.mem_alloc(packed_len * 4)

    rhs = np.zeros(num_new_features, np.uint32)
    thresher = cudafuncs.get_function("thresh")
    block = (512, 1, 1)
    grid = ((packed_len + 511) // 512, 1)

    cur_feature_idx = -1
    gpu_raw_feature = cuda.mem_alloc(D[0, :].nbytes)
    for offset, (idx, thresh) in enumerate(zip(indices, thresholds)):
        if cur_feature_idx != idx:
            cuda.memcpy_htod(gpu_raw_feature, D[idx, :])
            cur_feature_idx = idx
        st = time.time()
        thresher(gpu_raw_feature, gpu_labels, np.int32(D.shape[1]),
                 gpu_packed_features, np.int32(packed_len),
                 np.float32(thresh), np.int32(offset * packed_len),
                 gpu_labelsums,
                 block=block, grid=grid)
        cuda.memcpy_dtoh(labelsums, gpu_labelsums)
        rhs[offset] = np.sum(labelsums)

    gpu_labels.free()
    gpu_labelsums.free()
    return gpu_packed_features, packed_len, rhs

def outerprod(gpu_packed_features, num_new_features, packed_int_count):
    cu_prod = cudafuncs.get_function("outerprod")
    
    prod = np.zeros((num_new_features, num_new_features), np.uint32)
    gpu_prod = cuda.mem_alloc(num_new_features * num_new_features * 4)
    # Cuda has a 5 second limit on kernel executions, so we have to work in smaller batches
    sub_size = 100
    block = (512, 1, 1)
    streams = [cuda.Stream() for i in range(8)]
    sidx = 0
    for subi in range(0, num_new_features, sub_size):
        for subj in range(0, num_new_features, sub_size):
            sidx += 1
            grid = (min(sub_size, num_new_features - subi),
                    min(sub_size, num_new_features - subj))
            cu_prod(gpu_packed_features,
                    np.int32(packed_int_count),
                    np.int32(num_new_features),
                    np.int32(subi), np.int32(subj),
                    gpu_prod,
                    block=block, grid=grid, shared=512*4, stream=streams[sidx % 8])
    for s in streams:
        s.synchronize()
    cuda.memcpy_dtoh(prod, gpu_prod)
    gpu_prod.free()
    return prod

def balanced_choice(pop, count):
    prevcounts = defaultdict(int)
    out = []
    for c in range(count):
        c1 = random.randrange(pop)
        c2 = random.randrange(pop)
        cout = c1 if prevcounts[c1] < prevcounts[c2] else c2
        prevcounts[cout] += 1
        out.append(cout)
    return out

if __name__ == '__main__':
    sys.argv.pop(0)
    
    labeled_images = glob.glob(sys.argv[0] + '\*.tif')
    feature_files = glob.glob(sys.argv[0] + '\*.hdf5')
    assert len(labeled_images) == len(feature_files)

    D = []
    L = []
    for li, ff in zip(labeled_images, feature_files):
        d, l, names = extract_data([li], [ff])
        D.append(d)
        L.append(l)
      
        print "Labeled data for %s:", li
        for val in range(3):
            print "     label = ", val, ", count:", np.sum(L[-1] == val)

    indices = balanced_choice(D[0].shape[0], NUM_RANDOM_FEATURES)
    # assume the training sets are roughly balanced
    thresholds = [np.random.choice(random.choice(D)[idx, :]) for idx in indices]

    prods = []
    rhss = []
    FD = []
    # we can process 500x500 for a million pixels without timing out
    block_size = (1000 * 1000 * 1000000) / (NUM_RANDOM_FEATURES * NUM_RANDOM_FEATURES)
    for d, l in zip(D, L):
        rhs = 0
        prod = 0
        for base in range(0, d.shape[1], block_size):
            st = time.time()
            featureized_data, packed_len, this_rhs = \
                featureize(d[:, base:base+block_size], NUM_RANDOM_FEATURES, l[base:base+block_size],
                           indices, thresholds)
            print base, d.shape[1]
            print "featureizing took", time.time() - st
            st = time.time()
            this_prod = outerprod(featureized_data, NUM_RANDOM_FEATURES, packed_len)
            print "outer product took", time.time() - st
            rhs += this_rhs
            prod += np.maximum(this_prod, this_prod.T)
            featureized_data.free()
        prods.append(prod)
        rhss.append(rhs)
    print prod
    
    fullprod = sum(prods)
    fullrhs = sum(rhss)
    
    tot_err = 0
    warnings.filterwarnings('default')
    for idx, (d, l) in enumerate(zip(D, L)):
        allbut_prod = fullprod - prods[idx]
        allbut_rhs = fullrhs - rhss[idx]
        weights, residuals, rank, s = np.linalg.lstsq(allbut_prod, allbut_rhs)
        predicted_labels = np.zeros(l.size)
        for feature_idx, w, t in zip(indices, weights, thresholds):
            predicted_labels += w * (d[feature_idx, :] > t)
        err = np.abs(l - predicted_labels) - 0.5
        err[err < 0] = 0
        tot_err += np.sum(err)
        print idx, np.sum(err)
    print tot_err, "error with all features"
        
    err_diff = []
    feature_lists =[]
    for i in range(len(names)):
        feature_lists += [[i]]
    for features in feature_lists: 
        err_sum = 0    
        for idx, (d, l) in enumerate(zip(D, L)):
            allbut_prod = fullprod - prods[idx]
            allbut_rhs = fullrhs - rhss[idx]
            cut_allbut_prod = np.copy(allbut_prod)
            cut_allbut_rhs = np.copy(allbut_rhs)
            for i in range(np.size(cut_allbut_rhs)):
                if (indices[i] in features):
                    cut_allbut_prod[:,i]=0
                    cut_allbut_prod[i,:]=0
                    cut_allbut_rhs[i] = 0
            weights, residuals, rank, s = np.linalg.lstsq(cut_allbut_prod, cut_allbut_rhs)
            predicted_labels = np.zeros(l.size)
            for feature_idx, w, t in zip(indices, weights, thresholds):
                predicted_labels += w * (d[feature_idx, :] > t)
            err = np.abs(l - predicted_labels) - 0.5
            err[err < 0] = 0
            err_sum += np.sum(err)
            print idx, np.sum(err)
        err_diff.append([features, err_sum-tot_err])
        print err_sum-tot_err, features, \n
    err_diff.sort(key = lambda x: x[1])
    print err_diff
