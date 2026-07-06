import pygame
import sys
from constants import *
from player import Player
from hook import Hook
from items import ItemManager
from levels import LevelManager
from ui import UI
from utils import load_image, load_sound

class GoldMinerGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("黄金矿工")
        self.clock = pygame.time.Clock()
        
        # 初始化游戏组件
        self.player = Player()
        self.hook = Hook(self.player.position)
        self.item_manager = ItemManager()
        self.level_manager = LevelManager()
        self.ui = UI()
        
        # 加载资源
        self.background = load_image("resources/images/background.png", BLACK, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.sounds = {
            'throw': load_sound("resources/sounds/throw.wav"),
            'grab': load_sound("resources/sounds/grab.wav"),
            'cash': load_sound("resources/sounds/cash.wav")
        }
        
        # 游戏状态
        self.game_state = "start"  # start, playing, level_complete, game_over
        self.time_left = 0
        self.level_start_time = 0
        
    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
                if self.game_state == "start" and event.key == pygame.K_SPACE:
                    self.start_game()
                
                elif self.game_state == "playing" and event.key == pygame.K_SPACE:
                    if self.hook.state == "swinging":
                        self.hook.throw()
                        self.play_sound('throw')
                
                elif self.game_state == "level_complete" and event.key == pygame.K_SPACE:
                    self.next_level()
                
                elif self.game_state == "game_over" and event.key == pygame.K_r:
                    self.reset_game()
        
        return True
    
    def start_game(self):
        """开始游戏"""
        self.game_state = "playing"
        self.time_left = self.level_manager.get_current_time_limit()
        self.level_start_time = pygame.time.get_ticks()
        self.item_manager.generate_level_items(self.level_manager.current_level)
    
    def next_level(self):
        """进入下一关"""
        self.level_manager.advance_level()
        self.start_game()
    
    def reset_game(self):
        """重置游戏"""
        self.player = Player()
        self.hook = Hook(self.player.position)
        self.item_manager = ItemManager()
        self.level_manager.reset()
        self.game_state = "start"
    
    def update(self, dt):
        """更新游戏状态"""
        if self.game_state == "playing":
            # 更新钩子
            self.hook.update(dt)
            
            # 检查碰撞
            if self.hook.state == "throwing":
                caught_item = self.item_manager.check_collision(self.hook.get_hook_rect())
                if caught_item:
                    self.hook.catch_item(caught_item)
                    self.play_sound('grab')
            
            # 检查钩子是否回到玩家位置
            if self.hook.state == "pulling" and self.hook.length <= 0:
                if self.hook.caught_item:
                    self.player.add_score(self.hook.caught_item.value)
                    self.play_sound('cash')
                    self.item_manager.remove_caught_items()
                    self.hook.caught_item = None
            
            # 更新时间
            current_time = pygame.time.get_ticks()
            elapsed_seconds = (current_time - self.level_start_time) // 1000
            self.time_left = max(0, self.level_manager.get_current_time_limit() - elapsed_seconds)
            
            # 检查关卡完成
            if self.player.score >= self.level_manager.get_current_target():
                self.game_state = "level_complete"
            
            # 检查时间结束
            if self.time_left <= 0:
                self.game_state = "game_over"
    
    def play_sound(self, sound_name):
        """播放音效"""
        sound = self.sounds.get(sound_name)
        if sound:
            sound.play()
    
    def draw(self):
        """绘制游戏"""
        # 绘制背景
        self.screen.blit(self.background, (0, 0))
        
        if self.game_state == "start":
            self.ui.draw_start_screen(self.screen)
        
        elif self.game_state == "playing":
            # 绘制游戏元素
            self.item_manager.draw(self.screen)
            self.hook.draw(self.screen)
            self.player.draw(self.screen)
            self.ui.draw_game_ui(self.screen, self.player, self.level_manager, self.time_left)
        
        elif self.game_state == "level_complete":
            self.ui.draw_level_complete(self.screen, self.level_manager)
        
        elif self.game_state == "game_over":
            self.ui.draw_game_over(self.screen, self.player, self.level_manager)
        
        pygame.display.flip()
    
    def run(self):
        """运行游戏主循环"""
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # 转换为秒
            
            running = self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        sys.exit()