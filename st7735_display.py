import time
import board
import digitalio
import adafruit_st7735r
from PIL import Image, ImageDraw, ImageFont

spi = board.SPI()
tft_cs = digitalio.DigitalInOut(board.D5)
tft_dc = digitalio.DigitalInOut(board.D6)
tft_reset = digitalio.DigitalInOut(board.D12)

display = adafruit_st7735r.ST7735R(spi, cs=tft_cs, dc=tft_dc, rst=tft_reset, width=128, height=160)

for color in [(255,0,0), (0,255,0), (0,0,255)]:
    image = Image.new("RGB", (128,160), color)
    display.image(image)
    time.sleep(1)

image = Image.new("RGB", (128,160), (0,0,0))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
draw.text((10,70), "Hello TFT!", font=font, fill=(255,255,255))
display.image(image)

#pip3 install adafruit-circuitpython-st7735r RPi.GPIO Pillow
#sudo apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libopenjp2-7 libtiff5

