import sys
import threading
import time

import numpy as np
import cv2
import h5py

from fastdot import fastdot


NUM_RANDOM_FEATURES = 1000

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
        data.append([f[feature][...][mask_all] for feature in feature_names])
        f.close()
    return np.hstack(data), np.hstack(labels).astype(np.int32), feature_names

def featureize(D, names, num_new_features):
    '''For a KxN data matrix with K features, returns:
          - NxZ new 0/1 data matrix
          - Z new feature names of the form "feature > threshold"
    '''

    assert len(names) == D.shape[0]
    new_names = []
    new_features = np.zeros((D.shape[1], num_new_features), dtype=np.uint8)
    for n in range(num_new_features):
        idx = np.random.choice(D.shape[0])
        thresh = np.random.choice(D[idx, :])
        new_names.append("%s[...] > %f" % (names[idx], thresh))
        new_features[:, n] = (D[idx, :] > thresh)
    return new_features, new_names

def correlation_matrix_ZN(D, pool):
    Z, N = D.shape
    assert Z == NUM_RANDOM_FEATURES
    packed = np.packbits(D, axis=1)
    C = np.zeros((Z, Z))

    def countbits(v1in, v2in):
        def doit(v1, v2):
            if v2 is not None:
                v1 = np.bitwise_and(v1, v2)
            t = 0
            for shift in range(8):
                t += np.sum(np.bitwise_and(v1, 1 << shift) > 0)
            return t
        return pool.apply_async(doit, [v1in, v2in])

    CountBits = {}
    for i in range(Z):
        CountBits[i, i] = countbits(packed[i, :], None)
        for j in range(i):
            CountBits[i, j] = CountBits[j, i] = countbits(packed[i, :], packed[j, :])

    for i in range(Z):
        for j in range(Z):
            C[i, j] = CountBits[i, j].get()

    return C

def correlation_matrix_NZ(D, pool):
    N, Z = D.shape
    assert Z == NUM_RANDOM_FEATURES
    return fastdot(D)

if __name__ == '__main__':
    from multiprocessing.pool import ThreadPool
    if not hasattr(threading.current_thread(), "_children"):
        threading.current_thread()._children = weakref.WeakKeyDictionary()
    pool = ThreadPool(8)

    sys.argv.pop(0)
    labeled_images = sys.argv[:(len(sys.argv) // 2)]
    feature_files = sys.argv[(len(sys.argv) // 2):]
    assert len(labeled_images) == len(feature_files)
    D, L, names = extract_data(labeled_images, feature_files)
    print "Labeled data:"
    for val in range(3):
        print "     label = ", val, ", count:", np.sum(L == val)

    featureized_data, new_feature_names = featureize(D, names, NUM_RANDOM_FEATURES)
    st = time.time()
    Corr = correlation_matrix_NZ(featureized_data, pool)
    print "Correlation took", time.time() - st
    rhs = np.dot(featureized_data.T, (L - 1))
    print "solving"
    weights, residuals, rank, s = np.linalg.lstsq(Corr, rhs)

    # create the rules
    rules = " + ".join(["%f * (%s)" % (w, n) 
                        for w, n in zip(weights, new_feature_names)])

    for imn, fn in zip(labeled_images, feature_files):
        f = h5py.File(fn, 'r')
        locs = dict((k, f[k]) for k in f.keys())
        res = eval(rules, locs)
        outim = np.dstack((res < -0.5,
                           np.logical_and(res >= -0.5, res < 0.5),
                           res > 0.5)).astype(np.uint8) * 255
        cv2.imwrite("predicted_%s" % imn, outim)
        f.close()
