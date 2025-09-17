# 飞书数据同步工具

这是一个专业的飞书多维表格数据同步工具，支持从Excel/CSV文件读取数据并同步到飞书多维表格，具有完整的字段映射、数据验证和错误处理功能。

## 功能特性

- ✅ **多格式支持**: 支持Excel (.xlsx) 和CSV文件
- 🎯 **指定字段映射**: 通过配置文件灵活映射源字段到目标字段
- 🔍 **数据验证**: 自动验证字段存在性和数据格式
- 📊 **批量处理**: 支持大量数据的批量插入
- 📝 **详细日志**: 完整的操作日志和进度显示
- ⚡ **错误处理**: 完善的错误处理和重试机制
- 🎨 **进度条显示**: 实时显示同步进度

## 安装依赖

```bash
pip install pandas requests tqdm
```

## 配置文件

创建 `feishu_sync_config.json` 配置文件：

```json
{
  "feishu": {
    "app_id": "你的飞书应用ID",
    "app_secret": "你的飞书应用密钥",
    "base_url": "https://open.feishu.cn/open-apis",
    "app_token": "你的多维表格应用token",
    "table_id": "你的表格ID"
  },
  "data_source": {
    "file_path": "data/your_data.xlsx",
    "file_type": "excel",
    "sheet_name": "Sheet1",
    "encoding": "utf-8"
  },
  "field_mapping": {
    "源字段名1": "目标字段名1",
    "源字段名2": "目标字段名2",
    "公司名称": "公司",
    "公司类型": "公司类型",
    "工作地点": "地点",
    "所属行业(新增)": "所属行业",
    "招聘类型": "招聘类型",
    "更新时间": "更新时间",
    "备注": "备注"
  },
  "sync_options": {
    "batch_size": 50,
    "max_retries": 3,
    "retry_delay": 1,
    "skip_empty_rows": true
  },
  "logging": {
    "level": "INFO",
    "log_file": "logs/feishu_sync.log",
    "console_output": true
  }
}
```

## 字段类型支持

工具自动识别并处理不同类型的飞书字段：

- **文本字段**: 直接字符串值
- **单选字段**: 字符串值（如：公司类型、是否笔试）
- **多选字段**: 逗号分隔的字符串会自动转换为数组（如：地点、所属行业、招聘类型）
- **日期字段**: 自动转换为Unix时间戳（支持 YYYY-MM-DD 格式）
- **URL字段**: 自动验证URL格式

## 使用方法

### 1. 基本使用

```bash
python feishu_data_sync.py
```

### 2. 指定配置文件

```python
from feishu_data_sync import FeishuDataSync

# 使用自定义配置文件
sync = FeishuDataSync("custom_config.json")
result = sync.sync_data()
print(f"同步完成: {result['success_count']} 条记录")
```

### 3. 编程方式使用

```python
from feishu_data_sync import FeishuDataSync

def main():
    try:
        # 初始化同步器
        sync = FeishuDataSync()
        
        # 执行同步
        result = sync.sync_data()
        
        # 处理结果
        if result['success']:
            print(f"✅ 同步成功: {result['success_count']} 条记录")
            print(f"⏱️ 耗时: {result['duration']:.2f} 秒")
        else:
            print(f"❌ 同步失败: {result['error']}")
            
    except Exception as e:
        print(f"程序执行出错: {str(e)}")

if __name__ == "__main__":
    main()
```
## 运行，插入数据记录

```bash
# 插入一个表
python feishu_data_sync.py 
# 插入多表
python feishu_multi_table_sync.py 
```

## 配置说明

### 飞书应用配置

1. 在飞书开放平台创建应用
2. 获取 `app_id` 和 `app_secret`
3. 在多维表格中获取 `app_token` 和 `table_id`

### 数据源配置

- `file_path`: 数据文件路径（支持相对路径和绝对路径）
- `file_type`: 文件类型（"excel" 或 "csv"）
- `sheet_name`: Excel工作表名称（仅Excel文件需要）
- `encoding`: 文件编码（仅CSV文件需要）

### 字段映射配置

在 `field_mapping` 中配置源字段到目标字段的映射关系：

