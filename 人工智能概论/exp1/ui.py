import pygame
from constants import *

class UI:
    def __init__(self):
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 36)
        self.font_small = pygame.font.SysFont(None, 24)
    
    def draw_game_ui(self, screen, player, level_manager, time_left):
        """绘制游戏界面UI"""
        # 绘制分数
        score_text = self.font_medium.render(f"分数: ${player.score}", True, WHITE)
        money_text = self.font_medium.render(f"金钱: ${player.money}", True, WHITE)
        level_text = self.font_medium.render(f"关卡: {level_manager.current_level}", True, WHITE)
        target_text = self.font_medium.render(f"目标: ${level_manager.get_current_target()}", True, WHITE)
        time_text = self.font_medium.render(f"时间: {int(time_left)}秒", True, WHITE)
        
        screen.blit(score_text, (10, 10))
        screen.blit(money_text, (10, 50))
        screen.blit(level_text, (SCREEN_WIDTH - 150, 10))
        screen.blit(target_text, (SCREEN_WIDTH - 150, 50))
        screen.blit(time_text, (SCREEN_WIDTH // 2 - 50, 10))
    
    def draw_start_screen(self, screen):
        """绘制开始屏幕"""
        title = self.font_large.render("黄金矿工", True, GOLD)
        instruction = self.font_medium.render("按空格键开始游戏", True, WHITE)
        
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 3))
        screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, SCREEN_HEIGHT // 2))
    
    def draw_game_over(self, screen, player, level_manager):
        """绘制游戏结束界面"""
        game_over = self.font_large.render("游戏结束", True, RED)
        score = self.font_medium.render(f"最终分数: ${player.score}", True, WHITE)
        level = self.font_medium.render(f"达到关卡: {level_manager.current_level}", True, WHITE)
        restart = self.font_medium.render("按R键重新开始", True, WHITE)
        
        screen.blit(game_over, (SCREEN_WIDTH // 2 - game_over.get_width() // 2, SCREEN_HEIGHT // 3))
        screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(level, (SCREEN_WIDTH // 2 - level.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
    
    def draw_level_complete(self, screen, level_manager):
        """绘制关卡完成界面"""
        complete = self.font_large.render("关卡完成!", True, GREEN)
        next_level = self.font_medium.render(f"准备进入关卡 {level_manager.current_level + 1}", True, WHITE)
        continue_text = self.font_medium.render("按空格键继续", True, WHITE)
        
        screen.blit(complete, (SCREEN_WIDTH // 2 - complete.get_width() // 2, SCREEN_HEIGHT // 3))
        screen.blit(next_level, (SCREEN_WIDTH // 2 - next_level.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))