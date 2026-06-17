# convert_icon.py
from PIL import Image

img = Image.open("assets/icon.png")
img.save("assets/app_icon.ico", format="ICO", 
         sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
print("✅ Иконка готова!")