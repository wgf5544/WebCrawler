# GiveMeOC 网站爬虫

这是一个用于爬取 [GiveMeOC](https://www.givemeoc.com/) 网站校招信息的爬虫工具。该工具可以指定爬取的页码范围，并将数据保存为多种格式。

## 功能特点

- 支持指定起始和结束页码进行爬取
- 自动检测网站总页数
- 支持多种数据输出格式（CSV、Excel、JSON）
- 数据自动清洗和格式化
- **"招聘公告"和"相关链接"列保存为可点击的超链接**
- 支持下载只读的腾讯表格文档
- 动态中文列头提取，确保数据准确性
- 支持本地ChromeDriver自动匹配
- 无头浏览器模式，提升爬取效率
- 智能分页导航，支持JavaScript动态分页
- 一键完成所有工作的便捷模式
- 简单易用的命令行界面

## 环境要求

- Python 3.7+
- Chrome 浏览器（用于Selenium驱动）
- 本地ChromeDriver（程序会自动匹配版本）

## 安装

1. 克隆仓库

```bash
git clone https://github.com/yourusername/WebCrawler.git
cd WebCrawler
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python main.py
```

这将爬取所有页面的数据，并保存为Excel格式。

### 指定页码范围

```bash
python main.py --start-page 1 --end-page 5
```

这将爬取第1页到第5页的数据。

### 指定输出格式

```bash
python main.py --format excel
```

支持的格式有：csv、excel（默认）、json

### 指定输出文件名

```bash
python main.py --output my_data
```

如果不指定，将使用时间戳作为文件名。

### 完整参数列表

```
用法: main.py [-h] [-s START_PAGE] [-e END_PAGE] [-o OUTPUT] [-f {csv,excel,json}] [-d OUTPUT_DIR] [--headless] [--no-headless] [--tencent-doc TENCENT_DOC] [--all-in-one]

GiveMeOC网站爬虫工具

可选参数:
  -h, --help            显示帮助信息并退出
  -s START_PAGE, --start-page START_PAGE
                        起始页码 (默认: 1)
  -e END_PAGE, --end-page END_PAGE
                        结束页码 (默认: 爬取到最后一页)
  -o OUTPUT, --output OUTPUT
                        输出文件名 (默认: 使用时间戳)
  -f {csv,excel,json}, --format {csv,excel,json}
                        输出文件格式 (默认: excel)
  -d OUTPUT_DIR, --output-dir OUTPUT_DIR
                        输出目录 (默认: data)
  --headless            使用无头模式运行浏览器 (默认: True)
  --no-headless         不使用无头模式运行浏览器
  --tencent-doc TENCENT_DOC
                        腾讯文档URL，用于下载只读的腾讯表格文档
  --all-in-one          一键完成所有工作：爬取数据、处理链接并保存为Excel
```

## 示例

### 爬取数据并保存为Excel格式（带超链接）

```bash
python main.py --start-page 2 --end-page 10 --format excel --output givemeoc_data
```

### 一键完成所有工作

```bash
python main.py --start-page 1 --end-page 5 --all-in-one --output givemeoc_complete
```

### 下载腾讯表格文档

```bash
# 方式一：命令行直接传入
python main.py --tencent-doc "https://docs.qq.com/sheet/DV3ViQmlObHFIQnRN?tab=bnoaks" --output tencent_data

# 方式二：配置文件指定 URL/输出名（推荐与浏览器登录态复用一起使用）
# 在 config.toml 中添加：
# [crawler]
# tencent_doc = "https://docs.qq.com/sheet/DV3ViQmlObHFIQnRN?tab=bnoaks"
# output = "tencent_data"
# chrome_user_data_dir = "~/Library/Application Support/Google/Chrome"
# chrome_profile_dir = "Default"
# 然后运行：
python main.py --config config.toml
```

### 复用已登录的Chrome会话

复用已登录的 Chrome 会话进行抓取（示例，macOS）：

```bash
python main.py --start-page 1 --end-page 3 \
  --chrome-user-data-dir "$HOME/Library/Application Support/Google/Chrome" \
  --chrome-profile-dir "Default" \
  --output-dir data --format excel
```

- --chrome-user-data-dir：你的 Chrome 用户数据目录；
- --chrome-profile-dir：配置目录名（常见为 Default、Profile 1 等）。

提供这两个参数后，程序会复用你当前浏览器的登录状态，并将 Cookies 注入 HTTP 会话，从而访问登录后可见的页面。

使用配置文件（推荐，命令更简洁）：

1) 已在项目根目录提供 config.toml（可直接修改）；关键项：
   - crawler.output_dir、crawler.format
   - crawler.chrome_user_data_dir、crawler.chrome_profile_dir
