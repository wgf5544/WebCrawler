#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书多维表格批量数据插入和删除测试
"""

import os
import requests
import json
import time

# 配置信息（从环境变量读取，或在此处设置默认值）
APP_ID = os.environ.get("FEISHU_APP_ID", "cli_xxxxxxxxxxxxxxxxx")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
BASE_ID = "UNYybgr35a9L8zs6XOOc58CYnKg"
TABLE_ID = "tblO7DEGTOixsix1"

def get_access_token():
    """获取访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        print(f"❌ 获取令牌失败: {result}")
        return None

def insert_multiple_records(token, test_data_list):
    """批量插入多条记录"""
    print(f"\n=== 批量插入 {len(test_data_list)} 条记录 ===")
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records/batch_create"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 构造批量插入数据
    records = []
    for i, company_name in enumerate(test_data_list, 1):
        records.append({
            "fields": {
                "公司": f"{company_name}",
                "备注": f"测试数据{i} - 请删除"
            }
        })
    
    data = {"records": records}
    
    print(f"发送数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    print(f"批量插入结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get("code") == 0:
        record_ids = [record["record_id"] for record in result["data"]["records"]]
        print(f"✅ 成功插入 {len(record_ids)} 条记录")
        print(f"记录ID列表: {record_ids}")
        return record_ids
    else:
        print(f"❌ 批量插入失败: {result}")
        return []

def delete_records(token, record_ids):
    """删除指定记录"""
    print(f"\n=== 删除 {len(record_ids)} 条测试记录 ===")
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records/batch_delete"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {"records": record_ids}
    
    print(f"删除记录ID: {record_ids}")
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    print(f"删除结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get("code") == 0:
        print(f"✅ 成功删除 {len(record_ids)} 条记录")
        return True
    else:
        print(f"❌ 删除失败: {result}")
        return False

def query_recent_records(token, limit=10):
    """查询最近的记录"""
    print(f"\n=== 查询最近 {limit} 条记录 ===")
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "page_size": limit,
        "sort": '[{"field_name": "创建时间", "desc": true}]'
    }
    
    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    
    if result.get("code") == 0:
        records = result["data"]["items"]
        print(f"✅ 查询到 {len(records)} 条记录")
        for i, record in enumerate(records, 1):
            fields = record.get("fields", {})
            company = fields.get("公司", "未知")
            remark = fields.get("备注", "")
            print(f"  {i}. 公司: {company}, 备注: {remark}")
        return records
    else:
        print(f"❌ 查询失败: {result}")
        return []

def main():
    print("🚀 开始飞书多维表格批量操作测试")
    
    # 获取令牌
    token = get_access_token()
    if not token:
        print("❌ 无法获取访问令牌，测试终止")
        return
    
    # 测试数据
    test_companies = [
        "测试公司A",
        "测试公司B", 
        "测试公司C",
        "测试公司D",
        "测试公司E"
    ]
    
    # 查询插入前的记录
    print("\n📋 插入前的记录状态:")
    query_recent_records(token, 5)
    
    # 批量插入记录
    inserted_record_ids = insert_multiple_records(token, test_companies)
    
    if not inserted_record_ids:
        print("❌ 插入失败，测试终止")
        return
    
    # 等待一下让数据同步
    print("\n⏳ 等待数据同步...")
    time.sleep(2)
    
    # 查询插入后的记录
    print("\n📋 插入后的记录状态:")
    query_recent_records(token, 10)
    
    # 询问是否删除测试数据
    print(f"\n🗑️  准备删除 {len(inserted_record_ids)} 条测试数据")
    print("测试数据ID:", inserted_record_ids)
    
    # 自动删除测试数据
    print("⏳ 3秒后自动删除测试数据...")
    time.sleep(3)
    
    # 删除测试记录
    delete_success = delete_records(token, inserted_record_ids)
    
    if delete_success:
        # 等待删除同步
        print("\n⏳ 等待删除同步...")
        time.sleep(2)
        
        # 查询删除后的记录
        print("\n📋 删除后的记录状态:")
        query_recent_records(token, 5)
    
    print("\n📊 批量操作测试完成")

if __name__ == "__main__":
    main()