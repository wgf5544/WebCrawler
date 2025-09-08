#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
import time  # 添加time模块
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore
from src.crawler.spider import GiveMeOCSpider
from src.crawler.tencent_spider import TencentDocSpider
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
    parser.add_argument('-f', '--format', type=str, choices=['csv', 'excel', 'json'], default='excel',
                        help='输出文件格式 (默认: excel)')
    parser.add_argument('-d', '--output-dir', type=str, default='data',
                        help='输出目录 (默认: data)')
    parser.add_argument('--tencent-doc', type=str, default=None,
                        help='腾讯文档URL，用于下载只读的腾讯表格文档')
    parser.add_argument('--all-in-one', action='store_true', default=False,
                        help='一键完成所有工作：爬取数据、处理链接并保存为Excel')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='启用无头浏览器模式 (默认: True)')
    parser.add_argument('--no-headless', action='store_true', default=False,
                        help='禁用无头浏览器模式，显示浏览器窗口')
    parser.add_argument('--config', type=str, default='config.toml',
                        help='配置文件路径 (默认: config.toml)')
    
    return parser.parse_args()


def load_config(path: str) -> dict:
    if not path:
        return {}
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'rb') as f:
            cfg = tomllib.load(f)
            logger.info(f"已加载配置文件: {path}")
            return cfg or {}
    except Exception as e:
        logger.warning(f"读取配置文件失败: {e}")
        return {}


def apply_config_to_args(args, cfg: dict):
    if not cfg:
        return args
    section = cfg.get('crawler', cfg)
    for key, attr in [
        ('output_dir', 'output_dir'),
        ('format', 'format'),
        ('all_in_one', 'all_in_one'),
        ('tencent_doc', 'tencent_doc'),
        ('output', 'output'),
    ]:
        if key in section and section[key] is not None:
            setattr(args, attr, section[key])
    return args


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 读取配置文件并应用
    cfg = load_config(args.config)
    args = apply_config_to_args(args, cfg)
    
    try:
        # 处理腾讯文档下载
        if args.tencent_doc:
            output_dir = args.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            # 设置输出文件名
            output_file = args.output or f"tencent_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            if not output_file.endswith('.xlsx'):
                output_file = f"{output_file}.xlsx"
            
            output_path = os.path.join(output_dir, output_file)
            
            success = TencentDocSpider.download_tencent_doc_readonly(
                args.tencent_doc,
                output_path,
            )
            if success:
                logger.info(f"腾讯文档已成功下载到: {output_path}")
            else:
                logger.error("腾讯文档下载失败")
                return 1
            
            return 0
        
        # 创建爬虫实例
        headless_mode = not args.no_headless  # 如果指定了--no-headless则禁用无头模式
        spider = GiveMeOCSpider(headless=headless_mode)
        logger.info(f"浏览器模式: {'无头模式' if headless_mode else '显示窗口模式'}")
        
        # 创建数据处理器，传入列头映射配置
        column_mapping = cfg.get('column_mapping', {})
        processor = DataProcessor(column_mapping=column_mapping)
        
        # 爬取数据
        logger.info(f"开始爬取数据，起始页: {args.start_page}, 结束页: {args.end_page if args.end_page else '最后一页'}")
        
        # 获取总页数
        total_pages = spider.get_total_pages()
        end_page = args.end_page if args.end_page else total_pages
        
        all_data = []
        for page_num in range(args.start_page, min(end_page + 1, total_pages + 1)):
            logger.info(f"正在爬取第{page_num}页...")
            page_data = spider.crawl_page(page_num)
            all_data.extend(page_data)
            
            # 简单的延时避免请求过快
            if page_num < end_page:
                time.sleep(2)
        
        if not all_data:
            logger.warning("未获取到任何数据")
            return 1
        
        # 转换为DataFrame
        import pandas as pd
        df = pd.DataFrame(all_data)
        
        # 清洗数据
        cleaned_df = processor.clean_data(df)
        
        # 保存数据
        output_file = args.output
        
        # 根据指定格式保存
        format_type = args.format.lower()
        if format_type == 'csv':
            # CSV格式直接保存DataFrame
            if not output_file:
                output_file = f"givemeoc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            if not output_file.endswith('.csv'):
                output_file += '.csv'
            filepath = os.path.join(args.output_dir, output_file)
            os.makedirs(args.output_dir, exist_ok=True)
            cleaned_df.to_csv(filepath, index=False, encoding='utf-8-sig')
            saved_path = filepath
        elif format_type == 'excel':
            saved_path = processor.save_to_excel(cleaned_df, filename=output_file)
        elif format_type == 'json':
            saved_path = processor.save_to_json(cleaned_df, filename=output_file)
        else:
            logger.error(f"不支持的输出格式: {args.format}")
            return 1
        
        if saved_path:
            logger.info(f"数据已保存到: {saved_path}")
            logger.info(f"共爬取 {len(cleaned_df)} 条数据")
            logger.info(f"输出格式: {format_type}")
            
            if format_type == 'excel':
                logger.info("表格中的'招聘公告'和相关链接列已设置为超链接")
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())