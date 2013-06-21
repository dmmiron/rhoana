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
print forest_files

var_counts = np.zeros(500)

for forest in forest_files:
    f_file = h5py.File(forest, 'r')
    bestvar = f_file['/forest/bestvar'][...]
    for row in range(bestvar.shape[0]):
        var_counts += np.bincount(bestvar[row], minlength=501)[1:]
     
counts = []   
for i in range(500):
    counts.append([i, var_counts[i]])

counts.sort(key = lambda x : x[1])
counts = np.array(counts, dtype = int)
#plt.bar(range(500), counts[:,0])
#plt.bar(counts[:,0], counts[:,1])
#plt.show()

best_twenty = counts[480:,0]
best_hundred = counts[400:,0]


feature_folder = "C:\\Users\\DanielMiron\\Documents\\autoencoder"
feature_files = sorted(glob.glob(feature_folder+"\*.h5"))

feature_out_folder = "C:\\Users\\DanielMiron\\Documents\\autoencoder_top20\\"

for feat_file in feature_files:
    
    features = h5py.File(feat_file, 'r')
    output_path = feature_out_folder + str(re.findall('\d+', feat_file)[0]) + "_autoencoder_features_top20.hdf5"
    out_file = h5py.File(output_path, 'w')
    for feature in best_twenty:
        feature_mat = features['/autoencoder_' + '%04i' % feature][...]
        out_file['/autoencoder_' + '%04i' % feature] = feature_mat
    out_file.close()
    features.close()
    
def recombine_features():
    output_folder = "C:\\Users\\DanielMiron\\Documents\\combined_features"
    auto_folder = "C:\\Users\\DanielMiron\\Documents\\autoencoder_top20"
    hand_folder = "C:\\Users\\DanielMiron\\Documents\\third_round"
    
    auto_files = sorted(glob.glob(auto_folder + "\*.hdf5"))
    hand_files = sorted(glob.glob(hand_folder + "\*.hdf5"))
    
    feature_elim = range(69,94) + range(34, 42)
    for a_file, h_file in zip(auto_files, hand_files):
        
        out_file = h5py.File(output_folder + "\\combined_" + str(re.findall('\d+', h_file)[0])+ ".hdf5", 'w')
        a_features = h5py.File(a_file, 'r')
        for feature in sorted(a_features.keys()):
            print a_features.keys()
            out_file[feature] = a_features[feature][...]
        a_features.close()
        h_features = h5py.File(h_file, 'r')
        for idx, feature in enumerate(sorted(h_features.keys())):
            if (not idx in feature_elim):
                out_file[feature] = h_features[feature][...]
        h_features.close()
        out_file.close()
    
recombine_features()