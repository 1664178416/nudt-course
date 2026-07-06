import torch
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
import platform
import os

# ===========================
# 1. 基础配置
# ===========================
# 既然服务器不支持中文，我们直接用通用字体，并把标签改为英文
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False 

# CIFAR-10 类别名称
class_names = ['Plane', 'Car', 'Bird', 'Cat', 'Deer', 
               'Dog', 'Frog', 'Horse', 'Ship', 'Truck']

# 结果保存的文件名
RESULT_FILE = "experiments/exp_outputs1/results_test.pt" 
REPORT_FILE = "final_analysis_report.txt"
MATRIX_FILE = "confusion_matrix.png"

# ===========================
# 2. 加载数据
# ===========================
# 自动寻找文件逻辑
if not os.path.exists(RESULT_FILE):
    # 尝试在当前目录找
    if os.path.exists("results_test.pt"):
        RESULT_FILE = "results_test.pt"
    else:
        print(f"❌ Error: File not found: {RESULT_FILE}")
        exit(1)

print(f"==> Loading: {RESULT_FILE}")
data = torch.load(RESULT_FILE)

targets = data["targets"].numpy()
preds = data["preds"].numpy()
probs = data["probs"].numpy()

# 打开文本文件准备写入
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    
    # ===========================
    # 3. 生成分类报告
    # ===========================
    print("==> Generating Classification Report...")
    report = classification_report(targets, preds, target_names=class_names, digits=4)
    
    print(report)
    
    f.write("=== Classification Performance Report ===\n")
    f.write(report)
    f.write("\n\n")

    # ===========================
    # 4. 绘制并保存混淆矩阵 (全英文版)
    # ===========================
    print(f"==> Plotting Confusion Matrix to {MATRIX_FILE}...")
    cm = confusion_matrix(targets, preds)
    
    plt.figure(figsize=(12, 10))
    # annot=True 显示数值, fmt='d' 显示整数
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names)
    
    # [修改点] 这里全部改成英文，彻底解决 Linux 字体缺失报错
    plt.title("Confusion Matrix (Test Set)", fontsize=15)
    plt.xlabel("Predicted Label", fontsize=12)
    plt.ylabel("True Label", fontsize=12)
    
    plt.tight_layout()
    plt.savefig(MATRIX_FILE, dpi=300)
    plt.close()

    # ===========================
    # 5. 深度分析：Top 10 错误样本
    # ===========================
    f.write("=== Top 10 Hard Negatives (High Confidence Errors) ===\n")
    f.write("Format: Index | True Label | Pred Label | Confidence\n")
    f.write("-" * 60 + "\n")

    wrong_indices = np.where(preds != targets)[0]
    
    if len(wrong_indices) > 0:
        wrong_confidences = []
        for idx in wrong_indices:
            wrong_confidences.append(probs[idx][preds[idx]])
        
        # 排序：置信度从高到低
        sorted_error_indices = np.argsort(wrong_confidences)[::-1]
        
        # 打印表头
        print(f"\n{'Index':<8} | {'True Label':<12} | {'Pred Label':<12} | {'Conf.':<10}")
        print("-" * 50)

        top_k = 10
        for i in range(min(top_k, len(sorted_error_indices))):
            idx_in_wrong = sorted_error_indices[i]
            original_idx = wrong_indices[idx_in_wrong]
            
            true_label = class_names[targets[original_idx]]
            pred_label = class_names[preds[original_idx]]
            confidence = probs[original_idx][preds[original_idx]]
            
            # 格式化输出
            line_file = f"{original_idx:<8} | {true_label:<12} | {pred_label:<12} | {confidence:.2%}"
            line_print = f"{original_idx:<8} | {true_label:<12} | {pred_label:<12} | {confidence:.2%}"
            
            print(line_print)
            f.write(line_file + "\n")
    else:
        msg = "Amazing! 100% Accuracy on Test Set."
        print(msg)
        f.write(msg + "\n")

print(f"\n✅ Analysis Done!")
print(f"   - Report saved to: {REPORT_FILE}")
print(f"   - Plot saved to: {MATRIX_FILE}")