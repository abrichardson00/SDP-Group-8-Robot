import pyzbar
from skimage import io

def get_tray_number(img_path):
    tray_img = io.imread(img_path)
    # find the barcodes in the image and decode each of the barcodes
    barcodes = pyzbar.decode(tray_img)
    barcode = barcodes[0] # only 1 bar code...

    data = barcode.data.decode("utf-8")
    print(data)
    tray_number = int(data)

    return tray_number