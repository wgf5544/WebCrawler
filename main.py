#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
from typing import Optional, List, Dict, Any

from src.crawler.spider import GiveMeOCSpider
from src.utils.data_processor import DataProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='GiveMeOC网站爬虫工具')
    
    parser.add_argument('-s', '--start-page', type=int, default=1,
                        help='起始页码 (默认: 1)')
    parser.add_argument('-e', '--end-page', type=int, default=None,
                        help='结束页码 (默认: 爬取到最后一页)')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='输出文件名 (默认: 使用时间戳)')
    parser.add_argument('-f', '--format', type=str, choices=['csv', 'excel', 'json'], default='csv',
                        help='输出文件格式 (默认: csv)')
    parser.add_argument('-d', '--output-dir', type=str, default='data',
                        help='输出目录 (默认: data)')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='使用无头模式运行浏览器 (默认: True)')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                        help='不使用无头模式运行浏览器')
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    try:
        # 创建爬虫实例
        spider = GiveMeOCSpider(headless=args.headless)
        
        # 创建数据处理器
        processor = DataProcessor(output_dir=args.output_dir)
        
        # 爬取数据
        logger.info(f"开始爬取数据，起始页: {args.start_page}, 结束页: {args.end_page if args.end_page else '最后一页'}")
        raw_data = spider.crawl_pages(start_page=args.start_page, end_page=args.end_page)
        
        if not raw_data:
            logger.warning("未获取到任何数据")
            return
        
        # 清洗数据
        cleaned_data = processor.clean_data(raw_data)
        
        # 保存数据
        output_file = args.output
        if args.format.lower() == 'csv':
            saved_path = processor.save_to_csv(cleaned_data, filename=output_file)
        elif args.format.lower() == 'excel':
            saved_path = processor.save_to_excel(cleaned_data, filename=output_file)
        elif args.format.lower() == 'json':
            saved_path = processor.save_to_json(cleaned_data, filename=output_file)
        else:
            logger.error(f"不支持的输出格式: {args.format}")
            return
        
        if saved_path:
            logger.info(f"数据已保存到: {saved_path}")
            logger.info(f"共爬取 {len(cleaned_data)} 条数据")
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())