# calculating a tray's capacity from image
import os
import numpy as np
from skimage import io

empty_tray_image = io.imread(os.getcwd() + "/empty.jpg")
empty_tray_image_norm = np.divide(empty_tray_image, np.sum(empty_tray_image, axis=-1, keepdims=-1))

def get_capacity(image_name):
    tray_img = io.imread(os.getcwd() + "/" + image_name)
    if (tray_img.shape != empty_tray_image.shape):
        raise Exception('Tray image is not the same shape as the reference empty tray image')
    
    tray_img_norm = np.divide(tray_img, np.sum(tray_img, axis=-1, keepdims=-1))
    #io.imshow(tray_img_norm)
    #io.show()

    diff = empty_tray_image_norm - tray_img_norm
    #io.imshow(diff)
    #io.show()

    # grayscale image detailing how different each pixel in the tray image is to the empty reference image
    abs_diff = np.linalg.norm(diff,axis=-1) # values are > 0, could actually be > 1 too... max would be sqrt(3)?
    #io.imshow(abs_diff)
    #io.show()

    # threshold this to get a binary image. 
    # Then we just sum this entire numpy array (which is 1 where stuff is stored in tray and 0 where there is space)
    thresh_image = abs_diff > 0.1
    #io.imshow(thresh_image)
    #io.show()
    
    # return the capacity estimation between 0 and 1 
    # this is just diff_sum normalized by the max possible difference - the whole area of the image.
    img_area = tray_img.shape[0]*tray_img.shape[1]
    
    return np.sum(thresh_image) / img_area
    
#print(get_capacity("rock1.jpg"))