import cv2
import numpy as np
import depthai as dai


class Reefscape():
    def __init__(self):
        pass

    def detect(self, cvImage):
        frame = cvImage
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 
        
        # Threshold of blue in HSV space 
        lower_blue = np.array([60, 88, 18])
        upper_blue = np.array([93, 255, 255])
    
        # preparing the mask to overlay 
        mask = cv2.inRange(hsv, lower_blue, upper_blue) 
        self.blurry_mask = cv2.GaussianBlur(mask, (21,21), 0) 
        
    # Apply Hough transform on the blurred image. 
        detected_circles = cv2.HoughCircles(self.blurry_mask,  
                        cv2.HOUGH_GRADIENT, 1, 70, param1 = 260, 
                    param2 = 30, minRadius = 50, maxRadius = 280) 
        
        # Draw circles that are detected and the frame rate. 
        detections = []

        if detected_circles is not None: 
            # Convert the circle parameters a, b and r to integers. 
            detected_circles = np.uint16(np.around(detected_circles)) 
            count = 0
            for pt in detected_circles[0, :]: 
                cx, cy, r = pt[0], pt[1], pt[2] 
                #detections.update()
                algae = {}
                algae["cx"] = int(cx)
                algae["cy"] = int(cy)
                algae["r"] = int(r)
                
                detections.append({"objectLabel":"algae" + str(count), "cx":int(cx), "cy":int(cy), "r":int(r)})
                count += 1
                # Draw the circumference of the circle. 
                cv2.circle(frame, (cx, cy), r, (0, 255, 0), 2)
                cv2.circle(self.blurry_mask, (cx, cy), r, (0, 255, 255), 2) 
                # Draw a small circle (of radius 1) to show the center. 
                cv2.circle(frame, (cx, cy), 1, (0, 255, 0), 3) 
                cv2.circle(self.blurry_mask, (cx, cy), 1, (0, 0, 255), 3) 
        return detections
    
    def show(self):
        return self.blurry_mask
    