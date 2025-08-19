#!/usr/bin/env python3

import json
import cv2
import depthai as dai
import contextlib
import cProfile
import robotpy_apriltag
import CameraPipeline as camPipe
from Detections import Detections
from AprilTag5 import AprilTag
from FRC import FRC
import ConfigManager as cm

# Prints "interesting" information about the camera
# and returns the camera intrinsics

def printDeviceInfo(devInfo: dai.DeviceInfo):
    device: dai.Device = dai.Device(devInfo)
    mxId = devInfo.getMxId()
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


def profile():
    with contextlib.ExitStack() as stack:
        frc = FRC() # Instantiate an FRC object

        deviceInfos = dai.Device.getAllAvailableDevices() # Get all available device info

        oakCameras = [] # Create an empty list of cameras
        print(len(deviceInfos))

        # This section enumerates all connected devices and prints out their information
        # It needs to be customized to each year's set of cameras and uses

        for deviceInfo in deviceInfos:
            deviceInfo: dai.DeviceInfo # Give deviceInfo a type

            mxId = deviceInfo.getMxId() # Get the cameraID (mxID) from the deviceInfo
            cameraIntrinsics = printDeviceInfo(deviceInfo) # Call the function to print out this info

            # In this sample code, we connect to every camera we find

            print("===Connected to ", mxId) # Print that we connected to that camera

            # Here we can customize the NN being used on the camera
            # You can have different NN's on each camera (or none)

            # Find the correct resolutions for each camera in mv.json

            if cm.mvConfig.getCamera(mxId)["monoResolution"] == "THE_400_P":
                monoResolution = dai.MonoCameraProperties.SensorResolution.THE_400_P
            elif cm.mvConfig.getCamera(mxId)["monoResolution"] == "THE_480_P":
                monoResolution = dai.MonoCameraProperties.SensorResolution.THE_480_P
            else:
                monoResolution = dai.MonoCameraProperties.SensorResolution.THE_480_P # Defaults for camera sizes

            if cm.mvConfig.getCamera(mxId)["rgbResolution"] == "THE_800_P":
                rgbResolution = dai.ColorCameraProperties.SensorResolution.THE_800_P
            elif cm.mvConfig.getCamera(mxId)["rgbResolution"] == "THE_1080_P":
                rgbResolution = dai.ColorCameraProperties.SensorResolution.THE_1080_P #"1080x720"...?
            else:
                rgbResolution = dai.ColorCameraProperties.SensorResolution.THE_1080_P # Defaults for camera sizes

            # Even if the camera supports depth, you can force it to not use depth
            # Create a camera pipeline object from the camera pipeline class using:
            # The name associated with the cameraID in the mv.json file, the camera's info, if we want to use the depth from the camera, and the file associated with the neural network config
            cam1 = camPipe.CameraPipeline(cm.mvConfig.getCamera(mxId)['name'], deviceInfo, useDepth=True, nnFile="/boot/nn.json", monoResolution=monoResolution, rgbResolution=rgbResolution) # /boot/nn.json

            # This is where the camera is set up and the pipeline is built
            # First, create the Spatial Detection Network (SDN) object

            sdn = cam1.setupSDN() # In the camera pipeline call another method to set up the spacial detection network for it given the NN config file and return a spacial detection node

            # Now build the pipeline

            cam1.buildPipeline(sdn, cm.mvConfig.getCamera(mxId)['invert']) # Build the pipeline with the above returned spacial detection node and the info of if the camera is inverted or not

            # Serialize the pipeline

            # cam1.serializePipeline() # TEST

            # Start the pipeline

            cam1.startPipeline()

            # Either of the following can be set to None if not needed for a particular camera

            detector = Detections(cam1.bbfraction, cam1.LABELS) # Create a detector object for the camera given some device and NN info
            tagDetector = AprilTag(cm.mvConfig.tagFamily, cm.mvConfig.tagSize, cam1.cameraIntrinsics, robotpy_apriltag.AprilTagField.k2024Crescendo) 
            # Create an AprilTag detection object and supply the tag family, size, some camera intrinsics, and a special variable depending on the FRC season (Remove special variable if it's the wrong season?)

            # Add the camera to the list of cameras, along with the detectors, etc.

            oakCameras.append((cam1, mxId, detector, tagDetector)) # add a tuple of the camera pipeline, cameraID, object detector, and AprilTag detector to the list of cameras

            # Testing values for low frame count

            lowCount = 1
            allCount = 1

        while True:
            cam : camPipe # Type cam to be a camPipe

            # Loop through all the cameras.  For each camera, process the next frame

            for (cam, mxId, detector, tagDetector) in oakCameras:

                # Process the next frame.  If anything new arrived, processNextFrame will return True
                # try:
                if cam.processNextFrame():

                    # If the camera has a detection object, process the detections

                    objects = []

                    if detector is not None and cam.detections is not None and len(cam.detections) != 0:
                        objects = detector.processDetections(cam.detections, cam.frame, cam.depthFrameColor)

                    # If the camera has an AprilTag object, detect any AprilTags that might be seen

                    if tagDetector is not None and cam.frame is not None:
                        objects.extend(tagDetector.detect(cam.frame, cam.depthFrame))
                        if cam.fps < 16:
                            lowCount += 1
                        allCount += 1
                        # print(f"Fps: (same): {cam.fps}")
                        # print(f"Low (MV4.5.py bottom): {lowCount}")
                        # print("Percent Low (same): " + str(lowCount / allCount))
                        cv2.putText(cam.frame, "fps: {:.2f}".format(cam.fps), (2, cam.frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 1.0, (255, 255, 255))

                    res = frc.sd.putString("ObjectTracker-fps", "fps : {:.2f}".format(cam.fps))
                    res = frc.ntinst.flush() # Puts all values onto table immediately

                    # Display the results to the GUI and push frames to the camera server

                    frc.displayCamResults(cam)

                    # Write the objects to the Network Table

                    frc.writeObjectsToNetworkTable(objects, cam)

                    frc.sendResultsToDS(oakCameras)
                # except Exception as e:
                    # print(e)
                    # print("Continuing... (we should fix this)")

            # This won't work in the final version, but it's a way to exit the program

            if cv2.waitKey(1) == ord('q'):
                break

# cProfile.run('profile()', 'stats.prof')
profile()