2) 只需输入起止页即可运行：

```bash
python main.py -s 1 -e 3 --config config.toml
```

如需自定义配置文件路径：
```bash
python main.py -s 1 -e 5 --config /path/to/your/config.toml
```

## 跨平台兼容性问题修复

### 问题描述
在Windows环境下提交代码后，macOS环境下运行时出现以下错误：
```
main.py: error: unrecognized arguments: --config config.toml
```

### 问题原因
1. **参数定义缺失**：main.py中的argparse没有定义`--config`参数
2. **硬编码配置路径**：代码中硬编码使用'config.toml'，无法通过命令行指定配置文件
3. **跨平台开发不一致**：不同环境下的代码版本不同步

### 解决方案
1. **添加--config参数**：在argparse中添加了`--config`参数支持
2. **动态配置加载**：修改配置文件加载逻辑，支持通过命令行指定配置文件路径
3. **向后兼容**：保持默认配置文件为'config.toml'，确保现有用法不受影响

### 修复后的用法
```bash
# 使用默认配置文件
python main.py -s 1 -e 3

# 指定配置文件
python main.py -s 1 -e 3 --config config.toml

# 使用自定义配置文件路径
python main.py -s 1 -e 5 --config /path/to/your/config.toml
```

## 最新修复功能

### ✅ 已修复和优化的功能

1. **分页功能修复**
   - 修复了分页逻辑，确保能正确访问不同页面而不是总是第一页
   - 实现智能JavaScript分页导航，支持多种分页方式
   - 优化URL构建和页面导航机制

2. **无头浏览器模式**
   - 默认启用无头模式，提升爬取效率
   - 避免每次都弹出浏览器窗口
   - 支持手动切换有头/无头模式

3. **超链接功能修复**
   - "招聘公告"列正确设置为可点击的超链接
   - "相关链接"列也支持超链接功能
   - Excel文件中点击可直接跳转到对应网页

4. **中文列头提取**
   - 动态提取中文列头，确保与网站数据结构一致
   - 自动适应网站列头变化

5. **ChromeDriver兼容性**
   - 自动匹配本地Chrome浏览器版本
   - 无需手动下载和配置ChromeDriver

6. **数据准确性**
   - 修复了数据清洗过程中的空值处理问题
   - 确保所有字段正确映射和保存

7. **代码结构优化**
   - 简化了DataProcessor类结构
   - 优化了错误处理和日志记录

### 📊 数据字段说明

爬取的数据包含以下字段（中文列头）：
- 公司名称
- 公司类型
- 所属行业(新增)
- 招聘类型
- 工作地点(全国 会匹配所有搜索)
- 招聘对象
- 岗位(专业/岗位投递误区?(可点击))
- 投递进度
- 更新时间
- 投递截止
- 相关链接（超链接）
- 招聘公告（超链接）
- 内推码
- 备注

## 注意事项

- 请合理设置爬取频率，避免对目标网站造成过大压力
- 爬取的数据仅用于个人学习和研究，请勿用于商业用途
- 使用Selenium需要安装Chrome浏览器，程序会自动下载对应的ChromeDriver
- 如遇到网络问题，可尝试使用代理或调整爬取速度

## 故障排除

### 常见问题

1. **ChromeDriver版本不匹配**
   - 程序会自动检测并匹配合适的ChromeDriver版本
   - 如仍有问题，请确保Chrome浏览器已更新到最新版本

2. **数据为空或格式错误**
   - 检查网络连接是否正常
   - 确认目标网站结构未发生重大变化
   - 查看日志文件获取详细错误信息

3. **Excel超链接不工作**
   - 确保使用Microsoft Excel或兼容的电子表格软件打开
   - 检查网络连接是否正常

## 许可证

MIT