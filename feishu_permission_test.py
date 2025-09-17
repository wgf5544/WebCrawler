import requests
import json

# 配置信息
APP_ID = "cli_a84049866cf9900d"
APP_SECRET = "FMgHyMOXVEcBLikld8Vcpf0pUjLcrhiZ"
BASE_ID = "UNYybgr35a9L8zs6XOOc58CYnKg"
TABLE_ID = "tblO7DEGTOixsix1"

def get_access_token(app_id, app_secret):
    """获取访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": app_id, "app_secret": app_secret}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        
        print(f"获取令牌响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        if response_data.get("code") == 0:
            return response_data.get("tenant_access_token")
        else:
            raise Exception(f"获取访问令牌失败: {response_data.get('msg')}")
    except Exception as e:
        print(f"获取令牌异常: {str(e)}")
        raise

def test_app_permissions(access_token):
    """测试应用基本权限"""
    print("\n=== 测试应用基本权限 ===")
    
    # 测试1: 获取应用信息
    try:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        print(f"应用信息响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        if response_data.get("code") == 0:
            print("✅ 应用访问权限正常")
            return True
        else:
            print(f"❌ 应用访问失败: {response_data.get('msg')}")
            return False
            
    except Exception as e:
        print(f"❌ 应用权限测试异常: {str(e)}")
        return False

def test_table_permissions(access_token):
    """测试表格权限"""
    print("\n=== 测试表格权限 ===")
    
    # 测试1: 获取表格列表
    try:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        print(f"表格列表响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        if response_data.get("code") == 0:
            print("✅ 表格列表获取成功")
            tables = response_data.get("data", {}).get("items", [])
            print(f"找到 {len(tables)} 个表格:")
            for table in tables:
                print(f"  - 表格名: {table.get('name')}")
                print(f"    表格ID: {table.get('table_id')}")
            return True
        else:
            print(f"❌ 表格列表获取失败: {response_data.get('msg')}")
            return False
            
    except Exception as e:
        print(f"❌ 表格权限测试异常: {str(e)}")
        return False

def test_field_permissions(access_token):
    """测试字段权限"""
    print("\n=== 测试字段权限 ===")
    
    try:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/fields"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        print(f"字段信息响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        if response_data.get("code") == 0:
            print("✅ 字段信息获取成功")
            fields = response_data.get("data", {}).get("items", [])
            print(f"找到 {len(fields)} 个字段:")
            for field in fields:
                print(f"  - 字段名: {field.get('field_name')}")
                print(f"    字段ID: {field.get('field_id')}")
                print(f"    字段类型: {field.get('type')}")
            return fields
        else:
            print(f"❌ 字段信息获取失败: {response_data.get('msg')}")
            return None
            
    except Exception as e:
        print(f"❌ 字段权限测试异常: {str(e)}")
        return None

def test_record_permissions(access_token):
    """测试记录权限"""
    print("\n=== 测试记录权限 ===")
    
    # 测试1: 读取记录
    try:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 只获取前5条记录
        params = {"page_size": 5}
        
        response = requests.get(url, headers=headers, params=params)
        response_data = response.json()
        
        print(f"记录读取响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        if response_data.get("code") == 0:
            print("✅ 记录读取权限正常")
            records = response_data.get("data", {}).get("items", [])
            print(f"读取到 {len(records)} 条记录")
            return True
        else:
            print(f"❌ 记录读取失败: {response_data.get('msg')}")
            return False
            
    except Exception as e:
        print(f"❌ 记录权限测试异常: {str(e)}")
        return False

def test_write_permissions(access_token, fields_info=None):
    """测试写入权限"""
    print("\n=== 测试写入权限 ===")
    
    # 如果有字段信息，使用第一个文本字段进行测试
    test_data = {}
    if fields_info:
        for field in fields_info:
            if field.get('type') == 1:  # 文本类型
                field_id = field.get('field_id')
                field_name = field.get('field_name')
                # 使用field_id作为key，而不是field_name
                test_data[field_id] = f"测试数据_{field_name}"
                print(f"使用字段: {field_name} (ID: {field_id})")
                break
    
    # 如果没有找到合适的字段，从已知字段中选择
    if not test_data:
        # 从测试输出可以看到存在"公司"字段，field_id为"fldvonP6L8"
        test_data = {"fldvonP6L8": "测试数据_公司"}
        print("使用默认字段: 公司 (ID: fldvonP6L8)")
    
    try:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "fields": test_data
        }
        
        print(f"测试写入数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        
        print(f"写入测试响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        if response_data.get("code") == 0:
            print("✅ 记录写入权限正常")
            return True
        else:
            print(f"❌ 记录写入失败: {response_data.get('msg')}")
            return False
            
    except Exception as e:
        print(f"❌ 写入权限测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始飞书API权限全面测试")
    print(f"应用ID: {APP_ID}")
    print(f"多维表格ID: {BASE_ID}")
    print(f"数据表ID: {TABLE_ID}")
    
    try:
        # 1. 获取访问令牌
        print("\n1️⃣ 获取访问令牌...")
        access_token = get_access_token(APP_ID, APP_SECRET)
        print(f"✅ 访问令牌获取成功: {access_token[:20]}...")
        
        # 2. 测试应用权限
        print("\n2️⃣ 测试应用权限...")
        app_ok = test_app_permissions(access_token)
        
        # 3. 测试表格权限
        print("\n3️⃣ 测试表格权限...")
        table_ok = test_table_permissions(access_token)
        
        # 4. 测试字段权限
        print("\n4️⃣ 测试字段权限...")
        fields_info = test_field_permissions(access_token)
        
        # 5. 测试记录读取权限
        print("\n5️⃣ 测试记录读取权限...")
        read_ok = test_record_permissions(access_token)
        
        # 6. 测试记录写入权限
        print("\n6️⃣ 测试记录写入权限...")
        write_ok = test_write_permissions(access_token, fields_info)
        
        # 总结
        print("\n" + "="*50)
        print("📊 测试结果总结:")
        print(f"应用访问权限: {'✅ 正常' if app_ok else '❌ 异常'}")
        print(f"表格访问权限: {'✅ 正常' if table_ok else '❌ 异常'}")
        print(f"字段读取权限: {'✅ 正常' if fields_info else '❌ 异常'}")
        print(f"记录读取权限: {'✅ 正常' if read_ok else '❌ 异常'}")
        print(f"记录写入权限: {'✅ 正常' if write_ok else '❌ 异常'}")
        
        if all([app_ok, table_ok, fields_info, read_ok, write_ok]):
            print("\n🎉 所有权限测试通过！可以正常使用飞书API")
        else:
            print("\n⚠️  部分权限测试失败，需要检查应用权限配置")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {str(e)}")

if __name__ == "__main__":
    main()