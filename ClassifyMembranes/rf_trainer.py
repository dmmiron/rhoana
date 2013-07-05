#-----------------------
#Random Forest Trainer
#
#Daniel Miron
#7/2/2013
#-----------------------

import numpy as np
import forest


class Forest_Trainer:
    def __init__(self, data, bin_size, num_bins):
        self.data = data
        self.bin_size = bin_size
        self.num_bins = num_bins
        self.location = 0
        self.num_features = len(data.keys)
        self.bins = self.make_bins()
        self.forest = forest.Forest(nclass = 3) #will play around with ntrees for memory size
        self.iterations = 5 #will adjust with ntrees
        self.num_trees = 100
        
    def make_bins(self):
        bins = []
        for i in range(self.num_bins):
            bins.append([np.zeros((self.num_features, self.bin_size)), np.zeros(self.bin_size)])
        return bins 
            
    def fill_bins(self):
        '''Takes arrays of feature data and labels and fills bins, sampling if necessary'''
        #Enough space in bins to put all data
        if (self.location + np.size(self.data.labels) <= self.bin_size):
            for feature_bin, label_bin in self.bins:
                feature_bin[:,self.location:self.location+np.size(self.data.labels)] = self.data.features
                label_bin[self.location:self.location+np.size(self.data.labels)] = self.data.labels
            self.location += np.size(self.data.labels)
        #bins not yet full, but not enough room for all new data
        elif self.location < self.bin_size:
            for feature_bin, label_bin in self.bins:
                feature_bin[:,self.location:] = self.data.features[:,:self.bin_size-self.location]
                label_bin[self.location:] = self.data.labels[:self.bin_size-self.location]
                features = self.data.features[:,self.bin_size-self.location:]
                labels = self.data.labels[self.bin_size-self.location:]
            self.location += np.size(labels)
            
            #sample the remaining data into the bins
            self.sample(features, labels)
        #bins full
        else:
            self.sample(features, labels)
    
    def sample(self, features, labels):
        '''Given full bins and data samples new data in'''
        for feature_bin, label_bin in self.bins:
            for pixel in range(np.size(labels)):
                rand_loc = np.random.randint(0, self.location+1) #+1 to make inclusive
                if rand_loc < self.bin_size:
                    print "changed"
                    feature_bin[:,rand_loc] = features[:,pixel]
                    label_bin[rand_loc] = labels[pixel]
                self.location+=1
                
    def train(self):
        '''Trains a new forest'''
        for features, labels in self.bins:
            if self.location <self.bin_size:
                features = features[:,:self.location]
                labels = labels[:self.location]
            self.forest.make_forest(features, labels, self.num_trees, self.iterations)
        


