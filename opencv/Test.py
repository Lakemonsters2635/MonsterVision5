from ReefscapeDetections import Reefscape
import cv2

detectorr = Reefscape()
while True:
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    dict = detectorr.detect(frame)
    print(dict)
    cv2.imshow("Masked Detection", detectorr.show())
    if cv2.waitKey(1) == ord("q"):
        break
