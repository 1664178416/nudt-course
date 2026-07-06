import numpy as np
import torch

def compute_grpo_advantages(rewards, group_ids, clip_eps=1e-8):
    """
    计算GRPO相对优势

    参数:
        rewards: 每个样本的奖励值，形状为 [batch_size]
        group_ids: 每个样本所属的组ID，形状为 [batch_size]
        clip_eps: 防止除以零的小常数

    返回:
        advantages: GRPO相对优势，形状为 [batch_size]
    """
    # 转换为numpy便于分组操作
    rewards_np = rewards.cpu().numpy()
    unique_groups = np.unique(group_ids)

    # 初始化优势数组
    advantages = np.zeros_like(rewards_np)

    # 对每个组分别计算
    for group in unique_groups:
        # 获取当前组的样本索引
        group_mask = (group_ids == group)
        group_rewards = rewards_np[group_mask]

        # 计算组内均值和标准差
        group_mean = np.mean(group_rewards)
        group_std = np.std(group_rewards)

        # 计算相对优势 (归一化)
        group_advantages = (group_rewards - group_mean) / (group_std + clip_eps)

        # 将计算结果放回原位置
        advantages[group_mask] = group_advantages

    return torch.tensor(advantages, dtype=rewards.dtype, device=rewards.device)

# 示例使用
if __name__ == "__main__":
    # 模拟一批样本的奖励值
    rewards = torch.tensor([0.5, 0.8, 0.3, 0.9, 0.6, 0.2])

    # 定义样本所属的组 (假设有2个组)
    group_ids = np.array([0, 0, 0, 1, 1, 1])

    # 计算GRPO优势
    advantages = compute_grpo_advantages(rewards, group_ids)

    print("原始奖励:", rewards.numpy())
    print("GRPO优势:", advantages.numpy())