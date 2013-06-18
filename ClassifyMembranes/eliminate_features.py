#--------------------------------------
#Wrapper for Random Forest Classifier-Feature Elimination
#Daniel Miron
#6/17/2013
#--------------------------------------

import glob
import sys
import train_gpu_randomforest as trainer
import predict_gpu_randomforest as predict

def main(argv):
    im_folder = argv[0]
    features = []
    forest_file = 'C:\\Users\\DanielMiron\\Documents\\rhoana_forest_3class.hdf5'
    
    if (len(argv) > 1):
        features = [int(n) for n in argv[1].split(',') if n.isdigit()]
    
    print im_folder
    
    trainer.train(im_folder, forest_file, features)
    input_image_folder = 'C:\\Users\\DanielMiron\\Documents\\third_round'
    input_image_suffix = '_labeled_update_sec.tif'
    input_features_suffix = '.hdf5'
    output_folder = 'C:\\Users\\DanielMiron\\Documents\\output\\'
    err = predict.predict(forest_file, input_image_folder, input_image_suffix,
                            input_features_suffix, output_folder, features)
    print err

    
    
if (__name__ == '__main__'):    
    main(sys.argv[1:])