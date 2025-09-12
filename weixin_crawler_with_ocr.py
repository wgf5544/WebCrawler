#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章爬虫 - 带OCR图片文字识别功能
支持提取图片中的文字内容

依赖安装:
pip install selenium beautifulsoup4 lxml pandas pillow pytesseract easyocr

注意: 需要安装Tesseract OCR引擎
macOS: brew install tesseract tesseract-lang
Ubuntu: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
Windows: 下载安装包 https://github.com/UB-Mannheim/tesseract/wiki
"""

import time
import requests
import traceback
from io import BytesIO
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from PIL import Image
import pandas as pd

# OCR引擎选择
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️  Tesseract OCR未安装，将跳过OCR功能")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("⚠️  EasyOCR未安装，将跳过EasyOCR功能")


class WeixinCrawlerWithOCR:
    """微信文章爬虫 - 带OCR功能"""
    
    def __init__(self, headless=True, wait_time=15, ocr_engine='auto'):
        """
        初始化爬虫
        
        Args:
            headless: 是否使用无头模式
            wait_time: 页面加载等待时间
            ocr_engine: OCR引擎选择 ('tesseract', 'easyocr', 'auto')
        """
        self.headless = headless
        self.wait_time = wait_time
        self.driver = None
        self.ocr_engine = ocr_engine
        self.easyocr_reader = None
        
        # 初始化OCR引擎
        self._init_ocr()
    
    def _init_ocr(self):
        """初始化OCR引擎"""
        if self.ocr_engine == 'auto':
            if EASYOCR_AVAILABLE:
                self.ocr_engine = 'easyocr'
                print("🔍 使用EasyOCR引擎")
            elif TESSERACT_AVAILABLE:
                self.ocr_engine = 'tesseract'
                print("🔍 使用Tesseract OCR引擎")
            else:
                self.ocr_engine = None
                print("❌ 未找到可用的OCR引擎")
        
        if self.ocr_engine == 'easyocr' and EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['ch_sim', 'en'])
                print("✅ EasyOCR初始化成功")
            except Exception as e:
                print(f"❌ EasyOCR初始化失败: {e}")
                self.ocr_engine = 'tesseract' if TESSERACT_AVAILABLE else None
    
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # 反爬虫检测配置
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置User-Agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # 执行反检测脚本
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        
        print("✅ 浏览器驱动初始化完成")
    
    def crawl_article(self, url):
        """爬取微信文章页面源代码"""
        if not self.driver:
            self.setup_driver()
        
        try:
            print(f"正在访问: {url}")
            self.driver.get(url)
            
            # 检查页面状态
            if "参数错误" in self.driver.page_source or "该内容已被发布者删除" in self.driver.page_source:
                print("⚠️  检测到参数错误，URL可能无效")
            
            # 等待页面基本加载
            time.sleep(3)
            
            # 等待标题加载
            wait = WebDriverWait(self.driver, self.wait_time)
            try:
                wait.until(EC.any_of(
                    EC.presence_of_element_located((By.ID, "activity-name")),
                    EC.presence_of_element_located((By.CLASS_NAME, "rich_media_title")),
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                ))
                print("✅ 标题已加载")
            except TimeoutException:
                print("⚠️  标题加载超时")
            
            # 等待内容区域加载
            try:
                wait.until(EC.any_of(
                    EC.presence_of_element_located((By.ID, "js_content")),
                    EC.presence_of_element_located((By.CLASS_NAME, "rich_media_content")),
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                ))
                print("✅ 内容区域已加载")
            except TimeoutException:
                print("⚠️  内容区域加载超时")
            
            # 滚动页面触发懒加载
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # 触发可能的动态内容加载
            self.driver.execute_script("""
                // 触发各种可能的事件
                window.dispatchEvent(new Event('scroll'));
                window.dispatchEvent(new Event('resize'));
                document.dispatchEvent(new Event('DOMContentLoaded'));
            """)
            
            time.sleep(3)
            
            page_source = self.driver.page_source
            print(f"页面源代码长度: {len(page_source)}")
            
            return page_source
            
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            traceback.print_exc()
            return None
    
    def download_image(self, img_url, base_url):
        """下载图片"""
        try:
            # 处理相对URL
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = urljoin(base_url, img_url)
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': base_url
            }
            
            response = requests.get(img_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 转换为PIL Image对象
            image = Image.open(BytesIO(response.content))
            return image
            
        except Exception as e:
            print(f"⚠️  图片下载失败 {img_url}: {e}")
            return None
    
    def extract_text_from_image(self, image):
        """从图片中提取文字"""
        if not image or not self.ocr_engine:
            return ""
        
        try:
            if self.ocr_engine == 'tesseract' and TESSERACT_AVAILABLE:
                # 使用Tesseract OCR
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                return text.strip()
            
            elif self.ocr_engine == 'easyocr' and self.easyocr_reader:
                # 使用EasyOCR
                import numpy as np
                img_array = np.array(image)
                results = self.easyocr_reader.readtext(img_array)
                
                # 提取文字内容
                texts = []
                for (bbox, text, confidence) in results:
                    if confidence > 0.5:  # 置信度阈值
                        texts.append(text)
                
                return ' '.join(texts)
            
        except Exception as e:
            print(f"⚠️  OCR识别失败: {e}")
        
        return ""
    
    def extract_content(self, page_source, base_url=None):
        """提取文章内容，包括OCR图片文字识别"""
        if not page_source:
            return {
                'title': '未知标题',
                'content': '',
                'images': [],
                'image_texts': [],  # 新增：图片中的文字
                'tables': []
            }
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 提取标题
        title = "未知标题"
        title_selectors = [
            "#activity-name",
            ".rich_media_title",
            "h1",
            ".title",
            "title"
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element and title_element.get_text(strip=True):
                title = title_element.get_text(strip=True)
                print(f"✅ 找到标题: {title}")
                break
        
        if title == "未知标题":
            print("⚠️  未找到有效标题")
        
        # 提取内容
        content_selectors = [
            "#js_content",
            ".rich_media_content",
            "article",
            ".article-content",
            "main",
            ".content"
        ]
        
        content_element = None
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content_element = element
                print(f"✅ 使用选择器 {selector} 提取到内容，长度: {len(element.get_text(strip=True))}")
                break
        
        if not content_element:
            print("⚠️  未找到内容区域，尝试从body提取")
            content_element = soup.find('body')
        
        # 提取文本内容
        paragraphs = []
        images = []
        image_texts = []  # 存储图片中识别的文字
        
        if content_element:
            # 提取图片信息和OCR文字
            img_elements = content_element.find_all('img')
            print(f"🖼️  找到 {len(img_elements)} 张图片")
            
            for i, img in enumerate(img_elements, 1):
                img_info = {
                    'src': img.get('src', ''),
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                }
                images.append(img_info)
                
                # OCR识别图片中的文字
                if self.ocr_engine and img_info['src']:
                    print(f"🔍 正在识别第 {i} 张图片中的文字...")
                    image_obj = self.download_image(img_info['src'], base_url or '')
                    if image_obj:
                        ocr_text = self.extract_text_from_image(image_obj)
                        if ocr_text:
                            image_texts.append({
                                'image_index': i,
                                'text': ocr_text,
                                'src': img_info['src']
                            })
                            print(f"✅ 图片 {i} 识别到文字: {ocr_text[:50]}...")
                            
                            # 将OCR识别的文字添加到正文内容中
                            paragraphs.append(f"[图片{i}文字内容]: {ocr_text}")
                        else:
                            print(f"⚠️  图片 {i} 未识别到文字")
            
            # 提取常规文本内容
            text_elements = content_element.find_all(['p', 'div', 'span', 'section', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            for element in text_elements:
                text = element.get_text(strip=True)
                if text and len(text) > 10 and not self._is_navigation_text(text):
                    paragraphs.append(text)
            
            # 如果没有提取到足够的文本，尝试其他方法
            if len(paragraphs) < 3:
                for string in content_element.stripped_strings:
                    text = string.strip()
                    if len(text) > 10 and not self._is_navigation_text(text):
                        paragraphs.append(text)
        
        # 提取表格
        tables = []
        table_elements = soup.find_all('table')
        for table in table_elements:
            table_data = []
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if any(row_data):  # 只添加非空行
                    table_data.append(row_data)
            if table_data:
                tables.append(table_data)
        
        # 去重和过滤
        unique_paragraphs = []
        seen = set()
        for p in paragraphs:
            if p not in seen and len(p.strip()) > 5:
                unique_paragraphs.append(p)
                seen.add(p)
        
        content = '\n\n'.join(unique_paragraphs)
        
        return {
            'title': title,
            'content': content,
            'images': images,
            'image_texts': image_texts,  # 新增：图片中的文字
            'tables': tables
        }
    
    def _is_navigation_text(self, text):
        """判断是否为导航或无关文本"""
        nav_keywords = [
            "微信扫一扫", "关注该公众号", "分享到", "点击查看", "阅读原文",
            "在看", "点赞", "分享", "收藏", "写留言", "朋友圈", "QQ空间",
            "新浪微博", "QQ好友", "请在微信搜索", "长按识别", "扫描二维码"
        ]
        return any(keyword in text for keyword in nav_keywords)
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("✅ 浏览器已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


def test_weixin_crawler_with_ocr():
    """测试微信爬虫OCR功能"""
    # 测试URL列表
    test_urls = [
        "https://mp.weixin.qq.com/s/lt-up7a7BeYY5nVUU0sCeQ",  # 普睿司曼校园招聘
        "https://mp.weixin.qq.com/s/Ub9BKKto3kSCH5tXXE_Ztg",  # 备用测试URL
    ]
    
    print("🚀 微信文章爬虫 - OCR功能测试")
    print("=" * 80)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n测试 {i}: 微信文章爬取 + OCR文字识别")
        print(f"URL: {url}")
        print("=" * 80)
        
        try:
            with WeixinCrawlerWithOCR(headless=True, ocr_engine='auto') as crawler:
                # 爬取页面
                page_source = crawler.crawl_article(url)
                
                if page_source:
                    # 提取内容
                    result = crawler.extract_content(page_source, url)
                    
                    print(f"\n📊 提取结果:")
                    print(f"标题: {result['title']}")
                    print(f"内容长度: {len(result['content'])} 字符")
                    print(f"图片数量: {len(result['images'])}")
                    print(f"识别到文字的图片数量: {len(result['image_texts'])}")
                    print(f"表格数量: {len(result['tables'])}")
                    
                    # 显示图片OCR结果
                    if result['image_texts']:
                        print(f"\n🔍 图片文字识别结果:")
                        for img_text in result['image_texts']:
                            print(f"图片 {img_text['image_index']}: {img_text['text'][:100]}...")
                    
                    # 显示内容预览
                    if result['content']:
                        print(f"\n📄 内容预览:")
                        preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                        print(preview)
                    else:
                        print(f"\n⚠️  未能提取到文本内容")
                        print("可能的原因:")
                        print("- 文章主要包含图片内容（已通过OCR识别）")
                        print("- 需要登录微信查看")
                        print("- URL已失效或需要特殊权限")
                        print("- 内容完全由JavaScript动态生成")
                else:
                    print("❌ 未能获取页面内容")
                    
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            traceback.print_exc()
        
        print("✅ 测试完成")
    
    print("\n💡 OCR功能使用提示:")
    print("1. 首次使用EasyOCR会下载模型文件，请耐心等待")
    print("2. OCR识别准确率取决于图片质量和文字清晰度")
    print("3. 支持中英文混合识别")
    print("4. 可以通过调整置信度阈值来过滤低质量识别结果")
    print("5. 建议在网络良好的环境下使用，图片下载需要时间")


if __name__ == "__main__":
    test_weixin_crawler_with_ocr()