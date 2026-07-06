import pygame
import os
import math
from constants import BLACK

def load_image(path, default_color=None, default_size=(50, 50)):
    """加载图片，如果不存在则创建默认图形"""
    try:
        if os.path.exists(path):
            image = pygame.image.load(path)
            return image.convert_alpha()
        else:
            # 创建默认图形
            surf = pygame.Surface(default_size, pygame.SRCALPHA)
            if default_color:
                pygame.draw.rect(surf, default_color, (0, 0, *default_size))
                pygame.draw.rect(surf, BLACK, (0, 0, *default_size), 2)
            return surf
    except:
        surf = pygame.Surface(default_size, pygame.SRCALPHA)
        if default_color:
            pygame.draw.rect(surf, default_color, (0, 0, *default_size))
            pygame.draw.rect(surf, BLACK, (0, 0, *default_size), 2)
        return surf

def load_sound(path):
    """加载音效，如果不存在则返回None"""
    try:
        if os.path.exists(path):
            return pygame.mixer.Sound(path)
        return None
    except:
        return None

def distance(p1, p2):
    """计算两点间距离"""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def rotate_point(point, center, angle):
    """绕中心点旋转点"""
    x = point[0] - center[0]
    y = point[1] - center[1]
    
    rotated_x = x * math.cos(angle) - y * math.sin(angle)
    rotated_y = x * math.sin(angle) + y * math.cos(angle)
    
    return (rotated_x + center[0], rotated_y + center[1])