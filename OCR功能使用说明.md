# 微信文章OCR文字识别功能使用说明

## 功能概述

我已经为您的微信文章爬虫添加了OCR（光学字符识别）功能，现在可以：

✅ **提取图片中的文字内容**  
✅ **支持中英文混合识别**  
✅ **优先使用图片alt属性**  
✅ **自动下载并识别图片**  
✅ **将识别结果整合到文章正文中**  

## 文件说明

### 1. `weixin_ocr_simple.py` - 推荐使用
- 使用Tesseract OCR引擎
- 依赖简单，兼容性好
- 支持中英文识别
- 已安装并可直接使用

### 2. `weixin_crawler_with_ocr.py` - 功能完整版
- 支持多种OCR引擎（Tesseract + EasyOCR）
- 功能更强大，但依赖复杂
- 需要解决依赖冲突问题

## 使用方法

### 基本使用

```python
from weixin_ocr_simple import WeixinOCRCrawler

# 使用上下文管理器
with WeixinOCRCrawler(headless=True) as crawler:
    # 爬取页面
    page_source = crawler.crawl_article(url)
    
    # 提取内容（包括OCR识别）
    result = crawler.extract_content_with_ocr(page_source, url)
    
    print(f"标题: {result['title']}")
    print(f"内容: {result['content']}")
    print(f"图片文字: {result['image_texts']}")
```

### 返回结果说明

```python
result = {
    'title': '文章标题',
    'content': '完整正文内容（包含OCR识别的图片文字）',
    'images': [  # 图片信息列表
        {
            'index': 1,
            'src': '图片URL',
            'alt': '图片alt属性',
            'title': '图片title属性'
        }
    ],
    'image_texts': [  # 图片文字识别结果
        {
            'image_index': 1,
            'text': '识别到的文字内容',
            'source': 'ocr',  # 或 'alt_attribute'
            'src': '图片URL'
        }
    ],
    'tables': []  # 表格数据
}
```

## OCR识别策略

### 1. 智能识别顺序
1. **优先使用alt属性**: 如果图片有有意义的alt文字，直接使用
2. **OCR识别**: 如果alt属性为空或无意义，则下载图片进行OCR识别
3. **多语言支持**: 自动尝试中英文混合、纯英文、纯中文识别

### 2. 文字过滤
- 过滤长度小于3个字符的识别结果
- 移除明显的噪声和无意义字符
- 智能判断导航文本并过滤

### 3. 结果整合
- OCR识别的文字会自动添加到正文内容中
- 格式：`[图片N文字内容]: 识别到的文字`
- 保持原有文本结构不变

## 如何获取有效的微信文章URL

### 方法1: 通过微信分享
1. 在微信中打开文章
2. 点击右上角「...」
3. 选择「复制链接」
4. 获得类似格式：`https://mp.weixin.qq.com/s/xxxxx`

### 方法2: 通过公众号历史消息
1. 进入公众号主页
2. 点击「历史消息」
3. 找到目标文章
4. 复制文章链接

### 方法3: 使用测试URL
以下是一些可能有效的测试URL（需要验证）：
```
https://mp.weixin.qq.com/s/example1
https://mp.weixin.qq.com/s/example2
```

## 常见问题解决

### 1. "参数错误"或"该内容已被发布者删除"
**原因**: URL无效、需要登录或文章已删除  
**解决**: 使用有效的公开文章URL

### 2. OCR识别准确率低
**原因**: 图片质量差、文字模糊、字体特殊  
**解决**: 
- 确保图片清晰
- 尝试不同的OCR参数
- 手动检查图片内容

### 3. 图片下载失败
**原因**: 网络问题、图片URL无效、防盗链  
**解决**:
- 检查网络连接
- 确认图片URL有效
- 尝试使用代理

### 4. 识别速度慢
**原因**: 图片较多、网络较慢  
**解决**:
- 减少并发请求
- 使用更快的网络
- 考虑批量处理

## 性能优化建议

### 1. 图片处理优化
```python
# 调整图片大小以提高识别速度
image = image.resize((800, 600))  # 适当缩放

# 图片预处理
image = image.convert('L')  # 转为灰度图
```

### 2. 并发控制
```python
# 限制同时处理的图片数量
max_concurrent_images = 3
```

### 3. 缓存机制
```python
# 缓存已识别的图片结果
image_cache = {}
```

## 扩展功能建议

### 1. 图片保存
```python
# 保存识别的图片到本地
image.save(f'images/image_{i}.jpg')
```

### 2. 识别结果导出
```python
# 导出OCR结果到Excel
import pandas as pd
df = pd.DataFrame(result['image_texts'])
df.to_excel('ocr_results.xlsx')
```

### 3. 批量处理
```python
# 批量处理多个文章
urls = ['url1', 'url2', 'url3']
for url in urls:
    result = crawler.extract_content_with_ocr(page_source, url)
    # 处理结果
```

## 技术细节

### OCR引擎配置
```python
# Tesseract自定义配置
custom_config = r'--oem 3 --psm 6'
# oem 3: 使用默认OCR引擎
# psm 6: 假设文本为单一文本块
```

### 支持的语言
- `chi_sim`: 简体中文
- `eng`: 英文
- `chi_sim+eng`: 中英文混合

### 图片格式支持
- JPG/JPEG
- PNG
- GIF（静态）
- BMP
- TIFF

## 使用示例

### 完整示例代码
```python
#!/usr/bin/env python3
from weixin_ocr_simple import WeixinOCRCrawler

def extract_weixin_article_with_ocr(url):
    """提取微信文章内容，包括图片文字识别"""
    try:
        with WeixinOCRCrawler(headless=True) as crawler:
            # 爬取页面
            print(f"正在爬取: {url}")
            page_source = crawler.crawl_article(url)
            
            if not page_source:
                return None
            
            # 提取内容（包括OCR）
            result = crawler.extract_content_with_ocr(page_source, url)
            
            # 输出结果
            print(f"\n标题: {result['title']}")
            print(f"内容长度: {len(result['content'])} 字符")
            print(f"图片数量: {len(result['images'])}")
            print(f"识别文字的图片: {len(result['image_texts'])}")
            
            # 保存结果
            with open('article_content.txt', 'w', encoding='utf-8') as f:
                f.write(f"标题: {result['title']}\n\n")
                f.write(result['content'])
            
            print("\n✅ 内容已保存到 article_content.txt")
            return result
            
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    url = "https://mp.weixin.qq.com/s/your-article-url"
    result = extract_weixin_article_with_ocr(url)
```

## 总结

通过添加OCR功能，您的微信文章爬虫现在可以：

1. **完整提取文章内容** - 包括文字和图片中的文字
2. **智能识别策略** - 优先使用alt属性，必要时进行OCR
3. **多语言支持** - 中英文混合识别
4. **结果整合** - 将图片文字自然融入正文
5. **错误处理** - 完善的异常处理和日志输出

现在您可以获取到图片中的文字内容了！请使用有效的微信文章URL进行测试。