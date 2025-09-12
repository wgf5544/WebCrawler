from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd

def crawl_weixin_article(url):
    """爬取微信文章内容"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 执行反检测脚本
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"正在访问: {url}")
        driver.get(url)
        
        # 等待页面基本加载
        wait = WebDriverWait(driver, 20)
        
        # 检查是否需要验证或登录
        try:
            # 检查是否有验证码或登录提示
            if "验证" in driver.page_source or "登录" in driver.page_source:
                print("检测到需要验证或登录")
        except:
            pass
        
        # 等待标题加载
        title_loaded = False
        try:
            wait.until(EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.rich_media_title")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2.rich_media_title")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "title"))
            ))
            title_loaded = True
            print("页面标题已加载")
        except:
            print("标题加载超时")
        
        # 等待内容区域
        content_loaded = False
        try:
            wait.until(EC.any_of(
                EC.presence_of_element_located((By.ID, "js_content")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".rich_media_content")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
            ))
            content_loaded = True
            print("内容区域已加载")
        except:
            print("内容区域加载超时")
        
        # 滚动页面触发懒加载
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # 额外等待动态内容
        time.sleep(5)
        
        page_source = driver.page_source
        print(f"页面源代码长度: {len(page_source)}")
        
        return page_source, title_loaded, content_loaded
        
    finally:
        driver.quit()

def extract_content_advanced(page_source):
    """高级内容提取"""
    soup = BeautifulSoup(page_source, "lxml")
    
    # 提取标题
    title = "未知标题"
    title_selectors = [
        "h1.rich_media_title",
        "h2.rich_media_title", 
        "h1",
        "h2",
        ".rich_media_title",
        "title"
    ]
    
    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem and title_elem.get_text(strip=True):
            title = title_elem.get_text(strip=True)
            print(f"找到标题 (使用选择器 {selector}): {title}")
            break
    
    # 提取正文内容
    content = ""
    content_selectors = [
        "#js_content",
        ".rich_media_content", 
        "article",
        ".article-content",
        "main",
        ".content"
    ]
    
    for selector in content_selectors:
        content_elem = soup.select_one(selector)
        if content_elem:
            print(f"尝试选择器: {selector}")
            
            # 提取文本内容
            paragraphs = []
            
            # 方法1: 提取所有文本元素
            text_elements = content_elem.find_all(["p", "div", "span", "section", "h1", "h2", "h3", "h4", "h5", "h6"])
            for elem in text_elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 10 and text not in paragraphs:
                    paragraphs.append(text)
            
            # 方法2: 提取所有字符串节点
            if not paragraphs:
                for string in content_elem.stripped_strings:
                    if len(string.strip()) > 10:
                        paragraphs.append(string.strip())
            
            # 方法3: 直接获取文本
            if not paragraphs:
                direct_text = content_elem.get_text(strip=True)
                if direct_text and len(direct_text) > 20:
                    paragraphs = [direct_text]
            
            if paragraphs:
                content = "\n\n".join(paragraphs)
                print(f"使用选择器 {selector} 提取到内容，长度: {len(content)}")
                print(f"段落数量: {len(paragraphs)}")
                break
    
    # 如果还是没有内容，尝试从整个页面提取
    if not content:
        print("尝试从整个页面提取内容")
        body = soup.find("body")
        if body:
            all_text = body.get_text(strip=True)
            # 过滤掉导航、菜单等无关内容
            lines = [line.strip() for line in all_text.split('\n') if line.strip() and len(line.strip()) > 10]
            if lines:
                content = "\n".join(lines[:50])  # 只取前50行
                print(f"从body提取内容，行数: {len(lines)}")
    
    return {
        "title": title,
        "content": content,
        "content_length": len(content)
    }

def test_multiple_urls():
    """测试多个URL"""
    test_urls = [
        "https://mp.weixin.qq.com/s/Ub9BKKto3kSCH5tXXE_Ztg",
        # 可以添加更多测试URL
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {url}")
        print(f"{'='*60}")
        
        try:
            page_source, title_loaded, content_loaded = crawl_weixin_article(url)
            result = extract_content_advanced(page_source)
            
            print(f"\n结果:")
            print(f"标题: {result['title']}")
            print(f"内容长度: {result['content_length']}")
            
            if result['content']:
                print(f"\n内容预览:")
                preview = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
                print(preview)
            else:
                print("\n⚠️  未能提取到有效内容")
                print("可能的原因:")
                print("- 需要登录验证")
                print("- 内容完全由JavaScript动态生成")
                print("- 页面结构特殊")
                print("- URL无效或已失效")
            
        except Exception as e:
            print(f"处理URL时发生错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_multiple_urls()