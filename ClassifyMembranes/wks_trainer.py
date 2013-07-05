#----------------------
#Weighted Kitchen Sink Trainer
#Daniel Miron
#7/3/2013
#
#
#----------------------

from fastdot import fastdot
import numpy as np
import time

class Kitchen_Sink_Trainer:
    def __init__(self, data, num_rand, out_queue):
        self.data = data
        self.corr = None
        self.rhs = None
        self.first = True
        self.num_rand = num_rand
        self.out_q = out_queue
        
        
    def train(self, isVector):
            '''Adds current correlation and rhs to previous results then 
            computes and sends new rules to output queue'''
            featureized_data, new_feature_names = self.featureize(self.data.features, self.data.keys , self.num_rand)
            st = time.time()
            Corr = self.correlation_matrix_NZ(featureized_data, self.num_rand)
            print "Correlation took", time.time() - st
            rhs = np.dot(featureized_data.T, (self.data.labels))
            print "solving"
            if self.first:
                self.rhs = rhs
                self.corr = Corr
                self.first = False
            else:
                self.rhs+=rhs
                self.corr+=Corr
            
            weights, residuals, rank, s = np.linalg.lstsq(self.corr, self.rhs)
    
            # create the rules
            rules = " + ".join(["%f * (%s)" % (w, n) 
                            for w, n in zip(weights, new_feature_names)])
            rule_file = open(self.data.image_folder + "\\rules.txt", "w")
            rule_file.write(rules)
            rule_file.close()
            
            self.out_q.put(rules)
                            
    def featureize(self, D, names, num_new_features):
        '''For a KxN data matrix with K features, returns:
        - NxZ new 0/1 data matrix
        - Z new feature names of the form "feature > threshold"
        '''
        new_features = np.zeros((D.shape[1], num_new_features), dtype=np.uint8)
        new_names = []
        print D
        
        for idx, (feat_idx, thresh) in enumerate(self.data.rand_feat_indices):
            new_features[:,idx] = (D[feat_idx,:] > thresh)
            new_names.append("%s[...] > %f" % (names[int(feat_idx)], thresh))

        return new_features, new_names
        
    def correlation_matrix_NZ(self, D, num_rand_features):
        N, Z = D.shape
        assert Z == num_rand_features
        return fastdot(D)