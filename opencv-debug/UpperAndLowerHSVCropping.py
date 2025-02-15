import cv2
import numpy as np
import time 
# Global variables
ref_point = []

def click_and_crop(event, x, y, flags, param):
    global ref_point

    if event == cv2.EVENT_LBUTTONDOWN:
        ref_point = [(x, y)]


    elif event == cv2.EVENT_LBUTTONUP:
        ref_point.append((x, y))

        # Draws the rectangle
        cv2.rectangle(image, ref_point[0], ref_point[1], (0, 255, 0), 2)
        cv2.imshow("Image", image)
        

image = cv2.imread("images\\AlgeaDetection-5.png")  
#We create a clone of the image so that we can still see the original, this one is for cropping
clone = image
cv2.namedWindow("Image")
cv2.setMouseCallback("Image", click_and_crop)
#cv2.setMouseCallback("Image", click_and_crop)

while True:
    cv2.imshow("Image", image)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("r"):  
        image = clone

    if key == ord("q"):  
        break

    elif key == ord("c") and len(ref_point) == 2:  
        x1, y1 = ref_point[0]
        x2, y2 = ref_point[1]
        #x3, y3 = ref_point[2]
        #x4, y4 = ref_point[3]
        
        #x1, x2 = min(x1, x2), max(x1, x2)
        #y1, y2 = min(y1, y2), max(y1, y2)

        
        cropped = clone[y1:y2, x1:x2]
        cropped_hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
        #Cropped hsv has rows, columns and the color values, I just want the color values, so numpy reshapes the array into three columns, and -1, and automaticaly calculated amount of rows
        hsv_value_list = cropped_hsv.reshape(-1, 3)
        cv2.imshow("Image", cropped_hsv)
        # Instead of finding a min and max(because we would would basicaly just get black and white) we get the color values that include 95% of all the colrs in the highlighted area
        lower_bound = np.percentile(hsv_value_list, 0.5, axis=0).astype(int)
        upper_bound = np.percentile(hsv_value_list, 99.5, axis=0).astype(int)

        print("Lower HSV Bound: " + str(lower_bound))
        print("Upper HSV Bound: " + str(upper_bound))
    
cv2.destroyAllWindows()