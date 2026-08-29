# -*- coding: utf-8 -*-
"""
验证码自动破解模块 — 贝壳极验点选验证码。
用法：from captcha_solver import crack_captcha
      crack_captcha(page)   # True=通过, False=失败

核心原理：
  极验的提示文字只是"请在下图依次点击"，不包含具体目标。
  真正的提示在 .geetest_ques_tips 里的小图片中（显示要点的文字/图标）。
  本模块将提示图片和验证码大图拼成一张图发给超级鹰，
  超级鹰看到"目标"+"搜索区域"后能准确返回坐标。
"""
import time, random, requests, sys, json, io
from PIL import Image

#!/usr/bin/env python
# coding:utf-8

import requests
from hashlib import md5

# 更改超级鹰账号、密码
ACCOUNT = '超级鹰账号'
PASSWORD = '超级鹰密码'

"""
参数说明:
page  当前打开的浏览器对象
"""
def crack_captcha(page, max_retries=3):
    """破解验证码。返回 True/False。"""

    for attempt in range(max_retries):
        # ---- 检测是否有验证码 ----
        url = (page.url or '').lower()
        has_captcha = any(k in url for k in ['hip.ke.com/captcha', 'captcha.lianjia.com'])
        has_trigger = _js(page, "return !!document.querySelector('[class*=\"geetest_btn_click\"]');")
        if not has_captcha and not has_trigger:
            return True

        print(f"  captcha attempt {attempt+1}/{max_retries}")

        # ==== 第一步：先触发弹窗，等验证码图片完全加载 ====
        # 必须先触发再识别，否则下载的图片 URL 可能是旧的、bg 尺寸为 0
        page_info = json.loads(_js(page, """
            var d = {};
            var bg = document.querySelector('[class*="geetest_bg"]');
            if (bg) {
                var r = bg.getBoundingClientRect();
                d.bg_x = Math.round(r.x); d.bg_y = Math.round(r.y);
                d.bg_w = Math.round(r.width); d.bg_h = Math.round(r.height);
                var s = (bg.getAttribute('style')||'').replace(/&quot;/g,'"').replace(/"/g,'"');
                var m = s.match(/url\\(["']?([^"')]+)["']?\\)/);
                d.bg_url = m ? m[1] : '';
            } else { d.bg_w = 0; d.bg_h = 0; d.bg_url = ''; }

            var btn = document.querySelector('[class*="geetest_btn_click"]');
            if (!btn) btn = document.querySelector('[class*="geetest_holder"]');
            if (btn) {
                var br = btn.getBoundingClientRect();
                d.btn_cx = Math.round(br.x+br.width/2);
                d.btn_cy = Math.round(br.y+br.height/2);
            }
            return JSON.stringify(d);
        """))

        # 如果 bg 还没加载（弹窗未触发），先点击触发按钮
        if page_info.get('bg_w', 0) < 10:
            btn_cx = page_info.get('btn_cx', 0)
            btn_cy = page_info.get('btn_cy', 0)
            if btn_cx <= 0:
                _js(page, "var r=document.querySelector('[class*=\"geetest_refresh\"]');if(r)r.click();"); time.sleep(1.5)
                continue

            print("    triggering popup...")
            _cdp_click(page, btn_cx, btn_cy)

            # 等待 bg 加载出尺寸
            for i in range(30):
                time.sleep(0.5)
                page_info = json.loads(_js(page, """
                    var bg = document.querySelector('[class*="geetest_bg"]');
                    if (!bg) return '{}';
                    var r = bg.getBoundingClientRect();
                    var s = (bg.getAttribute('style')||'').replace(/&quot;/g,'"').replace(/"/g,'"');
                    var m = s.match(/url\\(["']?([^"')]+)["']?\\)/);
                    return JSON.stringify({bg_x:Math.round(r.x),bg_y:Math.round(r.y),
                        bg_w:Math.round(r.width),bg_h:Math.round(r.height),
                        bg_url:m?m[1]:''});
                """))
                if page_info.get('bg_w', 0) > 10:
                    print(f"    bg loaded after {(i+1)*0.5:.1f}s: {page_info['bg_w']}x{page_info['bg_h']}")
                    break

            if page_info.get('bg_w', 0) < 10:
                # 再试一次点击
                _cdp_click(page, btn_cx, btn_cy)
                for i in range(20):
                    time.sleep(0.5)
                    page_info = json.loads(_js(page, """
                        var bg = document.querySelector('[class*="geetest_bg"]');
                        if (!bg) return '{}';
                        var r = bg.getBoundingClientRect();
                        var s = (bg.getAttribute('style')||'').replace(/&quot;/g,'"').replace(/"/g,'"');
                        var m = s.match(/url\\(["']?([^"')]+)["']?\\)/);
                        return JSON.stringify({bg_x:Math.round(r.x),bg_y:Math.round(r.y),
                            bg_w:Math.round(r.width),bg_h:Math.round(r.height),
                            bg_url:m?m[1]:''});
                    """))
                    if page_info.get('bg_w', 0) > 10:
                        break

        if page_info.get('bg_w', 0) < 10:
            _js(page, "var r=document.querySelector('[class*=\"geetest_refresh\"]');if(r)r.click();"); time.sleep(1.5)
            continue

        # ==== 第二步：获取提示文字和提示图（此时弹窗已展开，所有数据都是最新的）====
        extra = json.loads(_js(page, """
            var d = {};
            var tip = document.querySelector('[class*="geetest_text_tips"]');
            d.tip_text = tip ? (tip.textContent||'').trim() : '';
            var ques = document.querySelector('[class*="geetest_ques_tips"]');
            d.hint_urls = [];
            if (ques) {
                var imgs = ques.querySelectorAll('img');
                for (var i=0; i<imgs.length; i++)
                    if (imgs[i].src) d.hint_urls.push(imgs[i].src);
            }
            return JSON.stringify(d);
        """))
        page_info.update(extra)
        print(f"    tip='{page_info.get('tip_text','')}'  hints={len(page_info.get('hint_urls',[]))}")

        # ==== 第三步：下载提示图 + 验证码大图（此时都是最新的）====
        hint_imgs = []
        for hurl in page_info.get('hint_urls', []):
            data = _dl(hurl)
            if data: hint_imgs.append(data)

        # 下载验证码大图
        bg_url = page_info['bg_url']
        if bg_url.startswith('//'): bg_url = 'https:' + bg_url
        bg_img = _dl(bg_url)
        if not bg_img:
            _js(page, "var r=document.querySelector('[class*=\"geetest_refresh\"]');if(r)r.click();"); time.sleep(1.5)
            continue

        print(f"    downloaded {len(hint_imgs)} hints + bg ({len(bg_img)} bytes)")

        # ==== 第四步：拼接图片 → 超级鹰识别 ====
        composite, bg_ox, bg_oy = _build_composite(hint_imgs, bg_img)
        print(f"    composite: {composite.width}x{composite.height}  bg_offset=({bg_ox},{bg_oy})")

        # 转为 bytes 发给超级鹰
        buf = io.BytesIO()
        composite.save(buf, format='JPEG', quality=90)
        composite_bytes = buf.getvalue()

        codetype = 9101 if '语序' in page_info.get('tip_text', '') else 9005
        result = _cj.PostPic(composite_bytes, codetype)
        if result.get('err_no') != 0:
            _js(page, "var r=document.querySelector('[class*=\"geetest_refresh\"]');if(r)r.click();"); time.sleep(1.5)
            continue

        ps = result.get('pic_str', '')
        pic_id = result.get('pic_id', '')
        if not ps:
            _js(page, "var r=document.querySelector('[class*=\"geetest_refresh\"]');if(r)r.click();"); time.sleep(1.5)
            continue

        # 解析坐标，减去拼接偏移（超级鹰返回的是拼接图坐标，需转换为 bg 图坐标）
        coords = []
        try:
            for p in ps.split('|'):
                a, b = p.strip().split(',')
                x, y = int(a) - bg_ox, int(b) - bg_oy
                coords.append((x, y))
        except: continue

        print(f"    raw_coords={ps}  adjusted={coords}")

        if not coords:
            _js(page, "var r=document.querySelector('[class*=\"geetest_refresh\"]');if(r)r.click();"); time.sleep(1.5)
            continue

        # ==== 第五步：CDP 点击坐标 ====
        ox, oy = page_info['bg_x'], page_info['bg_y']
        for i, (x, y) in enumerate(coords):
            _cdp_click(page, ox + x, oy + y)
            print(f"    click #{i+1}: ({x},{y}) -> vp({ox+x},{oy+y})")
            time.sleep(random.uniform(0.35, 0.7))

        # ==== 第六步：提交并等结果 ====
        for _ in range(5):
            _js(page, """
                var b=document.querySelector('[class*="geetest_submit"]');
                if(b && !b.classList.contains('geetest_disable')) b.click();
            """)
            time.sleep(0.8)
            if _js(page, """
                var p=document.querySelector('[class*="geetest_popup_wrap"]');
                if(!p) return true;
                var r=p.getBoundingClientRect();
                return r.width<10 || window.getComputedStyle(p).display==='none';
            """): break

        # ==== 第七步：验证结果 ====
        time.sleep(random.uniform(2, 4))
        _js(page, "var m=document.querySelector('#errorModal');if(m){var c=document.querySelector('#confirmBtn');if(c)c.click();}")
        time.sleep(1.5)

        cur = (page.url or '').lower()
        if 'ke.com/ershoufang' in cur:
            return True
        if not _js(page, "return !!document.querySelector('[class*=\"geetest_btn_click\"]');"):
            return True

        if pic_id: _cj.ReportError(pic_id)

    time.sleep(30)
    return 'ke.com/ershoufang' in (page.url or '').lower()

