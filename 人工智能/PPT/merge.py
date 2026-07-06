import os
import fitz  # PyMuPDF
import re

# ================= 配置区 =================
# 'stitch' : 执行 3合1 纵向拼接并合并
# 'merge'  : 仅按字典序直接合并
MODE = 'stitch' 

# 输出目录名称
OUTPUT_DIR = "output"
# 最终文件名
FINAL_NAME = "FINAL_RESULT.pdf"
# ==========================================

def natural_sort_key(s):
    """自然排序算法：确保 1, 2, 10, 16 顺序正确"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def process_stitch(input_path, output_path):
    """纵向拼接 3 页为 1 页，无白边且保持原宽"""
    try:
        src_doc = fitz.open(input_path)
        out_doc = fitz.open()
        num_pages = len(src_doc)
        
        for i in range(0, num_pages, 3):
            batch = [src_doc[j] for j in range(i, min(i + 3, num_pages))]
            base_w = batch[0].rect.width
            
            total_h = 0
            configs = []
            for p in batch:
                scale = base_w / p.rect.width
                h = p.rect.height * scale
                configs.append((p.number, h))
                total_h += h
            
            new_page = out_doc.new_page(width=base_w, height=total_h)
            curr_y = 0
            for p_num, s_h in configs:
                rect = fitz.Rect(0, curr_y, base_w, curr_y + s_h)
                new_page.show_pdf_page(rect, src_doc, p_num)
                curr_y += s_h
                
        out_doc.save(output_path)
        return True
    except Exception as e:
        print(f"❌ 处理 {input_path} 失败: {e}")
        return False

def main():
    # 1. 准备输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 已创建输出文件夹: {OUTPUT_DIR}")

    target_final_path = os.path.join(OUTPUT_DIR, FINAL_NAME)
    
    # 2. 扫描当前目录下的原始 PDF
    all_files = [f for f in os.listdir('.') 
                 if f.lower().endswith('.pdf') 
                 and not f.startswith('new_') 
                 and f != FINAL_NAME]
    
    all_files.sort(key=natural_sort_key)
    
    if not all_files:
        print("💡 当前目录下未发现 PDF 文件，请确认脚本放置位置正确。")
        return

    final_doc = fitz.open()

    if MODE == 'stitch':
        print(f"🚀 模式：【3合1拼接】 -> 输出至 {OUTPUT_DIR}")
        for pdf in all_files:
            # 中间件存放在 output 文件夹
            tmp_name = os.path.join(OUTPUT_DIR, f"new_{pdf}")
            if process_stitch(pdf, tmp_name):
                print(f"✅ 已完成拼接: {pdf}")
                with fitz.open(tmp_name) as tmp:
                    final_doc.insert_pdf(tmp)
            # 如果你希望保留中间件，可以注释掉下面这一行
            # if os.path.exists(tmp_name): os.remove(tmp_name)
    else:
        print(f"🚀 模式：【直接合并】 -> 输出至 {OUTPUT_DIR}")
        for pdf in all_files:
            print(f"➕ 正在加入合并: {pdf}")
            with fitz.open(pdf) as src:
                final_doc.insert_pdf(src)

    # 3. 保存最终结果
    if len(final_doc) > 0:
        final_doc.save(target_final_path)
        final_doc.close()
        print("\n" + "="*50)
        print(f"🎉 任务圆满完成！")
        print(f"📄 最终文件位置: {os.path.abspath(target_final_path)}")
        print("="*50)

if __name__ == "__main__":
    main()