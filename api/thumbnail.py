from http.server import BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import json
import base64
import urllib.request

class handler(BaseHTTPRequestHandler):
    
    def _set_headers(self, status=200, content_type='application/json'):
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
            # 요청 데이터 읽기
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # JSON 파싱
            data = json.loads(post_data.decode('utf-8'))
            title = data.get('title', 'タイトルなし')
            keyword = data.get('keyword', '')
            
            # 썸네일 생성
            img_base64 = create_thumbnail(title, keyword)
            
            # 응답
            self._set_headers()
            result = {
                'success': True,
                'image': img_base64
            }
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self._set_headers(500)
            error_response = {
                'success': False,
                'error': str(e)
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

def create_thumbnail(title, keyword):
    """일본어 썸네일 생성"""
    
    # 이미지 생성 (1200x630 - SNS 최적 크기)
    img = Image.new('RGB', (1200, 630), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # 그라데이션 배경
    for i in range(630):
        r = 102 - int(i * 0.15)
        g = 126 - int(i * 0.12)
        b = 234 - int(i * 0.08)
        draw.line([(0, i), (1200, i)], fill=(max(0, r), max(0, g), max(0, b)))
    
    # 일본어 폰트 다운로드 (Google Fonts)
    try:
        # Noto Sans JP 폰트 다운로드
        font_url = "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf"
        font_data = BytesIO(urllib.request.urlopen(font_url).read())
        font_title = ImageFont.truetype(font_data, 70)
        font_data.seek(0)  # 리셋
        font_keyword = ImageFont.truetype(font_data, 40)
    except:
        # 폰트 로드 실패 시 기본 폰트
        font_title = ImageFont.load_default()
        font_keyword = ImageFont.load_default()
    
    # 제목 텍스트 줄바꿈 처리
    lines = wrap_text(draw, title, font_title, 1000)
    
    # 제목 그리기 (최대 3줄)
    y = 180
    for line in lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        width = bbox[2] - bbox[0]
        x = (1200 - width) // 2
        
        # 그림자
        draw.text((x+3, y+3), line, font=font_title, fill='rgba(0,0,0,0.5)')
        # 메인 텍스트
        draw.text((x, y), line, font=font_title, fill='white')
        y += 90
    
    # 키워드 배지
    if keyword:
        badge_y = 520
        bbox = draw.textbbox((0, 0), keyword, font=font_keyword)
        badge_width = (bbox[2] - bbox[0]) + 40
        badge_x = (1200 - badge_width) // 2
        
        # 배지 배경
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_width, badge_y + 60],
            radius=30,
            fill='#764ba2'
        )
        
        # 키워드 텍스트
        text_bbox = draw.textbbox((0, 0), keyword, font=font_keyword)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = badge_x + (badge_width - text_width) // 2
        draw.text((text_x, badge_y + 12), keyword, font=font_keyword, fill='white')
    
    # Base64로 변환
    buffer = BytesIO()
    img.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_base64

def wrap_text(draw, text, font, max_width):
    """텍스트 자동 줄바꿈"""
    lines = []
    words = text.split()
    current_line = ''
    
    for word in words:
        test_line = current_line + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) < max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word
    
    if current_line:
        lines.append(current_line.strip())
    
    return lines if lines else [text]
```

**Commit new file** 클릭

---

## 3단계: Vercel 배포

### A. Vercel 계정 연결
1. [vercel.com](https://vercel.com) 접속
2. **Sign Up** 또는 **Log In** (GitHub 계정으로)

### B. 프로젝트 Import
1. Dashboard → **Add New...** → **Project**
2. **Import Git Repository** 선택
3. 방금 만든 `thumbnail-api-jp` 선택
4. **Import** 클릭

### C. 배포 설정
```
Framework Preset: Other
Build Command: (비워두기)
Output Directory: (비워두기)
```

5. **Deploy** 클릭
6. 배포 완료 후 **URL 복사** (예: `https://thumbnail-api-jp.vercel.app`)

---

## 4단계: Make.com 연동

### HTTP > Make a request

**설정:**
```
URL: https://thumbnail-api-jp.vercel.app/api/thumbnail
Method: POST

Headers:
Content-Type: application/json

Body (JSON):
{
  "title": "{{포스트 제목}}",
  "keyword": "{{포커스 키워드}}"
}
```

**응답 처리:**
- `{{image}}` 값을 Base64로 받음
- WordPress에 업로드

---

## 5단계: 테스트

### A. Postman으로 테스트 (선택사항)
```
POST https://thumbnail-api-jp.vercel.app/api/thumbnail

Body:
{
  "title": "日本の美しい桜スポット10選",
  "keyword": "桜"
}