class Chaojiying_Client(object):

    def __init__(self, username, password, soft_id):
        self.username = username
        password =  password.encode('utf8')
        self.password = md5(password).hexdigest()
        self.soft_id = soft_id
        self.base_params = {
            'user': self.username,
            'pass2': self.password,
            'softid': self.soft_id,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }

    def PostPic(self, im, codetype):
        """
        im: 图片字节
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
        }
        params.update(self.base_params)
        files = {'userfile': ('ccc.jpg', im)}
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', data=params, files=files, headers=self.headers)
        return r.json()

    def PostPic_base64(self, base64_str, codetype):
        """
        im: 图片字节
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
            'file_base64':base64_str
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', data=params, headers=self.headers)
        return r.json()

    def ReportError(self, im_id):
        """
        im_id:报错题目的图片ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/ReportError.php', data=params, headers=self.headers)
        return r.json()


if __name__ == '__main__':
    chaojiying = Chaojiying_Client(ACCOUNT, PASSWORD, '977219')	#用户中心>>软件ID 生成一个替换 96001
    im = open('a.jpg', 'rb').read()#本地图片文件路径 来替换 a.jpg 有时WIN系统须要//
    """
    0秒找到各种缺口，各种色块，三角形，方形，菱形，心形，太阳，星形，月亮，五星，梯形，水滴，箭头，小飞机，圆环，盾形等各种图形块。

    9900，得到图像上所有的图形块信息，每个图形块用矩形定位(x1,y1,x2,y2)，即左上角和右下角；多矩形以 | 分隔，按可信度排列从大到小。可信度是指找得到图形块的可信度,和图形块的形状没关系。
    9901，仅适用图像上有且仅有一个图形块的，  返回一个中心点坐标(x,y)。返回用9900识别后的第一个框的中心点坐标。
    9902，仅适用图像上有且仅有两个图形块的，  返回两个中心点坐标(x1,y1|x2,y2)。返回用9900识别后的前两个框的中心点坐标。两个坐标的x值相减的绝对值是这两个坐标的水平距离。

    9902：

    以curl为例，在windows中进入cmd到终端窗口。
    curl https://upload.chaojiying.net/Upload/Processing.php -X POST -F "user=您的账号" -F "pass=您的密码" -F "softid=96001" -F "codetype=9902" -F "userfile=@图像文件本地路径"
    返回json信息
    {"err_no":0,"err_str":"OK","pic_id":"1280001100000010001","pic_str":"16,42|244,42","md5":"8e6fc22caf34c815fafb658bf912d24c"}
    "x,y"代表一个坐标点，图像左上角为原点"0,0"；x是从左往右数的像率px值；y是从上往下数的像率px值。多坐标以|分隔。
    进入用户中心，点识别记录，在图像区那里点 坐标 按纽，就可以显示坐标信息。
    """
    print(chaojiying.PostPic(im, 9900))
    # print( chaojiying.PostPic(base64_str, 1902))#此处为传入 base64代码


_cj = Chaojiying_Client(username=ACCOUNT, password=PASSWORD, soft_id='977219')


def _js(page, code):
    try: return page.run_js(code)
    except: return None


def _cdp_click(page, x, y):
    """使用 CDP 底层鼠标事件点击 viewport 坐标（绕过自动化检测）"""
    try:
        page.run_cdp('Input.dispatchMouseEvent', type='mouseMoved', x=x, y=y, button='left', clickCount=0)
        time.sleep(0.03)
        page.run_cdp('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button='left', clickCount=1)
        time.sleep(random.uniform(0.06, 0.13))
        page.run_cdp('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button='left', clickCount=1)
    except: pass


def _dl(url, referer='https://hip.ke.com/'):
    """下载图片，返回 (bytes, PIL.Image)"""
    if not url: return None
    if url.startswith('//'): url = 'https:' + url
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36', 'Referer': referer}
    try:
        r = requests.get(url, headers=h, timeout=15)
        if r.status_code == 200 and len(r.content) > 100:
            return r.content
    except: pass
    return None


def _build_composite(hint_imgs, bg_img):
    """
    将提示图片和验证码大图拼接为一张图。
    布局：提示图水平排列在顶部白底上 → 分隔线 → 验证码大图。
    返回 (composite_PIL_Image, hint_section_height)
    """
    # 统一提示图高度为 36px
    HINT_H = 36
    PAD = 8          # 提示图之间的间距
    SEP = 2          # 分隔线高度
    MARGIN = 10      # 左右边距

    resized_hints = []
    for raw in hint_imgs:
        try:
            im = Image.open(io.BytesIO(raw)).convert('RGBA')
            ratio = HINT_H / im.height
            new_w = max(int(im.width * ratio), 1)
            im = im.resize((new_w, HINT_H), Image.LANCZOS)
            resized_hints.append(im)
        except: pass

    if not resized_hints:
        # 没有提示图，直接用原图，偏移量为 0
        return Image.open(io.BytesIO(bg_img)).convert('RGB'), 0, 0

    # 计算拼接画布宽度：取提示图总宽和验证码图宽中的较大值
    hints_total_w = sum(im.width for im in resized_hints) + PAD * (len(resized_hints) - 1) + MARGIN * 2
    bg_pil = Image.open(io.BytesIO(bg_img)).convert('RGB')
    canvas_w = max(hints_total_w, bg_pil.width)
    hint_area_h = MARGIN + HINT_H + MARGIN  # 上下各留间距
    sep_area_h = SEP
    canvas_h = hint_area_h + sep_area_h + bg_pil.height

    # 创建白色画布
    canvas = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))

    # 粘贴提示图（水平居中排列）
    x = (canvas_w - sum(im.width for im in resized_hints) - PAD * (len(resized_hints) - 1)) // 2
    y = MARGIN
    for im in resized_hints:
        # 白色背景
        bg = Image.new('RGB', im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[3] if im.mode == 'RGBA' else None)
        canvas.paste(bg, (x, y))
        x += im.width + PAD

    # 分隔线（浅灰）
    for px in range(canvas_w):
        for py in range(hint_area_h, hint_area_h + sep_area_h):
            if 0 <= px < canvas_w and 0 <= py < canvas_h:
                canvas.putpixel((px, py), (220, 220, 220))

    # 粘贴验证码大图（水平居中）
    bg_x = (canvas_w - bg_pil.width) // 2
    canvas.paste(bg_pil, (bg_x, hint_area_h + sep_area_h))

    bg_offset_x = (canvas_w - bg_pil.width) // 2
    bg_offset_y = hint_area_h + sep_area_h
    return canvas, bg_offset_x, bg_offset_y



