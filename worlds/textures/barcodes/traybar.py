from barcode import EAN8
from barcode.writer import ImageWriter

tray_codes = {}


for height in range(5):
    for fb in (0,1):
        for lr in (0,1):
            tray_code = ""
            if fb == 0:
                tray_code += "B"
            else:
                tray_code += "F"
            
            if lr == 0:
                tray_code += "L"
            else:
                tray_code += "R"
            
            tray_code += str(height)

            tray_codes[tray_code] = "0000%s%s%s" % (fb, lr, height)


writer = ImageWriter(format="JPEG")

for tray_name, barcode_data in tray_codes.items():

    tray_barcode = EAN8(barcode_data, writer=writer)
    tray_barcode.save(tray_name, {"module_width": 1.0, "module_height": 2.0, "font_size": 0})
