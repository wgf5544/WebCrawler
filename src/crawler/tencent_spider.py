#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import logging
import json
import re
import html as _html
import base64
import urllib.parse as urlparse
from typing import List, Dict, Any, Optional

import requests
import pandas as pd
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
logger = logging.getLogger('TencentDocSpider')

class TencentDocSpider:
    """
    用于下载和解析只读腾讯文档（表格）的爬虫。

    此类提供的功能可从腾讯文档 URL 中提取数据，
    特别是针对那些处于只读模式且不提供直接下载选项的表格。
    它采用一系列策略来最大化成功率：

    1.  **Selenium 驱动的 Cookie 导出 + 离线 API 获取**:
        首先，它会启动一个浏览器访问文档 URL，以捕获必要的登录会话 cookie。
        然后，它将这些 cookie 与 `requests` 结合使用，访问前端加载数据时所用的内部 `dop-api` 端点。
        如果存在有效的登录会话，这通常是最可靠的方法。

    2.  **从页面源直接提取数据**:
        如果 API 获取失败，它会分析页面的初始 HTML。腾讯文档有时会将
        初始数据以 JSON 或 Base64 编码格式直接嵌入 HTML 中
        （例如，在 `window.basicClientVars` 中）。此方法会解析 HTML 以查找并解码此数据。

    3.  **实时浏览器交互（UI 绕过）**:
        作为最后的备用方案，它使用完整的浏览器模拟（通过 Selenium）以编程方式与页面交互。
        这包括：
        - 尝试从全局 JavaScript 变量（例如 `window.padInitialData`）中提取数据。
        - 在浏览器内执行对 `dop-api` 端点的 `fetch` 调用，模仿前端的行为以获取作为 JSONP 响应的数据。

    提取的数据通常包含一个或多个表格（工作表），然后保存到单个 Excel 文件中，每个表格位于其自己的工作表中。
    """

    @staticmethod
    def download_tencent_doc_readonly(url: str, output_path: str, headless: bool = True,
                                     chrome_user_data_dir: Optional[str] = None,
                                     chrome_profile_dir: Optional[str] = None) -> bool:
        """
        下载只读腾讯文档的主方法。
        它负责协调不同的下载策略。
        """
        try:
            logger.info(f"开始下载腾讯文档: {url}")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 策略 1: 使用 Selenium 获取 cookie，然后使用离线方法
            # 这通常是最可靠的方法。
            spider = None
            try:
                spider = TencentDocSpider(headless=headless,
                                           chrome_user_data_dir=chrome_user_data_dir,
                                           chrome_profile_dir=chrome_profile_dir)
                if spider._export_selenium_cookies_to_session(url):
                    logger.info("成功从 Selenium 导出登录会话。")
                    spider.session.headers.update({
                        'Referer': url,
                        'Origin': 'https://docs.qq.com'
                    })
                    if spider._offline_bypass_methods(url, output_path, allow_placeholder=False):
                        logger.info("使用 Selenium 会话通过离线 API 方法成功提取数据。")
                        return True
                else:
                    logger.warning("无法导出 Selenium cookie。在没有登录会话的情况下继续。")
            except Exception as e:
                logger.warning(f"基于 Selenium 的会话导出失败: {e}。正在尝试其他方法。")
            finally:
                if spider:
                    spider.close()

            # 策略 2: 完全浏览器模拟作为备用方案
            logger.info("回退到完全浏览器模拟（UI 绕过）。")
            if TencentDocSpider._bypass_ui_restrictions(url, output_path, headless, chrome_user_data_dir, chrome_profile_dir):
                logger.info("通过 Selenium UI 绕过成功提取数据。")
                return True

            logger.error(f"所有下载策略均失败: {url}")
            return False

        except Exception as e:
            logger.error(f"下载腾讯文档时发生意外错误: {e}", exc_info=True)
            return False

    def __init__(self, headless: bool = True, chrome_user_data_dir: Optional[str] = None, chrome_profile_dir: Optional[str] = None):
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        self.session.headers.update(self.headers)
        self.chrome_user_data_dir = os.path.expanduser(chrome_user_data_dir) if chrome_user_data_dir else None
        self.chrome_profile_dir = chrome_profile_dir

    def _init_driver(self):
        if self.driver:
            return
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        if self.chrome_user_data_dir:
            options.add_argument(f"--user-data-dir={self.chrome_user_data_dir}")
            if self.chrome_profile_dir:
                options.add_argument(f"--profile-directory={self.chrome_profile_dir}")
        try:
            # 尝试使用 webdriver-manager 自动管理驱动
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            raise RuntimeError(f"无法初始化 ChromeDriver: {e}")

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
        self.session.close()

    def _export_selenium_cookies_to_session(self, domain_url: str) -> bool:
        try:
            self._init_driver()
            self.driver.get(domain_url)
            # 等待页面加载完成，确保 cookie 已设置
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            time.sleep(5)  # 等待任何动态 cookie 设置
            cookies = self.driver.get_cookies()
            if not cookies:
                logger.warning("在浏览器中未找到该域的 cookie。")
                return False
            self.session.cookies.clear()
            for c in cookies:
                self.session.cookies.set(c['name'], c['value'], domain=c['domain'], path=c['path'])
            logger.info(f"已将会话中的 {len(cookies)} 个 cookie 导出到 requests。")
            return True
        except Exception as e:
            logger.error(f"无法导出 Selenium cookie: {e}", exc_info=True)
            return False

    def _offline_bypass_methods(self, url: str, output_path: str, allow_placeholder: bool = True) -> bool:
        try:
            logger.info("正在尝试离线提取方法...")
            response = self.session.get(url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"无法获取页面，状态码: {response.status_code}")
                return False

            html_content = response.text
            debug_html_path = output_path.replace('.xlsx', '_debug.html')
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"已将调试 HTML 保存到 {debug_html_path}")

            # 策略 A: 从 HTML 中查找并获取 `dop-api/opendoc` URL
            pat_any = r'(?:https?:)?//docs\\.qq\\.com/dop-api/opendoc\\?[^\\s\\\'\\\"<>\\)\\(]+'
            opendoc_urls = re.findall(pat_any, html_content, re.IGNORECASE)
            if opendoc_urls:
                logger.info(f"找到 {len(opendoc_urls)} 个潜在的 dop-api URL。正在尝试获取...")
                for rel_url in opendoc_urls:
                    full_url = _html.unescape(rel_url)
                    if full_url.startswith('//'):
                        full_url = 'https:' + full_url
                    resp = self.session.get(full_url, timeout=30)
                    if resp.status_code == 200 and resp.text:
                        tables = self._parse_jsonp_and_extract_tables(resp.text)
                        if tables and self._save_tables_to_excel(tables, output_path):
                            logger.info("从 dop-api URL 成功提取并保存数据。")
                            return True
            else:
                logger.info("在 HTML 中未找到 dop-api URL。正在尝试下一种方法。")

            # 策略 B: 从 HTML 中查找并解码 `basicClientVars`
            m = re.search(r"basicClientVars\\s*=\\s*JSON\\.parse\\(\\s*decodeURIComponent\\(\\s*escape\\(\\s*atob\\((['\"])(.*?)\\1\\)\\s*\\)\\s*\\)\\s*\\)", html_content, re.IGNORECASE | re.DOTALL)
            if m:
                logger.info("找到 basicClientVars。正在解码...")
                b64_data = _html.unescape(m.group(2))
                try:
                    decoded_json = base64.b64decode(b64_data).decode('utf-8')
                    data_obj = json.loads(decoded_json)
                    tables = self._extract_tables_from_json(data_obj)
                    if tables and self._save_tables_to_excel(tables, output_path):
                        logger.info("从 basicClientVars 成功提取并保存数据。")
                        return True
                except Exception as e:
                    logger.warning(f"无法解码或解析 basicClientVars: {e}")

            if allow_placeholder:
                pd.DataFrame([["只读文档，无法自动提取数据。"]]).to_excel(output_path, index=False, header=False)
                logger.info(f"已创建占位文件: {output_path}")
                return True

            return False
        except Exception as e:
            logger.error(f"离线绕过方法失败: {e}", exc_info=True)
            return False

    @staticmethod
    def _bypass_ui_restrictions(url: str, output_path: str, headless: bool,
                               chrome_user_data_dir: Optional[str],
                               chrome_profile_dir: Optional[str]) -> bool:
        driver = None
        try:
            options = Options()
            if headless:
                options.add_argument('--headless=new')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-blink-features=AutomationControlled')
            if chrome_user_data_dir:
                options.add_argument(f"--user-data-dir={os.path.expanduser(chrome_user_data_dir)}")
                if chrome_profile_dir:
                    options.add_argument(f"--profile-directory={chrome_profile_dir}")

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

            # 策略 A: 从全局 JS 变量中提取
            js_collect = '''
                return (function(){
                  function safe(obj){ try{ return JSON.stringify(obj); }catch(e){ return null; } }
                  var w = window; var res = [];
                  try{ if (w.padInitialData) res.push({k:'padInitialData', v: safe(w.padInitialData)});}catch(e){}
                  try{ if (w.g_InitialData) res.push({k:'g_InitialData', v: safe(w.g_InitialData)});}catch(e){}
                  try{ if (w.__INITIAL_STATE__) res.push({k:'__INITIAL_STATE__', v: safe(w.__INITIAL_STATE__)});}catch(e){}
                  try{ if (w.__NUXT__ && w.__NUXT__.state) res.push({k:'__NUXT__.state', v: safe(w.__NUXT__.state)});}catch(e){}
                  return res;
                })();
            '''
            candidates = driver.execute_script(js_collect)
            if isinstance(candidates, list):
                for item in candidates:
                    if item and item.get('v'):
                        try:
                            obj = json.loads(item['v'])
                            tables = TencentDocSpider._extract_tables_from_json(obj)
                            if tables and TencentDocSpider._save_tables_to_excel(tables, output_path):
                                logger.info(f"从全局变量成功提取数据: {item['k']}")
                                return True
                        except Exception:
                            continue

            # 策略 B: 浏览器内 fetch 回退
            logger.info("全局变量未产生数据。正在尝试浏览器内 fetch。")
            js_fetch = r'''
                const cb = arguments[0];
                (async () => {
                  try {
                    const html = document.documentElement.innerHTML;
                    const m = html.match(/(?:https?:)?\\/\\/docs\\.qq\\.com\\/dop-api\\/opendoc\\?[^\\s\'\"<>\\)\\(]+/i);
                    if (!m) { cb({ok:false, err:'no_url'}); return; }
                    let url = m[0];
                    if (url.startsWith('//')) url = window.location.protocol + url;
                    const resp = await fetch(url, { credentials: 'include' });
                    const txt = await resp.text();
                    cb({ok:true, url, txt});
                  } catch (e) {
                    cb({ok:false, err: String(e)});
                  }
                })();
            '''
            res = driver.execute_async_script(js_fetch)
            if isinstance(res, dict) and res.get('ok') and res.get('txt'):
                tables = TencentDocSpider._parse_jsonp_and_extract_tables(res['txt'])
                if tables and TencentDocSpider._save_tables_to_excel(tables, output_path):
                    logger.info("使用浏览器内 fetch 成功提取数据。")
                    return True

            return False
        except Exception as e:
            logger.error(f"UI 绕过失败: {e}", exc_info=True)
            return False
        finally:
            if driver:
                driver.quit()

    @staticmethod
    def _parse_jsonp_and_extract_tables(text: str) -> List[Dict[str, Any]]:
        """解析 JSONP 响应文本并提取表格。"""
        m = re.search(r'clientVarsCallback\\s*(?:&&\\s*clientVarsCallback)?\\s*\\((.*)\\)\\s*;?\\s*$', text, re.DOTALL)
        if m:
            payload = m.group(1)
            try:
                obj = json.loads(payload)
                return TencentDocSpider._extract_tables_from_json(obj)
            except Exception as e:
                logger.debug(f"无法解析 JSONP 载荷: {e}")
        return []

    @staticmethod
    def _extract_tables_from_json(obj: Any) -> List[Dict[str, Any]]:
        """从复杂的前端 JSON 对象中尽可能提取表格数据。"""
        tables: List[Dict[str, Any]] = []
        
        def add_table(name: Optional[str], data: List[List[Any]]):
            if not data or not any(isinstance(r, (list, tuple)) and r for r in data):
                return
            tables.append({
                'name': name or f'Sheet{len(tables) + 1}',
                'data': [[str(v) if v is not None else "" for v in (r or [])] for r in data]
            })

        def from_celldata(sheet: Dict[str, Any]) -> Optional[List[List[str]]]:
            cells = sheet.get('celldata') or sheet.get('cellData')
            if not isinstance(cells, list) or not cells:
                return None
            
            max_r, max_c = 0, 0
            for item in cells:
                try:
                    r, c = int(item.get('r')), int(item.get('c'))
                    max_r, max_c = max(max_r, r), max(max_c, c)
                except (ValueError, TypeError):
                    continue
            
            grid = [["" for _ in range(max_c + 1)] for _ in range(max_r + 1)]
            for item in cells:
                try:
                    r, c = int(item.get('r')), int(item.get('c'))
                    v = item.get('v', {})
                    text = v.get('m', '') if isinstance(v, dict) else v
                    grid[r][c] = str(text) if text is not None else ""
                except (ValueError, TypeError):
                    continue
            return grid

        def from_rows(sheet: Dict[str, Any]) -> Optional[List[List[str]]]:
            rows = sheet.get('rows') or sheet.get('data')
            if not isinstance(rows, list) or not rows:
                return None
            
            data = []
            for r in rows:
                if isinstance(r, dict):
                    cells = r.get('cells', [])
                    row_data = []
                    for cell in cells:
                        val = ''
                        if isinstance(cell, dict):
                            v = cell.get('v', cell.get('value', ''))
                            val = v.get('text', v) if isinstance(v, dict) else v
                        else:
                            val = cell
                        row_data.append(str(val) if val is not None else "")
                    data.append(row_data)
                elif isinstance(r, (list, tuple)):
                    data.append([str(c) if c is not None else "" for c in r])
            return data if data else None

        def scan(node: Any):
            if isinstance(node, dict):
                sheets = node.get('sheets') or node.get('sheetList')
                if isinstance(sheets, list):
                    for s in sheets:
                        if isinstance(s, dict):
                            name = s.get('name') or s.get('title')
                            table_data = from_rows(s) or from_celldata(s)
                            if table_data:
                                add_table(name, table_data)
                            else:
                                scan(s)
                else:
                    table_data = from_rows(node) or from_celldata(node)
                    if table_data:
                        add_table(node.get('name'), table_data)
                    else:
                        for value in node.values():
                            scan(value)
            elif isinstance(node, list):
                for item in node:
                    scan(item)
        
        scan(obj)
        return tables

    @staticmethod
    def _save_tables_to_excel(tables: List[Dict[str, Any]], output_path: str) -> bool:
        if not tables:
            return False
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for i, table_data in enumerate(tables):
                    df = pd.DataFrame(table_data.get('data', []))
                    sheet_name = table_data.get('name') or f'Sheet{i+1}'
                    # 清理工作表名称，移除无效字符并截断到31个字符
                    safe_name = re.sub(r'[\\/*?:\[\]]', '_', sheet_name)[:31]
                    df.to_excel(writer, sheet_name=safe_name, index=False, header=False)
            logger.info(f"成功将 {len(tables)} 个表格保存到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"无法保存到 Excel: {e}")
            return False