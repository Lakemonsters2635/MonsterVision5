# importing open cv
import cv2
import numpy as np
import depthai as dai
import time
# Create pipeline
pipeline = dai.Pipeline()
cam = pipeline.create(dai.node.ColorCamera)
cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
cam.setPreviewSize(1280,720)
xout = pipeline.create(dai.node.XLinkOut)
xout.setStreamName("rgb")
cam.preview.link(xout.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:
    qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
        
#cam = cv2.VideoCapture(0)
#print("yay")
    while True:
        start = time.perf_counter()
        frame = qRgb.get().getFrame()
        #_,frame = cam.read()
        #print(frame)
        #frame = cv2.imread('C:\\Users\\prest\\Downloads\\AlgeaDetection-1.png')
        
        #hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 
        
        # Threshold of blue in HSV space 
        lower_blue = np.array([60, 88, 18])
        upper_blue = np.array([93, 255, 255])
    
        # preparing the mask to overlay 
        mask = cv2.inRange(hsv, lower_blue, upper_blue) 
        blurry_mask = cv2.GaussianBlur(mask, (21,21), 0)
        # The black region in the mask has the value of 0, 
        # so when multiplied with original image removes all non-blue regions 
        #result = cv2.bitwise_and(frame, frame, mask = mask) 

        #gray = cv2.cvtColor(blurry_mask, cv2.COLOR_BGR2GRAY)
        #mask = cv2.inRange(hsv, lower_blue, upper_blue) 
        

        #gray_blurred = cv2.blur(gray, (8, 8)) 
        gray_blurred = blurry_mask 
        
    # Apply Hough transform on the blurred image. 
        detected_circles = cv2.HoughCircles(gray_blurred,  
                        cv2.HOUGH_GRADIENT, 1, 70, param1 = 260, 
                    param2 = 30, minRadius = 50, maxRadius = 280) 
        
        
        
        # Draw circles that are detected and the frame rate. 
        if detected_circles is not None: 
            print("yay circles")
            # Convert the circle parameters a, b and r to integers. 
            detected_circles = np.uint16(np.around(detected_circles)) 
        
            for pt in detected_circles[0, :]: 
                a, b, r = pt[0], pt[1], pt[2] 
                # Draw the circumference of the circle. 
                cv2.circle(frame, (a, b), r, (0, 255, 0), 2)
                cv2.circle(gray_blurred, (a, b), r, (0, 255, 255), 2) 
                # Draw a small circle (of radius 1) to show the center. 
                cv2.circle(frame, (a, b), 1, (0, 255, 0), 3) 
                cv2.circle(gray_blurred, (a, b), 1, (0, 0, 255), 3) 
                
                #cv2.imshow("Mask", mask)
        else:
            print("no circles")
        #Draw the frame rate onto the frame
        end = time.perf_counter()
        fps = 1/(end-start)
        cv2.putText(gray_blurred, f"Frame Rate: {int(fps)}",(7,70), cv2.FONT_HERSHEY_SIMPLEX , 3, (255,255,255), 2, cv2.LINE_AA)

        cv2.imshow("Detected Circle", frame) 
        cv2.imshow("Blue", gray_blurred) 
        cv2.imshow("Mask", blurry_mask) 
        time.sleep(0.002)
        if cv2.waitKey(1) == ord("q"):
            break

cv2.destroyAllWindows()
#cam.release()