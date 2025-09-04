# GiveMeOC 网站爬虫

这是一个用于爬取 [GiveMeOC](https://www.givemeoc.com/) 网站校招信息的爬虫工具。该工具可以指定爬取的页码范围，并将数据保存为多种格式。

## 功能特点

- 支持指定起始和结束页码进行爬取
- 自动检测网站总页数
- 支持多种数据输出格式（CSV、Excel、JSON）
- 数据自动清洗和格式化
- 简单易用的命令行界面

## 环境要求

- Python 3.7+
- Chrome 浏览器（用于Selenium驱动）

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

这将爬取所有页面的数据，并保存为CSV格式。

### 指定页码范围

```bash
python main.py --start-page 1 --end-page 5
```

这将爬取第1页到第5页的数据。

### 指定输出格式

```bash
python main.py --format excel
```

支持的格式有：csv（默认）、excel、json

### 指定输出文件名

```bash
python main.py --output my_data
```

如果不指定，将使用时间戳作为文件名。

### 完整参数列表

```
用法: main.py [-h] [-s START_PAGE] [-e END_PAGE] [-o OUTPUT] [-f {csv,excel,json}] [-d OUTPUT_DIR] [--headless] [--no-headless]

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
                        输出文件格式 (默认: csv)
  -d OUTPUT_DIR, --output-dir OUTPUT_DIR
                        输出目录 (默认: data)
  --headless            使用无头模式运行浏览器 (默认: True)
  --no-headless         不使用无头模式运行浏览器
```

## 示例

爬取第2页到第10页的数据，并保存为Excel格式：

```bash
python main.py --start-page 2 --end-page 10 --format excel --output givemeoc_data
```

## 注意事项

- 请合理设置爬取频率，避免对目标网站造成过大压力
- 爬取的数据仅用于个人学习和研究，请勿用于商业用途
- 使用Selenium需要安装Chrome浏览器，程序会自动下载对应的ChromeDriver

## 许可证

MIT