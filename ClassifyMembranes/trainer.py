#--------------------------
#General Trainer-Has both kitchen sink and random forest training abilities
#Daniel Miron
#6/25/2013
#
#--------------------------

import sys
import time
import numpy as np
import Training_Data as data
import random
import rf_trainer as rf
import wks_trainer as wks

from fastdot import fastdot


class Trainer:
    def __init__(self, image_folder, in_queue, out_queue, parent_thread, 
                num_rand_features, num_bins, bin_size):
        self.data = data.Training_Data(image_folder, num_rand_features)
        self.wks = wks.Kitchen_Sink_Trainer(self.data, num_rand_features)
        self.rf = rf.Forest_Trainer(self.data, bin_size, num_bins)
        self.in_q = in_queue
        self.out_q = out_queue
        self.parent = parent_thread
        self.done = False

    def set_done(self, done):
        self.done = done
        
    def run(self):
        #self.train()
        while True:
            if not self.done:
                self.get_from_queue()
            else:
                return
                
    def get_from_queue(self):
        '''Gets data from queue and controls flow of training'''
        if (self.in_q.empty()):
            time.sleep(3)
            return
        else:
            temp = []
            while True:
                while not self.in_q.empty():
                    temp += [self.in_q.get()]
                    if len(temp)==300:
                        self.data.update_features(temp)
                        self.wks.train(True)
                        #self.data.mask()
                        #self.train(False)
                        return
                time.sleep(3)
                if self.in_q.empty():
                    self.data.update_features(temp)
                    self.wks.train(True)
                    #self.data.mask()
                    #self.train(False)
                    return


        
