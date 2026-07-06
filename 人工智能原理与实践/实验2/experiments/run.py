import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import argparse
import os
import sys
import json
import numpy as np
from datetime import datetime
from tqdm import tqdm
import platform

# ===========================
# 1. 绘图与字体配置 (解决中文乱码)
# ===========================
import matplotlib
# 设置后端为 'Agg'，这样在没有显示器的服务器上也能保存图片
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

# 自动检测系统并设置中文字体
sys_plat = platform.system()
if sys_plat == 'Windows':
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
elif sys_plat == 'Darwin':
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC']
else:
    # Linux/Server: 尝试常见字体，如果没有则回退到无衬线字体
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'DejaVu Sans']

plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# ===========================
# 导入自定义模型
# ===========================
try:
    from model import get_model
except ImportError:
    print("❌ Error: 'model.py' not found. Please ensure your model file exists.")
    sys.exit(1)

# ===========================
# 2. 实验管理工具类
# ===========================
class ExperimentManager:
    def __init__(self, base_dir="experiments"):
        # 创建带时间戳的实验目录，例如: experiments/exp_20231230_103000
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.exp_dir = os.path.join(base_dir, f"exp_{timestamp}")
        os.makedirs(self.exp_dir, exist_ok=True)
        
        self.log_path = os.path.join(self.exp_dir, "log.txt")
        self.log(f"==> 实验目录已创建: {self.exp_dir}")
        self.log(f"==> 运行设备: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
        
        # 记录训练历史
        self.history = {
            "epoch": [],
            "train_loss": [], "train_acc": [],
            "test_loss": [], "test_acc": [],
            "lr": []
        }

    def log(self, message):
        """同时打印到控制台和日志文件"""
        print(message)
        with open(self.log_path, "a", encoding='utf-8') as f:
            f.write(message + "\n")

    def update_history(self, epoch, train_loss, train_acc, test_loss, test_acc, lr):
        self.history["epoch"].append(epoch)
        self.history["train_loss"].append(train_loss)
        self.history["train_acc"].append(train_acc)
        self.history["test_loss"].append(test_loss)
        self.history["test_acc"].append(test_acc)
        self.history["lr"].append(lr)
        
        # 实时保存为 JSON，防止中断丢失
        with open(os.path.join(self.exp_dir, "metrics.json"), "w") as f:
            json.dump(self.history, f, indent=4)

    def plot_and_save_curves(self):
        """绘制并保存详细的训练曲线"""
        epochs = self.history["epoch"]
        
        plt.figure(figsize=(18, 5))
        
        # 子图1: 损失 Loss
        plt.subplot(1, 3, 1)
        plt.plot(epochs, self.history["train_loss"], label='训练集 Loss', linewidth=2)
        plt.plot(epochs, self.history["test_loss"], label='测试集 Loss', linewidth=2, linestyle='--')
        plt.title('训练与测试损失曲线', fontsize=12)
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # 子图2: 准确率 Accuracy
        plt.subplot(1, 3, 2)
        plt.plot(epochs, self.history["train_acc"], label='训练集 Acc', linewidth=2)
        plt.plot(epochs, self.history["test_acc"], label='测试集 Acc', linewidth=2, linestyle='--')
        plt.title('训练与测试准确率曲线', fontsize=12)
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy (%)')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # 子图3: 学习率 LR
        plt.subplot(1, 3, 3)
        plt.plot(epochs, self.history["lr"], color='purple', linestyle='-.')
        plt.title('学习率变化曲线', fontsize=12)
        plt.xlabel('Epoch')
        plt.ylabel('Learning Rate')
        plt.grid(True, alpha=0.3)

        save_path = os.path.join(self.exp_dir, "training_analysis_curves.png")
        plt.tight_layout()
        plt.savefig(save_path, dpi=150)
        plt.close()
        self.log(f"==> 训练曲线图已保存至: {save_path}")

# ===========================
# 3. 数据准备
# ===========================
def get_dataloaders(batch_size):
    stats = ((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))

    # 训练增强：AutoAugment
    transform_train = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.AutoAugment(transforms.AutoAugmentPolicy.CIFAR10),
        transforms.ToTensor(),
        transforms.Normalize(*stats),
        transforms.RandomErasing(p=0.25)
    ])

    # 测试/推理增强：仅标准化
    transform_test = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(*stats),
    ])

    trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform_train)
    # 为了后续做纯净的“训练集推理”，我们需要一个没有增强的 Train Loader
    trainset_pure = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform_test)
    
    testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform_test)

    # Windows下 workers建议设为0或2，Linux可设为4
    num_workers = 2 if platform.system() == 'Windows' else 4
    
    trainloader = DataLoader(trainset, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    # 纯净的训练集 Loader (不打乱，方便对应索引)
    trainloader_pure = DataLoader(trainset_pure, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)
    testloader = DataLoader(testset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)
    
    return trainloader, trainloader_pure, testloader, trainset.classes

# ===========================
# 4. 训练与评估函数
# ===========================
def train_one_epoch(model, dataloader, optimizer, criterion, scaler, device, epoch, total_epochs):
    model.train()
    running_loss = 0
    correct = 0
    total = 0
    
    loop = tqdm(dataloader, desc=f"Epoch {epoch}/{total_epochs} [Train]", leave=False)
    
    for inputs, targets in loop:
        inputs, targets = inputs.to(device), targets.to(device)
        
        optimizer.zero_grad()
        with torch.amp.autocast('cuda'):
            outputs = model(inputs)
            loss = criterion(outputs, targets)
        
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()
        
        loop.set_postfix(loss=loss.item(), acc=f"{100.*correct/total:.2f}%")
        
    return running_loss / len(dataloader), 100. * correct / total

def evaluate(model, dataloader, criterion, device, use_tta=False, desc="[Test]"):
    """
    通用评估函数。
    返回: 平均Loss, 准确率, 以及详细的推理数据(targets, preds, probs)
    """
    model.eval()
    running_loss = 0
    correct = 0
    total = 0
    
    all_targets = []
    all_preds = []
    all_probs = []
    
    loop = tqdm(dataloader, desc=desc, leave=False)
    
    with torch.no_grad():
        for inputs, targets in loop:
            inputs, targets = inputs.to(device), targets.to(device)
            
            with torch.amp.autocast('cuda'):
                if use_tta:
                    # Test Time Augmentation: 原图 + 水平翻转
                    out1 = model(inputs)
                    out2 = model(torch.flip(inputs, dims=[3]))
                    outputs = (out1 + out2) / 2
                else:
                    outputs = model(inputs)
                
                loss = criterion(outputs, targets)

            running_loss += loss.item()
            
            # 计算概率和预测
            probs = torch.softmax(outputs, dim=1)
            _, predicted = outputs.max(1)
            
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
            
            # 收集数据 (转移到CPU以节省显存)
            all_targets.append(targets.cpu())
            all_preds.append(predicted.cpu())
            all_probs.append(probs.cpu())
            
            loop.set_postfix(acc=f"{100.*correct/total:.2f}%")

    avg_loss = running_loss / len(dataloader)
    avg_acc = 100. * correct / total
    
    # 合并所有批次的数据
    results = {
        "targets": torch.cat(all_targets),
        "preds": torch.cat(all_preds),
        "probs": torch.cat(all_probs)
    }
    
    return avg_loss, avg_acc, results

# ===========================
# 5. 辅助功能：保存可视化样本
# ===========================
def save_sample_images(model, dataloader, classes, exp_manager, device, filename="sample_predictions.png"):
    """保存一批图片，显示预测结果与真实标签"""
    model.eval()
    images, labels = next(iter(dataloader))
    images, labels = images[:16].to(device), labels[:16].to(device)
    
    with torch.no_grad():
        outputs = model(images)
        _, preds = outputs.max(1)
        
    # 反归一化
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1).to(device)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1).to(device)
    images = images * std + mean
    
    plt.figure(figsize=(12, 12))
    for i in range(len(images)):
        img = images[i].cpu().permute(1, 2, 0).numpy()
        img = np.clip(img, 0, 1)
        
        plt.subplot(4, 4, i + 1)
        plt.imshow(img)
        
        pred_label = classes[preds[i]]
        true_label = classes[labels[i]]
        
        color = 'green' if preds[i] == labels[i] else 'red'
        plt.title(f"Pre: {pred_label}\nTrue: {true_label}", color=color, fontsize=10)
        plt.axis('off')
        
    save_path = os.path.join(exp_manager.exp_dir, filename)
    plt.savefig(save_path)
    plt.close()
    exp_manager.log(f"==> 样本预测图已保存: {save_path}")

