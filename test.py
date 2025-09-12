from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd

def crawl_weixin_article(url):
    # 1. 配置浏览器（无头模式，不弹出窗口）
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # 无头模式
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")  # 模拟真实浏览器UA
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 2. 启动浏览器并访问链接
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        
        # 3. 等待页面关键元素加载完成
        wait = WebDriverWait(driver, 15)
        
        # 等待标题加载
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.rich_media_title, h1, h2, title")))
            print("页面标题已加载")
        except:
            print("标题加载超时，继续处理")
        
        # 等待正文内容加载
        try:
            wait.until(EC.presence_of_element_located((By.ID, "js_content")))
            print("正文内容区域已加载")
        except:
            print("正文内容区域加载超时，尝试其他选择器")
        
        # 尝试触发内容加载的JavaScript事件
        try:
            driver.execute_script("""
                // 触发可能的懒加载
                window.dispatchEvent(new Event('scroll'));
                window.dispatchEvent(new Event('resize'));
                
                // 尝试触发微信文章的内容加载
                if (typeof window.onload === 'function') {
                    window.onload();
                }
            """)
        except Exception as e:
            print(f"JavaScript执行失败: {e}")
        
        # 额外等待动态内容加载
        time.sleep(8)  # 增加等待时间
        
        # 滚动页面确保所有内容加载
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # 等待文本内容出现
        try:
            wait.until(lambda driver: len(driver.find_element(By.ID, "js_content").text.strip()) > 0)
            print("检测到文本内容")
        except:
            print("文本内容可能仍在加载中")
            time.sleep(5)  # 再等待5秒
        
        # 4. 获取页面源代码
        page_source = driver.page_source
        print(f"页面源代码长度: {len(page_source)}")
        
    finally:
        driver.quit()  # 确保浏览器关闭

    return page_source

def extract_content(page_source):
    soup = BeautifulSoup(page_source, "lxml")  # 用lxml解析器（速度快）
    
    # 1. 提取文章标题
    title_element = soup.find("h2", class_="rich_media_title")
    if title_element:
        title = title_element.get_text(strip=True)
        print(f"文章标题：{title}")
    else:
        # 尝试其他可能的标题选择器
        title_alternatives = [
            soup.find("h1"),
            soup.find("h2"),
            soup.find("title")
        ]
        title = "未找到标题"
        for alt in title_alternatives:
            if alt and alt.get_text(strip=True):
                title = alt.get_text(strip=True)
                print(f"文章标题：{title}")
                break
        else:
            print("警告：未找到文章标题")
            title = "未知标题"

    # 2. 提取正文内容（微信文章正文在id="js_content"内）
    content_div = soup.find("div", id="js_content")
    paragraphs = []
    main_content = ""
    
    if content_div:
        print("找到正文内容区域")
        print(f"js_content区域HTML长度: {len(str(content_div))}")
        
        # 调试：检查内容区域的结构
        direct_text = content_div.get_text(strip=True)
        print(f"js_content直接文本长度: {len(direct_text)}")
        
        # 提取所有文本内容，包括段落、div等
        text_elements = content_div.find_all(["p", "div", "span", "section"])
        print(f"找到 {len(text_elements)} 个文本元素")
        
        # 提取图片的alt属性作为内容
        images = content_div.find_all("img")
        print(f"找到 {len(images)} 个图片")
        
        for img in images:
            alt_text = img.get("alt", "")
            if alt_text and alt_text != "图片" and len(alt_text) > 2:
                paragraphs.append(f"[图片: {alt_text}]")
        
        for element in text_elements:
            text = element.get_text(strip=True)
            if text and len(text) > 5:  # 降低过滤阈值
                # 避免重复内容
                if text not in paragraphs:
                    paragraphs.append(text)
        
        # 尝试提取所有可见文本，包括可能被CSS隐藏的内容
        all_text_nodes = []
        for text_node in content_div.stripped_strings:
            if len(text_node.strip()) > 3:
                all_text_nodes.append(text_node.strip())
        
        if all_text_nodes:
            print(f"找到 {len(all_text_nodes)} 个文本节点")
            for text_node in all_text_nodes[:10]:  # 显示前10个
                print(f"文本节点: {text_node[:50]}...")
            paragraphs.extend(all_text_nodes)
        
        # 如果没有找到段落，尝试直接获取整个内容区域的文本
        if not paragraphs:
            main_content = direct_text
            print(f"直接提取内容长度: {len(main_content)}")
            if len(main_content) == 0:
                # 尝试获取innerHTML
                print("尝试分析HTML结构...")
                print(f"内容区域子元素数量: {len(content_div.find_all())}")
                # 获取前500个字符用于调试
                html_sample = str(content_div)[:500]
                print(f"HTML样本: {html_sample}")
        else:
            main_content = "\n\n".join(paragraphs)
            print(f"提取到 {len(paragraphs)} 个段落")
    else:
        print("警告：未找到文章正文内容，尝试其他选择器")
        # 尝试其他可能的内容选择器
        alternative_selectors = [
            "div.rich_media_content",
            "div[id*='content']",
            "article",
            "div.article-content",
            "main"
        ]
        
        for selector in alternative_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                main_content = content_div.get_text(strip=True)
                print(f"使用选择器 {selector} 找到内容，长度: {len(main_content)}")
                break
        
        if not main_content:
            # 最后尝试：获取body中的所有文本
            body = soup.find("body")
            if body:
                main_content = body.get_text(strip=True)
                print(f"从body提取内容，长度: {len(main_content)}")

    # 3. 提取表格数据（如宣讲会安排）
    tables = []
    if content_div:
        for table in content_div.find_all("table"):
            try:
                # 用pandas读取HTML表格，转为DataFrame
                df = pd.read_html(str(table))[0]  # read_html返回列表，取第一个表格
                tables.append(df)
            except Exception as e:
                print(f"警告：解析表格时出错: {e}")
    else:
        print("警告：无法提取表格，未找到内容区域")

    return {
        "title": title,
        "content": main_content,
        "main_content": main_content,  # 保持兼容性
        "tables": tables  # 表格列表（每个元素是DataFrame）
    }

def main():
    # 测试URL（微信文章链接）
    url = "https://mp.weixin.qq.com/s/Ub9BKKto3kSCH5tXXE_Ztg"
    
    try:
        # 1. 爬取页面源代码
        page_source = crawl_weixin_article(url)
        
        # 2. 解析并提取内容
        result = extract_content(page_source)
        
        # 3. 输出结果
        print(f"\n文章标题: {result['title']}")
        
        if result['main_content'] and len(result['main_content'].strip()) > 0:
            print(f"\n文章正文: {result['main_content']}")
        else:
            print("\n警告：未能提取到文章正文内容")
            print("这可能是因为：")
            print("1. 文章内容主要为图片")
            print("2. 内容需要登录才能查看")
            print("3. 内容通过复杂的JavaScript动态加载")
            print("4. 页面结构发生了变化")
        
        if result['tables']:
            print(f"\n找到 {len(result['tables'])} 个表格")
            for i, table in enumerate(result['tables']):
                print(f"表格 {i+1}:")
                print(table.head())
        
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
