import os
import sys
import wx
import threading
from Queue import Queue
import numpy as np
import numpy.random as rand
import glob

sys.path.append('C:\Python27\Lib\site-packages')
import cv2
import wks_predictor as predictor
import main_trainer as trainer


class ImageWindow(wx.Window):

    colours = ['Red', 'Green', 'Blue']

    thicknesses = [1,3,5,7,9]

    def __init__(self, parent):
        super(ImageWindow, self).__init__(parent, style=wx.NO_FULL_REPAINT_ON_RESIZE) 
        
        self.folderPath = ""

        dialog = wx.DirDialog(None, "Choose a directory:",
        style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal() == wx.ID_OK:
            self.folderPath = dialog.GetPath()
            picPaths = sorted(glob.glob(self.folderPath + "\\*.tif"))
            print "Folder path is:", self.folderPath
            print "Pictures loaded..."

        self.file_list = []
        self.file_index = 0
        for filename in picPaths: 
            if filename.endswith('.tif'):
                self.file_list += [filename]  

        self.initDrawing()
        self.makeMenu()
        self.bindEvents()
        self.initBuffer()



    #-----
    def initDrawing(self):
        # self.SetBackgroundColour('WHITE')
        self.currentThickness = self.thicknesses[0] 
        self.currentColour = self.colours[0]
        self.lines = []
        self.previousPosition = (0, 0)
        self.filename = self.file_list[0]
        predictor_queue.put(self.filename)
        # "C:\\Documents and Settings\\Brian Baek\\Desktop\\py files\\ECS_training_data\\04_labeled_update_sec.tif")



    #-----
    def initBuffer(self):
        ''' Initialize the bitmap used for buffering the display. '''
        size = self.GetClientSize()
        self.image_arrays = []
        self.bitmaps = []
        for im in self.file_list:
            self.image_arrays.append(cv2.imread(im))
            image = wx.Image(im, wx.BITMAP_TYPE_ANY)
            self.bitmaps.append(image.ConvertToBitmap())
            
        self.image_array = cv2.imread(self.filename)
        self.predictor_array = []

        # get height and width of images (assumes all are same size)   
        self.width = image.GetWidth() 
        self.height = image.GetHeight()
        
        #load first image into buffer
        self.buffer = self.bitmaps[self.file_index]
       
        self.dc = wx.MemoryDC()
        self.dc.SelectObject(self.buffer)
        self.dc.SelectObject(wx.NullBitmap)
        # dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        self.dc.Clear()
        self.drawLines(self.dc, *self.lines)
        self.reInitBuffer = False


    #-----
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
    

    #-----
    def bindEvents(self):

        key_original_img = wx.NewId()
        key_overlay_img = wx.NewId()
        key_composite_img = wx.NewId()
        forward_key = wx.NewId()
        back_key = wx.NewId()

        # Creates hotkeys
        self.accel_tbl = wx.AcceleratorTable([(wx.ACCEL_NORMAL, ord('W'), key_original_img), 
            (wx.ACCEL_NORMAL, ord('E'), key_overlay_img),
            (wx.ACCEL_NORMAL, ord('R'), key_composite_img),
            (wx.ACCEL_NORMAL, ord('F'), forward_key),
            (wx.ACCEL_NORMAL, ord('B'), back_key)])                                             
        self.SetAcceleratorTable(self.accel_tbl)


        # Event bindings
        self.Bind(wx.EVT_MENU, self.onReturnImage, id=key_original_img)
        self.Bind(wx.EVT_MENU, self.onReturnOverlay, id=key_overlay_img)
        self.Bind(wx.EVT_MENU, self.onReturnComposite, id=key_composite_img)
        self.Bind(wx.EVT_MENU, self.ForwardImage, id=forward_key)
        self.Bind(wx.EVT_MENU, self.ReverseImage, id=back_key)

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


    def onPaint(self, event):
        ''' Called when the window is exposed. '''
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.  Since we don't need to draw anything else
        # here that's all there is to it.
        dc = wx.BufferedPaintDC(self, self.buffer)     #draws buffer_bmap to client wx.Window


    #-----
    # Switch display image events
    def onReturnImage(self, event):
        self.buffer = self.bitmaps[self.file_index]
        self.dc.SelectObject(self.buffer)
        self.Refresh()      # changes display image on wx.Window
        print "ReturnImage"
    

    def onReturnOverlay(self, event):
        w = self.width
        h= self.height
        print "overlay"  
        # Receive array from display_input queue
        while not display_queue.empty():
            self.predictor_array = display_queue.get()
        if not self.predictor_array == []:
            image = wx.ImageFromBuffer(w, h, self.predictor_array)
            print np.shape(self.predictor_array)
            self.predictor_output_bmap = image.ConvertToBitmap() # predictor classifier overlay
            self.buffer = self.predictor_output_bmap
            self.dc.SelectObject(self.buffer)
            self.Refresh()
            print "ReturnOverlay"


    def onReturnComposite(self, event):
        while not display_queue.empty():
            self.predictor_array = display_queue.get()
        if not self.predictor_array == []:
            # Convert predictor overlay from bitmap to wx.Image
            self.predictor_overlay_image = wx.ImageFromBitmap (self.predictor_output_bmap)
    
            # Composite image (image + overlay) generator
            w = self.width
            h= self.height
            self.composite = wx.EmptyImage(w, h)
            self.opacity = 0.5
            self.composite_array = (self.opacity*self.image_arrays[self.file_index] 
                                    + (1-self.opacity)*self.predictor_array).astype(np.uint8)
            image = wx.ImageFromBuffer(w, h, self.composite_array)
            composite_bitmap = image.ConvertToBitmap()
            
            # Display image
            self.buffer = composite_bitmap
            self.dc.SelectObject(self.buffer)
            self.Refresh()
            print "ReturnComposite" 


    def ForwardImage(self, event):
        if self.file_index == (len(self.file_list)-1):
            self.file_index = 0
            print "beginning(load)Image"
        else:
            self.file_index +=1
        image = self.file_list[self.file_index]
        self.buffer = self.bitmaps[self.file_index]
        self.dc.SelectObject(self.buffer)
        self.Refresh()  
        print "Viewing: %s" % image
        predictor_queue.put(image)


    def ReverseImage(self, event):
        if self.file_index == 0:
            self.file_index = len(self.file_list)-1
            print "beginning(rev)Image"
        else:
            self.file_index -=1

        image = self.file_list[self.file_index]
        self.buffer = self.bitmaps[self.file_index]
        self.dc.SelectObject(self.buffer)
        self.Refresh()  
        print "Viewing: %s" % image
        predictor_queue.put(image)


    # Mouse buttons and motion:
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


            # color = numerical code 
            if self.currentColour=='Red':
                self.colorcode = 0
            elif self.currentColour=='Green':
                self.colorcode = 1
            elif self.currentColour=='Blue':
                self.colorcode = 2

            # place line coordinates, color label, and filename in training_queue
            item = [lineSegment[:2], lineSegment[2:], self.colorcode, self.currentThickness, self.filename]  
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


#-----

class ImageFrame(wx.Frame):
    def __init__(self, parent=None):
        super(ImageFrame, self).__init__(parent, title="Image Viewer", 
            size=(1024, 1024), 
            style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.sketch = ImageWindow(self)

        self.statusbar = self.CreateStatusBar()
        self.initToolbar()
        self.initMenubar()
        self.initSpinner()

        # slider = wx.Slider(self.sketch, value=50, minValue=1, maxValue=100, pos=(10,10), size=(100,-1), style =wx.SL_AUTOTICKS | wx.SL_LABELS, name="Opacity:")
        # slider.SetTickFreq(5,10)
        # self.SetDimensions(x=-1,y=-1,width=self.sketch.width, height=self.sketch.height, sizeFlags=wx.SIZE_AUTO)
        # self.Center(direction=wx.BOTH)
    # Toolbar
    def initToolbar(self):
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((16, 16))

        # Set icons into toolbar
        open_icon = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, (16, 16))
        back_icon = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR, (16, 16))
        forward_icon = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR, (16, 16))
        savelines_icon = wx.ArtProvider.GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_TOOLBAR, (16, 16))

        openTool = self.toolbar.AddSimpleTool(wx.ID_ANY, open_icon, "Open New Directory", "Open an Image Directory")
        backTool = self.toolbar.AddSimpleTool(wx.ID_ANY, back_icon, "Go to Previous Image", "Go to previous image or press 'B'")
        forwardTool = self.toolbar.AddSimpleTool(wx.ID_ANY, forward_icon, "Go to Next Image", "Goes to next image or press 'F'")
        savelinesTool = self.toolbar.AddSimpleTool(wx.ID_ANY, savelines_icon, "Save drawn lines", "Saves freeform, labeled lines or press '__'")

        self.Bind(wx.EVT_MENU, self.onOpenDirectory, openTool)
        self.Bind(wx.EVT_MENU, self.sketch.ForwardImage, forwardTool)
        self.Bind(wx.EVT_MENU, self.sketch.ReverseImage, backTool)
        self.Bind(wx.EVT_MENU, self.onSaveLines, savelinesTool)

        self.toolbar.Realize()


    def onOpenDirectory(self, event):
        self.folderPath = ""

        dialog = wx.DirDialog(None, "Choose an image directory:",
        style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal() == wx.ID_OK:


            self.folderPath = dialog.GetPath()
            picPaths = sorted(glob.glob(self.folderPath + "\\*.tif"))
            print "Image folder path is:", self.folderPath

    # def onSaveLines(self, event):
    #     item = self.sketch.onMotion
    #     print "here is save lines", item


    # Menu 
    def initMenubar(self):
        menubar = wx.MenuBar()
        filemenu = wx.Menu()
        drawnlinemenu = wx.Menu()

        # Pull-down menus
        menubar.Append(filemenu, "File")
        menubar.Append(drawnlinemenu, "Drawn Lines")

        # Individual menu items
        save_overlay = filemenu.Append(wx.ID_ANY, "Save Predictor Overlay", "This will save the current predictor overlay")
        exit = filemenu.Append(wx.ID_ANY, "Exit program", "This will close image viewer")
        savelines = drawnlinemenu.Append(wx.ID_ANY, "Save drawn lines", "This will save current drawn lines")
        loadlines = drawnlinemenu.Append(wx.ID_ANY, "Load lines", "This will load previously drawn lines")

        self.Bind(wx.EVT_MENU, self.SaveOverlay, save_overlay)
        self. Bind(wx.EVT_MENU, self.onExit, exit)

        self.Bind(wx.EVT_MENU, self.onSaveLines,savelines)        
        self.Bind(wx.EVT_MENU, self.onLoadLines, loadlines)

        self.SetMenuBar(menubar)

    def SaveOverlay(self, event):
        self.sketch.predictor_output_bmap.SaveFile("predictor_overlay_save.tif", wx.BITMAP_TYPE_TIF)
        print "Overlay saved."

    def onExit(self, event):
        self.Close()

    def onSaveLines(self, event):
        dialog = wx.FileDialog(self, "Save file as:", style= wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() ==wx.ID_CANCEL:
            return
        output = dialog.GetPath()
        self.sketch.buffer.SaveFile(output, wx.BITMAP_TYPE_TIF)

    def onLoadLines(self, event):
        print "make save and load lines functions"


    def initSpinner(self):
        spinner = wx.SpinCtrl(self.sketch, id=-1, pos=(0,0), size=(80,-1), style=wx.SP_ARROW_KEYS)
        spinner.SetRange(1,100)
        spinner.SetValue(50)

        # for n in spinner.SetValue():
        #     sketch.opacity = n
        #     print "spinner value is %s" % n



        # while spinner.GetValue() > 0:
        #    print "spin val %d" % spinner.GetValue()

#---------------------------------------------------------------------------------------
if __name__ == '__main__':
    training_queue = Queue()
    predictor_queue =Queue()
    display_queue = Queue()
    
    app = wx.App(False)
    frame = ImageFrame()
    frame.Show()
  
    num_rand = 10
    num_bins = 1
    bin_size = 3000
    trainer = trainer.Trainer('C:\\Users\\DanielMiron\\Documents\\test', training_queue,
                                predictor_queue, threading.currentThread(), num_rand, num_bins, bin_size)
    predictor = predictor.Predictor(predictor_queue, display_queue, trainer.data, threading.currentThread())
    
    # # #set the first picture opened (used during Imagesing)
    
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
    