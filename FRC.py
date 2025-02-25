# Import libraries

import json
import sys
import time
import numpy as np
import ConfigManager as cm


usingNTCore = False
try:
# Older OSes use pynetworktables
    from networktables import NetworkTables # type: ignore
    from networktables import NetworkTablesInstance # type: ignore
except ImportError:
# New have ntcore preinstalled
    import ntcore # type: ignore
    usingNTCore = True

import cv2 # Import the cv2 image library
import platform # Import the default package from python that allows you to check system platform info
cscoreAvailable = False
if cm.mvConfig.showPreview:
    cscoreAvailable = True # Turn on and off the Camera server
    try:
        from cscore import CameraServer # type: ignore
    except ImportError:
        cscoreAvailable = False



class FRC:


    def __init__(self, mxId):
        # Tells you if you are on the robot or not by looking at the platform name (if you are using the WPILib pi image?)
        # onRobot really should be called "headless".  It means there's no graphics capability on the underlying hardware

        self.onRobot = platform.uname().node == "wpilibpi"


        # NetworkTable Instance holder; Initialized below
        self.ntinst = None
        # Vision NetworkTable; Initialized below; getTable MonsterVision
        self.sd = None
        # Num frames; Maybe used for FPS counting?
        self.frame_counter = 0
        # FPS counting
        self.lastTime = 0

        # Create a NetworkTable Instance
        if usingNTCore:
            self.ntinst = ntcore.NetworkTableInstance.getDefault()
        else:
            self.ntinst = NetworkTablesInstance.getDefault()

        # Sets up the NT depending on config
        if cm.frcConfig.server:
            print("Setting up NetworkTables server")
            self.ntinst.startServer()
        else: # TODO ADRIEN - Look more into what this code below actually does
            print("Setting up NetworkTables client for team {}".format(cm.frcConfig.team))
            self.ntinst.startClient4("Eclipse")        # Name of camera in the network table
            self.ntinst.setServerTeam(cm.frcConfig.team) # How to identify the network table server
            self.ntinst.startDSClient()

        # Get the MonsterVision NT; Maybe creates it
        if usingNTCore:
            self.sd = self.ntinst.getTable("MonsterVision " + mxId)
        else:
            self.sd = NetworkTables.getTable("MonsterVision " + mxId)

        # TODO perhaps width should be function of # of cameras

        if cscoreAvailable:
            # self.cs = CameraServer.getInstance()
            CameraServer.enableLogging()
            self.csoutput = CameraServer.putVideo("MonsterVision", cm.mvConfig.PREVIEW_WIDTH, cm.mvConfig.PREVIEW_HEIGHT) # TODOnot        


    # Return True if we're running on Romi.  False if we're a coprocessor on a big 'bot
    # Never used but checks if the files exists
    def is_romi(self):
        try:
            with open(cm.ROMI_FILE, "rt", encoding="utf-8") as f:
                json.load(f)
                # j = json.load(f)
        except OSError as err:
            print("Could not open '{}': {}".format(cm.ROMI_FILE, err), file=sys.stderr)
            return False
        return True


    # NT writing for NN detections and AprilTags
    def writeObjectsToNetworkTable(self, objects, cam):
        jasonString = json.dumps(objects)
        res = self.sd.putString("ObjectTracker-" + cam.name, jasonString)
        res = self.ntinst.flush() # Puts all values onto table immediately
        res = True

    # Display windows if you are not running headless
    def displayCamResults(self, cam):
        if not self.onRobot:
            if cam.frame is not None:
                cv2.imshow(cam.name + " rgb", cam.frame)
            # if cam.ispFrame is not None:
            #     cv2.imshow(cam.name + " ISP", cam.ispFrame) 
            if cam.depthFrameColor is not None:
                cv2.imshow(cam.name + " depth", cam.depthFrameColor)


    # Composite all camera images into a single frame for DS display
    def sendResultsToDS(self, cams):
        # First, enumerate the images

        if cscoreAvailable:
            self.frame_counter += 1

            # This is so we only send every 4th frame (I think according to mv.json)
            if self.frame_counter % cm.mvConfig.DS_SUBSAMPLING == 0:
                images = [] # Holds all the different versions of the images like depth and ISP and RGB
                # for each camera extract the tuple of info
                for camTuple in cams:
                    cam = camTuple[0] # Get cam name
                    if cam.frame is not None: # If there is a frame append it to the images
                        if cam.frame.shape[0] == 534: # If the camera has the exact height of the global shutter OAK-D PRO
                            # Pad the frame to match the height of the other OAK-D PRO. These values are HARDCODED!!! Can cause problems later? 1280=widthNormal, 854=widthGlobal, 720=heightNormal, 534=heightGlobal
                            paddedFrame = np.array(cv2.copyMakeBorder(cam.frame, (720-534)//2, (720-534)//2, (1280-854)//2, (1280-854)//2, cv2.BORDER_CONSTANT, value=[0,0,0]))
                            images.append(paddedFrame)
                        else:
                            images.append(cam.frame)
                
                if len(images) > 0: # If there are any images then resize them and put them to the webserver (wpilibpi.local/1181)
                    if len(images) > 1: # If there are more than 1 then stack them together. eg. stack the image with the bonding boxes
                        # print(len(images), "FUNK TIME")
                        img = cv2.hconcat(images)
                        # print("Hcat:", (images[i].shape for i in range(len(images))))
                    else:
                        img = images[0]
                        # print("One:", images[0].shape)

                    dim = (int(img.shape[1] * cm.mvConfig.DS_SCALE) , int(img.shape[0] * cm.mvConfig.DS_SCALE)) # Calculate the correct scale
                    resized = cv2.resize(img, dim) # Resize to the correct scale that we want according to  mv.json
                    self.csoutput.putFrame(resized) # Output the frame to the webserver
