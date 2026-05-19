#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import sys
from datetime import datetime

# 配置信息（从环境变量读取，或在此处设置默认值）
APP_ID = os.environ.get("FEISHU_APP_ID", "cli_xxxxxxxxxxxxxxxxx")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
BASE_ID = "UNYybgr35a9L8zs6XOOc58CYnKg"
TABLE_ID = "tblO7DEGTOixsix1"

class FeishuBitableClient:
    """飞书多维表格客户端"""
    
    def __init__(self, app_id, app_secret, base_id, table_id):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_id = base_id
        self.table_id = table_id
        self.token = None
        self.field_mapping = {}
        
    def get_token(self):
        """获取访问令牌"""
        if self.token:
            return self.token
            
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {"app_id": self.app_id, "app_secret": self.app_secret}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                self.token = result.get("tenant_access_token")
                print(f"✅ 令牌获取成功")
                return self.token
            else:
                raise Exception(f"获取令牌失败: {result.get('msg')}")
                
        except Exception as e:
            print(f"❌ 获取令牌异常: {str(e)}")
            raise
    
    def get_fields(self):
        """获取表格字段信息"""
        token = self.get_token()
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            result = response.json()
            
            if result.get("code") == 0:
                fields = result.get("data", {}).get("items", [])
                
                # 构建字段映射
                for field in fields:
                    field_name = field.get("field_name")
                    field_id = field.get("field_id")
                    field_type = field.get("type")
                    
                    self.field_mapping[field_name] = {
                        "id": field_id,
                        "type": field_type,
                        "property": field.get("property", {})
                    }
                
                print(f"✅ 获取到 {len(fields)} 个字段")
                return self.field_mapping
                
            else:
                print(f"❌ 获取字段信息失败: {result.get('msg')}")
                # 即使获取字段失败，也可以尝试直接插入
                return {}
                
        except Exception as e:
            print(f"❌ 获取字段信息异常: {str(e)}")
            return {}
    
    def insert_record(self, data, use_field_id=False):
        """插入记录"""
        token = self.get_token()
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 如果需要使用字段ID，转换字段名称
        if use_field_id and self.field_mapping:
            converted_data = {}
            for field_name, value in data.items():
                if field_name in self.field_mapping:
                    field_id = self.field_mapping[field_name]["id"]
                    converted_data[field_id] = value
                else:
                    converted_data[field_name] = value
            data = converted_data
        
        payload = {
            "records": [{
                "fields": data
            }]
        }
        
        try:
            print(f"📤 发送请求: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            response = requests.post(url, headers=headers, json=payload)
            result = response.json()
            
            print(f"📥 响应状态码: {response.status_code}")
            
            if result.get("code") == 0:
                records = result.get("data", {}).get("records", [])
                if records:
                    record_id = records[0].get("record_id")
                    print(f"✅ 插入成功！记录ID: {record_id}")
                    return record_id
                else:
                    print("✅ 插入成功！但未返回记录ID")
                    return True
            else:
                print(f"❌ 插入失败: {result.get('msg')}")
                print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 分析错误信息
                error = result.get("error", {})
                if "permission_violations" in error:
                    print("\n权限问题:")
                    for violation in error["permission_violations"]:
                        subject = violation.get('subject')
                        print(f"  - 缺少权限: {subject}")
                        
                        # 提供权限申请链接
                        if subject:
                            auth_url = f"https://open.feishu.cn/app/{self.app_id}/auth?q={subject}&op_from=openapi&token_type=tenant"
                            print(f"    申请链接: {auth_url}")
                
                if "field_violations" in error:
                    print("\n字段问题:")
                    for violation in error["field_violations"]:
                        field = violation.get('field')
                        description = violation.get('description')
                        print(f"  - 字段错误: {field} - {description}")
                
                return False
                
        except Exception as e:
            print(f"❌ 插入异常: {str(e)}")
            return False
    
    def test_insert_strategies(self, test_data):
        """测试不同的插入策略"""
        print("🧪 测试不同的插入策略")
        
        # 获取字段信息
        self.get_fields()
        
        strategies = [
            {"name": "策略1: 使用字段名称", "use_field_id": False},
            {"name": "策略2: 使用字段ID", "use_field_id": True},
        ]
        
        for strategy in strategies:
            print(f"\n--- {strategy['name']} ---")
            
            success = self.insert_record(test_data, use_field_id=strategy['use_field_id'])
            
            if success:
                print(f"🎉 {strategy['name']} 成功！")
                return strategy
            else:
                print(f"❌ {strategy['name']} 失败")
        
        print("❌ 所有策略都失败了")
        return None

def main():
    """主函数"""
    print("🚀 飞书多维表格数据插入解决方案")
    print(f"应用ID: {APP_ID}")
    print(f"表格ID: {BASE_ID}")
    print(f"数据表ID: {TABLE_ID}")
    print("-" * 50)
    
    # 创建客户端
    client = FeishuBitableClient(APP_ID, APP_SECRET, BASE_ID, TABLE_ID)
    
    # 测试数据
    test_data = {
        "公司": f"测试公司_{datetime.now().strftime('%H%M%S')}",
        "更新时间": datetime.now().strftime('%Y-%m-%d'),
        "公司类型": "外企"
    }
    
    print(f"📋 测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        # 测试插入策略
        successful_strategy = client.test_insert_strategies(test_data)
        
        if successful_strategy:
            print(f"\n🎯 找到可用的插入策略: {successful_strategy['name']}")
            
            # 演示批量插入
            print("\n📦 演示批量插入:")
            batch_data = [
                {
                    "公司": f"批量测试公司1_{datetime.now().strftime('%H%M%S')}",
                    "公司类型": "国企"
                },
                {
                    "公司": f"批量测试公司2_{datetime.now().strftime('%H%M%S')}",
                    "公司类型": "民企"
                }
            ]
            
            for i, data in enumerate(batch_data, 1):
                print(f"\n插入第 {i} 条记录:")
                client.insert_record(data, use_field_id=successful_strategy['use_field_id'])
        else:
            print("\n❌ 未找到可用的插入策略")
            print("\n💡 可能的解决方案:")
            print("1. 检查应用权限配置，确保有 base:record:write 权限")
            print("2. 确认表格ID和数据表ID是否正确")
            print("3. 检查字段名称是否匹配")
            print("4. 确认字段类型和数据格式是否匹配")
            
            # 显示权限申请链接
            print("\n🔗 权限申请链接:")
            permissions = ["base:record:write", "bitable:app", "base:record:read"]
            for perm in permissions:
                url = f"https://open.feishu.cn/app/{APP_ID}/auth?q={perm}&op_from=openapi&token_type=tenant"
                print(f"{perm}: {url}")
        
    except Exception as e:
        print(f"❌ 程序执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()