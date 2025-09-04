#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DataProcessor')


class DataProcessor:
    """数据处理类，用于清洗和保存爬取的数据"""
    
    def __init__(self, output_dir: str = "data"):
        """初始化数据处理器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def clean_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清洗数据
        
        Args:
            data: 原始数据列表
            
        Returns:
            清洗后的数据列表
        """
        if not data:
            return []
        
        cleaned_data = []
        for item in data:
            # 创建新的数据项，避免修改原始数据
            cleaned_item = {}
            
            # 处理每个字段
            for key, value in item.items():
                # 去除空白字符
                if isinstance(value, str):
                    value = value.strip()
                    # 如果是空字符串，设为None
                    if value == "":
                        value = None
                
                # 处理特殊字段
                if key == "公司名称" and value:
                    # 确保公司名称不包含特殊字符
                    value = value.replace('\n', ' ').replace('\r', ' ').strip()
                
                # 处理日期字段
                if ("日期" in key or "时间" in key) and value:
                    try:
                        # 尝试解析日期格式
                        date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(value, fmt)
                                value = parsed_date.strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.warning(f"日期解析失败: {value}, 错误: {e}")
                
                # 保存处理后的字段
                cleaned_item[key] = value
            
            cleaned_data.append(cleaned_item)
        
        logger.info(f"数据清洗完成，处理 {len(data)} 条数据")
        return cleaned_data
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """将数据保存为CSV文件
        
        Args:
            data: 数据列表
            filename: 文件名，如果为None则使用当前时间戳
            
        Returns:
            保存的文件路径
        """
        if not data:
            logger.warning("没有数据可保存")
            return ""
        
        # 如果没有指定文件名，使用当前时间戳
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"givemeoc_data_{timestamp}.csv"
        
        # 确保文件名有.csv后缀
        if not filename.endswith(".csv"):
            filename += ".csv"
        
        # 构建完整的文件路径
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # 转换为DataFrame并保存
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')  # 使用带BOM的UTF-8编码，兼容Excel
            logger.info(f"数据已保存到CSV文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存CSV文件时出错: {e}")
            return ""
    
    def save_to_excel(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """将数据保存为Excel文件
        
        Args:
            data: 数据列表
            filename: 文件名，如果为None则使用当前时间戳
            
        Returns:
            保存的文件路径
        """
        if not data:
            logger.warning("没有数据可保存")
            return ""
        
        # 如果没有指定文件名，使用当前时间戳
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"givemeoc_data_{timestamp}.xlsx"
        
        # 确保文件名有.xlsx后缀
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"
        
        # 构建完整的文件路径
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # 转换为DataFrame并保存
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine='openpyxl')
            logger.info(f"数据已保存到Excel文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存Excel文件时出错: {e}")
            return ""
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """将数据保存为JSON文件
        
        Args:
            data: 数据列表
            filename: 文件名，如果为None则使用当前时间戳
            
        Returns:
            保存的文件路径
        """
        if not data:
            logger.warning("没有数据可保存")
            return ""
        
        # 如果没有指定文件名，使用当前时间戳
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"givemeoc_data_{timestamp}.json"
        
        # 确保文件名有.json后缀
        if not filename.endswith(".json"):
            filename += ".json"
        
        # 构建完整的文件路径
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # 自定义JSON序列化，处理日期等特殊类型
            class CustomJSONEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.strftime("%Y-%m-%d %H:%M:%S")
                    return super().default(obj)
            
            # 保存为JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
            
            logger.info(f"数据已保存到JSON文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存JSON文件时出错: {e}")
            return ""