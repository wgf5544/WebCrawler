#!/usr/bin/env python3
"""
获取飞书多维表格字段信息的工具
用于查看表格中实际的字段名称和ID
"""

import json
import requests
import time


def get_access_token(app_id: str, app_secret: str) -> str:
    """获取访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        return result["tenant_access_token"]
    else:
        raise Exception(f"获取访问令牌失败: {result}")


def get_table_fields(access_token: str, base_id: str, table_id: str) -> dict:
    """获取表格字段信息"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{base_id}/tables/{table_id}/fields"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    result = response.json()
    
    if result.get("code") == 0:
        return result["data"]
    else:
        raise Exception(f"获取字段信息失败: {result}")


def main():
    """主函数"""
    # 从配置文件读取应用信息
    with open('feishu_multi_table_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    app_id = config['feishu']['app_id']
    app_secret = config['feishu']['app_secret']
    
    # 获取访问令牌
    print("🔑 获取访问令牌...")
    access_token = get_access_token(app_id, app_secret)
    print("✅ 访问令牌获取成功")
    
    # 遍历所有表格
    for table_config in config['tables']:
        table_name = table_config['name']
        base_id = table_config['base_id']
        table_id = table_config['table_id']
        
        print(f"\n📊 获取表格字段信息: {table_name}")
        print(f"Base ID: {base_id}")
        print(f"Table ID: {table_id}")
        
        try:
            fields_data = get_table_fields(access_token, base_id, table_id)
            
            print(f"✅ 字段信息获取成功，共 {len(fields_data['items'])} 个字段:")
            print("-" * 80)
            
            for field in fields_data['items']:
                field_id = field['field_id']
                field_name = field['field_name']
                field_type = field['type']
                
                print(f"字段ID: {field_id}")
                print(f"字段名称: {field_name}")
                print(f"字段类型: {field_type}")
                print("-" * 40)
                
        except Exception as e:
            print(f"❌ 获取字段信息失败: {str(e)}")
        
        # 避免API限流
        time.sleep(1)


if __name__ == "__main__":
    main()