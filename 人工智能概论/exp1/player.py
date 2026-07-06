import pygame
from constants import *
from utils import load_image

class Player:
    def __init__(self):
        self.position = (SCREEN_WIDTH // 2, 100)
        self.score = 0
        self.money = 0
        self.image = load_image("resources/images/miner.png", GREEN, (60, 60))
    
    def add_score(self, points):
        """增加分数"""
        self.score += points
        self.money += points
    
    def draw(self, screen):
        """绘制玩家"""
        screen.blit(self.image, (self.position[0] - 30, self.position[1] - 30))