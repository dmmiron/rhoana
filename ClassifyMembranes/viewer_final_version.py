#http://wiki.wxpython.org  How to learn wxPython
'''https://svn.broadinstitute.org/CellProfiler/trunk/WormProfiler/drawdemo.py
list of event identifiers:
http://docs.wxwidgets.org/stable/wx_stdevtid.html

doodle code: http://wiki.wxpython.org/WxHowtoDrawing?action=raw

This module contains the DoodleWindow class which is a window that you
can do simple drawings upon.

checkout:
http://stackoverflow.com/questions/15760525/wx-staticbitmap-simple-transparency-mask-png-bmp
http://wiki.wxpython.org/WorkingWithImages#Converting_Binary-Valued_Alpha_Transparency_into_True_.28256_values.29_Alpha_Transparency
http://wiki.wxpython.org/Transparent%20Frames
http://wxpython.org/docs/api/wx.DC-class.html#Blit
http://stackoverflow.com/questions/5255325/getting-a-windows-transparency-wxpython
http://stackoverflow.com/questions/6670483/wxpythons-settransparent-doesnt-capture-user-input-if-set-to-an-opacity-of-zer
http://stackoverflow.com/questions/15760525/wx-staticbitmap-simple-transparency-mask-png-bmp
http://www.daniweb.com/software-development/python/threads/128350/starting-wxpython-gui-code


'''
# execfile("C:/Documents and Settings/Brian Baek/Desktop/py files/doodle_frame.py")

import os
import sys
sys.path.append(r'C:\Python27\Lib\site-packages')
import wx
import cv2
import numpy as np
import numpy.random as rand
import threading
from Queue import Queue
import wks_predictor as predictor
import wks_trainer as trainer


