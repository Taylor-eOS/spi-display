import time
import board
import digitalio
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7735

MODE = "system" #Set to "text", "image", or "system"
IMAGE_FILE = "display_image.png"
WIDTH = 128
HEIGHT = 160
SAMPLE_TEXT = """In the beginning was the Word, and the Word was with God, and the Word was God. The same was in the beginning with God. All things were made by him; and without him was not any thing made that was made."""
spi = board.SPI()
tft_cs = digitalio.DigitalInOut(board.D5)
tft_dc = digitalio.DigitalInOut(board.D6)
tft_reset = digitalio.DigitalInOut(board.D12)
display = st7735.ST7735R(spi, cs=tft_cs, dc=tft_dc, rst=tft_reset, width=WIDTH, height=HEIGHT)
_WIFI_CACHE = {"iface": None, "last_rssi": None, "alpha": 0.3}

def try_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

def wrap_text(text, font, max_width):
    lines = []
    words = text.split()
    current_line = ""
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), test_line, font=font)
        if bbox[2] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def display_text():
    font = try_font(11)
    image = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = 4
    max_width = WIDTH - 2 * margin
    lines = wrap_text(SAMPLE_TEXT, font, max_width)
    line_height = 13
    y = margin
    for line in lines:
        if y + line_height > HEIGHT - margin:
            break
        draw.text((margin, y), line, font=font, fill=(255, 255, 255))
        y += line_height
    display.image(image)

def display_image():
    if os.path.exists(IMAGE_FILE):
        try:
            img = Image.open(IMAGE_FILE)
            img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            pixels = img.load()
            for y in range(img.height):
                for x in range(img.width):
                    r, g, b = pixels[x, y]
                    pixels[x, y] = (b, g, r)
            display.image(img)
        except Exception as e:
            error_img = Image.new("RGB", (WIDTH, HEIGHT), (40, 0, 0))
            draw = ImageDraw.Draw(error_img)
            font = try_font(10)
            draw.text((10, HEIGHT//2 - 10), f"Error loading\n{IMAGE_FILE}", font=font, fill=(255, 255, 255))
            display.image(error_img)
    else:
        error_img = Image.new("RGB", (WIDTH, HEIGHT), (40, 0, 0))
        draw = ImageDraw.Draw(error_img)
        font = try_font(10)
        draw.text((10, HEIGHT//2 - 10), f"{IMAGE_FILE}\nnot found", font=font, fill=(255, 255, 255))
        display.image(error_img)

def get_cpu_temp():
    try:
        temp = subprocess.check_output(["vcgencmd", "measure_temp"]).decode('utf-8')
        return temp.split('=')[1].split("'")[0] + "°C"
    except:
        return "N/A"

def get_ip_address():
    try:
        result = subprocess.check_output(["hostname", "-I"]).decode('utf-8').strip()
        return result.split()[0] if result else "No IP"
    except:
        return "No IP"

def get_system_info():
    try:
        with open('/proc/stat') as f:
            for line in f:
                if line.startswith('cpu '):
                    fields = line.split()
                    total = sum(int(x) for x in fields[1:8])
                    idle = int(fields[4])
                    return (total - idle) / total * 100 if total > 0 else 0
    except:
        return 0

def get_memory_info():
    try:
        with open('/proc/meminfo') as f:
            mem_total = mem_free = 0
            for line in f:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1])
                elif line.startswith('MemFree:'):
                    mem_free = int(line.split()[1])
            return (mem_total - mem_free) / mem_total * 100 if mem_total > 0 else 0
    except:
        return 0

def get_disk_info():
    try:
        stat = os.statvfs('/')
        total = stat.f_blocks * stat.f_frsize
        used = (stat.f_blocks - stat.f_bfree) * stat.f_frsize
        return (used / total) * 100 if total > 0 else 0
    except:
        return 0

def get_uptime():
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds
    except:
        return 0

def _detect_iface(timeout=0.2):
    import subprocess, re
    try:
        p = subprocess.run(["iw", "dev"], capture_output=True, text=True, timeout=timeout)
        for line in p.stdout.splitlines():
            line = line.strip()
            if line.startswith("Interface"):
                return line.split()[1]
    except:
        pass
    try:
        with open("/proc/net/wireless", "r") as f:
            lines = f.readlines()
        for l in lines[2:]:
            parts = l.split()
            if parts:
                return parts[0].strip(":")
    except:
        pass
    return None

def get_wifi_strength():
    import subprocess, re
    ssid = ""
    try:
        ssid = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True, timeout=0.15).stdout.strip()
    except:
        ssid = ""
    iface = _WIFI_CACHE.get("iface")
    if not iface:
        iface = _detect_iface()
        _WIFI_CACHE["iface"] = iface
    rssi = None
    pct = None
    if iface:
        try:
            out = subprocess.run(["iw", "dev", iface, "link"], capture_output=True, text=True, timeout=0.25).stdout
            m = re.search(r"signal:\s*(-?\d+)\s*dBm", out)
            if m:
                rssi = int(m.group(1))
        except:
            rssi = None
    if rssi is None:
        try:
            with open("/proc/net/wireless", "r") as f:
                lines = f.readlines()
            for l in lines[2:]:
                parts = l.split()
                if len(parts) >= 3:
                    qual = parts[2].strip(".")
                    try:
                        qval = float(qual)
                        pct = max(0.0, min(100.0, (qval / 70.0) * 100.0))
                        break
                    except:
                        continue
        except:
            pct = None
    if rssi is None and pct is None:
        try:
            out = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=0.25).stdout
            m = re.search(r"Signal level=(-?\d+)", out)
            if m:
                rssi = int(m.group(1))
        except:
            rssi = None
    if rssi is not None:
        last = _WIFI_CACHE.get("last_rssi")
        alpha = _WIFI_CACHE.get("alpha", 0.3)
        smooth = rssi if last is None else (last * (1.0 - alpha) + rssi * alpha)
        _WIFI_CACHE["last_rssi"] = smooth
        rssi_int = int(round(smooth))
        if rssi_int <= -100:
            pct = 0.0
        elif rssi_int >= -50:
            pct = 100.0
        else:
            pct = 2.0 * (rssi_int + 100.0)
        return (ssid + " " if ssid else "") + f"{pct:.0f}% ({rssi_int} dBm)"
    if pct is not None:
        return (ssid + " " if ssid else "") + f"{pct:.0f}%"
    return "No WiFi" if not ssid else ssid

