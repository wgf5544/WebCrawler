#!/usr/bin/env python3
"""
测试字段值清洗功能
"""

import pandas as pd
import json
from feishu_multi_table_sync import FeishuMultiTableSync

def test_field_cleaning():
    """测试字段值清洗功能"""
    print("🧪 开始测试字段值清洗功能...")
    
    # 读取Excel数据
    try:
        df = pd.read_excel("data/givemeoc_20250917_234858.xlsx", sheet_name="招聘信息")
        print(f"📊 成功读取数据: {len(df)} 行")
        
        # 查看招聘对象字段的唯一值
        if '招聘对象' in df.columns:
            unique_values = df['招聘对象'].dropna().unique()
            print(f"\n📋 招聘对象字段的唯一值:")
            for i, value in enumerate(unique_values[:20], 1):  # 只显示前20个
                print(f"  {i}. {value}")
            if len(unique_values) > 20:
                print(f"  ... 还有 {len(unique_values) - 20} 个值")
        
        # 初始化同步器
        sync = FeishuMultiTableSync()
        
        # 测试字段值清洗
        print(f"\n🧹 测试字段值清洗:")
        test_values = [
            "2026年毕业生",
            "2025年毕业生", 
            "2024年毕业生",
            "应届毕业生",
            "往届毕业生",
            "社会招聘",
            "校园招聘",
            "其他值"  # 不在清洗规则中的值
        ]
        
        for value in test_values:
            cleaned = sync.clean_field_value("招聘对象", value)
            if cleaned != value:
                print(f"  ✅ '{value}' -> '{cleaned}'")
            else:
                print(f"  ➡️ '{value}' (无变化)")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_field_cleaning()