import pygame
import random
from constants import *
from utils import load_image

class Item:
    def __init__(self, item_type, position):
        self.type = item_type
        self.position = position
        self.value = ITEM_VALUES[item_type]
        self.weight = ITEM_WEIGHTS[item_type]
        self.size = ITEM_SIZES[item_type]
        self.caught = False
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.center = position
        
        # 加载图片或创建默认图形
        self.image = self._load_image()
    
    def _load_image(self):
        """根据物品类型加载对应的图片"""
        image_paths = {
            ITEM_GOLD_SMALL: "resources/images/gold/small.png",
            ITEM_GOLD_MEDIUM: "resources/images/gold/medium.png",
            ITEM_GOLD_LARGE: "resources/images/gold/large.png",
            ITEM_STONE_SMALL: "resources/images/stone/small.png",
            ITEM_STONE_MEDIUM: "resources/images/stone/medium.png",
            ITEM_STONE_LARGE: "resources/images/stone/large.png",
            ITEM_DIAMOND: "resources/images/diamond.png",
            ITEM_BOMB: "resources/images/bomb.png"
        }
        
        colors = {
            ITEM_GOLD_SMALL: GOLD,
            ITEM_GOLD_MEDIUM: GOLD,
            ITEM_GOLD_LARGE: GOLD,
            ITEM_STONE_SMALL: GRAY,
            ITEM_STONE_MEDIUM: GRAY,
            ITEM_STONE_LARGE: GRAY,
            ITEM_DIAMOND: BLUE,
            ITEM_BOMB: RED
        }
        
        path = image_paths.get(self.type, "")
        color = colors.get(self.type, WHITE)
        size = (self.size, self.size)
        
        return load_image(path, color, size)
    
    def draw(self, screen):
        """绘制物品"""
        screen.blit(self.image, self.rect)
        
        # 如果被钩住，显示价值
        if self.caught:
            font = pygame.font.SysFont(None, 24)
            text = font.render(f"${self.value}", True, WHITE)
            screen.blit(text, (self.rect.centerx - text.get_width() // 2, 
                              self.rect.top - 20))

class ItemManager:
    def __init__(self):
        self.items = []
        self.caught_items = []
    
    def generate_level_items(self, level):
        """根据关卡生成物品"""
        self.items = []
        
        # 根据关卡难度调整物品数量和类型
        num_items = 10 + level * 2
        
        for _ in range(num_items):
            item_type = self._get_random_item_type(level)
            position = self._get_valid_position()
            self.items.append(Item(item_type, position))
    
    def _get_random_item_type(self, level):
        """根据关卡随机生成物品类型"""
        # 随着关卡提高，高价值物品出现概率增加
        probabilities = {
            ITEM_GOLD_SMALL: 0.3 - level * 0.02,
            ITEM_GOLD_MEDIUM: 0.2 + level * 0.01,
            ITEM_GOLD_LARGE: 0.1 + level * 0.01,
            ITEM_STONE_SMALL: 0.2 - level * 0.02,
            ITEM_STONE_MEDIUM: 0.1 - level * 0.01,
            ITEM_STONE_LARGE: 0.05,
            ITEM_DIAMOND: 0.02 + level * 0.005,
            ITEM_BOMB: 0.03
        }
        
        # 确保概率总和为1
        total = sum(probabilities.values())
        for key in probabilities:
            probabilities[key] /= total
        
        rand = random.random()
        cumulative = 0
        
        for item_type, prob in probabilities.items():
            cumulative += prob
            if rand <= cumulative:
                return item_type
        
        return ITEM_GOLD_SMALL
    
    def _get_valid_position(self):
        """获取有效的物品位置（不重叠）"""
        max_attempts = 100
        
        for _ in range(max_attempts):
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = random.randint(200, SCREEN_HEIGHT - 100)
            
            # 检查是否与其他物品重叠
            valid = True
            new_rect = pygame.Rect(0, 0, 50, 50)
            new_rect.center = (x, y)
            
            for item in self.items:
                if new_rect.colliderect(item.rect):
                    valid = False
                    break
            
            if valid:
                return (x, y)
        
        # 如果找不到有效位置，返回随机位置
        return (random.randint(100, SCREEN_WIDTH - 100), 
                random.randint(200, SCREEN_HEIGHT - 100))
    
    def check_collision(self, hook_rect):
        """检查钩子与物品的碰撞"""
        for item in self.items:
            if not item.caught and hook_rect.colliderect(item.rect):
                item.caught = True
                self.caught_items.append(item)
                return item
        
        return None
    
    def draw(self, screen):
        """绘制所有物品"""
        for item in self.items:
            item.draw(screen)
    
    def remove_caught_items(self):
        """移除已被捕获的物品"""
        self.items = [item for item in self.items if not item.caught]
        self.caught_items = []