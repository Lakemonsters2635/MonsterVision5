#!/usr/bin/env python3

import cv2
import depthai as dai
import contextlib


def createPipeline():
    # Start defining a pipeline
    pipeline = dai.Pipeline()
    # Define a source - color camera TODO in v3, use Camera node instead (still works, but deprecated)
    camRgb = pipeline.create(dai.node.ColorCamera)

    camRgb.setPreviewSize(300, 300)
    camRgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    camRgb.setInterleaved(False)

    # In v3, instead of linking to XLink, we are directly creating queues from the node
    cameraOutput = camRgb.preview

    return pipeline, cameraOutput


deviceInfos = dai.Device.getAllAvailableDevices()

qRgbMap = []

for deviceInfo in deviceInfos:
    pipeline, cameraOutput = createPipeline()

    # Start pipeline with this device (v3)
    device = pipeline.start(deviceInfo)

    print("===Connected to ", deviceInfo.getMxId())
    mxId = device.getMxId()
    cameras = device.getConnectedCameras()
    usbSpeed = device.getUsbSpeed()
    eepromData = device.readCalibration2().getEepromData()
    print("   >>> MXID:", mxId)
    print("   >>> Num of cameras:", len(cameras))
    print("   >>> USB speed:", usbSpeed)
    if eepromData.boardName != "":
        print("   >>> Board name:", eepromData.boardName)
    if eepromData.productName != "":
        print("   >>> Product name:", eepromData.productName)

    xxx = device.getIrDrivers()

    # Create host queue from the camera output node
    q_rgb = cameraOutput.createOutputQueue(maxSize=4, blocking=False)
    stream_name = "rgb-" + mxId + "-" + eepromData.productName
    qRgbMap.append((q_rgb, stream_name))

while True:
    for q_rgb, stream_name in qRgbMap:
        if q_rgb.has():
            cv2.imshow(stream_name, q_rgb.get().getCvFrame())

    if cv2.waitKey(1) == ord("q"):
        break
