#--------------------------
#Weighted Kitchen Sink Trainer
#Daniel Miron
#6/25/2013
#
#--------------------------

import sys
import time
import numpy as np
import Training_Data as data
import random

from fastdot import fastdot


class Trainer:
    def __init__(self, image_folder, in_queue, out_queue, parent_thread):
        self.data = data.Training_Data(image_folder)
        self.in_q = in_queue
        self.out_q = out_queue
        self.num_rand = 0
        self.parent = parent_thread
        self.done = False
        
    def set_done(self, done):
        self.done = done
        
    def run(self):
        trained = True
        print "trainer running"
        while True:
            if not self.done:
                trained = self.get_from_queue(trained)
            else:
                return
                
    def get_from_queue(self, trained):
        if (self.in_q.empty() and not trained):
            time.sleep(3)
            self.train()
            return True
        elif (self.in_q.empty()):
            time.sleep(3)
            return True
        else:
            temp = []
            timeout = False
            while True:
                while not self.in_q.empty():
                    timeout = False
                    temp += [self.in_q.get()]
                    if len(temp)==1000:
                        self.data.update_features(temp)
                        return False
                time.sleep(5)
                if self.in_q.empty():
                    self.data.update_features(temp)
                    return False
            
    def set_num_rand(self, num):
        self.num_rand = num

    def train(self):
        featureized_data, new_feature_names = self.featureize(self.data.features, self.data.keys , self.num_rand)
        st = time.time()
        Corr = self.correlation_matrix_NZ(featureized_data, self.num_rand)
        print "Correlation took", time.time() - st
        rhs = np.dot(featureized_data.T, (self.data.labels))
        print "solving"
        weights, residuals, rank, s = np.linalg.lstsq(Corr, rhs)

        # create the rules
        rules = " + ".join(["%f * (%s)" % (w, n) 
                        for w, n in zip(weights, new_feature_names)])
        print "solved"
        self.out_q.put(rules)
                        
    def featureize(self, D, names, num_new_features):
        '''For a KxN data matrix with K features, returns:
          - NxZ new 0/1 data matrix
          - Z new feature names of the form "feature > threshold"
        '''
        
        new_names = []
        print D
        new_features = np.zeros((D.shape[1], num_new_features), dtype=np.uint8)
        for n in range(num_new_features):
            idx = np.random.choice(D.shape[0])
            thresh = np.random.choice(D[idx, :])
            new_names.append("%s[...] > %f" % (names[idx], thresh))
            new_features[:, n] = (D[idx, :] > thresh)
        return new_features, new_names
        
    def correlation_matrix_NZ(self, D, num_rand_features):
        N, Z = D.shape
        assert Z == num_rand_features
        return fastdot(D)
        
