import cv2
import depthai as dai
import ConfigManager as cm


def _average_depth_coord(pt1, pt2, padding_factor):
    factor = 1 - padding_factor
    x_shift = (pt2[0] - pt1[0]) * factor / 2
    y_shift = (pt2[1] - pt1[1]) * factor / 2
    av_pt1 = int(pt1[0] + x_shift), int(pt1[1] + y_shift)
    av_pt2 = int(pt2[0] - x_shift), int(pt2[1] - y_shift)
    return av_pt1, av_pt2

def mapDetectionCoordinatesToFrame(roi : dai.Rect, inputSize, shape):
    (height, width) = inputSize
    (Height, Width, _depth) = shape

    scale = height / Height

    # roi = roi.denormalize(width, height)

    roi.x = (roi.x - width/2)/scale + Width/2
    roi.y = (roi.y - height/2)/scale + Height/2
    roi.height = roi.height/scale
    roi.width = roi.width/scale

    return roi



INCHES_PER_MILLIMETER = 0.0393701

class Detections:

    def __init__(self, bbfraction, LABELS):
        self.bbfraction = bbfraction
        self.LABELS = LABELS


    def ProcessOak1Detections(self, detections, frame):
        height = frame.shape[0]
        width = frame.shape[1]

        # re-initializes objects to zero/empty before each frame is read
        objects = []

        for detection in detections:
            # Get the detection bounding box (in % coordinates), and denormalize it to the NN frame coordinates.
            detectionBB = dai.Rect(dai.Point2f(detection.xmin, detection.ymin), dai.Point2f(detection.xmax, detection.ymax))
            roiDenorm = detectionBB.denormalize(cm.nnConfig.inputSize[0], cm.nnConfig.inputSize[1])
            
            # Now map the denormalized bounding box to the full frame coordinates
            roiMapped = mapDetectionCoordinatesToFrame(roiDenorm, cm.nnConfig.inputSize, frame.shape)
            topLeft = roiMapped.topLeft()
            bottomRight = roiMapped.bottomRight()
            xmin = int(topLeft.x)
            ymin = int(topLeft.y)
            xmax = int(bottomRight.x)
            ymax = int(bottomRight.y)

            # From this point on, everything is in RGB Frame (frame) coordinates

            # Find center of bounding box

            cX = (xmin + xmax) / 2
            cY = (ymin + ymax) / 2
            R = max((xmax - xmin), (ymax - ymin)) /2

            x1 = xmin
            x2 = xmax
            y1 = ymin
            y2 = ymax

            try:
                label = self.LABELS[detection.label]

            except KeyError:
                label = detection.label

            if detection.label == 1:
                color = (255, 0, 0)
            else:
                color = (0, 0, 255)

            #print(detection.spatialCoordinates.x, detection.spatialCoordinates.y, detection.spatialCoordinates.z)

            cv2.putText(frame, str(label), (x1 + 10, y1 + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(frame, "{:.2f}".format(detection.confidence * 100), (x1 + 10, y1 + 35),
                        cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(frame, f"X: {round(cX, 3)} px", (x1 + 10, y1 + 50), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(frame, f"Y: {round(cY, 3)} px", (x1 + 10, y1 + 65), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(frame, f"R: {round(R, 3)} px", (x1 + 10, y1 + 80), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)

            cv2.circle(frame, (int(cX), int(cY)), 5, (0, 0, 255), -1)
            cv2.circle(frame, (int(cX), int(cY)), int(R), (255, 0, 0), 2)

            # cv2.rectangle(self.frame, (x1, y1), (x2, y2), color, cv2.FONT_HERSHEY_SIMPLEX)

            objects.append({"objectLabel": self.LABELS[detection.label], "x": cX,
                            "y": cY, "z": R,
                            "confidence": round(detection.confidence, 2)})

        return objects                


    def processDetections(self, detections, frame, depthFrameColor):

        if frame is None:
            return
        
        # If no depth info, must be an OAK-1
        if depthFrameColor is None:
            return self.ProcessOak1Detections(detections, frame)
        
        # If the frame is available, draw bounding boxes on it and show the frame
        height = frame.shape[0]
        width = frame.shape[1]

        # re-initializes objects to zero/empty before each frame is read
        objects = []
        s_detections = sorted(detections, key=lambda det: det.label * 100000 + det.spatialCoordinates.z)
        # print(s_detections)

        for detection in s_detections:
            if detection.label == 1:
                color = (255, 0, 0)
            else:
                color = (0, 0, 255)

# Get the detection bounding box (in % coordinates), and denormalize it to the NN frame coordinates.
            detectionBB = dai.Rect(dai.Point2f(detection.xmin, detection.ymin), dai.Point2f(detection.xmax, detection.ymax))
            roiDenorm = detectionBB.denormalize(cm.nnConfig.inputSize[0], cm.nnConfig.inputSize[1])
            
            # Now map the denormalized bounding box to the full frame coordinates
            roiMapped = mapDetectionCoordinatesToFrame(roiDenorm, cm.nnConfig.inputSize, frame.shape)
            topLeft = roiMapped.topLeft()
            bottomRight = roiMapped.bottomRight()
            xmin = int(topLeft.x)
            ymin = int(topLeft.y)
            xmax = int(bottomRight.x)
            ymax = int(bottomRight.y)

            # And draw the BB rectangle on the frame
           
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 1)

            # Scribbling text on the frame

            x1 = xmin
            x2 = xmax
            y1 = ymin
            y2 = ymax

            try:
                label = self.LABELS[detection.label]

            except KeyError:
                label = detection.label

            # Draw the BB over which the depth is computed
            avg_pt1, avg_pt2 = _average_depth_coord([xmin, ymin],
                                                   [xmax, ymax],
                                                   self.bbfraction)

            cv2.rectangle(frame, avg_pt1, avg_pt2, (0, 255, 255), 1)

            x = round(int(detection.spatialCoordinates.x * INCHES_PER_MILLIMETER), 1)
            y = round(int(detection.spatialCoordinates.y * INCHES_PER_MILLIMETER), 1)
            z = round(int(detection.spatialCoordinates.z * INCHES_PER_MILLIMETER), 1)

            cv2.putText(frame, str(label), (x1 + 10, y1 + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(frame, "{:.2f}".format(detection.confidence * 100), (x1 + 10, y1 + 35),
                        cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(frame, f"X: {x} in", (x1 + 10, y1 + 50), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(frame, f"Y: {y} in", (x1 + 10, y1 + 65), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(frame, f"Z: {z} in", (x1 + 10, y1 + 80), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), cv2.FONT_HERSHEY_SIMPLEX)

            objects.append({"objectLabel": self.LABELS[detection.label], "x": x,
                            "y": y, "z": z,
                            "confidence": round(detection.confidence, 2), "xa": None,  "ya": None,  "za": None}) # Maybe shoudl be 0.0

        return objects            