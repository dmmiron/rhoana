#-------------------------------
#Training Updater-Adds new features and labels from sketch data and passes to training
#Daniel Miron
#6/21/2013
#
#-------------------------------
import sys
sys.path.append(r'C:\Python27\Lib\site-packages')
import h5py
import glob
import cv2
import numpy as np
import warnings

class Training_Data:
    def __init__(self, image_folder):
        self.feature_file_names = sorted(glob.glob(image_folder + "\*.hdf5"))
        self.image_file_names = sorted(glob.glob(image_folder + "\*.tif"))
        self.features, self.labels, self.files, self.keys = self.extract_data(self.feature_file_names, self.image_file_names)
        
    def extract_data(self, feature_file_names, image_file_names):
        '''Seeds the feature and label matrix with already labeled data'''
        labels = []
        features = []
        files = []
        
        for f_file, im_file in zip(feature_file_names, image_file_names):
            temp_features = []
            f = h5py.File(f_file, 'r')
            files.append([f, f_file, im_file]) #feature_file object, feature_file name, image_file_name
            im = cv2.imread(im_file)
            mask0 = im[:, :, 0] > np.maximum(im[:, :, 1], im[:, :, 2])
            mask1 = im[:, :, 1] > np.maximum(im[:, :, 0], im[:, :, 2])
            mask2 = im[:, :, 2] > np.maximum(im[:, :, 0], im[:, :, 1])
            mask_all = (mask0 | mask1 | mask2)
            labels.append((mask1 * 1 + mask2 * 2)[mask_all])
            for feature in f.keys():
                temp_features.append(f[feature][...][mask_all].astype(np.float32))
            features.append(np.vstack(temp_features))
            print "files " + f_file + ", " + im_file + " read"
        return np.hstack(features), np.hstack(labels).astype(np.int32), files, files[0][0].keys()
            
    
    
    #Currently assuming format of line data is [start, end, label, image]
    def update_features(self, feature_file, lines):
        '''Appends new data from drawn lines to feature and label matrices'''
        
        num_pixels =0
        new_labels = []
        for idx, (start, end, label) in enumerate(lines):
            xdist = np.abs(start[0]-end[0])
            ydist = np.abs(start[1]-end[1])
            num_pixels+=max(xdist+1, ydist+1)
            
            #Expand the new labels from lines to pixels
            new_labels += [label]*num_pixels
        
        #append the new pixel labels
        self.labels = np.hstack((self.labels, new_labels))
        
        new_features = np.zeros((len(feature_file.keys()), num_pixels))
    
        for idx, feature in enumerate(feature_file.keys()):
            offset = 0
            for start, end, label in lines:
                #Get region of interest
                mini = min(start[0], end[0])
                maxi = max(start[0], end[0])
                minj = min(start[1], end[1])
                maxj = max(start[1], end[1])
                roi  = feature_file[feature][mini:maxi+1, minj:maxj+1][...]
                
                #Get indices of pixels in line
                steps = max(maxi-mini+1, maxj-minj+1) #num pixels is size of larger dimension +1
                icoords = np.linspace(start[0]-mini, end[0]-mini, steps)
                icoords = np.round(icoords).astype(np.int32)
                jcoords = np.linspace(start[1]-minj, end[1]-minj, steps)
                jcoords = np.round(jcoords).astype(np.int32)
                #add the data for current line to feature array
                feat_data = roi[icoords, jcoords]
                print icoords,jcoords
                new_features[idx, offset:offset+len(feat_data)] = feat_data
                offset += len(feat_data)
                
        #append the new features       
        self.features = np.hstack((self.features, new_features))    
        
    def check_lines(self, lines):
        '''Makes sure the lines are acceptable data. Removes lines that 
        do not fit in the image and outputs a warning'''
        
        #assumes all files are same size
        im_shape = np.shape(self.files[0][0][self.keys[0]])
        for (start, end, label) in lines:
            if (start[0]>=im_shape[0] or end[0]>=im_shape[0]):
                warnings.warn("One of the x values is too large. " + str(start) + " " + str(end))
                lines.remove([start,end,label])
            elif (start[1]>=im_shape[1] or end[1]>=im_shape[1]):
                warnings.warn("One of the y values is too large"  + str(start) + " " + str(end))
                lines.remove([start,end,label])
            elif (start[0] < 0 or end[0] < 0):
                warnings.warn("one of the x values is less than 0" + str(start) + " " + str(end)) 
                lines.remove([start,end,label])
            elif (start[1] < 1 or end[1]<1):
                warnings.warn("One of the y values is less than 0" + str(start) + " " + str(end))
                lines.remove([start,end,label])
    
           
                
data = Training_Data(r'C:\Users\DanielMiron\Documents\test')
                