# ===========================
# 主程序
# ===========================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--epochs', type=int, default=40)
    args = parser.parse_args()

    # 配置
    BATCH_SIZE = 64
    LEARNING_RATE = 1e-5
    EPOCHS = args.epochs
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 初始化管理器
    exp = ExperimentManager()
    
    # 加载数据 (trainloader_pure 用于最后的数据分析)
    trainloader, trainloader_pure, testloader, classes = get_dataloaders(BATCH_SIZE)
    exp.log(f"==> Classes: {classes}")

    # 模型、损失、优化器
    model = get_model(DEVICE)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.05)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    scaler = torch.amp.GradScaler('cuda')

    best_acc = 0.0
    start_epoch = 1
    best_model_path = os.path.join(exp.exp_dir, "best_model.pth")

    # Resume 逻辑
    if args.resume and os.path.exists("my_model.pth"):
        exp.log("==> Loading existing model 'my_model.pth'...")
        state = torch.load("my_model.pth")
        model.load_state_dict(state)

    # ---------------------------
    # 开始训练
    # ---------------------------
    exp.log(f"\n==> Start Training ({EPOCHS} epochs)...")
    
    for epoch in range(start_epoch, EPOCHS + 1):
        # 1. 训练
        train_loss, train_acc = train_one_epoch(model, trainloader, optimizer, criterion, scaler, DEVICE, epoch, EPOCHS)
        
        # 2. 验证 (开启TTA)
        test_loss, test_acc, _ = evaluate(model, testloader, criterion, DEVICE, use_tta=True, desc="[Val]")
        
        # 3. 记录日志
        current_lr = optimizer.param_groups[0]['lr']
        exp.update_history(epoch, train_loss, train_acc, test_loss, test_acc, current_lr)
        
        log_str = (f"Epoch {epoch:02d} | LR: {current_lr:.2e} | "
                   f"Train Loss: {train_loss:.4f} Acc: {train_acc:.2f}% | "
                   f"Test Loss: {test_loss:.4f} Acc: {test_acc:.2f}%")
        exp.log(log_str)

        # 4. 保存最佳模型
        if test_acc > best_acc:
            best_acc = test_acc
            torch.save(model.state_dict(), best_model_path)
            exp.log(f"    >>> New Best Model Saved! (Acc: {best_acc:.2f}%)")
        
        scheduler.step()

    exp.log("\n==> Training Finished.")
    exp.log(f"==> Best Validation Accuracy: {best_acc:.2f}%")
    
    # ---------------------------
    # 后处理分析阶段 (Post-Analysis)
    # ---------------------------
    exp.log("\n========================================")
    exp.log("==> Starting Full Data Analysis...")
    exp.log("========================================")
    
    # 1. 绘制并保存曲线
    exp.plot_and_save_curves()
    
    # 2. 加载最佳权重进行最终推理
    exp.log(f"==> Loading best weights from {best_model_path}")
    model.load_state_dict(torch.load(best_model_path))
    
    # 3. 保存可视化样本 (Test Set)
    save_sample_images(model, testloader, classes, exp, DEVICE, "test_samples.png")

    # 4. 获取【测试集】的完整推理数据 (targets, preds, probs)
    exp.log("==> Inferencing on [TEST SET] (Clean)...")
    _, test_final_acc, test_results = evaluate(model, testloader, criterion, DEVICE, use_tta=True, desc="[Final Test]")
    torch.save(test_results, os.path.join(exp.exp_dir, "results_test.pt"))
    exp.log(f"==> Test Results saved to 'results_test.pt' (Acc: {test_final_acc:.2f}%)")

    # 5. 获取【训练集】的完整推理数据 (Clean, No Augmentation)
    #    这对分析过拟合、找出难样本非常有用
    exp.log("==> Inferencing on [TRAIN SET] (Clean, No Augment)...")
    _, train_final_acc, train_results = evaluate(model, trainloader_pure, criterion, DEVICE, use_tta=False, desc="[Final Train]")
    torch.save(train_results, os.path.join(exp.exp_dir, "results_train.pt"))
    exp.log(f"==> Train Results saved to 'results_train.pt' (Acc: {train_final_acc:.2f}%)")
    
    exp.log("\n==> All Done! Data saved in: " + exp.exp_dir)

if __name__ == '__main__':
    # 设置显卡ID
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    main()