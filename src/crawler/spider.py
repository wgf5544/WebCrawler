#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
from typing import List, Dict, Any, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GiveMeOCSpider')


class GiveMeOCSpider:
    """爬取 GiveMeOC 网站的校招信息"""
    
    BASE_URL = "https://www.givemeoc.com/"
    
    def __init__(self, headless: bool = True):
        """初始化爬虫
        
        Args:
            headless: 是否使用无头模式运行浏览器
        """
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.session.headers.update(self.headers)
    
    def _init_driver(self):
        """初始化Selenium WebDriver"""
        if self.driver is not None:
            return
        
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(1920, 1080)
    
    def close(self):
        """关闭浏览器和会话"""
        if self.driver is not None:
            self.driver.quit()
            self.driver = None
        self.session.close()
    
    def get_total_pages(self) -> int:
        """获取总页数
        
        Returns:
            总页数
        """
        try:
            self._init_driver()
            self.driver.get(self.BASE_URL)
            
            # 等待页面加载完成
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pagination"))
            )
            
            # 获取分页信息
            pagination = self.driver.find_element(By.CSS_SELECTOR, ".pagination")
            page_items = pagination.find_elements(By.TAG_NAME, "li")
            
            # 最后第二个元素通常是最后一页的页码（最后一个是下一页按钮）
            if len(page_items) >= 2:
                last_page_text = page_items[-2].text.strip()
                if last_page_text.isdigit():
                    return int(last_page_text)
            
            # 如果无法获取，尝试其他方法或返回默认值
            logger.warning("无法获取总页数，返回默认值1")
            return 1
            
        except Exception as e:
            logger.error(f"获取总页数时出错: {e}")
            return 1
    
    def crawl_page(self, page_num: int) -> List[Dict[str, Any]]:
        """爬取指定页码的数据
        
        Args:
            page_num: 页码
            
        Returns:
            该页的数据列表
        """
        try:
            url = f"{self.BASE_URL}?page={page_num}"
            logger.info(f"正在爬取第 {page_num} 页: {url}")
            
            self._init_driver()
            self.driver.get(url)
            
            # 等待表格加载完成
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table"))
            )
            
            # 获取表格内容
            table = self.driver.find_element(By.CSS_SELECTOR, "table.table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            # 解析表头
            headers = []
            header_row = rows[0] if rows else None
            if header_row:
                headers = [th.text.strip() for th in header_row.find_elements(By.TAG_NAME, "th")]
            
            # 解析数据行
            data = []
            for row in rows[1:]:  # 跳过表头行
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    continue
                    
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.text.strip()
                    else:
                        # 如果表头不足，使用索引作为键
                        row_data[f"column_{i}"] = cell.text.strip()
                
                # 获取链接
                links = row.find_elements(By.TAG_NAME, "a")
                if links:
                    row_data["links"] = [{
                        "text": link.text.strip(),
                        "href": link.get_attribute("href")
                    } for link in links if link.get_attribute("href")]
                
                data.append(row_data)
            
            logger.info(f"第 {page_num} 页爬取完成，获取 {len(data)} 条数据")
            return data
            
        except Exception as e:
            logger.error(f"爬取第 {page_num} 页时出错: {e}")
            return []
    
    def crawl_pages(self, start_page: int = 1, end_page: Optional[int] = None) -> List[Dict[str, Any]]:
        """爬取指定范围页码的数据
        
        Args:
            start_page: 起始页码
            end_page: 结束页码，如果为None则爬取到最后一页
            
        Returns:
            所有页的数据列表
        """
        try:
            # 获取总页数
            total_pages = self.get_total_pages()
            logger.info(f"网站总页数: {total_pages}")
            
            # 确定结束页码
            if end_page is None or end_page > total_pages:
                end_page = total_pages
            
            # 验证页码范围
            if start_page < 1:
                start_page = 1
            if start_page > end_page:
                logger.warning(f"起始页码 {start_page} 大于结束页码 {end_page}，无数据返回")
                return []
            
            # 爬取每一页
            all_data = []
            for page_num in range(start_page, end_page + 1):
                page_data = self.crawl_page(page_num)
                all_data.extend(page_data)
                
                # 添加延迟，避免请求过于频繁
                if page_num < end_page:
                    time.sleep(2)
            
            logger.info(f"爬取完成，共获取 {len(all_data)} 条数据")
            return all_data
            
        except Exception as e:
            logger.error(f"爬取页面范围时出错: {e}")
            return []
        finally:
            self.close()