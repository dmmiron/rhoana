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
        self.filename = 'C:/Users/brian/Desktop/ECS_training_data/04_labeled_update_sec.tif' 
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
        self.predictor_array = display_input.get()
        print self.predictor_array        
        image = wx.ImageFromBuffer(w, h, self.predictor_array)
        self.predictor_output_bmap = image.ConvertToBitmap()    # predictor classifier overlay
        self.buffer = self.predictor_output_bmap
        self.dc.SelectObject(self.buffer)
        self.Refresh()
        print "ReturnOverlay"

    def onReturnComposite(self, event):
        # Convert predictor overlay from bitmap to wx.Image
        self.predictor_overlay_image = wx.ImageFromBitmap (self.predictor_output_bmap)

        # Composite image (image + overlay) generator
        w = self.width
        h= self.height
        self.composite = wx.EmptyImage(w, h)
        opacity = 0.5
        for y in xrange(h):
            for x in xrange(w):
                r = opacity * self.image.GetRed(x, y) + (1-opacity) * self.predictor_overlay_image.GetRed(x, y)
                g = opacity * self.image.GetGreen(x, y) + (1-opacity) * self.predictor_overlay_image.GetGreen(x, y)
                b = opacity * self.image.GetBlue(x, y) + (1-opacity) * self.predictor_overlay_image.GetBlue(x, y)
                self.composite.SetRGB(x, y, r, g, b)      # assigns RGB values to each pixel
        self.composite_bmap = self.composite.ConvertToBitmap()      # composite of original image and predictor overlay

        # Display image
        self.buffer =  self.composite_bmap
        self.dc.SelectObject(self.buffer)
        self.Refresh()
        print "ReturnComposite"    
