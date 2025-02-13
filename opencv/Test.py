from ReefscapeDetections import Reefscape
import cv2
import depthai as dai

detectorr = Reefscape()
#cam = cv2.VideoCapture(0)
pipeline = dai.Pipeline()
cam = pipeline.create(dai.node.ColorCamera)
cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
cam.setPreviewSize(1280,720)
xout = pipeline.create(dai.node.XLinkOut)
xout.setStreamName("rgb")
cam.preview.link(xout.input)
with dai.Device(pipeline) as device:
    qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
    while True:
        frame = qRgb.get().getFrame()
        #ret, frame = cam.read()
        dict = detectorr.detect(frame)
        print(dict)
        #cv2.imshow("Masked Detection", detectorr.show())
        if cv2.waitKey(1) == ord("q"):
            break
