#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
示例脚本，展示如何使用爬虫API
"""

import logging
from src.crawler.spider import GiveMeOCSpider
from src.utils.data_processor import DataProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('example')


def example_usage():
    """示例：爬取前3页数据并保存为不同格式"""
    try:
        # 创建爬虫实例
        spider = GiveMeOCSpider(headless=True)
        
        # 爬取数据
        logger.info("开始爬取数据...")
        data = spider.crawl_pages(start_page=1, end_page=3)
        
        if not data:
            logger.warning("未获取到任何数据")
            return
        
        logger.info(f"爬取完成，获取到 {len(data)} 条数据")
        
        # 创建数据处理器
        processor = DataProcessor()
        
        # 清洗数据
        cleaned_data = processor.clean_data(data)
        
        # 保存为不同格式
        processor.save_to_csv(cleaned_data, "example_data")
        processor.save_to_excel(cleaned_data, "example_data")
        processor.save_to_json(cleaned_data, "example_data")
        
        logger.info("示例执行完成，数据已保存到data目录")
        
    except Exception as e:
        logger.error(f"示例执行出错: {e}")
    finally:
        # 确保关闭浏览器
        if 'spider' in locals():
            spider.close()


if __name__ == "__main__":
    example_usage()