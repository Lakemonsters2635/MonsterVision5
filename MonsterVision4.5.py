#!/usr/bin/env python3

import json
import cv2
import depthai as dai
import contextlib

import robotpy_apriltag
import CameraPipeline as capPipe
from Detections import Detections
from AprilTag5 import AprilTag
from FRC import FRC
import ConfigManager as cm


# Prints "interesting" information about the camera
# and returns the camera intrinsics

def printDeviceInfo(devInfo: dai.DeviceInfo):
        device: dai.Device = dai.Device(deviceInfo)
        mxId = deviceInfo.getMxId()
        cameras = device.getConnectedCameras()
        usbSpeed = device.getUsbSpeed()
        calibData = device.readCalibration()
        try:
            eepromData = calibData.getEepromData()
        except:
            eepromData = None
        if eepromData is not None: productName = eepromData.productName

        print("   >>> MXID:", mxId)
        print("   >>> Num of cameras:", len(cameras))
        for cam in cameras:
            print("   >>> Camera:", cam)
        print("   >>> USB speed:", usbSpeed)
        if eepromData is not None and eepromData.boardName != "":
            print("   >>> Board name:", eepromData.boardName)
        if eepromData is not None and eepromData.productName != "":
            print("   >>> Product name:", eepromData.productName)

        xxx = device.getIrDrivers()
        print("   >>> IR drivers:", xxx)

        return


with contextlib.ExitStack() as stack:
    frc = FRC()
    
    deviceInfos = dai.Device.getAllAvailableDevices()

    oakCameras = []

    # This section enumerates all connected devices and prints out their information
    # It needs to be customized to each year's set of cameras and uses

    for deviceInfo in deviceInfos:
        deviceInfo: dai.DeviceInfo

        mxId = deviceInfo.getMxId()
        cameraIntrinsics = printDeviceInfo(deviceInfo)

        # In this sample code, we connect to every camera we find

        print("===Connected to ", mxId)

        # Here we can customize the NN being used on the camera
        # You can have different NN's on each camera (or none)

        # Even if the camera supports depth, you can force it to not use depth
               
        cam1 = capPipe.CameraPipeline(cm.mvConfig.getCamera(mxId)['name'], deviceInfo, useDepth=True, nnFile="/boot/nn.json")
        # cam1 = capPipe.CameraPipeline(cm.mvConfig.getCamera(mxId)['name'], deviceInfo, useDepth=None, nnFile=None)

        # This is where the camera is set up and the pipeline is built
        # First, create the Spatial Detection Network (SDN) object
        
        sdn = cam1.setupSDN()

        # Now build the pipeline

        cam1.buildPipeline(sdn, cm.mvConfig.getCamera(mxId)['invert'])

        # Serialize the pipeline

        # cam1.serializePipeline()

        # Start the pipeline

        cam1.startPipeline()

        # Either of the following can be set to None if not needed for a particular camera

        detector = Detections(cam1.bbfraction, cam1.LABELS)
        tagDetector = AprilTag(cm.mvConfig.tagFamily, cm.mvConfig.tagSize, cam1.cameraIntrinsics, robotpy_apriltag.AprilTagField.k2024Crescendo)

        # Add the camera to the list of cameras, along with the detectors, etc.

        oakCameras.append((cam1, mxId, detector, tagDetector))

        # oakCameras = []
        
    while True:
        cam : capPipe

        # Loop through all the cameras.  For each camera, process the next frame

        for (cam, mxId, detector, tagDetector) in oakCameras:

            # Process the next frame.  If anything new arrived, processNextFrame will return True

            if cam.processNextFrame():

                # If the camera has a detection object, process the detections

                objects = []

                if detector is not None and cam.detections is not None and len(cam.detections) != 0:
                    objects = detector.processDetections(cam.detections, cam.frame, cam.depthFrameColor)

                # If the camera has an AprilTag object, detect any AprilTags that might be seen

                if tagDetector is not None and cam.frame is not None:
                    objects.extend(tagDetector.detect(cam.frame, cam.depthFrame))

                    cv2.putText(cam.frame, "fps: {:.2f}".format(cam.fps), (2, cam.frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4,
                    (255, 255, 255))

                res = frc.sd.putString("ObjectTracker-fps", "fps : {:.2f}".format(cam.fps))
                res = frc.ntinst.flush() # Puts all values onto table immediately

                # Display the results to the GUI and push frames to the camera server
                
                frc.displayCamResults(cam)

                # Write the objects to the Network Table

                frc.writeObjectsToNetworkTable(objects, cam)

                frc.sendResultsToDS(oakCameras)

        # This won't work in the final version, but it's a way to exit the program

        if cv2.waitKey(1) == ord('q'):
            break