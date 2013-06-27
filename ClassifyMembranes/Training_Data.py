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
import train_gpu_randomforest as forest
import gc


class Training_Data:
    def __init__(self, image_folder):
        self.feature_file_names = sorted(glob.glob(image_folder + "\*.hdf5"))
        self.image_file_names = sorted(glob.glob(image_folder + "\*.tif"))
        self.features, self.labels, self.files, self.keys = self.extract_data(self.feature_file_names, self.image_file_names)
        self.file_dict = self.make_file_dict()
        
    def make_file_dict(self):
        '''creates a dictionary with image names as keys to feature files'''
        #contains IMAGE name as key
        file_dict = dict((ea[2],ea[0]) for ea in self.files)
        return file_dict
        
    def extract_data(self, feature_file_names, image_file_names):
        '''Seeds the feature and label matrix with already labeled data'''
        labels = []
        features = []
        files = []
        
        for f_file, im_file in zip(feature_file_names, image_file_names):
            f = h5py.File(f_file, 'r')
            files.append([f, f_file, im_file]) #feature_file object, feature_file name, image_file_name
            '''im = cv2.imread(im_file)
            mask2 = im[:, :, 0] > np.maximum(im[:, :, 1], im[:, :, 2])
            mask1 = im[:, :, 1] > np.maximum(im[:, :, 0], im[:, :, 2])
            mask0 = im[:, :, 2] > np.maximum(im[:, :, 0], im[:, :, 1])
            mask_all = (mask0 | mask1 | mask2)
            labels.append((mask1 * 1 + mask2 * 2)[mask_all])
            for feature in f.keys():
                temp_features.append(f[feature][...][mask_all].astype(np.float32))
            features.append(np.vstack(temp_features))'''
            print "files " + f_file + ", " + im_file + " read"
        #return np.hstack(features), np.hstack(labels).astype(np.int32), files, files[0][0].keys()
        return features, labels, files, files[0][0].keys()
            
    #Currently assuming format of line data is [start, end, label, image]
    def update_features(self, lines):
        '''Appends new data from drawn lines to feature and label matrices'''
        self.check_lines(lines)
        print len(lines)
        num_pixels =0
        tot_pixels = 0
        new_labels = []
        for idx, (start, end, label, feature_file) in enumerate(lines):
            xdist = np.abs(start[0]-end[0])
            ydist = np.abs(start[1]-end[1])
            num_pixels=max(xdist+1, ydist+1)
            tot_pixels+=num_pixels
            #Expand the new labels from lines to pixels
            new_labels += [label]*num_pixels
        
        #append the new pixel labels
        #self.labels = np.hstack((self.labels, new_labels))
        self.labels =new_labels
        
        new_features = np.zeros((len(self.keys), tot_pixels))
    
        for idx, feature in enumerate(self.keys):
            offset = 0
            for start, end, label, feature_file in lines:
                f_file = self.file_dict[feature_file]
                #Get region of interest
                mini = min(start[0], end[0])
                maxi = max(start[0], end[0])
                minj = min(start[1], end[1])
                maxj = max(start[1], end[1])
                roi  = f_file[feature][mini:maxi+1, minj:maxj+1][...]
                
                #Get indices of pixels in line
                steps = max(maxi-mini+1, maxj-minj+1) #num pixels is size of larger dimension +1
                icoords = np.linspace(start[0]-mini, end[0]-mini, steps)[:-1]
                icoords = np.round(icoords).astype(np.int32)
                jcoords = np.linspace(start[1]-minj, end[1]-minj, steps)[:-1]
                jcoords = np.round(jcoords).astype(np.int32)
                #add the data for current line to feature array
                feat_data = roi[icoords, jcoords]
                new_features[idx, offset:offset+len(feat_data)] = feat_data
                offset += len(feat_data)
                
        #append the new features 
        '''if self.features == []:
            self.features = new_features       
        else:
            self.features = np.hstack((self.features, new_features))'''
        self.features = new_features
        print np.shape(self.features), np.shape(self.labels)    
        
    def check_lines(self, lines):
        '''Makes sure the lines are acceptable data. Removes lines that 
        do not fit in the image and outputs a warning'''
        
        #assumes all files are same size
        im_shape = np.shape(self.files[0][0][self.keys[0]])
        for start, end, label, feature_file in lines:
            if (start[0]>=im_shape[0] or end[0]>=im_shape[0]):
                warnings.warn("One of the x values is too large. " + str(start) + " " + str(end))
                lines.remove([start,end,label, feature_file])
            elif (start[1]>=im_shape[1] or end[1]>=im_shape[1]):
                warnings.warn("One of the y values is too large"  + str(start) + " " + str(end))
                lines.remove([start,end,label, feature_file])
            elif (start[0] < 0 or end[0] < 0):
                warnings.warn("one of the x values is less than 0" + str(start) + " " + str(end)) 
                lines.remove([start,end,label, feature_file])
            elif (start[1] < 0 or end[1]<0):
                warnings.warn("One of the y values is less than 0" + str(start) + " " + str(end))
                lines.remove([start,end,label, feature_file])
                
    def close_files(self):
        for file in self.files:
            file[0].close()
            
#data = Training_Data("C:\\Users\\DanielMiron\\Documents\\test")