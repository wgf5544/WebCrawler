#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章爬虫 - 最终版本

功能特点:
1. 支持动态内容加载
2. 多种内容提取策略
3. 反爬虫检测
4. 详细的错误处理和调试信息
5. 支持多种微信文章格式

使用说明:
1. 确保已安装 Chrome 浏览器
2. 安装依赖: pip install selenium beautifulsoup4 lxml pandas
3. 运行脚本并提供微信文章URL

注意事项:
- 某些文章可能需要登录微信才能查看完整内容
- 部分文章内容可能主要为图片，文本内容较少
- 建议使用公开可访问的微信文章进行测试
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd
import re

class WeixinCrawler:
    def __init__(self, headless=True, wait_time=20):
        self.headless = headless
        self.wait_time = wait_time
        self.driver = None
    
    def setup_driver(self):
        """配置Chrome浏览器"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # 反检测配置
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # 执行反检测脚本
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def crawl_article(self, url):
        """爬取微信文章"""
        if not self.driver:
            self.setup_driver()
        
        try:
            print(f"正在访问: {url}")
            self.driver.get(url)
            
            # 检查页面状态
            self._check_page_status()
            
            # 等待内容加载
            self._wait_for_content()
            
            # 触发动态内容加载
            self._trigger_content_loading()
            
            # 获取页面源代码
            page_source = self.driver.page_source
            print(f"页面源代码长度: {len(page_source)}")
            
            return page_source
            
        except Exception as e:
            print(f"爬取过程中发生错误: {e}")
            raise
    
    def _check_page_status(self):
        """检查页面状态"""
        page_source = self.driver.page_source
        
        if "参数错误" in page_source:
            print("⚠️  检测到参数错误，URL可能无效")
        elif "验证" in page_source or "登录" in page_source:
            print("⚠️  检测到需要验证或登录")
        elif "访问过于频繁" in page_source:
            print("⚠️  访问频率过高，建议稍后重试")
        else:
            print("✅ 页面状态正常")
    
    def _wait_for_content(self):
        """等待内容加载"""
        wait = WebDriverWait(self.driver, self.wait_time)
        
        # 等待标题
        try:
            wait.until(EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.rich_media_title")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2.rich_media_title")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".rich_media_title")),
                EC.presence_of_element_located((By.TAG_NAME, "h1")),
                EC.presence_of_element_located((By.TAG_NAME, "h2"))
            ))
            print("✅ 标题已加载")
        except:
            print("⚠️  标题加载超时")
        
        # 等待内容区域
        try:
            wait.until(EC.any_of(
                EC.presence_of_element_located((By.ID, "js_content")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".rich_media_content")),
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            ))
            print("✅ 内容区域已加载")
        except:
            print("⚠️  内容区域加载超时")
    
    def _trigger_content_loading(self):
        """触发动态内容加载"""
        try:
            # 滚动页面
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # 触发事件
            self.driver.execute_script("""
                window.dispatchEvent(new Event('scroll'));
                window.dispatchEvent(new Event('resize'));
                window.dispatchEvent(new Event('load'));
            """)
            
            # 额外等待
            time.sleep(3)
            
        except Exception as e:
            print(f"触发内容加载时出错: {e}")
    
    def extract_content(self, page_source):
        """提取文章内容"""
        soup = BeautifulSoup(page_source, "lxml")
        
        # 提取标题
        title = self._extract_title(soup)
        
        # 提取正文
        content = self._extract_main_content(soup)
        
        # 提取图片信息
        images = self._extract_images(soup)
        
        # 提取表格
        tables = self._extract_tables(soup)
        
        return {
            "title": title,
            "content": content,
            "images": images,
            "tables": tables,
            "content_length": len(content),
            "image_count": len(images),
            "table_count": len(tables)
        }
    
    def _extract_title(self, soup):
        """提取标题"""
        title_selectors = [
            "h1.rich_media_title",
            "h2.rich_media_title",
            ".rich_media_title",
            "h1",
            "h2",
            "title"
        ]
        
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                title = elem.get_text(strip=True)
                # 过滤掉通用标题
                if title not in ["微信公众平台", "微信", "WeChat"]:
                    print(f"✅ 找到标题: {title}")
                    return title
        
        print("⚠️  未找到有效标题")
        return "未知标题"
    
    def _extract_main_content(self, soup):
        """提取正文内容"""
        content_selectors = [
            "#js_content",
            ".rich_media_content",
            "article",
            ".article-content",
            "main",
            ".content"
        ]
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                content = self._extract_text_from_element(elem)
                if content and len(content) > 50:  # 至少50个字符才认为是有效内容
                    print(f"✅ 使用选择器 {selector} 提取到内容，长度: {len(content)}")
                    return content
        
        # 如果都没找到，尝试从body提取
        body = soup.find("body")
        if body:
            content = self._extract_text_from_element(body)
            if content:
                print(f"⚠️  从body提取内容，长度: {len(content)}")
                return content
        
        print("❌ 未能提取到有效内容")
        return ""
    
    def _extract_text_from_element(self, element):
        """从元素中提取文本"""
        paragraphs = []
        
        # 方法1: 提取段落和文本元素
        text_elements = element.find_all(["p", "div", "span", "section", "h1", "h2", "h3", "h4", "h5", "h6"])
        for elem in text_elements:
            text = elem.get_text(strip=True)
            if text and len(text) > 10 and text not in paragraphs:
                # 过滤掉明显的导航或无关内容
                if not self._is_navigation_text(text):
                    paragraphs.append(text)
        
        # 方法2: 如果没有找到段落，提取所有文本节点
        if not paragraphs:
            for string in element.stripped_strings:
                text = string.strip()
                if len(text) > 10 and not self._is_navigation_text(text):
                    paragraphs.append(text)
        
        return "\n\n".join(paragraphs) if paragraphs else ""
    
    def _is_navigation_text(self, text):
        """判断是否为导航或无关文本"""
        nav_keywords = [
            "微信扫一扫", "关注该公众号", "分享到", "点击查看", "阅读原文",
            "在看", "点赞", "分享", "收藏", "写留言", "视频小程序",
            "轻点两下", "取消赞", "取消在看", "参数错误"
        ]
        
        return any(keyword in text for keyword in nav_keywords)
    
    def _extract_images(self, soup):
        """提取图片信息"""
        images = []
        img_elements = soup.find_all("img")
        
        for img in img_elements:
            img_info = {
                "src": img.get("src", ""),
                "data-src": img.get("data-src", ""),
                "alt": img.get("alt", ""),
                "title": img.get("title", "")
            }
            if img_info["src"] or img_info["data-src"]:
                images.append(img_info)
        
        return images
    
    def _extract_tables(self, soup):
        """提取表格数据"""
        tables = []
        table_elements = soup.find_all("table")
        
        for table in table_elements:
            try:
                df = pd.read_html(str(table))[0]
                tables.append(df)
            except Exception as e:
                print(f"表格解析失败: {e}")
        
        return tables
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def main():
    """主函数 - 演示用法"""
    # 测试URL列表
    test_urls = [
        "https://mp.weixin.qq.com/s/lt-up7a7BeYY5nVUUOsCeQ",
        # 可以添加更多测试URL
    ]
    
    # 使用上下文管理器确保资源正确释放
    with WeixinCrawler(headless=True, wait_time=15) as crawler:
        for i, url in enumerate(test_urls, 1):
            print(f"\n{'='*80}")
            print(f"测试 {i}: 微信文章爬取")
            print(f"URL: {url}")
            print(f"{'='*80}")
            
            try:
                # 爬取页面
                page_source = crawler.crawl_article(url)
                
                # 提取内容
                result = crawler.extract_content(page_source)
                
                # 输出结果
                print(f"\n📊 提取结果:")
                print(f"标题: {result['title']}")
                print(f"内容长度: {result['content_length']} 字符")
                print(f"图片数量: {result['image_count']}")
                print(f"表格数量: {result['table_count']}")
                
                if result['content']:
                    print(f"\n📝 内容预览:")
                    preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                    print(preview)
                else:
                    print(f"\n⚠️  未能提取到文本内容")
                    print(f"可能的原因:")
                    print(f"- 文章主要包含图片内容")
                    print(f"- 需要登录微信查看")
                    print(f"- URL已失效或需要特殊权限")
                    print(f"- 内容完全由JavaScript动态生成")
                
                if result['images']:
                    print(f"\n🖼️  图片信息:")
                    for j, img in enumerate(result['images'][:3], 1):  # 只显示前3张
                        print(f"图片 {j}: {img['alt'] or '无描述'}")
                
                if result['tables']:
                    print(f"\n📋 表格信息:")
                    for j, table in enumerate(result['tables'], 1):
                        print(f"表格 {j}: {table.shape[0]}行 x {table.shape[1]}列")
                
            except Exception as e:
                print(f"❌ 处理失败: {e}")
                import traceback
                traceback.print_exc()
    
    print(f"\n✅ 测试完成")
    print(f"\n💡 使用提示:")
    print(f"1. 如果内容提取失败，尝试使用公开可访问的微信文章")
    print(f"2. 某些文章可能需要在微信中打开才能查看完整内容")
    print(f"3. 可以修改 headless=False 来观察浏览器行为")
    print(f"4. 调整 wait_time 参数来适应不同的网络环境")

if __name__ == "__main__":
    main()