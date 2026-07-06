import pygame
import sys
import math
import random

# 初始化pygame
pygame.init()

# 游戏窗口设置
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("黄金矿工")

# 颜色定义
BACKGROUND = (50, 50, 100)
HOOK_COLOR = (200, 200, 200)
GOLD_COLOR = (255, 215, 0)
BOMB_COLOR = (100, 100, 100)
TEXT_COLOR = (255, 255, 255)
LINE_COLOR = (150, 150, 150)

# 游戏参数
clock = pygame.time.Clock()
FPS = 60

# 钩子参数
hook_length = 0
max_hook_length = 400
hook_speed = 5
hook_angle = math.pi / 4  # 初始角度
hook_angular_velocity = 0.02
hook_base_x = WIDTH // 2
hook_base_y = 100
hook_end_x = 0
hook_end_y = 0
hook_state = "swinging"  # "swinging", "extending", "retracting"
target_angle = hook_angle  # 目标角度（鼠标点击方向）
caught_object = None

# 分数
score = 0
font = pygame.font.SysFont('simhei', 36)  # 使用支持中文的字体

# 黄金和炸弹
class GameObject:
    def __init__(self, x, y, radius, obj_type, value):
        self.x = x
        self.y = y
        self.radius = radius
        self.type = obj_type  # "gold" or "bomb"
        self.value = value
        self.caught = False
        
        # 为炸弹添加移动属性
        if self.type == "bomb":
            self.speed = random.uniform(0.5, 1.5)
            self.direction = random.choice([-1, 1])  # 左或右
            self.min_x = self.radius
            self.max_x = WIDTH - self.radius
            
    def update(self):
        # 只有炸弹会移动
        if self.type == "bomb" and not self.caught:
            self.x += self.speed * self.direction
            # 碰到边界改变方向
            if self.x <= self.min_x or self.x >= self.max_x:
                self.direction *= -1
                
    def draw(self):
        if self.type == "gold":
            pygame.draw.circle(screen, GOLD_COLOR, (int(self.x), int(self.y)), self.radius)
            # 添加黄金光泽
            pygame.draw.circle(screen, (255, 255, 200), 
                              (int(self.x - self.radius//3), int(self.y - self.radius//3)), 
                              self.radius//3)
        else:  # bomb
            pygame.draw.circle(screen, BOMB_COLOR, (int(self.x), int(self.y)), self.radius)
            # 添加炸弹引线
            pygame.draw.rect(screen, (150, 75, 0), 
                            (int(self.x - 3), int(self.y - self.radius - 5), 6, 10))
            
    def check_collision(self, hook_x, hook_y):
        distance = math.sqrt((self.x - hook_x)**2 + (self.y - hook_y)**2)
        return distance <= self.radius

# 检查新物体是否与现有物体重叠
def is_overlapping(new_obj, existing_objects, min_distance=50):
    for obj in existing_objects:
        distance = math.sqrt((new_obj.x - obj.x)**2 + (new_obj.y - obj.y)**2)
        if distance < min_distance:
            return True
    return False

# 创建游戏对象
objects = []
def create_objects():
    objects.clear()
    gold_count = 0
    bomb_count = 0
    
    while len(objects) < 8:
        x = random.randint(100, WIDTH - 100)
        y = random.randint(200, HEIGHT - 100)
        radius = random.randint(20, 40)
        
        # 控制黄金和炸弹的比例
        if gold_count < 6:  # 最多6个黄金
            obj_type = "gold"
            value = radius * 2  # 黄金价值与大小相关
            gold_count += 1
        else:
            obj_type = "bomb"
            value = -50
            bomb_count += 1
            
        new_obj = GameObject(x, y, radius, obj_type, value)
        
        # 检查是否与现有物体重叠
        if not is_overlapping(new_obj, objects):
            objects.append(new_obj)
        else:
            # 如果重叠，调整计数
            if obj_type == "gold":
                gold_count -= 1
            else:
                bomb_count -= 1

# 初始化游戏对象
create_objects()

# 游戏主循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and hook_state == "swinging":
            # 获取鼠标位置并计算目标角度
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = mouse_x - hook_base_x
            dy = mouse_y - hook_base_y
            target_angle = math.atan2(dy, dx)
            hook_state = "extending"
    
    # 更新钩子状态
    if hook_state == "swinging":
        hook_angle += hook_angular_velocity
        if hook_angle > math.pi * 0.75 or hook_angle < math.pi * 0.25:
            hook_angular_velocity *= -1
            
    elif hook_state == "extending":
        hook_length += hook_speed
        if hook_length >= max_hook_length:
            hook_state = "retracting"
        else:
            # 检查是否捕获物体
            for obj in objects:
                if not obj.caught and obj.check_collision(hook_end_x, hook_end_y):
                    caught_object = obj
                    obj.caught = True
                    hook_state = "retracting"
                    break
                    
    elif hook_state == "retracting":
        hook_length -= hook_speed
        if hook_length <= 0:
            hook_length = 0
            hook_state = "swinging"
            if caught_object:
                score += caught_object.value
                objects.remove(caught_object)
                # 如果物体太少，创建新物体
                if len(objects) < 4:
                    create_objects()
                caught_object = None
    
    # 计算钩子末端位置
    if hook_state == "swinging":
        hook_end_x = hook_base_x + hook_length * math.cos(hook_angle)
        hook_end_y = hook_base_y + hook_length * math.sin(hook_angle)
    else:
        hook_end_x = hook_base_x + hook_length * math.cos(target_angle)
        hook_end_y = hook_base_y + hook_length * math.sin(target_angle)
    
    # 更新所有物体（主要是炸弹的移动）
    for obj in objects:
        obj.update()
    
    # 如果捕获了物体，更新物体位置
    if caught_object:
        caught_object.x = hook_end_x
        caught_object.y = hook_end_y
    
    # 绘制背景
    screen.fill(BACKGROUND)
    
    # 绘制地面
    pygame.draw.rect(screen, (100, 70, 30), (0, HEIGHT - 50, WIDTH, 50))
    
    # 绘制游戏对象
    for obj in objects:
        obj.draw()
    
    # 绘制钩子
    pygame.draw.line(screen, LINE_COLOR, (hook_base_x, hook_base_y), (hook_end_x, hook_end_y), 3)
    pygame.draw.circle(screen, HOOK_COLOR, (int(hook_end_x), int(hook_end_y)), 10)
    
    # 绘制分数
    score_text = font.render(f"分数: {score}", True, TEXT_COLOR)
    screen.blit(score_text, (20, 20))
    
    # 绘制游戏说明
    instruction = font.render("点击鼠标放下钩子", True, TEXT_COLOR)
    screen.blit(instruction, (WIDTH // 2 - 100, 50))
    
    # 更新显示
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()



# TODO：换ui；把炸弹黄金换成论文、基金 accept, desk reject, lack of novelty
