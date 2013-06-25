#--------------------------------------
#Wrapper for Random Forest Classifier-Feature Elimination
#Daniel Miron
#6/17/2013
#--------------------------------------

import glob
import sys
sys.path.append(r'C:\Python27\Lib\site-packages')
import h5py
import numpy as np
import train_gpu_randomforest as trainer
import predict_gpu_randomforest as predict

def main(argv):
    im_folder = argv[0] #input images and features folder (currently autoencoder_top100)
    features = []
    
    #holds small forests as well as single consolidated forest
    forest_folder = 'C:\\Users\\DanielMiron\\Documents\\combined_forests'
    
    forest_file_prefix = '\\combined_forest'
    
    #combine small forests
    cons_forest_file = 'C:\\Users\\DanielMiron\\Documents\\combined_forests\\cons_forest.hdf5'
    
    training_iterations = 2
    
    #get features to eliminate from command line
    if (len(argv) > 1):
        features = [int(n) for n in argv[1].split(',') if n.isdigit()]
    
    trainer.train(im_folder, forest_folder+forest_file_prefix, features, training_iterations)
    
    consolidate_trees(forest_folder, cons_forest_file)
    
    input_image_folder = 'C:\\Users\\DanielMiron\\Documents\\training_files'
    input_image_suffix = '.tif'
    input_features_suffix = '.hdf5'
    output_folder = 'C:\\Users\\DanielMiron\\Documents\\combined_output\\'
    err = predict.predict(cons_forest_file, input_image_folder, input_image_suffix,
                            input_features_suffix, output_folder, features)
    print err

    
    
def consolidate_trees(forest_folder, cons_forest_file):
    bestvar = []
    xbestsplit = []
    treemap = []
    nodestatus = []
    nodeclass = []
    ndbigtree = []
    
    ntree = np.zeros(1)
    
    
    #Load all the data
    forest_files = sorted(glob.glob(forest_folder + "\*.hdf5"))
    for forest in forest_files:
        f_file = h5py.File(forest, 'r')
    
        bestvar.append(f_file['/forest/bestvar'][...])
        xbestsplit.append(f_file['/forest/xbestsplit'][...])
        treemap.append(f_file['/forest/treemap'][...])
        nodestatus.append(f_file['/forest/nodestatus'][...])
        nodeclass.append(f_file['/forest/nodeclass'][...])
        ndbigtree.append(f_file['/forest/ndbigtree'][...])
        
        ntree += f_file['/forest/ntree'][...]
        f_file.close()
    
    #concatenate the data
    bestvar = np.vstack(bestvar)
    xbestsplit = np.vstack(xbestsplit)
    treemap = np.vstack(treemap)
    nodestatus = np.vstack(nodestatus)
    nodeclass = np.vstack(nodeclass)
    ndbigtree = np.vstack(ndbigtree)
    
    #aggregate data sets
    out_file = h5py.File(cons_forest_file, 'w')
    out_file['/forest/bestvar'] = bestvar
    out_file['/forest/xbestsplit'] = xbestsplit
    out_file['/forest/treemap'] = treemap
    out_file['/forest/nodestatus'] = nodestatus
    out_file['/forest/nodeclass'] = nodeclass
    out_file['/forest/ndbigtree'] = ndbigtree

    out_file['/forest/ntree'] = ntree
    
    #constant data
    f_file = h5py.File(forest_files[0], 'r')
    out_file['/forest/mtry'] = f_file['/forest/mtry'][...]
    out_file['/forest/nclass'] = f_file['/forest/nclass'][...]
    out_file['/forest/classweights'] = f_file['/forest/classweights'][...]
    out_file['/forest/nrnodes'] = f_file['/forest/nrnodes'][...]
    f_file.close()
    out_file.close()
    
    
if (__name__ == '__main__'):    
    main(sys.argv[1:])