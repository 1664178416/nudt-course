import pygame
import random
import sys

# 初始化pygame
pygame.init()

# 游戏常量
WIDTH, HEIGHT = 500, 600
GRID_SIZE = 4
CELL_SIZE = 100
GRID_MARGIN = 10
GRID_PADDING = 10

# 颜色定义
BACKGROUND_COLOR = (250, 248, 239)
GRID_BACKGROUND_COLOR = (187, 173, 160)
EMPTY_CELL_COLOR = (205, 193, 180)
TEXT_COLOR = (119, 110, 101)
LIGHT_TEXT_COLOR = (249, 246, 242)

# 不同数字对应的颜色
CELL_COLORS = {
    0: (205, 193, 180),
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46)
}

# 创建游戏窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2048 Game")

# 加载字体
try:
    font = pygame.font.Font(None, 40)
    small_font = pygame.font.Font(None, 24)
    large_font = pygame.font.Font(None, 60)
except:
    font = pygame.font.SysFont(None, 40)
    small_font = pygame.font.SysFont(None, 24)
    large_font = pygame.font.SysFont(None, 60)

class Game2048:
    def __init__(self):
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.won = False
        self.add_new_tile()
        self.add_new_tile()
    
    def add_new_tile(self):
        """在随机空白位置添加一个新的方块(90%概率为2，10%概率为4)"""
        empty_cells = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if self.grid[i][j] == 0]
        if empty_cells:
            row, col = random.choice(empty_cells)
            self.grid[row][col] = 2 if random.random() < 0.9 else 4
            return True
        return False
    
    def move(self, direction):
        """根据方向移动方块并合并"""
        if self.game_over:
            return False
        
        moved = False
        # 复制当前网格状态，用于检查是否有移动发生
        old_grid = [row[:] for row in self.grid]
        
        if direction == 'left':
            for i in range(GRID_SIZE):
                row = self.grid[i]
                # 移除空格
                new_row = [num for num in row if num != 0]
                # 合并相同数字
                for j in range(len(new_row) - 1):
                    if new_row[j] == new_row[j + 1]:
                        new_row[j] *= 2
                        self.score += new_row[j]
                        if new_row[j] == 2048 and not self.won:
                            self.won = True
                        new_row[j + 1] = 0
                # 移除合并后产生的空格
                new_row = [num for num in new_row if num != 0]
                # 补齐空格
                new_row.extend([0] * (GRID_SIZE - len(new_row)))
                self.grid[i] = new_row
                if self.grid[i] != old_grid[i]:
                    moved = True
        
        elif direction == 'right':
            for i in range(GRID_SIZE):
                row = self.grid[i]
                new_row = [num for num in row if num != 0]
                for j in range(len(new_row) - 1, 0, -1):
                    if new_row[j] == new_row[j - 1]:
                        new_row[j] *= 2
                        self.score += new_row[j]
                        if new_row[j] == 2048 and not self.won:
                            self.won = True
                        new_row[j - 1] = 0
                new_row = [num for num in new_row if num != 0]
                new_row = [0] * (GRID_SIZE - len(new_row)) + new_row
                self.grid[i] = new_row
                if self.grid[i] != old_grid[i]:
                    moved = True
        
        elif direction == 'up':
            for j in range(GRID_SIZE):
                column = [self.grid[i][j] for i in range(GRID_SIZE) if self.grid[i][j] != 0]
                for i in range(len(column) - 1):
                    if column[i] == column[i + 1]:
                        column[i] *= 2
                        self.score += column[i]
                        if column[i] == 2048 and not self.won:
                            self.won = True
                        column[i + 1] = 0
                column = [num for num in column if num != 0]
                column.extend([0] * (GRID_SIZE - len(column)))
                for i in range(GRID_SIZE):
                    if self.grid[i][j] != column[i]:
                        moved = True
                    self.grid[i][j] = column[i]
        
        elif direction == 'down':
            for j in range(GRID_SIZE):
                column = [self.grid[i][j] for i in range(GRID_SIZE) if self.grid[i][j] != 0]
                for i in range(len(column) - 1, 0, -1):
                    if column[i] == column[i - 1]:
                        column[i] *= 2
                        self.score += column[i]
                        if column[i] == 2048 and not self.won:
                            self.won = True
                        column[i - 1] = 0
                column = [num for num in column if num != 0]
                column = [0] * (GRID_SIZE - len(column)) + column
                for i in range(GRID_SIZE):
                    if self.grid[i][j] != column[i]:
                        moved = True
                    self.grid[i][j] = column[i]
        
        # 如果有移动发生，则添加新方块并检查游戏是否结束
        if moved:
            self.add_new_tile()
            self.check_game_over()
        
        return moved
    
    def check_game_over(self):
        """检查游戏是否结束"""
        # 检查是否有空格
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.grid[i][j] == 0:
                    return
        
        # 检查是否可以合并
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                current = self.grid[i][j]
                # 检查右侧
                if j < GRID_SIZE - 1 and current == self.grid[i][j + 1]:
                    return
                # 检查下方
                if i < GRID_SIZE - 1 and current == self.grid[i + 1][j]:
                    return
        
        self.game_over = True
    
    def reset(self):
        """重置游戏"""
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.won = False
        self.add_new_tile()
        self.add_new_tile()
    
    def draw(self, screen):
        """绘制游戏界面"""
        # 绘制背景
        screen.fill(BACKGROUND_COLOR)
        
        # 绘制游戏标题
        title_text = large_font.render("2048", True, TEXT_COLOR)
        screen.blit(title_text, (20, 20))
        
        # 绘制分数
        score_text = small_font.render(f"Score: {self.score}", True, TEXT_COLOR)
        screen.blit(score_text, (WIDTH - 120, 30))
        
        # 绘制重置按钮
        reset_rect = pygame.Rect(WIDTH - 120, 70, 100, 40)
        pygame.draw.rect(screen, (143, 122, 102), reset_rect, border_radius=5)
        reset_text = small_font.render("Restart", True, LIGHT_TEXT_COLOR)
        screen.blit(reset_text, (WIDTH - 110, 80))
        
        # 计算网格位置使其居中
        grid_width = GRID_SIZE * CELL_SIZE + (GRID_SIZE - 1) * GRID_MARGIN
        grid_x = (WIDTH - grid_width) // 2
        grid_y = 150
        
        # 绘制网格背景
        grid_bg_rect = pygame.Rect(
            grid_x - GRID_PADDING, 
            grid_y - GRID_PADDING, 
            grid_width + 2 * GRID_PADDING, 
            grid_width + 2 * GRID_PADDING
        )
        pygame.draw.rect(screen, GRID_BACKGROUND_COLOR, grid_bg_rect, border_radius=5)
        
        # 绘制每个单元格
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                cell_x = grid_x + j * (CELL_SIZE + GRID_MARGIN)
                cell_y = grid_y + i * (CELL_SIZE + GRID_MARGIN)
                
                value = self.grid[i][j]
                cell_color = CELL_COLORS.get(value, (60, 58, 50))
                
                # 绘制单元格
                cell_rect = pygame.Rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, cell_color, cell_rect, border_radius=3)
                
                # 如果单元格有值，绘制数字
                if value != 0:
                    # 根据数字大小选择字体大小
                    if value < 100:
                        text_font = font
                    elif value < 1000:
                        text_font = pygame.font.Font(None, 35) if hasattr(pygame.font, 'Font') else pygame.font.SysFont(None, 35)
                    else:
                        text_font = pygame.font.Font(None, 30) if hasattr(pygame.font, 'Font') else pygame.font.SysFont(None, 30)
                    
                    # 根据数字大小选择文字颜色
                    text_color = TEXT_COLOR if value < 8 else LIGHT_TEXT_COLOR
                    text = text_font.render(str(value), True, text_color)
                    text_rect = text.get_rect(center=(cell_x + CELL_SIZE // 2, cell_y + CELL_SIZE // 2))
                    screen.blit(text, text_rect)
        
        # 绘制游戏状态提示
        if self.won and not self.game_over:
            status_text = font.render("You Win! Press R to restart", True, (237, 194, 46))
            screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, HEIGHT - 100))
        elif self.game_over:
            status_text = font.render("Game Over! Press R to restart", True, (246, 94, 59))
            screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, HEIGHT - 100))
        
        # 绘制操作提示
        hint_text = small_font.render("Use arrow keys to move, R to restart", True, TEXT_COLOR)
        screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT - 50))

def main():
    game = Game2048()
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    game.move('up')
                elif event.key == pygame.K_DOWN:
                    game.move('down')
                elif event.key == pygame.K_LEFT:
                    game.move('left')
                elif event.key == pygame.K_RIGHT:
                    game.move('right')
                elif event.key == pygame.K_r:
                    game.reset()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                reset_rect = pygame.Rect(WIDTH - 120, 70, 100, 40)
                if reset_rect.collidepoint(mouse_pos):
                    game.reset()
        
        # 绘制游戏
        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()