class ImagePanel(wx.Panel):
    """ 
    A very simple panel for displaying a wx.Image
    """
    def __init__(self, image, arr, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        
        self.image = image
        self.arr = arr
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def set_array(self, array):
        self.arr = array
        self.Refresh()
        
    def set_image(self, array):
        image = wx.ImageFromBuffer(np.shape(array)[0], np.shape(array)[1], array)
        self.image = image 
        self.Refresh()
         
    def new_image(self, array):
        self.arr = array
        self.Refresh()
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(wx.BitmapFromImage(self.image), 0, 0)
        

class DemoFrame(wx.Frame):
    """ This window displays a button """
    def __init__(self, title = "Micro App"):
        wx.Frame.__init__(self, None , -1, title)

        MenuBar = wx.MenuBar()
        FileMenu = wx.Menu()

        item = FileMenu.Append(wx.ID_ANY, text = "&Open")
        self.Bind(wx.EVT_MENU, self.OnOpen, item)

        item = FileMenu.Append(wx.ID_PREFERENCES, text = "&Preferences")
        self.Bind(wx.EVT_MENU, self.OnPrefs, item)

        item = FileMenu.Append(wx.ID_EXIT, text = "&Exit")
        self.Bind(wx.EVT_MENU, self.OnQuit, item)

        MenuBar.Append(FileMenu, "&File")
        
        HelpMenu = wx.Menu()

        item = HelpMenu.Append(wx.ID_HELP, "Test &Help",
                                "Help for this simple test")
        self.Bind(wx.EVT_MENU, self.OnHelp, item)

        ## this gets put in the App menu on OS-X
        item = HelpMenu.Append(wx.ID_ABOUT, "&About",
                                "More information About this program")
        self.Bind(wx.EVT_MENU, self.OnAbout, item)
        MenuBar.Append(HelpMenu, "&Help")

        self.SetMenuBar(MenuBar)

        btn = wx.Button(self, label = "NewImage")
        btn.Bind(wx.EVT_BUTTON, self.OnNewImage )

        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        ##Create numpy array, and image from it
        w = h = 1000
        self.array = rand.randint(0, 255, (h, w, 3)).astype('uint8')
        print self.array
        image = wx.ImageFromBuffer(w, h, self.array)
        #image = wx.Image("Images/cute_close_up.jpg")
        self.Panel = ImagePanel(image, self.array, self)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(btn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer.Add(self.Panel, 1, wx.GROW)
        
        self.SetSizer(sizer)

    def new_image(self, array):
        self.array = array
        self.Panel.Refresh()
        
    def OnNewImage(self, array, event = None):
        """
        create a new image by changing underlying numpy array
        """
        self.array = array
        self.Panel.Refresh()
        
        
    def OnQuit(self,Event):
        self.Destroy()
        
    def OnAbout(self, event):
        dlg = wx.MessageDialog(self, "This is a small program to test\n"
                                     "the use of menus on Mac, etc.\n",
                                "About Me", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnHelp(self, event):
        dlg = wx.MessageDialog(self, "This would be help\n"
                                     "If there was any\n",
                                "Test Help", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnOpen(self, event):
        dlg = wx.MessageDialog(self, "This would be an open Dialog\n"
                                     "If there was anything to open\n",
                                "Open File", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnPrefs(self, event):
        dlg = wx.MessageDialog(self, "This would be an preferences Dialog\n"
                                     "If there were any preferences to set.\n",
                                "Preferences", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()


"""class DoodleWindow(wx.Window):
    # colours = ['Black', 'Yellow', 'Red', 'Green', 'Blue', 'Purple', 
    #     'Brown', 'Aquamarine', 'Forest Green', 'Light Blue', 'Goldenrod', 
    #     'Cyan', 'Orange', 'Navy', 'Dark Grey', 'Light Grey']
    colours = ['Red', 'Green', 'Blue']

    # thicknesses = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128]
    thicknesses = [1, 2, 3, 4]

    def __init__(self, parent):
        super(DoodleWindow, self).__init__(parent, 
            style=wx.NO_FULL_REPAINT_ON_RESIZE)
        self.initDrawing()
        self.makeMenu()
        self.bindEvents()
        self.initBuffer()
        
    def initDrawing(self):
        # self.SetBackgroundColour('WHITE')
        self.currentThickness = self.thicknesses[0] 
        self.currentColour = self.colours[0]
        self.lines = []
        self.previousPosition = (0, 0)
        self.filename = 'C:\\Users\\DanielMiron\\Documents\\test\\04_labeled_update_sec.tif' 


    def bindEvents(self):

        # keystroke_original_img = wx.NewId()
        # keystroke_overlay_img = wx.NewId()

        # # forward_key = wx.NewId()
        # # back_key = wx.NewId()
        
        # self.accel_tbl = wx.AcceleratorTable([(wx.ACCEL_NORMAL, ord('I'), keystroke_original_img,
        #                                         wx.ACCEL_NORMAL, ord('O'), keystroke_overlay_img,
        #                                     # wx.ACCEL_NORMAL, ord('A'), back_key),
        #                                     #   (wx.ACCEL_NORMAL, ord('D'), forward_key)                              
        #                                      )])
        # self.SetAcceleratorTable(self.accel_tbl)


        # # Event bindings--
        # self.Bind(wx.EVT_MENU, self.onImageKey, id=keystroke_original_img)
        # self.Bind(wx.EVT_MENU, self.onOverlayKey, id=keystroke_overlay_img)
        # # self.Bind(wx.EVT_MENU, self.onForwardKey, id=forward_key)
        # # self.Bind(wx.EVT_MENU, self.onBackKey, id=back_key)

        for event, handler in [ \
                (wx.EVT_LEFT_DOWN, self.onLeftDown), # Start drawing
                (wx.EVT_LEFT_UP, self.onLeftUp),     # Stop drawing 
                (wx.EVT_MOTION, self.onMotion),      # Draw
                (wx.EVT_RIGHT_UP, self.onRightUp),   # Popup menu
                (wx.EVT_SIZE, self.onSize),          # Prepare for redraw
                (wx.EVT_IDLE, self.onIdle),          # Redraw
                (wx.EVT_PAINT, self.onPaint),        # Refresh
                (wx.EVT_WINDOW_DESTROY, self.cleanup)]:
            self.Bind(event, handler)

    def initBuffer(self):
        ''' Initialize the bitmap used for buffering the display. '''
        size = self.GetClientSize()
        graphicFilename = 'C:\\Users\\DanielMiron\\Documents\\test\\04_labeled_update_sec.tif' 
        #'C:/Documents and Settings/Brian Baek/Desktop/py files/ECS_training_data/04_labeled_update_sec.tif'
        predictor_filename = 'C:\\Users\\DanielMiron\\Documents\\test\\04_labeled_update_sec.tif'
        self.predictor_output = wx.Image( predictor_filename , wx.BITMAP_TYPE_ANY )
        self.image = wx.Image( graphicFilename, wx.BITMAP_TYPE_ANY )

        width = self.image.GetWidth()
        height = self.image.GetHeight()
        self.buffer = wx.EmptyImage(width, height)

        opacity = 0.5
        for y in xrange(height):
            for x in xrange(width):
                r = opacity * self.image.GetRed(x, y) + (1-opacity) * self.predictor_output.GetRed(x, y)
                g = opacity * self.image.GetGreen(x, y) + (1-opacity) * self.predictor_output.GetGreen(x, y)
                b = opacity * self.image.GetBlue(x, y) + (1-opacity) * self.predictor_output.GetBlue(x, y)
                self.buffer.SetRGB(x, y, r, g, b)
        self.buffer = self.buffer.ConvertToBitmap()

        # self.buffer = wx.Bitmap("C:/Documents and Settings/Brian Baek/Desktop/py files/ECS_training_data/04_labeled_update_sec.tif")


        # self.buffer = wx.EmptyBitmap(size.width, size.height)
        # dc = wx.BufferedDC(None, self.buffer)

        dc = wx.MemoryDC()
        dc.SelectObject(self.buffer)
        dc.SelectObject(wx.NullBitmap) 
        # dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        self.drawLines(dc, *self.lines)
        self.reInitBuffer = False


    def onPaint(self, event):
        ''' Called when the window is exposed. '''
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.  Since we don't need to draw anything else
        # here that's all there is to it.
        dc = wx.BufferedPaintDC(self, self.buffer)  



    def makeMenu(self):
        ''' Make a menu that can be popped up later. '''
        self.menu = wx.Menu()
        self.idToColourMap = self.addCheckableMenuItems(self.menu, 
            self.colours)
        self.bindMenuEvents(menuHandler=self.onMenuSetColour,
            updateUIHandler=self.onCheckMenuColours,
            ids=self.idToColourMap.keys())
        self.menu.Break() # Next menu items go in a new column of the menu
        self.idToThicknessMap = self.addCheckableMenuItems(self.menu,
            self.thicknesses)
        self.bindMenuEvents(menuHandler=self.onMenuSetThickness,
            updateUIHandler=self.onCheckMenuThickness,
            ids=self.idToThicknessMap.keys())

    @staticmethod
    def addCheckableMenuItems(menu, items):
        ''' Add a checkable menu entry to menu for each item in items. This
            method returns a dictionary that maps the menuIds to the
            items. '''
        idToItemMapping = {}
        for item in items:
            menuId = wx.NewId()
            idToItemMapping[menuId] = item
            menu.Append(menuId, str(item), kind=wx.ITEM_CHECK)
        return idToItemMapping

    def bindMenuEvents(self, menuHandler, updateUIHandler, ids): 
        ''' Bind the menu id's in the list ids to menuHandler and
            updateUIHandler. ''' 
        sortedIds = sorted(ids)
        firstId, lastId = sortedIds[0], sortedIds[-1]
        for event, handler in \
                [(wx.EVT_MENU_RANGE, menuHandler),
                 (wx.EVT_UPDATE_UI_RANGE, updateUIHandler)]:
            self.Bind(event, handler, id=firstId, id2=lastId)

    # Event handlers:"""
    
    
    
class ImageWindow(wx.Window):

    colours = ['Red', 'Green', 'Blue']

    thicknesses = [1, 2, 4]

    def __init__(self, parent):

        super(ImageWindow, self).__init__(parent, 
            style=wx.NO_FULL_REPAINT_ON_RESIZE)
        self.initDrawing()
        self.makeMenu()
        self.bindEvents()
        self.initBuffer()


        self.picPaths = []
        self.currentPicture = 0
        self.totalPictures = 0
        print "init Imagewindow"


    def initDrawing(self):
        # self.SetBackgroundColour('WHITE')
        self.currentThickness = self.thicknesses[0] 
        self.currentColour = self.colours[0]
        self.lines = []
        self.previousPosition = (0, 0)

        # CHANGE FILENAME TO LOCAL FILE!!
        self.filename = 'C:\\Users\\DanielMiron\\Documents\\test\\04_labeled_update_sec.tif' 
        # "C:/Documents and Settings/Brian Baek/Desktop/py files/ECS_training_data/04_labeled_update_sec.tif")
        self.opacity = 0.5  # opacity level for initBuffer()

    
    ###############################################


    def bindEvents(self):

        key_original_img = wx.NewId()
        key_overlay_img = wx.NewId()
        key_composite_img = wx.NewId()
        # forward_key = wx.NewId()
        # back_key = wx.NewId()
        
        self.accel_tbl = wx.AcceleratorTable([(wx.ACCEL_NORMAL, ord('W'), key_original_img), 
            (wx.ACCEL_NORMAL, ord('E'), key_overlay_img),
            (wx.ACCEL_NORMAL, ord('R'), key_composite_img)])
            # (wx.ACCEL_NORMAL, ord('D'), forward_key)])
                                            #   (wx.ACCEL_NORMAL, ord('D'), forward_key)                              
        self.SetAcceleratorTable(self.accel_tbl)

        # # Event bindings--
        self.Bind(wx.EVT_MENU, self.onReturnImage, id=key_original_img)
        self.Bind(wx.EVT_MENU, self.onReturnOverlay, id=key_overlay_img)
        self.Bind(wx.EVT_MENU, self.onReturnComposite, id=key_composite_img)


        # self.Bind(wx.EVT_MENU, self.nextPicture, id=forward_key)
  
        # self.Bind(wx.EVT_MENU, self.onBackKey, id=back_key)

        for event, handler in [ \
                (wx.EVT_LEFT_DOWN, self.onLeftDown), # Start drawing
                (wx.EVT_LEFT_UP, self.onLeftUp),     # Stop drawing 
                (wx.EVT_MOTION, self.onMotion),      # Draw
                (wx.EVT_RIGHT_UP, self.onRightUp),   # Popup menu
                (wx.EVT_SIZE, self.onSize),          # Prepare for redraw
                (wx.EVT_IDLE, self.onIdle),          # Redraw
                (wx.EVT_PAINT, self.onPaint),        # Refresh
                (wx.EVT_WINDOW_DESTROY, self.cleanup)]:
            self.Bind(event, handler)




    def initBuffer(self):
        ''' Initialize the bitmap used for buffering the display. '''
       
        size = self.GetClientSize()
       
        # Single file = predictor  
        # predictor_filename = 'C:/Users/brian/Desktop/ECS_training_data/04_labeled_update_sec.tif_cuda_pred.tif'
        # self.predictor_output = wx.Image( predictor_filename , wx.BITMAP_TYPE_ANY )
       
        self.image_array = cv2.imread(self.filename)
        self.predictor_array = []
        
        self.image = wx.Image( self.filename, wx.BITMAP_TYPE_ANY )  #self.image is original image(wx.Image)
        self.width = self.image.GetWidth()
        self.height = self.image.GetHeight()
        self.image_bmap = self.image.ConvertToBitmap()      # original image
        self.buffer = self.image_bmap
       
         
        self.dc = wx.MemoryDC()
        self.dc.SelectObject(self.buffer)
        self.dc.SelectObject(wx.NullBitmap) 
        # dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        self.dc.Clear()
        self.drawLines(self.dc, *self.lines)
        self.reInitBuffer = False


    def onPaint(self, event):
        ''' Called when the window is exposed. '''
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.  Since we don't need to draw anything else
        # here that's all there is to it.
        dc = wx.BufferedPaintDC(self, self.buffer)     #draws buffer_bmap to client wx.Window

    def makeMenu(self):
        ''' Make a menu that can be popped up later. '''
        self.menu = wx.Menu()
        self.idToColourMap = self.addCheckableMenuItems(self.menu, 
            self.colours)
        self.bindMenuEvents(menuHandler=self.onMenuSetColour,
            updateUIHandler=self.onCheckMenuColours,
            ids=self.idToColourMap.keys())
        self.menu.Break() # Next menu items go in a new column of the menu
        self.idToThicknessMap = self.addCheckableMenuItems(self.menu,
            self.thicknesses)
        self.bindMenuEvents(menuHandler=self.onMenuSetThickness,
            updateUIHandler=self.onCheckMenuThickness,
            ids=self.idToThicknessMap.keys())

    @staticmethod
    def addCheckableMenuItems(menu, items):
        ''' Add a checkable menu entry to menu for each item in items. This
            method returns a dictionary that maps the menuIds to the
            items. '''
        idToItemMapping = {}
        for item in items:
            menuId = wx.NewId()
            idToItemMapping[menuId] = item
            menu.Append(menuId, str(item), kind=wx.ITEM_CHECK)
        return idToItemMapping

    def bindMenuEvents(self, menuHandler, updateUIHandler, ids): 
        ''' Bind the menu id's in the list ids to menuHandler and
            updateUIHandler. ''' 
        sortedIds = sorted(ids)
        firstId, lastId = sortedIds[0], sortedIds[-1]
        for event, handler in \
                [(wx.EVT_MENU_RANGE, menuHandler),
                 (wx.EVT_UPDATE_UI_RANGE, updateUIHandler)]:
            self.Bind(event, handler, id=firstId, id2=lastId)

    #----------

    # Switch display image events
    def onReturnImage(self, event):
        self.buffer = self.image_bmap
        self.dc.SelectObject(self.buffer)
        self.Refresh()      # changes display image on wx.Window
        print "ReturnImage"

    # Receive predictor overlay from queue, then display
    def onReturnOverlay(self, event):
        w = self.width
        h= self.height
        

        # Random generated array input example 
        # self.predictor_array = rand.randint(0, 255, (h, w, 3)).astype('uint8')

    
        # Receive array from display_input queue
        while not display_queue.empty():
            self.predictor_array = display_queue.get()
        if not self.predictor_array == []:
        #print self.predictor_array        
            image = wx.ImageFromBuffer(w, h, self.predictor_array)
            print np.shape(self.predictor_array)
            self.predictor_output_bmap = image.ConvertToBitmap()    # predictor classifier overlay
            self.buffer = self.predictor_output_bmap
            self.dc.SelectObject(self.buffer)
            self.Refresh()
            print "ReturnOverlay"

    def onReturnComposite(self, event):
        if not self.predictor_array == []:
            # Convert predictor overlay from bitmap to wx.Image
            self.predictor_overlay_image = wx.ImageFromBitmap (self.predictor_output_bmap)
    
            # Composite image (image + overlay) generator
            w = self.width
            h= self.height
            self.composite = wx.EmptyImage(w, h)
            opacity = 0.5
            
            self.composite_array = (opacity*self.image_array + (1-opacity)*self.predictor_array).astype(np.uint8)
            print self.composite_array, np.shape(self.composite_array)
            image = wx.ImageFromBuffer(w, h, self.composite_array)
            self.composite_bitmap = image.ConvertToBitmap()
            
            # Display image
            self.buffer =  self.composite_bitmap
            self.dc.SelectObject(self.buffer)
            self.Refresh()
            print "ReturnComposite" 

    def onLeftDown(self, event):
        ''' Called when the left mouse button is pressed. '''
        
        self.currentLine = []
        self.previousPosition = event.GetPositionTuple()
        self.CaptureMouse()

    def onLeftUp(self, event):
        ''' Called when the left mouse button is released. '''
        if self.HasCapture():
            self.lines.append((self.currentColour, self.currentThickness, 
                self.currentLine))
            self.currentLine = []
            self.releasePosition = event.GetPositionTuple()
            self.ReleaseMouse()

    def onRightUp(self, event):
        ''' Called when the right mouse button is released, will popup
            the menu. '''
        self.PopupMenu(self.menu)

    def onMotion(self, event):
        ''' Called when the mouse is in motion. If the left button is
            dragging then draw a line from the last event position to the
            current one. Save the coordinants for redraws. '''
        if event.Dragging() and event.LeftIsDown():
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            currentPosition = event.GetPositionTuple()
            lineSegment = self.previousPosition + currentPosition
            self.drawLines(dc, (self.currentColour, self.currentThickness, 
                [lineSegment]))
            self.currentLine.append(lineSegment)
            self.previousPosition = currentPosition
            
            # color numerical code 
            if self.currentColour=='Red':
                self.colorcode = 0
            elif self.currentColour=='Green':
                self.colorcode = 1
            elif self.currentColour=='Blue':
                self.colorcode = 2


            # place line coordinates, color label, and filename in job_queue
            item = [lineSegment[:2], lineSegment[2:], self.colorcode, self.filename]  
            print item
            training_queue.put(item)
            
    def onSize(self, event):
        ''' Called when the window is resized. We set a flag so the idle
            handler will resize the buffer. '''
        self.reInitBuffer = True

    def onIdle(self, event):
        ''' If the size was changed then resize the bitmap used for double
            buffering to match the window size.  We do it in Idle time so
            there is only one refresh after resizing is done, not lots while
            it is happening. '''
        if self.reInitBuffer:
            self.initBuffer()
            self.Refresh(False)


    def cleanup(self, event):
        if hasattr(self, "menu"):
            self.menu.Destroy()
            del self.menu

    # These two event handlers are called before the menu is displayed
    # to determine which items should be checked.
    def onCheckMenuColours(self, event):
        colour = self.idToColourMap[event.GetId()]
        event.Check(colour == self.currentColour)

    def onCheckMenuThickness(self, event):
        thickness = self.idToThicknessMap[event.GetId()]
        event.Check(thickness == self.currentThickness)

    # Event handlers for the popup menu, uses the event ID to determine
    # the colour or the thickness to set.
    def onMenuSetColour(self, event):
        self.currentColour = self.idToColourMap[event.GetId()]

    def onMenuSetThickness(self, event):
        self.currentThickness = self.idToThicknessMap[event.GetId()]

    # Other methods
    @staticmethod
    def drawLines(dc, *lines):
        ''' drawLines takes a device context (dc) and a list of lines
        as arguments. Each line is a three-tuple: (colour, thickness,
        linesegments). linesegments is a list of coordinates: (x1, y1,
        x2, y2). '''
        dc.BeginDrawing()
        for colour, thickness, lineSegments in lines:
            pen = wx.Pen(wx.NamedColour(colour), thickness, wx.SOLID)
            dc.SetPen(pen)
            for lineSegment in lineSegments:
                dc.DrawLine(*lineSegment)
        dc.EndDrawing()



class DoodleFrame(wx.Frame):
    def __init__(self, parent=None):
        super(DoodleFrame, self).__init__(parent, title="Doodle Frame", 
            size=(1024, 1024), 
            style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        doodle = ImageWindow(self)
        self.window = doodle

#---------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(False)
    frame = DoodleFrame()
    frame.Show()
    #overlay_frame = DemoFrame()
    #overlay_frame.Show()
    #overlay_viewer = ImagePanel(None, None)

    
    # Create job queue and thread
    training_queue = Queue()
    predictor_queue =Queue()
    display_queue = Queue()
    
    trainer = trainer.Trainer('C:\\Users\\DanielMiron\\Documents\\test', training_queue, predictor_queue, threading.currentThread())
    predictor = predictor.Predictor(predictor_queue, display_queue, trainer.data, threading.currentThread())
    
    #set the number of random features chosen in kitchen sinks
    trainer.set_num_rand(1000)
    
    #set the first picture opened (used during testing)
    predictor.set_current_file('C:\\Users\\DanielMiron\\Documents\\test\\04_labeled_update_sec.tif')
    
    training_worker = threading.Thread(target = trainer.run, name = "trainer")
    predicting_worker = threading.Thread(target = predictor.run, name = "predictor")
    
    training_worker.daemon = True
    predicting_worker.daemon = True
    
    training_worker.start()
    predicting_worker.start()

    app.MainLoop()
    
    #Force trainer and predictor to stop
    trainer.set_done(True)
    predictor.set_done(True)
    