def display_system():
    font_small = try_font(9)
    font_med = try_font(11)
    image = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    cpu_percent = get_system_info()
    mem_percent = get_memory_info()
    disk_percent = get_disk_info()
    cpu_temp = get_cpu_temp()
    ip_addr = get_ip_address()
    y = 5
    line_height = 12
    draw.text((5, y), "RASPBERRY PI STATUS", font=font_med, fill=(0, 255, 255))
    y += line_height + 3
    draw.text((5, y), f"CPU: {cpu_percent:.1f}%", font=font_small, fill=(255, 255, 255))
    y += line_height
    draw.text((5, y), f"Temp: {cpu_temp}", font=font_small, fill=(255, 255, 255))
    y += line_height
    mem_color = (255, 100, 100) if mem_percent > 80 else (255, 255, 255)
    draw.text((5, y), f"RAM: {mem_percent:.1f}%", font=font_small, fill=mem_color)
    y += line_height
    disk_color = (255, 100, 100) if disk_percent > 90 else (255, 255, 255)
    draw.text((5, y), f"Disk: {disk_percent:.1f}%", font=font_small, fill=disk_color)
    y += line_height + 2
    draw.text((5, y), f"IP: {ip_addr}", font=font_small, fill=(100, 255, 100))
    y += line_height + 2
    wifi_str = get_wifi_strength()
    draw.text((5, y), f"{wifi_str}", font=font_small, fill=(100, 255, 100))
    y += line_height
    uptime_seconds = get_uptime()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    draw.text((5, y), f"Up: {hours}h {minutes}m", font=font_small, fill=(255, 255, 255))
    y += line_height
    try:
        with open('/proc/loadavg', 'r') as f:
            load_avg = float(f.readline().split()[0])
    except:
        load_avg = 0
    draw.text((5, y), f"Load: {load_avg:.2f}", font=font_small, fill=(255, 255, 255))
    y += line_height + 3
    current_time = time.strftime("%H:%M:%S")
    current_date = time.strftime("%Y-%m-%d")
    draw.text((5, y), current_date, font=font_small, fill=(200, 200, 200))
    y += line_height
    draw.text((5, y), current_time, font=font_med, fill=(255, 255, 0))
    display.image(image)


if MODE == "text":
    display_text()
elif MODE == "image":
    display_image()
elif MODE == "system":
    while True:
        display_system()
        time.sleep(5)
else:
    error_img = Image.new("RGB", (WIDTH, HEIGHT), (40, 0, 0))
    draw = ImageDraw.Draw(error_img)
    font = try_font(12)
    draw.text((10, HEIGHT//2 - 10), "Invalid MODE\nset in script", font=font, fill=(255, 255, 255))
    display.image(error_img)

if MODE != "system":
    while True:
        time.sleep(1)