```json
{
  "Excel中的字段名": "飞书表格中的字段名"
}
```

### 同步选项

- `batch_size`: 批量插入大小（建议50-100）
- `max_retries`: 最大重试次数
- `retry_delay`: 重试延迟（秒）
- `skip_empty_rows`: 是否跳过空行

## 日志文件

工具会生成详细的日志文件，包含：

- 同步开始和结束时间
- 数据验证结果
- 批量插入进度
- 错误信息和警告
- 最终统计结果

日志文件位置：`logs/feishu_sync.log`

## 错误处理

工具包含完善的错误处理机制：

1. **配置验证**: 检查配置文件完整性
2. **字段验证**: 验证源字段和目标字段存在性
3. **数据验证**: 检查数据格式和类型
4. **网络重试**: 自动重试失败的请求
5. **详细日志**: 记录所有错误和警告信息

## 常见问题

### Q: 如何处理多选字段？
A: 在Excel中使用逗号分隔多个值，工具会自动转换为数组格式。

### Q: 日期字段格式要求？
A: 支持 YYYY-MM-DD 格式，会自动转换为Unix时间戳。

### Q: 如何处理大量数据？
A: 工具支持批量处理，可以通过调整 `batch_size` 参数优化性能。

### Q: 同步失败怎么办？
A: 查看日志文件了解具体错误原因，工具会自动重试失败的请求。

## 示例数据格式

Excel文件示例：

| 公司名称 | 公司类型 | 工作地点 | 所属行业(新增) | 招聘类型 | 更新时间 |
|---------|---------|---------|---------------|---------|----------|
| 腾讯科技 | 民企 | 深圳,北京 | 互联网,软件 | 校招,社招 | 2025-09-04 |
| 阿里巴巴 | 民企 | 杭州 | 互联网 | 校招 | 2025-09-05 |

## 版本信息

- 版本: 1.0.0
- 作者: WebCrawler Team
- 更新时间: 2025-09-18

## 许可证

MIT License

## 测试，飞书表格测试表 id
```
"tables": [
    {
      "name": "更新到26.7表格",
      "base_id": "UNYybgr35a9L8zs6XOOc58CYnKg", 
      "table_id": "tblO7DEGTOixsix1",
      "field_mapping": {
        "公司名称": "公司",
        "公司类型": "公司类型",
        "工作地点": "地点",
        "所属行业(新增)": "所属行业",
        "招聘类型": "招聘类型",
        "招聘对象": "招聘对象",
        "更新时间": "更新时间",
        "备注": "备注",
        "招聘岗位": "岗位",
        "投递截止": "截止日期",
        "相关链接": "投递链接",
        "招聘公告": "公告链接",
        "内推码": "内推码"
      }
    },
    {
      "name": "更新到 26.1表格无投递和公告链接",
      "base_id": "Aerub0Ib8aaZf4sfoXvcJdvwntg",
      "table_id": "tbl4p5YrcCsZ6cuK",
      "field_mapping": {
        "公司名称": "公司",
        "公司类型": "公司类型",
        "工作地点": "地点",
        "所属行业(新增)": "所属行业",
        "招聘类型": "招聘类型",
        "招聘对象": "招聘对象",
        "更新时间": "更新时间",
        "备注": "备注",
        "招聘岗位": "岗位",
        "投递截止": "截止日期",
        "内推码": "内推码"
      }
    },
    {
      "name": "更新到 26.1 表格有链接的",
      "base_id": "CD6lbqYGiaafansDVYkcirqbnrg",
      "table_id": "tblqUbePX9t4EeVQ",
      "field_mapping": {
        "公司名称": "公司",
        "公司类型": "公司类型",
        "工作地点": "地点",
        "所属行业(新增)": "所属行业",
        "招聘类型": "招聘类型",
        "招聘对象": "招聘对象",
        "更新时间": "更新时间",
        "备注": "备注",
        "招聘岗位": "岗位",
        "投递截止": "截止日期",
        "相关链接": "投递链接",
        "招聘公告": "公告链接",
        "内推码": "内推码"
      }
    }
  ],
```