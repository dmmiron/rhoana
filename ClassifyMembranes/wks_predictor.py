#------------------------
#Weighted Kitchen Sinks Predictor
#Daniel Miron
#6/25/2013
#
#------------------------

import numpy as np
import Training_Data as data
import matplotlib.pyplot as plt
import matplotlib.image as img
import wx

class Predictor:
    def __init__(self, in_queue, out_queue, data, parent_thread):
        self.data = data
        self.in_q = in_queue
        self.out_q = out_queue
        self.current_file = ""
        self.rules = "" 
        self.parent = parent_thread
        self.done = False
        self.overlay = ""
    
    def set_done(self, done):
        self.done = done
        
    def run(self):
        while True:
            if not self.done:
                self.get_from_queue()
            else:
                return
                
    def set_current_file(self, im_file):
        self.current_file = im_file
    
    def get_from_queue(self):
        '''retrieves from queue and determines correct action based on object received'''
        temp = self.in_q.get()
        print "predictor getting from queue"
        if (self.data.file_dict.has_key(temp)):
            self.current_file = temp
        else:
            self.rules = temp
        if (not (self.current_file == "" or self.rules == "")):
            self.predict()
        
    def predict(self):
        '''calculates a classification overlay'''
        f_file = self.data.file_dict[self.current_file]
        locs = dict((k,f_file[k]) for k in f_file)
        res= eval(self.rules, locs)
        self.make_overlay(res)
                
                                    
    def make_overlay(self, pred):
        '''creates the overlay and submits it to the output queue'''
        red = np.zeros_like(pred)
        green = np.zeros_like(pred)
        blue = np.zeros_like(pred)
        
        red = np.clip(1.0-pred, 0,1)
        blue = np.clip(pred-1.0, 0,1)
        green = 1.0-red-blue
        
        overlay = (np.dstack((red, green, blue))*255).astype(np.uint8)
        print "overlay ready"
        #plt.imshow(overlay)
        self.overlay = overlay
        self.out_q.put(overlay)
        '''self.viewer.Panel.set_array(overlay)
        self.viewer.Panel.set_image(overlay)
        self.viewer.Panel.Refresh()'''


