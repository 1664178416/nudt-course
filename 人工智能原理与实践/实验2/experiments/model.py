import torch
import torch.nn as nn
import math

# ==========================================
# 1. 基础组件定义 (手写 Attention 和 MLP)
# ==========================================

class PatchEmbed(nn.Module):
    """将图像切分成 Patch 并映射为向量"""
    def __init__(self, img_size=224, patch_size=16, in_chans=3, embed_dim=768):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.grid_size = (img_size // patch_size, img_size // patch_size)
        self.num_patches = self.grid_size[0] * self.grid_size[1]

        # 使用卷积来实现 Patch 切分和线性映射，这是最高效的实现方式
        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        x = self.proj(x)  # [B, C, H, W] -> [B, Embed, Grid, Grid]
        x = x.flatten(2)  # -> [B, Embed, NumPatches]
        x = x.transpose(1, 2)  # -> [B, NumPatches, Embed]
        return x

class Attention(nn.Module):
    """多头自注意力机制 (Multi-Head Self-Attention)"""
    def __init__(self, dim, num_heads=12, qkv_bias=True, dropout=0.):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** -0.5

        # qkv 映射层
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(dropout)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(dropout)

    def forward(self, x):
        B, N, C = x.shape
        # 计算 qkv: [B, N, 3*C] -> [B, N, 3, Heads, HeadDim] -> [3, B, Heads, N, HeadDim]
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        # Attention Score: (Q @ K.T) / sqrt(d)
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)

        # Output: (Attn @ V)
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x

class MLP(nn.Module):
    """多层感知机 (Feed Forward Network)"""
    def __init__(self, in_features, hidden_features, act_layer=nn.GELU, drop=0.):
        super().__init__()
        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = act_layer()
        self.fc2 = nn.Linear(hidden_features, in_features)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x

