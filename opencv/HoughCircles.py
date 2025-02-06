# importing open cv
import cv2
import numpy as np

cam = cv2.VideoCapture(0)
print("yay")
while True:
    _,frame = cam.read()
    raw = frame
    #hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 
      
    # Threshold of blue in HSV space 
    lower_blue = np.array([0, 5, 5]) 
    upper_blue = np.array([40, 255, 255]) 
  
    # preparing the mask to overlay 
    mask = cv2.inRange(hsv, lower_blue, upper_blue) 
      
    # The black region in the mask has the value of 0, 
    # so when multiplied with original image removes all non-blue regions 
    result = cv2.bitwise_and(frame, frame, mask = mask) 

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #mask = cv2.inRange(hsv, lower_blue, upper_blue) 
      

    gray_blurred = cv2.blur(gray, (3, 3)) 
    
# Apply Hough transform on the blurred image. 
    detected_circles = cv2.HoughCircles(gray_blurred,  
                    cv2.HOUGH_GRADIENT, 1, 200, param1 = 100, 
                param2 = 50, minRadius = 20, maxRadius = 100) 
    
    # Draw circles that are detected. 
    if detected_circles is not None: 
        print("yay circles")
        # Convert the circle parameters a, b and r to integers. 
        detected_circles = np.uint16(np.around(detected_circles)) 
    
        for pt in detected_circles[0, :]: 
            a, b, r = pt[0], pt[1], pt[2] 
    
            # Draw the circumference of the circle. 
            cv2.circle(frame, (a, b), r, (0, 255, 0), 2) 
    
            # Draw a small circle (of radius 1) to show the center. 
            cv2.circle(frame, (a, b), 1, (0, 0, 255), 3) 
            
            #cv2.imshow("Mask", mask)
    else:
        print("no circles")
    cv2.imshow("Detected Circle", frame) 
    #cv2.imshow("Blue", result) 
    #cv2.imshow("Raw Camera Feed", raw)
    if cv2.waitKey(1) == ord("q"):
        break

cv2.destroyAllWindows()
cam.release()