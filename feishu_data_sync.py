#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书多维表格数据同步工具
支持从Excel/CSV文件读取数据并同步到飞书多维表格
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


def _load_env_config(config: Dict) -> Dict:
    """从环境变量覆盖飞书凭证（.env 文件优先于 JSON 配置）"""
    env_app_id = os.environ.get("FEISHU_APP_ID")
    env_app_secret = os.environ.get("FEISHU_APP_SECRET")
    if env_app_id:
        config["feishu"]["app_id"] = env_app_id
    if env_app_secret:
        config["feishu"]["app_secret"] = env_app_secret
    return config


class FeishuDataSync:
    """飞书数据同步类"""
    
    def __init__(self, config_path: str = "feishu_sync_config.json"):
        """
        初始化飞书数据同步工具
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.access_token = None
        self.logger = self._setup_logging()
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件，环境变量中的凭证优先于 JSON 配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        return _load_env_config(config)
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志记录"""
        logger = logging.getLogger('FeishuDataSync')
        logger.setLevel(getattr(logging, self.config['logging']['level']))
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        if self.config['logging']['console']:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 文件处理器
        if self.config['logging']['file']:
            log_file = Path(self.config['logging']['file'])
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def get_access_token(self) -> str:
        """获取飞书访问令牌"""
        if self.access_token:
            return self.access_token
            
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.config['feishu']['app_id'],
            "app_secret": self.config['feishu']['app_secret']
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                self.logger.info("✅ 成功获取访问令牌")
                return self.access_token
            else:
                raise Exception(f"获取令牌失败: {result}")
                
        except Exception as e:
            self.logger.error(f"❌ 获取访问令牌失败: {e}")
            raise
    
    def load_data_source(self) -> pd.DataFrame:
        """加载数据源"""
        data_config = self.config['data_source']
        file_path = data_config['file_path']
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"数据文件未找到: {file_path}")
        
        try:
            if data_config['type'] == 'excel':
                df = pd.read_excel(
                    file_path,
                    sheet_name=data_config.get('sheet_name')
                )
            elif data_config['type'] == 'csv':
                df = pd.read_csv(
                    file_path,
                    encoding=data_config.get('encoding', 'utf-8')
                )
            else:
                raise ValueError(f"不支持的数据源类型: {data_config['type']}")
            
            self.logger.info(f"✅ 成功加载数据源: {file_path}")
            self.logger.info(f"📊 数据形状: {df.shape}")
            self.logger.info(f"📋 列名: {df.columns.tolist()}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 加载数据源失败: {e}")
            raise
    
    def validate_field_mapping(self, df: pd.DataFrame) -> None:
        """验证字段映射配置"""
        self.logger.info("🔍 验证字段映射配置...")
        
        # 检查Excel中的源字段是否存在
        missing_source_fields = []
        for source_field in self.config['field_mapping'].keys():
            if source_field not in df.columns:
                missing_source_fields.append(source_field)
        
        if missing_source_fields:
            error_msg = f"Excel文件中缺少以下字段: {missing_source_fields}"
            self.logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # 获取飞书表格字段信息进行验证
        try:
            token = self.get_access_token()
            fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.config['feishu']['base_id']}/tables/{self.config['feishu']['table_id']}/fields"
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(fields_url, headers=headers)
            
            if response.status_code == 200:
                feishu_fields = {field['field_name'] for field in response.json()['data']['items']}
                missing_target_fields = []
                
                for target_field in self.config['field_mapping'].values():
                    if target_field not in feishu_fields:
                        missing_target_fields.append(target_field)
                
                if missing_target_fields:
                    error_msg = f"飞书表格中缺少以下字段: {missing_target_fields}"
                    self.logger.error(f"❌ {error_msg}")
                    raise ValueError(error_msg)
                    
                self.logger.info("✅ 字段映射验证通过")
            else:
                self.logger.warning("⚠️ 无法验证飞书表格字段，跳过验证")
                
        except Exception as e:
            self.logger.warning(f"⚠️ 字段验证失败，跳过验证: {str(e)}")
            
        self.logger.info("✅ 字段映射配置验证完成")
    
    def prepare_records(self, df: pd.DataFrame) -> List[Dict]:
        """准备要插入的记录数据"""
        self.logger.info("📝 准备记录数据...")
        
        records = []
        invalid_records = 0
        
        for index, row in df.iterrows():
            try:
                fields = {}
                
                # 遍历字段映射配置
                for source_field, target_field in self.config['field_mapping'].items():
                    if source_field in row and pd.notna(row[source_field]):
                        value = row[source_field]
                        
                        # 数据类型验证和转换 - 更严格的NaN检查
                        if pd.isna(value) or value == '' or str(value).lower() == 'nan' or value is None:
                            continue
                        
                        # 转换为字符串并清理
                        value_str = str(value).strip()
                        
                        # 再次检查转换后的字符串是否为空或NaN
                        if not value_str or value_str.lower() == 'nan':
                            continue
                            
                        # 根据字段类型处理数据
                        if target_field in ['地点', '所属行业', '招聘类型', '招聘对象', '岗位']:
                            # 多选字段
                            if ',' in value_str:
                                fields[target_field] = [item.strip() for item in value_str.split(',') if item.strip()]
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
            self.logger.warning(f"⚠️ 跳过 {invalid_records} 条无效记录")
            
        return records
    
    def batch_insert_records(self, records: List[Dict]) -> List[str]:
        """批量插入记录到飞书"""
        if not records:
            self.logger.warning("⚠️  没有记录需要插入")
            return []
        
        token = self.get_access_token()
        batch_size = self.config['sync_options']['batch_size']
        max_retries = self.config['sync_options']['max_retries']
        retry_delay = self.config['sync_options']['retry_delay']
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.config['feishu']['base_id']}/tables/{self.config['feishu']['table_id']}/records/batch_create"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        all_record_ids = []
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        self.logger.info(f"🚀 开始批量插入，总计 {len(records)} 条记录，分 {total_batches} 批处理")
        
        with tqdm(total=len(records), desc="同步进度", unit="条") as pbar:
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
                            
                            self.logger.info(f"✅ 批次 {batch_num}/{total_batches} 成功插入 {len(batch_ids)} 条记录")
                            pbar.update(len(batch_records))
                            break
                        else:
                            error_code = result.get("code", "未知")
                            error_msg = result.get("msg", "未知错误")
                            error_detail = f"批次 {batch_num} 插入失败 - 错误码: {error_code}, 错误信息: {error_msg}"
                            
                            # 记录详细的错误信息
                            self.logger.error(f"❌ API响应详情: {json.dumps(result, indent=2, ensure_ascii=False)}")
                            
                            if attempt < max_retries - 1:
                                self.logger.warning(f"⚠️  {error_detail}，{retry_delay}秒后重试...")
                                time.sleep(retry_delay)
                            else:
                                self.logger.error(f"❌ {error_detail}，已达最大重试次数")
                                
                                # 如果是字段验证错误，记录具体的记录内容
                                if "Invalid request parameter" in error_msg or "字段" in error_msg:
                                    self.logger.error(f"❌ 问题记录内容: {json.dumps(batch_records, indent=2, ensure_ascii=False)}")
                                
                                raise Exception(error_detail)
                                
                    except Exception as e:
                        if attempt < max_retries - 1:
                            self.logger.warning(f"⚠️  批次 {batch_num} 请求异常: {e}，{retry_delay}秒后重试...")
                            time.sleep(retry_delay)
                        else:
                            self.logger.error(f"❌ 批次 {batch_num} 请求失败: {e}")
                            raise
                
                # 批次间延迟，避免API限流
                if i + batch_size < len(records):
                    time.sleep(0.5)
        
        self.logger.info(f"🎉 批量插入完成！总计成功插入 {len(all_record_ids)} 条记录")
        return all_record_ids
    
    def sync_data(self) -> Dict[str, Any]:
        """执行数据同步"""
        start_time = datetime.now()
        self.logger.info("🚀 开始数据同步任务")
        
        try:
            # 1. 加载数据源
            df = self.load_data_source()
            
            # 2. 验证字段映射
            self.validate_field_mapping(df)
            
            # 3. 准备记录
            records = self.prepare_records(df)
            
            # 4. 批量插入
            record_ids = self.batch_insert_records(records)
            
            # 5. 统计结果
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                "success": True,
                "total_records": len(df),
                "inserted_records": len(record_ids),
                "record_ids": record_ids,
                "duration_seconds": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
            self.logger.info(f"🎉 数据同步任务完成！")
            self.logger.info(f"📊 总记录数: {result['total_records']}")
            self.logger.info(f"✅ 成功插入: {result['inserted_records']}")
            self.logger.info(f"⏱️  耗时: {duration:.2f} 秒")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                "success": False,
                "error": str(e),
                "duration_seconds": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
            self.logger.error(f"❌ 数据同步任务失败: {e}")
            return result


def main():
    """主函数"""
    try:
        # 创建同步器实例
        syncer = FeishuDataSync()
        
        # 执行同步
        result = syncer.sync_data()
        
        # 输出结果
        if result['success']:
            print(f"\n🎉 同步成功完成！")
            print(f"📊 插入记录数: {result['inserted_records']}")
            print(f"⏱️  耗时: {result['duration_seconds']:.2f} 秒")
        else:
            print(f"\n❌ 同步失败: {result['error']}")
            
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")


if __name__ == "__main__":
    main()