class Block(nn.Module):
    """Transformer Encoder Block"""
    def __init__(self, dim, num_heads, mlp_ratio=4., qkv_bias=True, drop=0.):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim, eps=1e-6)
        self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, dropout=drop)
        self.norm2 = nn.LayerNorm(dim, eps=1e-6)
        self.mlp = MLP(in_features=dim, hidden_features=int(dim * mlp_ratio), drop=drop)

    def forward(self, x):
        # 残差连接
        x = x + self.attn(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x

# ==========================================
# 2. 主模型定义 (Vision Transformer)
# ==========================================

class MyViT(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        # ViT-B/16 配置
        self.num_classes = num_classes
        self.embed_dim = 768
        self.patch_embed = PatchEmbed(img_size=224, patch_size=16, embed_dim=768)
        
        # Class Token (可学习的类别向量)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, 768))
        # Positional Embedding (位置编码)
        self.pos_embed = nn.Parameter(torch.zeros(1, 196 + 1, 768)) # 14x14 patches + 1 cls_token
        
        self.pos_drop = nn.Dropout(p=0.0)

        # 12 层 Transformer Block
        self.blocks = nn.Sequential(*[
            Block(dim=768, num_heads=12, mlp_ratio=4.0, qkv_bias=True)
            for _ in range(12)
        ])

        self.norm = nn.LayerNorm(768, eps=1e-6)
        
        # 分类头
        self.head = nn.Linear(768, num_classes)

        # 初始化权重
        self._init_weights()

    def _init_weights(self):
        # 简单的初始化，后面会被预训练权重覆盖
        nn.init.trunc_normal_(self.pos_embed, std=.02)
        nn.init.trunc_normal_(self.cls_token, std=.02)
        self.apply(self._init_vit_weights)

    def _init_vit_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.trunc_normal_(m.weight, std=.02)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    def forward(self, x):
        B = x.shape[0]
        x = self.patch_embed(x) # [B, 196, 768]

        # 拼接 Class Token
        cls_tokens = self.cls_token.expand(B, -1, -1) 
        x = torch.cat((cls_tokens, x), dim=1) # [B, 197, 768]

        # 加上位置编码
        x = x + self.pos_embed
        x = self.pos_drop(x)

        # 通过 Transformer Blocks
        x = self.blocks(x)

        x = self.norm(x)
        
        # 取出 Class Token 对应的输出用于分类
        x = x[:, 0] 
        x = self.head(x)
        return x

    # ==========================================
    # 3. 核心魔法：注入官方权重
    # ==========================================
    def load_official_weights(self, device):
        print("==> Downloading and injecting official ImageNet weights into your custom model...")
        from torchvision.models import vit_b_16, ViT_B_16_Weights
        
        # 下载官方模型
        official_model = vit_b_16(weights=ViT_B_16_Weights.IMAGENET1K_V1).to(device)
        official_dict = official_model.state_dict()
        my_dict = self.state_dict()

        # 建立映射关系 (因为我们手写的层命名可能和官方不一样，需要对齐)
        # 这里我们的命名尽量模仿了官方结构，但为了保险，我们手动复制
        
        # 1. Patch Embed
        my_dict['patch_embed.proj.weight'].copy_(official_dict['conv_proj.weight'])
        my_dict['patch_embed.proj.bias'].copy_(official_dict['conv_proj.bias'])
        
        # 2. Pos Embed & Cls Token
        my_dict['pos_embed'].copy_(official_dict['encoder.pos_embedding'])
        my_dict['cls_token'].copy_(official_dict['class_token'])
        
        # 3. Blocks (Loop copy)
        for i in range(12):
            prefix_official = f'encoder.layers.encoder_layer_{i}'
            prefix_my = f'blocks.{i}'
            
            # Norms
            my_dict[f'{prefix_my}.norm1.weight'].copy_(official_dict[f'{prefix_official}.ln_1.weight'])
            my_dict[f'{prefix_my}.norm1.bias'].copy_(official_dict[f'{prefix_official}.ln_1.bias'])
            my_dict[f'{prefix_my}.norm2.weight'].copy_(official_dict[f'{prefix_official}.ln_2.weight'])
            my_dict[f'{prefix_my}.norm2.bias'].copy_(official_dict[f'{prefix_official}.ln_2.bias'])
            
            # Attention
            # 官方的 in_proj_weight 把 q,k,v 拼在一起了，我们的 Linear 也是拼在一起的，可以直接拷贝
            my_dict[f'{prefix_my}.attn.qkv.weight'].copy_(official_dict[f'{prefix_official}.self_attention.in_proj_weight'])
            my_dict[f'{prefix_my}.attn.qkv.bias'].copy_(official_dict[f'{prefix_official}.self_attention.in_proj_bias'])
            my_dict[f'{prefix_my}.attn.proj.weight'].copy_(official_dict[f'{prefix_official}.self_attention.out_proj.weight'])
            my_dict[f'{prefix_my}.attn.proj.bias'].copy_(official_dict[f'{prefix_official}.self_attention.out_proj.bias'])
            
            # MLP
            my_dict[f'{prefix_my}.mlp.fc1.weight'].copy_(official_dict[f'{prefix_official}.mlp.0.weight'])
            my_dict[f'{prefix_my}.mlp.fc1.bias'].copy_(official_dict[f'{prefix_official}.mlp.0.bias'])
            my_dict[f'{prefix_my}.mlp.fc2.weight'].copy_(official_dict[f'{prefix_official}.mlp.3.weight'])
            my_dict[f'{prefix_my}.mlp.fc2.bias'].copy_(official_dict[f'{prefix_official}.mlp.3.bias'])

        # 4. Final Norm
        my_dict['norm.weight'].copy_(official_dict['encoder.ln.weight'])
        my_dict['norm.bias'].copy_(official_dict['encoder.ln.bias'])
        
        # 注意：Head 不复制，因为 ImageNet 是 1000 类，我们是 10 类，需要随机初始化训练
        
        self.load_state_dict(my_dict)
        print("==> Weights injected successfully!")

def get_model(device):
    model = MyViT(num_classes=10)
    model.load_official_weights(device)
    return model.to(device)