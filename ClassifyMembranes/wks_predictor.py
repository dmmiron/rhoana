#------------------------
#Weighted Kitchen Sinks Predictor
#Daniel Miron
#6/25/2013
#
#------------------------

import numpy as np
import Training_Data as data

class Predictor:
    def __init__(self, in_queue, out_queue, data):
        self.data = data
        self.in_q = in_queue
        self.out_q = out_queue
        self.current_file = ""
        self.rules = ""     
    
    def run(self):
        while True:
            self.get_from_queue()
    
    def get_from_queue(self):
        temp = self.in_q.get()
        if (self.data.file_dict.has_key(temp)):
            self.current_file = temp
        else:
            self.rules = temp
        if (not (self.current_file == "" or self.rules == "")):
            self.predict
        
    def predict(self, rules, feat_file):
        f_file = self.data.file_dict[feat_file]
        locs = dict((k,f_file[k]) for k in f_file)
        res= eval(rules, locs)
        self.make_overlay(res)
                
                                    
    def make_overlay(self, pred):
        red = np.zeros_like(pred)
        green = np.zeros_like(pred)
        blue = np.zeros_like(pred)
        
        red = np.clip(1.0-pred, 0,1)
        blue = np.clip(pred-1.0, 0,1)
        green = 1.0-red-blue
        
        overlay = (np.dstack((red, green, blue))*255).astype(np.uint8)
        self.out_q.put(overlay)

