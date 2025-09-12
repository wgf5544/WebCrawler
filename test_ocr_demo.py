#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信文章OCR功能演示脚本
使用真实的微信文章URL测试OCR文字识别功能
"""

from weixin_ocr_simple import WeixinOCRCrawler
import json

def demo_ocr_extraction():
    """演示OCR文字提取功能"""
    
    # 测试URL列表（这些是一些可能有效的微信文章URL格式）
    test_urls = [
        # 请替换为真实有效的微信文章URL
        "https://mp.weixin.qq.com/s/aoG8bfNZM7sPnD8nSt8veg",  # 替换为实际URL
        "https://mp.weixin.qq.com/s/kHAv-XraEN_82NGegRlZUw",  # 替换为实际URL
    ]
    
    print("🚀 微信文章OCR功能演示")
    print("=" * 50)
    print("\n📝 使用说明:")
    print("1. 请将test_urls列表中的URL替换为真实的微信文章链接")
    print("2. 确保文章是公开可访问的（不需要登录）")
    print("3. 文章中包含图片才能演示OCR功能")
    print("\n" + "=" * 50)
    
    # 如果用户提供了真实URL，可以在这里测试
    user_url = input("\n请输入要测试的微信文章URL（直接回车跳过）: ").strip()
    
    if user_url:
        test_urls = [user_url]
        print(f"\n🔍 开始测试用户提供的URL: {user_url}")
    else:
        print("\n⚠️  未提供URL，使用示例URL（可能无效）")
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {url}")
        print(f"{'='*60}")
        
        try:
            with WeixinOCRCrawler(headless=True, wait_time=20) as crawler:
                # 爬取页面
                page_source = crawler.crawl_article(url)
                
                if page_source:
                    # 提取内容（包括OCR）
                    result = crawler.extract_content_with_ocr(page_source, url)
                    
                    # 显示结果统计
                    print(f"\n📊 提取结果统计:")
                    print(f"  标题: {result['title']}")
                    print(f"  正文长度: {len(result['content'])} 字符")
                    print(f"  图片总数: {len(result['images'])}")
                    print(f"  识别到文字的图片: {len(result['image_texts'])}")
                    print(f"  表格数量: {len(result['tables'])}")
                    
                    # 显示图片信息
                    if result['images']:
                        print(f"\n🖼️  图片详情:")
                        for img in result['images']:
                            alt_text = img['alt'] if img['alt'] else "无alt属性"
                            print(f"  图片 {img['index']}: {alt_text}")
                    
                    # 显示OCR识别结果
                    if result['image_texts']:
                        print(f"\n🔍 OCR识别结果:")
                        for img_text in result['image_texts']:
                            source_type = "alt属性" if img_text['source'] == 'alt_attribute' else "OCR识别"
                            text_preview = img_text['text'][:80] + "..." if len(img_text['text']) > 80 else img_text['text']
                            print(f"  图片 {img_text['image_index']} ({source_type}):")
                            print(f"    {text_preview}")
                    else:
                        print(f"\n⚠️  未识别到图片文字")
                        if result['images']:
                            print("    可能原因: 图片中无文字、文字不清晰、或下载失败")
                        else:
                            print("    原因: 文章中没有图片")
                    
                    # 显示完整内容预览
                    if result['content']:
                        print(f"\n📄 完整内容预览（前500字符）:")
                        print("-" * 40)
                        preview = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
                        print(preview)
                        print("-" * 40)
                        
                        # 保存结果到文件
                        filename = f"article_{i}_content.txt"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"标题: {result['title']}\n")
                            f.write(f"URL: {url}\n")
                            f.write(f"提取时间: {__import__('datetime').datetime.now()}\n")
                            f.write("\n" + "="*50 + "\n")
                            f.write(result['content'])
                            
                            # 添加图片信息
                            if result['image_texts']:
                                f.write("\n\n" + "="*50 + "\n")
                                f.write("图片文字识别详情:\n")
                                for img_text in result['image_texts']:
                                    f.write(f"\n图片 {img_text['image_index']} ({img_text['source']}):")
                                    f.write(f"\n{img_text['text']}\n")
                        
                        print(f"\n✅ 完整内容已保存到: {filename}")
                        
                        # 保存JSON格式结果
                        json_filename = f"article_{i}_result.json"
                        with open(json_filename, 'w', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        print(f"✅ 结构化数据已保存到: {json_filename}")
                        
                    else:
                        print(f"\n❌ 未提取到有效内容")
                        print("可能原因:")
                        print("  - URL需要登录验证")
                        print("  - 文章已删除或失效")
                        print("  - 内容完全由JavaScript动态生成")
                        print("  - 网络连接问题")
                else:
                    print("❌ 无法获取页面源代码")
                    
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n✅ 测试 {i} 完成")
    
    print("\n" + "="*60)
    print("🎉 所有测试完成！")
    print("\n💡 使用提示:")
    print("1. 如果要测试OCR功能，请使用包含图片的微信文章")
    print("2. 确保文章是公开可访问的")
    print("3. OCR识别需要一些时间，请耐心等待")
    print("4. 识别结果会自动保存到本地文件")
    print("5. 可以查看生成的.txt和.json文件了解详细结果")

def show_ocr_capabilities():
    """展示OCR功能特性"""
    print("\n🔍 OCR功能特性:")
    print("\n1. 智能识别策略:")
    print("   ✅ 优先使用图片alt属性")
    print("   ✅ alt属性无效时进行OCR识别")
    print("   ✅ 支持多种图片格式")
    
    print("\n2. 多语言支持:")
    print("   ✅ 中文识别")
    print("   ✅ 英文识别")
    print("   ✅ 中英文混合识别")
    
    print("\n3. 结果整合:")
    print("   ✅ OCR结果自动添加到正文")
    print("   ✅ 保持原有文本结构")
    print("   ✅ 标注图片来源")
    
    print("\n4. 错误处理:")
    print("   ✅ 图片下载失败处理")
    print("   ✅ OCR识别失败处理")
    print("   ✅ 网络异常处理")
    
    print("\n5. 性能优化:")
    print("   ✅ 智能过滤无意义文字")
    print("   ✅ 去重处理")
    print("   ✅ 内容长度控制")

if __name__ == "__main__":
    show_ocr_capabilities()
    demo_ocr_extraction()