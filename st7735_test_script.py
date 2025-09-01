import time
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7735

WIDTH = 128
HEIGHT = 160

spi = board.SPI()
tft_cs = digitalio.DigitalInOut(board.D5)
tft_dc = digitalio.DigitalInOut(board.D6)
tft_reset = digitalio.DigitalInOut(board.D12)
display = st7735.ST7735R(spi, cs=tft_cs, dc=tft_dc, rst=tft_reset, width=WIDTH, height=HEIGHT)

def try_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

font_small = try_font(10)
font_med = try_font(14)

image = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
draw = ImageDraw.Draw(image)

draw.rectangle([(0,0),(WIDTH-1,HEIGHT-1)], outline=(255,0,255))
draw.rectangle([(2,2),(WIDTH-3,HEIGHT-3)], outline=(0,255,255))

for x in range(0, WIDTH, 16):
    draw.line([(x,0),(x,HEIGHT-1)], fill=(40,40,40))
for y in range(0, HEIGHT, 16):
    draw.line([(0,y),(WIDTH-1,y)], fill=(40,40,40))

draw.line([(WIDTH//2,0),(WIDTH//2,HEIGHT-1)], fill=(255,255,0))
draw.line([(0,HEIGHT//2),(WIDTH-1,HEIGHT//2)], fill=(255,255,0))

def draw_text(draw_obj, text, pos, font, fill=(255,255,255)):
    bbox = draw_obj.textbbox(pos, text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw_obj.text((pos[0], pos[1]), text, font=font, fill=fill)
    return w, h

draw_text(draw, "0,0", (2,2), font_small)
w, h = draw_text(draw, "top-right", (WIDTH-2,2), font_small)
draw_text(draw, "top-right", (WIDTH-2-w,2), font_small)
w, h = draw_text(draw, "bot-left", (2,HEIGHT-2), font_small)
draw_text(draw, "bot-left", (2,HEIGHT-2-h), font_small)
w, h = draw_text(draw, "bot-right", (WIDTH-2,HEIGHT-2), font_small)
draw_text(draw, "bot-right", (WIDTH-2-w,HEIGHT-2-h), font_small)

text = "CENTER"
bbox = draw.textbbox((0,0), text, font=font_med)
w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
draw_text(draw, text, ((WIDTH-w)//2, (HEIGHT-h)//2), font=font_med, fill=(0,255,0))

display.image(image)

while True:
    time.sleep(1)

