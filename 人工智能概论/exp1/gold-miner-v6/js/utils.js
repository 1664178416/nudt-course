// 游戏常量
const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 600;
const FPS = 60;

// 游戏状态
const GAME_STATES = {
    MENU: 'menu',
    PLAYING: 'playing',
    LEVEL_COMPLETE: 'level_complete',
    GAME_OVER: 'game_over',
    GAME_WIN: 'game_win'
};

// 物品类型
const ITEM_TYPES = {
    GOLD_SMALL: 'gold_small',
    GOLD_MEDIUM: 'gold_medium',
    GOLD_LARGE: 'gold_large',
    STONE_SMALL: 'stone_small',
    STONE_MEDIUM: 'stone_medium',
    STONE_LARGE: 'stone_large',
    DIAMOND: 'diamond',
    BOMB: 'bomb'
};

// 物品属性
const ITEM_PROPERTIES = {
    [ITEM_TYPES.GOLD_SMALL]: { value: 100, weight: 1, size: 20, color: '#FFD700' },
    [ITEM_TYPES.GOLD_MEDIUM]: { value: 300, weight: 2, size: 30, color: '#FFD700' },
    [ITEM_TYPES.GOLD_LARGE]: { value: 500, weight: 3, size: 40, color: '#FFD700' },
    [ITEM_TYPES.STONE_SMALL]: { value: 10, weight: 2, size: 20, color: '#808080' },
    [ITEM_TYPES.STONE_MEDIUM]: { value: 20, weight: 3, size: 30, color: '#808080' },
    [ITEM_TYPES.STONE_LARGE]: { value: 30, weight: 4, size: 40, color: '#808080' },
    [ITEM_TYPES.DIAMOND]: { value: 1000, weight: 0.5, size: 15, color: '#00BFFF' },
    [ITEM_TYPES.BOMB]: { value: -200, weight: 1, size: 25, color: '#FF0000' }
};

// 关卡配置
const LEVEL_CONFIG = [
    { 
        name: "初学者", 
        targetScore: 1000, 
        timeLimit: 60,
        itemCount: 8,
        probabilities: {
            [ITEM_TYPES.GOLD_SMALL]: 0.3,
            [ITEM_TYPES.GOLD_MEDIUM]: 0.2,
            [ITEM_TYPES.GOLD_LARGE]: 0.05,
            [ITEM_TYPES.STONE_SMALL]: 0.2,
            [ITEM_TYPES.STONE_MEDIUM]: 0.15,
            [ITEM_TYPES.STONE_LARGE]: 0.05,
            [ITEM_TYPES.DIAMOND]: 0.02,
            [ITEM_TYPES.BOMB]: 0.03
        }
    },
    { 
        name: "熟练者", 
        targetScore: 2500, 
        timeLimit: 60,
        itemCount: 12,
        probabilities: {
            [ITEM_TYPES.GOLD_SMALL]: 0.25,
            [ITEM_TYPES.GOLD_MEDIUM]: 0.2,
            [ITEM_TYPES.GOLD_LARGE]: 0.1,
            [ITEM_TYPES.STONE_SMALL]: 0.15,
            [ITEM_TYPES.STONE_MEDIUM]: 0.15,
            [ITEM_TYPES.STONE_LARGE]: 0.08,
            [ITEM_TYPES.DIAMOND]: 0.05,
            [ITEM_TYPES.BOMB]: 0.02
        }
    },
    { 
        name: "高手", 
        targetScore: 5000, 
        timeLimit: 60,
        itemCount: 16,
        probabilities: {
            [ITEM_TYPES.GOLD_SMALL]: 0.2,
            [ITEM_TYPES.GOLD_MEDIUM]: 0.2,
            [ITEM_TYPES.GOLD_LARGE]: 0.15,
            [ITEM_TYPES.STONE_SMALL]: 0.1,
            [ITEM_TYPES.STONE_MEDIUM]: 0.1,
            [ITEM_TYPES.STONE_LARGE]: 0.1,
            [ITEM_TYPES.DIAMOND]: 0.08,
            [ITEM_TYPES.BOMB]: 0.07
        }
    }
];

// 工具函数
class Utils {
    // 加载图片，如果不存在则使用默认颜色
    static loadImage(path, defaultColor, defaultSize = {width: 50, height: 50}) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = () => {
                // 创建默认图形
                const canvas = document.createElement('canvas');
                canvas.width = defaultSize.width;
                canvas.height = defaultSize.height;
                const ctx = canvas.getContext('2d');
                
                if (defaultColor) {
                    ctx.fillStyle = defaultColor;
                    ctx.fillRect(0, 0, defaultSize.width, defaultSize.height);
                    
                    ctx.strokeStyle = '#000';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(0, 0, defaultSize.width, defaultSize.height);
                }
                
                resolve(canvas);
            };
            img.src = path;
        });
    }
    
    // 计算两点之间的距离
    static distance(p1, p2) {
        return Math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2);
    }
    
    // 限制数值在范围内
    static clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }
    
    // 随机整数
    static randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
    
    // 随机浮点数
    static randomFloat(min, max) {
        return Math.random() * (max - min) + min;
    }
    
    // 检查两个矩形是否碰撞
    static checkRectCollision(rect1, rect2) {
        return rect1.x < rect2.x + rect2.width &&
               rect1.x + rect1.width > rect2.x &&
               rect1.y < rect2.y + rect2.height &&
               rect1.y + rect1.height > rect2.y;
    }
    
    // 检查点是否在矩形内
    static pointInRect(point, rect) {
        return point.x >= rect.x && 
               point.x <= rect.x + rect.width && 
               point.y >= rect.y && 
               point.y <= rect.y + rect.height;
    }
    
    // 检查两个圆形是否碰撞
    static checkCircleCollision(circle1, circle2) {
        const dx = circle1.x - circle2.x;
        const dy = circle1.y - circle2.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        return distance < circle1.radius + circle2.radius;
    }
}