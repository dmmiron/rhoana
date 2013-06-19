#--------------------------------------
#Wrapper for Random Forest Classifier-Feature Elimination
#Daniel Miron
#6/17/2013
#--------------------------------------

import glob
import sys
sys.path.append(r'C:\Python27\Lib\site-packages')
import train_gpu_randomforest as trainer
import predict_gpu_randomforest as predict

def main(argv):
    im_folder = argv[0] #input images and features folder (currently autoencoder_top100)
    features = []
    
    #holds small forests as well as single consolidated forest
    forest_folder = 'C:\\Users\\DanielMiron\\Documents\\autoencoder_top100_forests\\autoencoder_top100'
    
    #combined small forests
    cons_forest_file = 'C:\\Users\\DanielMiron\\Documents\\autoencoder_top100_forests\\autoencoder_top100\\cons_forest.hdf5'
    
    training_iterations = 1
    
    #get features to eliminate from command line
    if (len(argv) > 1):
        features = [int(n) for n in argv[1].split(',') if n.isdigit()]
    
    trainer.train(im_folder, forest_folder, features, training_iterations)
    
    consolidate_trees(forest_folder, cons_forest_file)
    
    
    input_image_folder = 'C:\\Users\\DanielMiron\\Documents\\'
    input_image_suffix = '_labeled_update_sec.tif'
    input_features_suffix = '.hdf5'
    output_folder = 'C:\\Users\\DanielMiron\\Documents\\autoencoder_top100_output\\'
    err = predict.predict(forest_file, input_image_folder, input_image_suffix,
                            input_features_suffix, output_folder, features)
    print err

    
    
def consolidate_trees(forest_folder, cons_forest_file):
    #copy individual forest files into one single consolidated file    
    
    
if (__name__ == '__main__'):    
    main(sys.argv[1:])