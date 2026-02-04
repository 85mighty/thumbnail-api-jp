from http.server import BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import json

class handler(BaseHTTPRequestHandler):
    
    def _set_headers(self, status=200, content_type='image/png'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
        
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            title = data.get('title', 'タイトルなし')
            keyword = data.get('keyword', '')
            bg_color1 = data.get('bg_color1', '#667eea')
            bg_color2 = data.get('bg_color2', '#764ba2')
            
            img_binary = create_thumbnail(title, keyword, bg_color1, bg_color2)
            
            self._set_headers(200, 'image/png')
            self.wfile.write(img_binary)
            
        except Exception as e:
            self._set_headers(500, 'application/json')
            error_response = {
                'success': False,
                'error': str(e)
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_thumbnail(title, keyword, bg_color1='#667eea', bg_color2='#764ba2'):
    color1 = hex_to_rgb(bg_color1)
    color2 = hex_to_rgb(bg_color2)
    
    img = Image.new('RGB', (1200, 630), color=color1)
    draw = ImageDraw.Draw(img)
    
    for i in range(630):
        ratio = i / 630
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        draw.line([(0, i), (1200, i)], fill=(r, g, b))
    
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_keyword = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
    except:
        font_title = ImageFont.load_default()
        font_keyword = ImageFont.load_default()
    
    max_width = 1000
    lines = []
    words = title.split()
    current_line = ''
    
    for word in words:
        test_line = current_line + word + ' '
        bbox = draw.textbbox((0, 0), test_line, font=font_title)
        if (bbox[2] - bbox[0]) < max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + ' '
    
    if current_line:
        lines.append(current_line.strip())
    
    y = 200
    for line in lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        width = bbox[2] - bbox[0]
        x = (1200 - width) // 2
        draw.text((x+3, y+3), line, font=font_title, fill=(0, 0, 0, 128))
        draw.text((x, y), line, font=font_title, fill='white')
        y += 80
    
    if keyword:
        badge_y = 520
        bbox = draw.textbbox((0, 0), keyword, font=font_keyword)
        badge_width = (bbox[2] - bbox[0]) + 40
        badge_x = (1200 - badge_width) // 2
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_width, badge_y + 55],
            radius=28,
            fill=color2
        )
        text_bbox = draw.textbbox((0, 0), keyword, font=font_keyword)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = badge_x + (badge_width - text_width) // 2
        draw.text((text_x, badge_y + 10), keyword, font=font_keyword, fill='white')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    return buffer.read()
