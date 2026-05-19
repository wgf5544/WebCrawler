# WebCrawler 项目

校招信息爬虫 + 飞书多维表格同步工具。

## 核心工作流

```
1. main.py                   爬取 givemeoc.com 数据 → data/givemeoc_*.xlsx
2. 人工清洗                   在 Excel 中删除重复数据、修正字段
3. feishu_multi_table_sync.py 导入清洗后的数据到飞书多维表格
```

步骤 2 和 3 不能自动化，因为需要人工判断重复数据。所以不要尝试合并成一条命令。

## 常用命令

```bash
python main.py -s 1 -e 5                        # 爬取第1-5页
python feishu_multi_table_sync.py                 # 多表同步（主力）
python feishu_data_sync.py                        # 单表同步（旧版，基本弃用）
```

## 目录结构

```
src/crawler/spider.py             GiveMeOC 爬虫（Selenium + Chrome）
src/crawler/tencent_spider.py     腾讯文档下载器
src/utils/data_processor.py       数据清洗 + Excel 输出（含超链接支持）
main.py                           爬虫入口
example.py                        爬虫 API 使用示例
feishu_multi_table_sync.py        飞书多表同步（主力）
feishu_data_sync.py               飞书单表同步（旧版，待合并后移除）
feishu_batch_test.py              飞书批量操作测试
feishu_permission_test.py         飞书权限测试
feishu_final_solution.py          飞书早期方案（参考用）
get_table_fields.py               查询飞书表格字段元数据
test_field_cleaning.py            字段清洗逻辑测试
config.toml                       爬虫配置
feishu_multi_table_config.json    飞书同步配置
feishu_sync_config.json           飞书单表同步配置
```

## 飞书 API 要点

- 权限双重模型：开放平台授权 AND 表格内添加文档应用
- API 基础 URL: `https://open.feishu.cn/open-apis`
- 密钥从 `.env` 读取，优先于 JSON 配置文件
- 多维表格字段类型：文本、单选、多选（数组）、日期（毫秒时间戳）、URL（link/text 对象）

## 配置格式差异

- `config.toml`: 爬虫参数（TOML 格式）
- `feishu_multi_table_config.json`: 飞书同步配置（JSON），密钥已迁移到 `.env`
- `.env`: 飞书 API 密钥，不提交 Git

## 已知问题

1. `feishu_data_sync.py` 和 `feishu_multi_table_sync.py` 有大量重复代码，应合并
2. 数据文件路径在 JSON 配置中写死，每次需手动修改
3. 无去重机制，重复运行会插入重复记录
4. 曾将 API 密钥提交到 Git 历史，需在飞书开放平台重置
