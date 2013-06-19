#-----------------------------
#Random Forest Best Variable Counter
#Daniel Miron
#6/19/2013
#
#Counts and plots the number of times each feature was used in random forest classifier
#-----------------------------

import glob
import sys
import h5py
import numpy as np
import matplotlib.pyplot as plt
import re


    
forest_folder = "C:\\Users\\DanielMiron\\Documents\\autoencoder_out"
forest_files = sorted(glob.glob(forest_folder + "\*.hdf5"))

var_counts = np.zeros(500)

for forest in forest_files:
    f_file = h5py.File(forest, 'r')
    bestvar = f_file['/forest/bestvar'][...]
    for row in range(bestvar.shape[0]):
        var_counts += np.bincount(bestvar[row], minlength=501)[1:]
     
counts = []   
for i in range(500):
    counts.append([i+1, var_counts[i]])

counts.sort(key = lambda x : x[1])
counts = np.array(counts, dtype = int)
#plt.bar(range(500), counts[:,0])
#plt.bar(counts[:,0], counts[:,1])
#plt.show()

best_hundred = counts[400:,0]

feature_folder = "C:\\Users\\DanielMiron\\Documents\\autoencoder"
feature_files = sorted(glob.glob(feature_folder+"\*.h5"))

feature_out_folder = "C:\\Users\\DanielMiron\\Documents\\autoencoder_top100\\"

for feat_file in feature_files:
    
    features = h5py.File(feat_file, 'r')
    output_path = feature_out_folder + str(re.findall('\d+', feat_file)[0]) + "_autoencoder_features_top100.hdf5"
    out_file = h5py.File(output_path, 'w')
    for feature in best_hundred:
        feature_mat = features['/autoencoder_' + '%04i' % feature][...]
        out_file['/autoencoder_' + '%04i' % feature] = feature_mat
    out_file.close()
    features.close()

