import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging
import json
import os

class GiveMeOCSpider:
    def __init__(self, headless=True):
        self.logger = logging.getLogger('GiveMeOCSpider')
        self.driver = None
        self.wait = None
        self.base_url = "https://www.givemeoc.com"
        self.headless = headless  # 保存无头模式设置
        
    def _setup_driver(self, headless=True):
        """设置Chrome驱动，优先使用本地ChromeDriver"""
        try:
            chrome_options = Options()
            
            # 启用无头模式（避免弹出浏览器窗口）
            if headless:
                chrome_options.add_argument('--headless')
                self.logger.info("启用无头浏览器模式")
            
            # 基础配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--no-proxy-server')  # 禁用代理
            chrome_options.add_argument('--disable-proxy-certificate-handler')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 添加用户代理
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
            
            # 设置窗口大小
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 禁用图片加载以提高速度（可选）
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            
            # 尝试使用本地ChromeDriver
            try:
                service = Service()
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.logger.info("使用本地ChromeDriver成功")
            except Exception as e:
                self.logger.warning(f"本地ChromeDriver失败: {str(e)}，尝试使用webdriver-manager")
                # 使用webdriver-manager作为回退
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.logger.info("使用webdriver-manager成功")
            
            # 执行脚本隐藏webdriver属性
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 15)
            self.logger.info("Chrome驱动设置完成")
            
        except Exception as e:
            self.logger.error(f"设置Chrome驱动失败: {str(e)}")
            raise
    
    def _get_table_headers(self):
        """动态获取表格的中文列头 - 增强版"""
        try:
            # 等待表头加载
            time.sleep(2)
            
            # 尝试多种选择器来获取表头，优先级从高到低
            header_selectors = [
                "thead tr th",
                "table thead tr th",
                ".ant-table-thead th",
                ".table-header th",
                "tr th",
                "th[data-field]",
                ".header-cell",
                ".table th"
            ]
            
            headers = []
            
            # 方法1：尝试从实际表头元素提取
            for selector in header_selectors:
                try:
                    header_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if header_elements and len(header_elements) > 0:
                        headers = []
                        for elem in header_elements:
                            text = elem.text.strip() if elem.text else ""
                            if not text:
                                # 尝试从其他属性获取文本
                                text = elem.get_attribute("title") or ""
                                if not text:
                                    text = elem.get_attribute("data-title") or ""
                            
                            # 如果还是没有文本，使用序号作为占位符
                            if not text:
                                text = f"列{len(headers) + 1}"
                            
                            headers.append(text)
                        
                        # 确保有有效表头
                        if len(headers) >= 2:  # 至少2列
                            self.logger.info(f"从选择器 '{selector}' 提取到表头: {headers}")
                            return headers
                        
                except Exception as e:
                    self.logger.debug(f"选择器 '{selector}' 失败: {e}")
                    continue
            
            # 方法2：尝试从表格第一行推断表头
            if not headers:
                try:
                    # 查找第一行数据
                    first_row = self.driver.find_element(By.CSS_SELECTOR, "tbody tr:first-child, table tbody tr:first-child")
                    if first_row:
                        cells = first_row.find_elements(By.TAG_NAME, "td")
                        if cells and len(cells) >= 2:
                            headers = [f"列{i+1}" for i in range(len(cells))]
                            self.logger.info(f"从第一行数据推断表头: {headers}")
                            return headers
                except:
                    pass
            
            # 方法3：使用更精确的默认表头，基于实际网站结构
            if not headers:
                # 基于givemeoc.com实际结构
                headers = ["相关链接", "招聘公告", "公司信息", "发布时间", "工作地点", "投递方式"]
                self.logger.warning("使用基于实际网站的默认表头")
            
            self.logger.info(f"最终使用表头: {headers}")
            return headers
            
        except Exception as e:
            self.logger.error(f"获取表头失败: {str(e)}")
            # 返回更合理的默认表头
            return ["相关链接", "招聘公告", "公司信息", "发布时间", "工作地点", "投递方式"]
    
    def _wait_and_get_rows(self, page_number):
        """等待页面加载并获取数据行"""
        try:
            # 等待页面完全加载
            time.sleep(random.uniform(2, 4))
            
            # 检查是否是错误页面
            if "error" in self.driver.title.lower() or "无法访问" in self.driver.title:
                self.logger.error(f"页面加载错误: {self.driver.title}")
                self.driver.save_screenshot(f"data/debug/error_page_{page_number}.png")
                return []
            
            # 等待表格出现
            table_selectors = [
                "table",
                ".ant-table-content",
                ".table-container",
                "[role='table']"
            ]
            
            table_found = False
            for selector in table_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    table_found = True
                    break
                except:
                    continue
            
            if not table_found:
                self.logger.warning(f"第{page_number}页未找到表格")
                return []
            
            # 获取表头
            headers = self._get_table_headers()
            
            # 获取数据行
            row_selectors = [
                "tbody tr",
                "table tbody tr",
                ".ant-table-tbody tr",
                "tr[data-row-key]"
            ]
            
            rows = []
            for selector in row_selectors:
                try:
                    rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if rows:
                        break
                except:
                    continue
            
            if not rows:
                self.logger.warning(f"第{page_number}页未找到数据行")
                return []
            
            self.logger.info(f"第{page_number}页找到 {len(rows)} 行数据")
            return headers, rows
            
        except Exception as e:
            self.logger.error(f"等待页面加载失败: {str(e)}")
            return None, []
    
    def get_total_pages(self):
        """获取总页数 - 增强版，支持大型网站"""
        try:
            self._setup_driver(self.headless)
            self.driver.get(self.base_url)
            
            # 等待页面完全加载
            time.sleep(8)  # 给更多时间加载
            
            # 保存首页截图用于调试
            self.driver.save_screenshot("data/debug/homepage_debug.png")
            
            # 方法1：直接查找分页组件中的最后一页
            pagination_methods = [
                # 方法1.1：查找分页数字
                {
                    "selector": ".ant-pagination-item:not(.ant-pagination-prev):not(.ant-pagination-next)",
                    "type": "text",
                    "description": "Ant Design分页"
                },
                {
                    "selector": ".pagination-item:not(.disabled)",
                    "type": "text",
                    "description": "自定义分页"
                },
                {
                    "selector": ".page-item:not(.disabled) a",
                    "type": "text",
                    "description": "Bootstrap分页"
                },
                {
                    "selector": ".pager-item",
                    "type": "text",
                    "description": "自定义分页"
                },
                {
                    "selector": ".page-numbers",
                    "type": "text",
                    "description": "WordPress风格分页"
                },
                {
                    "selector": ".pagination-numbers a",
                    "type": "text",
                    "description": "数字分页"
                },
                {
                    "selector": ".page-link:not(.disabled)",
                    "type": "text",
                    "description": "通用分页链接"
                },
                # 方法1.2：查找title属性
                {
                    "selector": "[title*='末页']",
                    "type": "title",
                    "description": "末页按钮"
                },
                {
                    "selector": "[title*='最后一页']",
                    "type": "title",
                    "description": "最后一页"
                },
                {
                    "selector": "[aria-label*='最后一页']",
                    "type": "aria-label",
                    "description": "无障碍标签"
                }
            ]
            
            total_pages = 1
            
            # 方法1：通过DOM元素直接查找
            for method in pagination_methods:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, method["selector"])
                    if elements:
                        page_numbers = []
                        
                        for elem in elements:
                            text = ""
                            if method["type"] == "text":
                                text = elem.text.strip()
                            elif method["type"] == "title":
                                text = elem.get_attribute("title") or ""
                            elif method["type"] == "aria-label":
                                text = elem.get_attribute("aria-label") or ""
                            
                            # 提取数字
                            if text:
                                # 匹配数字
                                import re
                                matches = re.findall(r'\d+', text)
                                if matches:
                                    page_numbers.extend([int(m) for m in matches])
                                elif text.isdigit():
                                    page_numbers.append(int(text))
                        
                        if page_numbers:
                            max_page = max(page_numbers)
                            if max_page > total_pages:
                                total_pages = max_page
                                self.logger.info(f"方法1 - {method['description']}找到最大页数: {total_pages}")
                                break
                                
                except Exception as e:
                    self.logger.debug(f"方法1.{pagination_methods.index(method)}失败: {e}")
                    continue
            
            # 方法2：通过JavaScript深度分析 - 专门查找总页数而非总记录数
            if total_pages <= 10:
                try:
                    js_result = self.driver.execute_script(r"""
                        function findTotalPages() {
                            let totalPages = 1;
                            
                            // 1. 查找明确的分页信息
                            const paginationSelectors = [
                                '.ant-pagination',
                                '.pagination',
                                '.pager',
                                '.page-nav',
                                '.pagination-container',
                                '[class*="pagination"]'
                            ];
                            
                            // 优先查找明确的总页数标识
                            for (let selector of paginationSelectors) {
                                const container = document.querySelector(selector);
                                if (container) {
                                    // 查找"共X页"或"1/X"格式
                                    const allText = container.textContent || '';
                                    
                                    // 匹配"共X页"格式
                                    const totalMatch = allText.match(/共\s*(\d+)\s*页/i);
                                    if (totalMatch) {
                                        const num = parseInt(totalMatch[1]);
                                        if (num > 0 && num <= 1000) { // 限制合理范围
                                            return num;
                                        }
                                    }
                                    
                                    // 匹配"1/X"或"第1页/共X页"格式
                                    const fractionMatch = allText.match(/\d+\s*\/\s*(\d+)/i);
                                    if (fractionMatch) {
                                        const num = parseInt(fractionMatch[1]);
                                        if (num > 0 && num <= 1000) {
                                            return num;
                                        }
                                    }
                                    
                                    // 查找最后一页按钮
                                    const lastButtons = container.querySelectorAll('[title*="末"], [title*="最后"], [aria-label*="最后"]');
                                    for (let btn of lastButtons) {
                                        const title = btn.getAttribute('title') || btn.getAttribute('aria-label') || '';
                                        const pageMatch = title.match(/(\d+)/);
                                        if (pageMatch) {
                                            const num = parseInt(pageMatch[1]);
                                            if (num > 0 && num <= 1000) {
                                                return num;
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // 2. 查找分页输入框的最大值
                            const pageInputs = document.querySelectorAll('input[type="number"], input[placeholder*="页"], input[name*="page"]');
                            for (let input of pageInputs) {
                                const maxVal = input.getAttribute('max');
                                if (maxVal) {
                                    const num = parseInt(maxVal);
                                    if (num > 0 && num <= 1000) {
                                        return num;
                                    }
                                }
                            }
                            
                            // 3. 查找分页文本中的最大页码
                            const pageTexts = document.querySelectorAll('.ant-pagination-item, .page-item, .pagination-item');
                            let maxPageNum = 1;
                            for (let item of pageTexts) {
                                const text = (item.textContent || '').trim();
                                const num = parseInt(text);
                                if (!isNaN(num) && num > maxPageNum && num <= 1000) {
                                    maxPageNum = num;
                                }
                            }
                            
                            if (maxPageNum > 1) {
                                return maxPageNum;
                            }
                            
                            return 1;
                        }
                        
                        return findTotalPages();
                    """)
                    
                    if js_result and 1 <= js_result <= 1000:
                        total_pages = js_result
                        self.logger.info(f"方法2 - 找到实际总页数: {total_pages}")
                        
                except Exception as js_error:
                    self.logger.debug(f"方法2 JavaScript失败: {js_error}")
            
            # 方法3：通过页面信息查找总页数
            if total_pages <= 10:
                try:
                    page_info = self.driver.execute_script(r"""
                        function getPageInfo() {
                            // 查找页面信息文本
                            const infoSelectors = [
                                '.page-info',
                                '.pagination-info',
                                '.total-info',
                                '[class*="total"]',
                                '.dataTables_info'
                            ];
                            
                            for (let selector of infoSelectors) {
                                const element = document.querySelector(selector);
                                if (element) {
                                    const text = (element.textContent || '').trim();
                                    
                                    // 匹配"显示 1-20，共256条"格式
                                    const recordMatch = text.match(/共\s*(\d+)\s*条/i);
                                    if (recordMatch) {
                                        const totalRecords = parseInt(recordMatch[1]);
                                        // 假设每页20条，计算总页数
                                        if (totalRecords > 0) {
                                            return Math.ceil(totalRecords / 20);
                                        }
                                    }
                                    
                                    // 匹配"1-20/256"格式
                                    const fractionMatch = text.match(/\/(\d+)/);
                                    if (fractionMatch) {
                                        const totalRecords = parseInt(fractionMatch[1]);
                                        if (totalRecords > 0) {
                                            return Math.ceil(totalRecords / 20);
                                        }
                                    }
                                }
                            }
                            
                            return 1;
                        }
                        
                        return getPageInfo();
                    """)
                    
                    if page_info and 1 <= page_info <= 1000:
                        total_pages = page_info
                        self.logger.info(f"方法3 - 通过记录数计算总页数: {total_pages}")
                        
                except Exception as info_error:
                    self.logger.debug(f"方法3 页面信息检测失败: {info_error}")
            
            # 方法4：手动验证实际页码
            if total_pages <= 10:
                try:
                    # 先尝试访问第5页看是否存在
                    test_pages = [5, 10, 20, 50, 100, 200]
                    
                    for test_page in test_pages:
                        if test_page > 1000:  # 限制最大测试页数
                            break
                            
                        test_url = f"{self.base_url}?page={test_page}"
                        self.logger.info(f"测试页码 {test_page} 是否存在...")
                        
                        self.driver.get(test_url)
                        time.sleep(3)
                        
                        # 检查该页是否有数据
                        rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr, table tbody tr")
                        if rows and len(rows) > 0:
                            # 查找当前页面的实际最大页数
                            current_max = self.driver.execute_script(r"""
                                function getCurrentMaxPage() {
                                    let maxPage = 1;
                                    
                                    // 查找分页信息
                                    const paginationSelectors = [
                                        '.ant-pagination',
                                        '.pagination',
                                        '.pager'
                                    ];
                                    
                                    for (let selector of paginationSelectors) {
                                        const container = document.querySelector(selector);
                                        if (container) {
                                            // 查找所有数字
                                            const texts = container.textContent || '';
                                            const numbers = texts.match(/\d+/g);
                                            if (numbers) {
                                                numbers.forEach(num => {
                                                    const n = parseInt(num);
                                                    if (n > 0 && n <= 10000) {
                                                        maxPage = Math.max(maxPage, n);
                                                    }
                                                });
                                            }
                                            
                                            // 查找最后一页链接
                                            const lastLinks = container.querySelectorAll('[title*="末"], [title*="最后"]');
                                            lastLinks.forEach(link => {
                                                const title = link.getAttribute('title') || '';
                                                const match = title.match(/(\d+)/);
                                                if (match) {
                                                    const n = parseInt(match[1]);
                                                    if (n > 0 && n <= 10000) {
                                                        maxPage = Math.max(maxPage, n);
                                                    }
                                                }
                                            });
                                        }
                                    }
                                    
                                    return maxPage;
                                }
                                
                                return getCurrentMaxPage();
                            """ % test_page)
                            
                            if current_max and 1 <= current_max <= 10000:
                                total_pages = current_max
                                self.logger.info(f"方法4 - 手动验证确认总页数: {total_pages}")
                                break
                        else:
                            self.logger.info(f"页码 {test_page} 无数据，可能总页数较少")
                            
                except Exception as manual_error:
                    self.logger.debug(f"方法4手动验证失败: {manual_error}")
            
            self.logger.info(f"最终检测到的总页数: {total_pages}")
            return total_pages
            
        except Exception as e:
            self.logger.error(f"获取总页数失败: {str(e)}")
            return 1
        finally:
            if self.driver:
                self.driver.quit()
    

    
    def _navigate_to_page_with_js(self, page_number):
        """使用JavaScript或点击事件导航到指定页面"""
        try:
            # 方法1: 直接使用URL参数导航（最可靠的方法）
            target_url = f"{self.base_url}?paged={page_number}"
            self.logger.info(f"直接导航到第{page_number}页URL: {target_url}")
            self.driver.get(target_url)
            time.sleep(3)  # 等待页面加载
            
            # 验证URL是否正确
            current_url = self.driver.current_url
            if f"paged={page_number}" in current_url or current_url == target_url:
                self.logger.info(f"URL导航成功，当前URL: {current_url}")
                return True
            
            # 方法2: 尝试使用页码输入框（备用方法）
            try:
                # 查找页码输入框
                page_input = self.driver.find_element(By.CSS_SELECTOR, ".crt-page-input, input[type='number']")
                go_button = self.driver.find_element(By.CSS_SELECTOR, ".crt-page-go-btn, button")
                
                if page_input and go_button:
                    self.logger.info(f"找到页码输入框，尝试输入{page_number}")
                    page_input.clear()
                    page_input.send_keys(str(page_number))
                    go_button.click()
                    time.sleep(3)
                    return True
            except Exception as e:
                self.logger.debug(f"页码输入框方法失败: {str(e)}")
            
            # 方法3: 尝试查找并点击分页链接
            try:
                # 查找包含目标页码的链接
                page_link = self.driver.find_element(By.XPATH, f"//a[@href='?paged={page_number}' or contains(@href, 'paged={page_number}')]")
                if page_link:
                    self.logger.info(f"找到第{page_number}页链接，尝试点击")
                    page_link.click()
                    time.sleep(3)
                    return True
            except Exception as e:
                self.logger.debug(f"分页链接方法失败: {str(e)}")
            
            # 方法4: 尝试查找并点击分页按钮（文本匹配）
            try:
                page_buttons = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{page_number}') and contains(@class, 'crt-page-link')]")
                if page_buttons:
                    self.logger.info(f"找到第{page_number}页按钮，尝试点击")
                    page_buttons[0].click()
                    time.sleep(3)
                    return True
            except Exception as e:
                self.logger.debug(f"分页按钮方法失败: {str(e)}")
            
            self.logger.warning(f"所有导航方法都失败，无法导航到第{page_number}页")
            return False
            
        except Exception as e:
            self.logger.error(f"导航到第{page_number}页时发生错误: {str(e)}")
            return False
    
    def _get_page_verification_info(self):
        """获取页面验证信息"""
        try:
            return self.driver.execute_script("""
                return {
                    url: window.location.href,
                    title: document.title,
                    hasTable: document.querySelector('table') !== null,
                    rowCount: document.querySelectorAll('tbody tr').length,
                    currentPage: (function() {
                        // 尝试从分页中获取当前页码
                        const active = document.querySelector('.ant-pagination-item-active, .page-item.active, .pagination-item.active');
                        if (active) {
                            return active.textContent.trim();
                        }
                        return 'unknown';
                    })()
                };
            """)
        except:
            return {}
    
    def crawl_page(self, page_number):
        """爬取指定页的数据 - 直接导航到目标页面"""
        data = []
        try:
            self._setup_driver(self.headless)
            
            # 直接导航到目标页面
            if page_number == 1:
                target_url = self.base_url
                self.logger.info(f"正在访问首页...")
            else:
                target_url = f"{self.base_url}?paged={page_number}"
                self.logger.info(f"正在访问第{page_number}页...")
            
            self.driver.get(target_url)
            
            # 等待页面完全加载
            time.sleep(5)
            
            # 验证页面加载状态
            current_url = self.driver.current_url
            page_title = self.driver.title
            self.logger.info(f"当前URL: {current_url}, 标题: {page_title}")
            
            if "错误" in page_title or "Error" in page_title or "404" in page_title:
                self.logger.error(f"页面加载失败，标题: {page_title}")
                return []
            
            # 等待表格加载
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
            except TimeoutException:
                self.logger.warning(f"第{page_number}页表格加载超时")
                return []
            
            # 验证是否成功导航到目标页面
            if page_number > 1 and f"paged={page_number}" not in current_url:
                self.logger.warning(f"URL导航可能失败，尝试备用方法")
                success = self._navigate_to_page_with_js(page_number)
                if not success:
                    self.logger.error(f"无法导航到第{page_number}页")
                    return []
                
                # 重新等待表格加载
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "table"))
                    )
                except TimeoutException:
                    self.logger.warning(f"第{page_number}页表格加载超时")
                    return []
            
            # 获取表头和数据行
            result = self._wait_and_get_rows(page_number)
            if result is None:
                return []
                
            headers, rows = result
            
            # 验证当前页面数据
            page_info = self.driver.execute_script("""
                return {
                    url: window.location.href,
                    title: document.title,
                    hasTable: document.querySelector('table') !== null,
                    rowCount: document.querySelectorAll('tbody tr').length
                };
            """)
            self.logger.info(f"页面验证信息: {page_info}")
            
            # 提取每行数据
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= len(headers):
                        row_data = {}
                        for i, header in enumerate(headers):
                            if i < len(cells):
                                cell_text = cells[i].text.strip()
                                
                                # 处理链接 - 只处理特定列
                                links = cells[i].find_elements(By.TAG_NAME, "a")
                                if links and header in ["相关链接", "招聘公告"]:
                                    href = links[0].get_attribute("href")
                                    if href and not href.startswith("javascript"):
                                        row_data[header] = href
                                    else:
                                        row_data[header] = cell_text
                                else:
                                    # 普通列直接保存文本
                                    row_data[header] = cell_text
                        
                        if row_data:  # 确保有数据
                            data.append(row_data)
                            
                except Exception as e:
                    self.logger.error(f"解析第{page_number}页第{len(data)+1}行失败: {str(e)}")
                    continue
            
            self.logger.info(f"第{page_number}页爬取完成，共{len(data)}条数据")
            
        except Exception as e:
            self.logger.error(f"爬取第{page_number}页失败: {str(e)}")
            # 保存错误页面
            try:
                if self.driver:
                    self.driver.save_screenshot(f"data/debug/page_{page_number}_error.png")
                    with open(f"data/debug/page_{page_number}_error.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
            except:
                pass
        finally:
            if self.driver:
                self.driver.quit()
        
        return data