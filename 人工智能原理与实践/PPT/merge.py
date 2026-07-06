import os
import fitz  # PyMuPDF
import re

def natural_sort_key(s):
    """自然排序：确保文件名 1, 2... 15, 16 顺序正确"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def process_single_pdf(input_path, output_path):
    """
    第一步：生成‘new_’开头的 3 合 1 文件。
    不使用 A4，宽度按原图对齐，高度为三张之和。
    """
    try:
        src_doc = fitz.open(input_path)
        out_doc = fitz.open()
        num_pages = len(src_doc)
        
        for i in range(0, num_pages, 3):
            batch = [src_doc[j] for j in range(i, min(i + 3, num_pages))]
            base_w = batch[0].rect.width
            
            # 计算这一组拼接后的总高度
            total_h = 0
            temp_configs = []
            for p in batch:
                scale = base_w / p.rect.width
                h = p.rect.height * scale
                temp_configs.append((p.number, h))
                total_h += h
            
            # 创建对应尺寸的长页面
            new_page = out_doc.new_page(width=base_w, height=total_h)
            
            # 拼接
            curr_y = 0
            for p_num, s_h in temp_configs:
                rect = fitz.Rect(0, curr_y, base_w, curr_y + s_h)
                new_page.show_pdf_page(rect, src_doc, p_num)
                curr_y += s_h
        
        out_doc.save(output_path)
        src_doc.close()
        out_doc.close()
        return True
    except Exception as e:
        print(f"❌ 处理单文件 {input_path} 失败: {e}")
        return False

def main():
    target_final = "FINAL_COLLECTION.pdf"
    
    # 1. 扫描原始课件并排序
    all_files = [f for f in os.listdir('.') 
                 if f.lower().endswith('.pdf') 
                 and not f.startswith('new_') 
                 and f != target_final]
    
    if not all_files:
        print("💡 文件夹里没有发现 PDF。")
        return

    all_files.sort(key=natural_sort_key)
    
    print("🚀 准备按照此顺序处理：")
    for idx, f in enumerate(all_files, 1):
        print(f"  {idx:02d}. {f}")

    # 2. 生成 new_ 中间文件
    new_files = []
    for pdf in all_files:
        out_name = f"new_{pdf}"
        if process_single_pdf(pdf, out_name):
            print(f"✅ 已生成中间件: {out_name}")
            new_files.append(out_name)
    
    # 3. 核心合并逻辑（纯拼接，不做任何压缩）
    if new_files:
        # 再次确保按顺序合并
        new_files.sort(key=natural_sort_key)
        
        print("\n📦 正在进行最后的总合并（纯搬运模式）...")
        try:
            final_doc = fitz.open()
            for f in new_files:
                # 以“插入”的方式直接把 sub_doc 的页面拿过来
                with fitz.open(f) as sub_doc:
                    final_doc.insert_pdf(sub_doc)
            
            # 【关键修改】：不做任何压缩参数，直接保存
            final_doc.save(target_final) 
            final_doc.close()
            
            print("\n" + "="*40)
            print("🎉 大功告成！")
            print(f"📁 最终文件：{os.path.abspath(target_final)}")
            print("="*40)
        except Exception as e:
            print(f"❌ 合并阶段报错了: {e}")

if __name__ == "__main__":
    main()