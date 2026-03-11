"""
Vercel 썸네일 API - 1:1 비율, 포커스 키워드 전용 (일본어 버전)
각 줄마다 다른 색상 (노란색, 초록색, 핑크색)
"""

from http.server import BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import json
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            keyword = data.get('keyword', 'キーワードなし')
            bg_color1 = data.get('bg_color1', '#667eea')
            bg_color2 = data.get('bg_color2', '#764ba2')
            
            thumbnail = self.create_thumbnail(keyword, bg_color1, bg_color2)
            
            buffer = BytesIO()
            thumbnail.save(buffer, format='PNG', quality=95)
            buffer.seek(0)
            
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(buffer.getvalue())))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(buffer.getvalue())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def download_japanese_font(self):
        try:
            font_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf"
            response = urllib.request.urlopen(font_url, timeout=10)
            return BytesIO(response.read())
        except:
            try:
                font_url = "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf"
                response = urllib.request.urlopen(font_url, timeout=10)
                return BytesIO(response.read())
            except:
                return None
    
    def load_font(self, size):
        font_data = self.download_japanese_font()
        if font_data:
            try:
                return ImageFont.truetype(font_data, size)
            except:
                return ImageFont.load_default()
        return ImageFont.load_default()
    
    def split_japanese_text(self, text, max_lines=4):
        words = text.split()
        return words[:max_lines]
    
    def create_thumbnail(self, keyword, bg_color1, bg_color2):
        size = 1080
        img = Image.new('RGB', (size, size), color=bg_color1)
        draw = ImageDraw.Draw(img)
        self.draw_gradient(draw, size, size, bg_color1, bg_color2)
        
        lines = self.split_japanese_text(keyword, max_lines=4)
        num_lines = len(lines)
        
        line_colors = [
            '#fff371',  # 노란색
            '#62ff00',  # 초록색
            '#ff00a2',  # 핑크색
            '#ff00a2'   # 핑크색
        ]
        
        if num_lines == 1:
            font_size = 320
        elif num_lines == 2:
            font_size = 260
        elif num_lines == 3:
            font_size = 210
        else:
            font_size = 170
        
        font = self.load_font(font_size)
        
        # ── 핵심 수정: bbox를 정확히 측정해서 실제 텍스트 높이만 사용 ──
        line_spacing = 60
        line_bboxes = []
        total_height = 0

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            # bbox = (left, top, right, bottom)
            # top은 음수일 수 있음 → 실제 높이 = bottom - top
            actual_height = bbox[3] - bbox[1]
            line_bboxes.append(bbox)
            total_height += actual_height

        total_height += line_spacing * (num_lines - 1)

        # 세로 중앙 시작점
        y_start = (size - total_height) // 2

        for i, line in enumerate(lines):
            bbox = line_bboxes[i]
            text_width = bbox[2] - bbox[0]
            actual_height = bbox[3] - bbox[1]

            # 가로 중앙
            x = (size - text_width) // 2
            # bbox[1]이 양수면 폰트 내부 상단 여백 → y에서 빼줘야 정확한 중앙
            y = y_start - bbox[1]

            color = line_colors[i % len(line_colors)]

            # 검은색 테두리 (8방향)
            outline_width = 15
            for ox in range(-outline_width, outline_width + 1, 5):
                for oy in range(-outline_width, outline_width + 1, 5):
                    if ox != 0 or oy != 0:
                        draw.text((x + ox, y + oy), line, font=font, fill='black')

            # 메인 텍스트
            draw.text((x, y), line, font=font, fill=color)

            y_start += actual_height + line_spacing

        return img
    
    def draw_gradient(self, draw, width, height, color1, color2):
        r1, g1, b1 = self.hex_to_rgb(color1)
        r2, g2, b2 = self.hex_to_rgb(color2)
        for y in range(height):
            ratio = y / height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
