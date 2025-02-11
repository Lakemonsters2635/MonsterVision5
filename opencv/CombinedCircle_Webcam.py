# For usage with computer webcam
import cv2
import numpy as np
import time

cam = cv2.VideoCapture(0)
while True:
    start = time.perf_counter()
    ret, frame = cam.read()
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 
    
    # Threshold of blue in HSV space 
    lower_blue = np.array([60, 88, 18])
    upper_blue = np.array([93, 255, 255])

    # preparing the mask to overlay 
    mask = cv2.inRange(hsv, lower_blue, upper_blue) 
    blurry_mask = cv2.GaussianBlur(mask, (21,21), 0) 
    
# Apply Hough transform on the blurred image. 
    detected_circles = cv2.HoughCircles(blurry_mask,  
                    cv2.HOUGH_GRADIENT, 1, 70, param1 = 260, 
                param2 = 30, minRadius = 50, maxRadius = 280) 
    
    # Draw circles that are detected and the frame rate. 
    detections = {}

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
            
            detections[f"algae{count}"] = algae
            count += 1
            # Draw the circumference of the circle. 
            cv2.circle(frame, (cx, cy), r, (0, 255, 0), 2)
            cv2.circle(blurry_mask, (cx, cy), r, (0, 255, 255), 2) 
            # Draw a small circle (of radius 1) to show the center. 
            cv2.circle(frame, (cx, cy), 1, (0, 255, 0), 3) 
            cv2.circle(blurry_mask, (cx, cy), 1, (0, 0, 255), 3) 

    #Draw the frame rate onto the frame
    end = time.perf_counter()
    fps = 1/(end-start)
    cv2.putText(blurry_mask, f"Frame Rate: {int(fps)}",(7,70), cv2.FONT_HERSHEY_SIMPLEX , 3, (255,255,255), 2, cv2.LINE_AA)

    cv2.imshow("Full Color Detection", frame) 
    cv2.imshow("Masked Detection", blurry_mask) 
    time.sleep(0.002)
    print(detections)
    if cv2.waitKey(1) == ord("q"):
        break

cv2.destroyAllWindows()