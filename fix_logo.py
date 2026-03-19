import os
from PIL import Image

image_path = "c:/Users/Yasin/OneDrive/Desktop/construction_app/static/images/logo.png"

if os.path.exists(image_path):
    img = Image.open(image_path)
    img = img.convert("RGBA")
    datas = img.getdata()
    
    new_data = []
    for item in datas:
        # If the pixel is mostly white (e.g., R>240, G>240, B>240)
        # make it transparent
        if item[0] > 230 and item[1] > 230 and item[2] > 230:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    img.save(image_path, "PNG")
    print(f"Made white transparent on {image_path}")
else:
    print(f"File not found: {image_path}")
