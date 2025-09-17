#!/usr/bin/env python3
"""
飞书多维表格数据同步工具 - 多表格版本
支持同时向多个飞书多维表格同步数据
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import requests
from tqdm import tqdm


class FeishuMultiTableSync:
    """飞书多表格数据同步器"""
    
    def __init__(self, config_path: str = "feishu_multi_table_config.json"):
        """初始化同步器"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.access_token = None
        self.token_expires_at = 0
        
        self.logger.info("🚀 飞书多表格数据同步器初始化完成")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("FeishuMultiTableSync")
        logger.setLevel(getattr(logging, self.config['logging']['level']))
        
        # 清除现有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 文件处理器
        log_file = Path(self.config['logging']['file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        if self.config['logging']['console']:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def get_access_token(self) -> str:
        """获取访问令牌"""
        # 检查令牌是否仍然有效
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        self.logger.info("🔑 获取飞书访问令牌...")
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.config['feishu']['app_id'],
            "app_secret": self.config['feishu']['app_secret']
        }
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        if result.get("code") == 0:
            self.access_token = result["tenant_access_token"]
            # 设置令牌过期时间（提前5分钟刷新）
            self.token_expires_at = time.time() + result.get("expire", 7200) - 300
            self.logger.info("✅ 访问令牌获取成功")
            return self.access_token
        else:
            raise Exception(f"获取访问令牌失败: {result}")
    
    def load_data_source(self) -> pd.DataFrame:
        """加载数据源"""
        self.logger.info("📂 加载数据源...")
        
        data_config = self.config['data_source']
        
        if data_config['type'] == 'excel':
            file_path = data_config['file_path']
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Excel文件不存在: {file_path}")
            
            # 读取Excel文件
            df = pd.read_excel(
                file_path,
                sheet_name=data_config['sheet_name'],
                engine='openpyxl'
            )
            
            self.logger.info(f"✅ 成功加载 {len(df)} 行数据")
            return df
        else:
            raise ValueError(f"不支持的数据源类型: {data_config['type']}")
    
    def validate_field_mapping(self, df: pd.DataFrame, field_mapping: Dict[str, str]) -> None:
        """验证字段映射"""
        self.logger.info("🔍 验证字段映射配置...")
        
        missing_fields = []
        for source_field in field_mapping.keys():
            if source_field not in df.columns:
                missing_fields.append(source_field)
                self.logger.warning(f"⚠️ 字段验证失败，跳过验证: '{source_field}'")
        
        if missing_fields:
            self.logger.warning(f"⚠️ 以下字段在数据源中不存在: {missing_fields}")
        
        self.logger.info("✅ 字段映射配置验证完成")
    
    def clean_field_value(self, field_name: str, value: str) -> str:
        """清洗字段值"""
        if 'field_cleaning' not in self.config:
            return value
        
        field_cleaning_rules = self.config['field_cleaning']
        
        # 检查是否有该字段的清洗规则
        if field_name in field_cleaning_rules:
            cleaning_map = field_cleaning_rules[field_name]
            # 如果找到匹配的规则，返回清洗后的值
            if value in cleaning_map:
                cleaned_value = cleaning_map[value]
                self.logger.debug(f"字段值清洗: {field_name} '{value}' -> '{cleaned_value}'")
                return cleaned_value
        
        return value
    
    def prepare_records(self, df: pd.DataFrame, field_mapping: Dict[str, str]) -> List[Dict]:
        """准备记录数据"""
        self.logger.info("📝 准备记录数据...")
        
        records = []
        invalid_records = 0
        
        for index, row in df.iterrows():
            try:
                fields = {}
                
                for source_field, target_field in field_mapping.items():
                    if source_field not in df.columns:
                        continue
                    
                    value = row[source_field]
                    
                    # 处理空值和NaN - 更严格的检查
                    if pd.isna(value) or value == '' or str(value).lower() == 'nan' or value is None:
                        continue
                    
                    # 转换为字符串并清理
                    value_str = str(value).strip()
                    
                    # 再次检查转换后的字符串是否为空或NaN
                    if not value_str or value_str.lower() == 'nan':
                        continue
                    
                    # 应用字段值清洗规则
                    value_str = self.clean_field_value(source_field, value_str)
                        
                    # 根据字段类型处理数据
                    if target_field in ['地点', '所属行业', '招聘类型', '招聘对象', '岗位']:
                        # 多选字段
                        if ',' in value_str:
                            # 对每个分割后的值也应用清洗规则
                            cleaned_items = []
                            for item in value_str.split(','):
                                item = item.strip()
                                if item:
                                    cleaned_item = self.clean_field_value(source_field, item)
                                    cleaned_items.append(cleaned_item)
                            fields[target_field] = cleaned_items
                        else:
                            fields[target_field] = [value_str] if value_str else []
                    elif target_field in ['公司类型', '是否笔试']:
                        # 单选字段，直接使用字符串
                        fields[target_field] = value_str
                    elif target_field == '更新时间':
                        # 日期字段，转换为Unix时间戳
                        try:
                            if value_str:
                                # 尝试解析日期字符串
                                dt = datetime.strptime(value_str, '%Y-%m-%d')
                                # 转换为Unix时间戳（毫秒）
                                fields[target_field] = int(dt.timestamp() * 1000)
                            else:
                                fields[target_field] = None
                        except ValueError:
                            self.logger.warning(f"第{index+1}行: 无法解析日期格式: {value_str}")
                            fields[target_field] = None
                    else:
                        # 文本、URL等其他字段
                        # 验证URL字段格式
                        if target_field in ['投递链接', '公告链接']:
                            if value_str:
                                # 如果URL不包含协议，自动添加https://
                                if not (value_str.startswith('http://') or value_str.startswith('https://')):
                                    # 检查是否是有效的域名格式
                                    if '.' in value_str and not value_str.startswith('www.'):
                                        value_str = 'https://' + value_str
                                    elif value_str.startswith('www.'):
                                        value_str = 'https://' + value_str
                                    else:
                                        self.logger.warning(f"第{index+1}行: URL格式不正确，跳过: {value_str}")
                                        continue
                                
                                # 飞书URL字段需要特殊格式：对象形式
                                fields[target_field] = {
                                    "link": value_str,
                                    "text": value_str  # 显示文本，可以自定义
                                }
                            else:
                                continue  # 空URL跳过
                        else:
                            # 普通文本字段
                            fields[target_field] = value_str
                
                # 只有当有有效字段时才添加记录
                if fields:
                    records.append({"fields": fields})
                else:
                    invalid_records += 1
                    self.logger.warning(f"第{index+1}行: 没有有效数据，跳过")
                    
            except Exception as e:
                invalid_records += 1
                self.logger.error(f"第{index+1}行: 处理记录时出错: {str(e)}")
                continue
        
        self.logger.info(f"✅ 记录准备完成: {len(records)} 条有效记录")
        if invalid_records > 0:
            self.logger.warning(f"⚠️ 跳过无效记录: {invalid_records} 条")
        
        return records
    
    def batch_insert_records(self, records: List[Dict], base_id: str, table_id: str, table_name: str) -> List[str]:
        """批量插入记录到指定表格"""
        if not records:
            self.logger.warning(f"⚠️ [{table_name}] 没有记录需要插入")
            return []
        
        token = self.get_access_token()
        batch_size = self.config['sync_options']['batch_size']
        max_retries = self.config['sync_options']['max_retries']
        retry_delay = self.config['sync_options']['retry_delay']
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{base_id}/tables/{table_id}/records/batch_create"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        all_record_ids = []
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        self.logger.info(f"🚀 [{table_name}] 开始批量插入，总计 {len(records)} 条记录，分 {total_batches} 批处理")
        
        with tqdm(total=len(records), desc=f"{table_name}同步进度", unit="条") as pbar:
            for i in range(0, len(records), batch_size):
                batch_records = records[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                data = {"records": batch_records}
                
                # 重试机制
                for attempt in range(max_retries):
                    try:
                        response = requests.post(url, headers=headers, json=data)
                        result = response.json()
                        
                        if result.get("code") == 0:
                            batch_ids = [record["record_id"] for record in result["data"]["records"]]
                            all_record_ids.extend(batch_ids)
                            
                            self.logger.info(f"✅ [{table_name}] 批次 {batch_num}/{total_batches} 成功插入 {len(batch_ids)} 条记录")
                            pbar.update(len(batch_records))
                            break
                        else:
                            error_code = result.get("code", "未知")
                            error_msg = result.get("msg", "未知错误")
                            error_detail = f"[{table_name}] 批次 {batch_num} 插入失败 - 错误码: {error_code}, 错误信息: {error_msg}"
                            
                            # 记录详细的错误信息
                            self.logger.error(f"❌ [{table_name}] API响应详情: {json.dumps(result, indent=2, ensure_ascii=False)}")
                            
                            if attempt < max_retries - 1:
                                self.logger.warning(f"⚠️ {error_detail}，{retry_delay}秒后重试...")
                                time.sleep(retry_delay)
                            else:
                                self.logger.error(f"❌ {error_detail}，已达最大重试次数")
                                
                                # 如果是字段验证错误，记录具体的记录内容
                                if "Invalid request parameter" in error_msg or "字段" in error_msg:
                                    self.logger.error(f"❌ [{table_name}] 问题记录内容: {json.dumps(batch_records, indent=2, ensure_ascii=False)}")
                                
                                if not self.config['sync_options'].get('continue_on_error', False):
                                    raise Exception(error_detail)
                                else:
                                    self.logger.warning(f"⚠️ [{table_name}] 跳过失败批次，继续处理下一批次")
                                    break
                                
                    except Exception as e:
                        if attempt < max_retries - 1:
                            self.logger.warning(f"⚠️ [{table_name}] 批次 {batch_num} 请求异常: {e}，{retry_delay}秒后重试...")
                            time.sleep(retry_delay)
                        else:
                            self.logger.error(f"❌ [{table_name}] 批次 {batch_num} 请求失败: {e}")
                            if not self.config['sync_options'].get('continue_on_error', False):
                                raise
                            else:
                                self.logger.warning(f"⚠️ [{table_name}] 跳过失败批次，继续处理下一批次")
                                break
                
                # 批次间延迟，避免API限流
                if i + batch_size < len(records):
                    time.sleep(0.5)
        
        self.logger.info(f"🎉 [{table_name}] 批量插入完成！总计成功插入 {len(all_record_ids)} 条记录")
        return all_record_ids
    
    def sync_data(self) -> Dict[str, Any]:
        """执行多表格数据同步"""
        start_time = time.time()
        
        try:
            self.logger.info("🎯 开始多表格数据同步任务...")
            
            # 获取访问令牌
            self.get_access_token()
            
            # 加载数据源
            df = self.load_data_source()
            
            # 同步结果统计
            sync_results = {
                "total_tables": len(self.config['tables']),
                "successful_tables": 0,
                "failed_tables": 0,
                "table_results": {}
            }
            
            # 遍历所有表格配置
            for table_config in self.config['tables']:
                table_name = table_config['name']
                base_id = table_config['base_id']
                table_id = table_config['table_id']
                field_mapping = table_config['field_mapping']
                
                try:
                    self.logger.info(f"📊 开始同步表格: {table_name}")
                    
                    # 验证字段映射
                    self.validate_field_mapping(df, field_mapping)
                    
                    # 准备记录
                    records = self.prepare_records(df, field_mapping)
                    
                    # 批量插入
                    record_ids = self.batch_insert_records(records, base_id, table_id, table_name)
                    
                    # 记录结果
                    sync_results["table_results"][table_name] = {
                        "success": True,
                        "records_inserted": len(record_ids),
                        "base_id": base_id,
                        "table_id": table_id
                    }
                    sync_results["successful_tables"] += 1
                    
                    self.logger.info(f"✅ [{table_name}] 同步完成，插入 {len(record_ids)} 条记录")
                    
                except Exception as e:
                    self.logger.error(f"❌ [{table_name}] 同步失败: {str(e)}")
                    sync_results["table_results"][table_name] = {
                        "success": False,
                        "error": str(e),
                        "base_id": base_id,
                        "table_id": table_id
                    }
                    sync_results["failed_tables"] += 1
                    
                    if not self.config['sync_options'].get('continue_on_error', True):
                        raise
            
            # 计算总耗时
            end_time = time.time()
            duration = end_time - start_time
            
            # 汇总结果
            total_inserted = sum(
                result.get("records_inserted", 0) 
                for result in sync_results["table_results"].values() 
                if result.get("success", False)
            )
            
            sync_results.update({
                "duration": duration,
                "total_records_inserted": total_inserted
            })
            
            self.logger.info("🎉 多表格数据同步任务完成！")
            self.logger.info(f"📊 成功表格数: {sync_results['successful_tables']}/{sync_results['total_tables']}")
            self.logger.info(f"✅ 总插入记录数: {total_inserted}")
            self.logger.info(f"⏱️ 总耗时: {duration:.2f} 秒")
            
            return sync_results
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            self.logger.error(f"❌ 多表格数据同步任务失败: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "duration": duration
            }


def main():
    """主函数"""
    try:
        # 创建同步器实例
        sync = FeishuMultiTableSync()
        
        # 执行同步
        result = sync.sync_data()
        
        # 输出结果
        if result.get("success", True):  # 默认为True，除非明确设置为False
            print(f"\n🎉 多表格同步成功完成！")
            print(f"📊 成功表格数: {result.get('successful_tables', 0)}/{result.get('total_tables', 0)}")
            print(f"📝 总插入记录数: {result.get('total_records_inserted', 0)}")
            print(f"⏱️ 总耗时: {result.get('duration', 0):.2f} 秒")
            
            # 显示各表格详细结果
            for table_name, table_result in result.get("table_results", {}).items():
                if table_result.get("success"):
                    print(f"  ✅ {table_name}: {table_result.get('records_inserted', 0)} 条记录")
                else:
                    print(f"  ❌ {table_name}: {table_result.get('error', '未知错误')}")
        else:
            print(f"\n❌ 多表格同步失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"\n❌ 程序执行失败: {str(e)}")


if __name__ == "__main__":
    main()