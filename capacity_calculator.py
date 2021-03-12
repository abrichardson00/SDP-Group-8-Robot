# calculating a tray's capacity from image
import os
import numpy as np
from skimage import io
from skimage.color import rgb2gray


empty_tray_image = io.imread(os.getcwd() + "/tray4.jpg")

THRESHOLD = 0.1

def get_capacity(tray_number): 
    tray_img = io.imread(os.getcwd() + "/tray" + str(tray_number) + ".jpg")
    if (tray_img.shape != empty_tray_image.shape):
        raise Exception('Tray image is not the same shape as the reference empty tray image')

    # grayscale image detailing how different each pixel in the tray image is to the empty reference image
    abs_diff = np.abs((tray_img - empty_tray_image)*(1.0/255.0),-1) # (values also normalized between 0 and 1)

    # lets threshold this to get a binary image. 
    # Then we just sum this entire numpy array (which is 1 where stuff is stored in tray and 0 where there is space)
    diff_sum = np.sum((abs_diff > THRESHOLD))
    
    # return the capacity estimation between 0 and 1 
    # this is just diff_sum normalized by the max possible difference - the whole area of the image.
    img_area = tray_img.shape[0]*tray_img.shape[1]
    return diff_sum / img_area
    
