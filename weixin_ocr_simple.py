#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章爬虫 - 简化版OCR功能
使用Tesseract OCR识别图片中的文字

依赖安装:
pip install selenium beautifulsoup4 lxml pandas pillow pytesseract
brew install tesseract tesseract-lang  # macOS
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

# OCR引擎
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    print("✅ Tesseract OCR可用")
except ImportError:
    TESSERACT_AVAILABLE = False
    print("❌ Tesseract OCR未安装")


class WeixinOCRCrawler:
    """微信文章爬虫 - 简化版OCR功能"""
    
    def __init__(self, headless=True, wait_time=15):
        """
        初始化爬虫
        
        Args:
            headless: 是否使用无头模式
            wait_time: 页面加载等待时间
        """
        self.headless = headless
        self.wait_time = wait_time
        self.driver = None
    
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
            
            # 跳过base64图片和无效URL
            if img_url.startswith('data:') or not img_url.startswith('http'):
                return None
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': base_url
            }
            
            response = requests.get(img_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 转换为PIL Image对象
            image = Image.open(BytesIO(response.content))
            
            # 转换为RGB模式（如果需要）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            print(f"⚠️  图片下载失败 {img_url}: {e}")
            return None
    
    def extract_text_from_image(self, image):
        """使用Tesseract OCR从图片中提取文字"""
        if not image or not TESSERACT_AVAILABLE:
            return ""
        
        try:
            # 使用Tesseract OCR，支持中英文
            # 配置OCR参数
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz一二三四五六七八九十百千万亿零壹贰叁肆伍陆柒捌玖拾佰仟萬億零'
            
            # 先尝试中英文混合识别
            text = pytesseract.image_to_string(image, lang='chi_sim+eng', config=custom_config)
            
            # 如果结果为空，尝试只用英文
            if not text.strip():
                text = pytesseract.image_to_string(image, lang='eng')
            
            # 如果还是为空，尝试只用中文
            if not text.strip():
                text = pytesseract.image_to_string(image, lang='chi_sim')
            
            # 清理文本
            text = text.strip()
            # 移除过短的识别结果（可能是噪声）
            if len(text) < 3:
                return ""
            
            return text
            
        except Exception as e:
            print(f"⚠️  OCR识别失败: {e}")
            return ""
    
    def extract_content_with_ocr(self, page_source, base_url=None):
        """提取文章内容，包括OCR图片文字识别"""
        if not page_source:
            return {
                'title': '未知标题',
                'content': '',
                'images': [],
                'image_texts': [],
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
                print(f"✅ 使用选择器 {selector} 提取到内容")
                break
        
        if not content_element:
            print("⚠️  未找到内容区域，尝试从body提取")
            content_element = soup.find('body')
        
        # 提取文本内容和图片
        paragraphs = []
        images = []
        image_texts = []
        
        if content_element:
            # 提取图片信息和OCR文字
            img_elements = content_element.find_all('img')
            print(f"🖼️  找到 {len(img_elements)} 张图片")
            
            for i, img in enumerate(img_elements, 1):
                img_src = img.get('src', '')
                img_alt = img.get('alt', '')
                img_title = img.get('title', '')
                
                img_info = {
                    'index': i,
                    'src': img_src,
                    'alt': img_alt,
                    'title': img_title
                }
                images.append(img_info)
                
                # 如果alt属性有有意义的文字，先使用alt
                if img_alt and len(img_alt) > 2 and img_alt not in ['图片', '图', 'image']:
                    image_texts.append({
                        'image_index': i,
                        'text': img_alt,
                        'source': 'alt_attribute',
                        'src': img_src
                    })
                    paragraphs.append(f"[图片{i}]: {img_alt}")
                    print(f"✅ 图片 {i} 使用alt属性: {img_alt}")
                    continue
                
                # OCR识别图片中的文字
                if TESSERACT_AVAILABLE and img_src:
                    print(f"🔍 正在OCR识别第 {i} 张图片...")
                    image_obj = self.download_image(img_src, base_url or '')
                    if image_obj:
                        ocr_text = self.extract_text_from_image(image_obj)
                        if ocr_text:
                            image_texts.append({
                                'image_index': i,
                                'text': ocr_text,
                                'source': 'ocr',
                                'src': img_src
                            })
                            paragraphs.append(f"[图片{i}文字内容]: {ocr_text}")
                            print(f"✅ 图片 {i} OCR识别: {ocr_text[:50]}...")
                        else:
                            print(f"⚠️  图片 {i} OCR未识别到文字")
                    else:
                        print(f"⚠️  图片 {i} 下载失败")
            
            # 提取常规文本内容
            text_elements = content_element.find_all(['p', 'div', 'span', 'section', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            for element in text_elements:
                text = element.get_text(strip=True)
                if text and len(text) > 5 and not self._is_navigation_text(text):
                    paragraphs.append(text)
            
            # 如果没有提取到足够的文本，尝试其他方法
            if len([p for p in paragraphs if not p.startswith('[图片')]) < 2:
                print("⚠️  常规文本较少，尝试提取所有文本节点")
                for string in content_element.stripped_strings:
                    text = string.strip()
                    if len(text) > 5 and not self._is_navigation_text(text):
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
            if p not in seen and len(p.strip()) > 3:
                unique_paragraphs.append(p)
                seen.add(p)
        
        content = '\n\n'.join(unique_paragraphs)
        
        return {
            'title': title,
            'content': content,
            'images': images,
            'image_texts': image_texts,
            'tables': tables
        }
    
    def _is_navigation_text(self, text):
        """判断是否为导航或无关文本"""
        nav_keywords = [
            "微信扫一扫", "关注该公众号", "分享到", "点击查看", "阅读原文",
            "在看", "点赞", "分享", "收藏", "写留言", "朋友圈", "QQ空间",
            "新浪微博", "QQ好友", "请在微信搜索", "长按识别", "扫描二维码",
            "参数错误", "该内容已被发布者删除", "此内容因违规无法查看"
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


def test_weixin_ocr():
    """测试微信爬虫OCR功能"""
    # 测试URL
    test_url = "https://mp.weixin.qq.com/s/kHAv-XraEN_82NGegRlZUw"
    
    print("🚀 微信文章爬虫 - OCR文字识别测试")
    print("=" * 60)
    print(f"测试URL: {test_url}")
    print("=" * 60)
    
    try:
        with WeixinOCRCrawler(headless=True) as crawler:
            # 爬取页面
            page_source = crawler.crawl_article(test_url)
            
            if page_source:
                # 提取内容（包括OCR）
                result = crawler.extract_content_with_ocr(page_source, test_url)
                
                print(f"\n📊 提取结果:")
                print(f"标题: {result['title']}")
                print(f"内容长度: {len(result['content'])} 字符")
                print(f"图片数量: {len(result['images'])}")
                print(f"识别到文字的图片数量: {len(result['image_texts'])}")
                print(f"表格数量: {len(result['tables'])}")
                
                # 显示图片信息
                if result['images']:
                    print(f"\n🖼️  图片信息:")
                    for img in result['images']:
                        print(f"图片 {img['index']}: {img['alt'] or '无alt属性'}")
                
                # 显示图片OCR结果
                if result['image_texts']:
                    print(f"\n🔍 图片文字识别结果:")
                    for img_text in result['image_texts']:
                        source_type = "alt属性" if img_text['source'] == 'alt_attribute' else "OCR识别"
                        print(f"图片 {img_text['image_index']} ({source_type}): {img_text['text'][:100]}...")
                
                # 显示内容预览
                if result['content']:
                    print(f"\n📄 内容预览:")
                    preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                    print(preview)
                else:
                    print(f"\n⚠️  未能提取到文本内容")
                    print("可能的原因:")
                    print("- 文章主要包含图片内容（已通过OCR识别）")
                    print("- 需要登录微信查看")
                    print("- URL已失效或需要特殊权限")
                    
            else:
                print("❌ 未能获取页面内容")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        traceback.print_exc()
    
    print("\n✅ 测试完成")
    
    print("\n💡 OCR功能使用提示:")
    print("1. OCR识别准确率取决于图片质量和文字清晰度")
    print("2. 支持中英文混合识别")
    print("3. 优先使用图片的alt属性，如果没有再进行OCR识别")
    print("4. 建议在网络良好的环境下使用")
    print("5. 如果图片较多，识别过程可能需要一些时间")


if __name__ == "__main__":
    test_weixin_ocr()