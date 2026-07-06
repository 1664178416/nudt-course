import pygame
import math
from constants import *
from utils import load_image, rotate_point

class Hook:
    def __init__(self, player_position):
        self.player_x, self.player_y = player_position
        self.angle = 0  # 当前角度（弧度）
        self.direction = 1  # 摆动方向：1为顺时针，-1为逆时针
        self.length = 0
        self.max_length = 400
        self.speed = 0
        self.state = "swinging"  # swinging, throwing, pulling, caught
        self.caught_item = None
        self.hook_image = load_image("resources/images/hook.png", RED, (20, 20))
        
    def update(self, dt):
        """更新钩子状态"""
        if self.state == "swinging":
            self._update_swing(dt)
        elif self.state == "throwing":
            self._update_throwing(dt)
        elif self.state == "pulling":
            self._update_pulling(dt)
        elif self.state == "caught":
            self._update_caught(dt)
    
    def _update_swing(self, dt):
        """更新摆动状态"""
        self.angle += SWING_SPEED * self.direction
        
        # 改变方向当达到最大角度
        if abs(self.angle) > MAX_SWING_ANGLE:
            self.direction *= -1
            self.angle = MAX_SWING_ANGLE * self.direction
    
    def _update_throwing(self, dt):
        """更新抛出状态"""
        self.length += HOOK_SPEED * 10
        
        # 如果达到最大长度或超出屏幕，开始收回
        if (self.length > self.max_length or 
            self.get_hook_position()[1] < 0 or 
            self.get_hook_position()[0] < 0 or 
            self.get_hook_position()[0] > SCREEN_WIDTH):
            self.state = "pulling"
    
    def _update_pulling(self, dt):
        """更新收回状态"""
        if self.caught_item:
            # 如果有物品，减慢收回速度
            self.length -= HOOK_SPEED * (1 / self.caught_item.weight)
        else:
            self.length -= HOOK_SPEED * 2
        
        # 如果回到玩家位置，回到摆动状态
        if self.length <= 0:
            self.length = 0
            self.state = "swinging"
            self.caught_item = None
    
    def _update_caught(self, dt):
        """更新捕获状态（钩住物品但未开始收回）"""
        pass
    
    def throw(self):
        """抛出钩子"""
        if self.state == "swinging":
            self.state = "throwing"
    
    def get_hook_position(self):
        """获取钩子当前位置"""
        hook_x = self.player_x + self.length * math.sin(self.angle)
        hook_y = self.player_y + self.length * math.cos(self.angle)
        return (hook_x, hook_y)
    
    def get_hook_rect(self):
        """获取钩子的碰撞矩形"""
        hook_pos = self.get_hook_position()
        return pygame.Rect(hook_pos[0] - 10, hook_pos[1] - 10, 20, 20)
    
    def catch_item(self, item):
        """捕获物品"""
        self.caught_item = item
        self.state = "pulling"
    
    def draw(self, screen):
        """绘制钩子和绳索"""
        hook_pos = self.get_hook_position()
        
        # 绘制绳索
        pygame.draw.line(screen, BROWN, (self.player_x, self.player_y), hook_pos, 2)
        
        # 绘制钩子
        rotated_hook = pygame.transform.rotate(self.hook_image, -math.degrees(self.angle))
        hook_rect = rotated_hook.get_rect(center=hook_pos)
        screen.blit(rotated_hook, hook_rect)
        
        # 如果捕获了物品，绘制连接线
        if self.caught_item:
            pygame.draw.line(screen, WHITE, hook_pos, 
                           self.caught_item.rect.center, 1)