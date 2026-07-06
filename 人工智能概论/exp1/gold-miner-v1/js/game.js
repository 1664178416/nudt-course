// 游戏常量
const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 600;
const FPS = 60;

// 游戏状态
const GAME_STATES = {
    MENU: 'menu',
    PLAYING: 'playing',
    LEVEL_COMPLETE: 'level_complete',
    GAME_OVER: 'game_over'
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
            [ITEM_TYPES.GOLD_SMALL]: 0.4,
            [ITEM_TYPES.GOLD_MEDIUM]: 0.2,
            [ITEM_TYPES.GOLD_LARGE]: 0.05,
            [ITEM_TYPES.STONE_SMALL]: 0.2,
            [ITEM_TYPES.STONE_MEDIUM]: 0.1,
            [ITEM_TYPES.STONE_LARGE]: 0.03,
            [ITEM_TYPES.DIAMOND]: 0.01,
            [ITEM_TYPES.BOMB]: 0.01
        }
    },
    { 
        name: "熟练者", 
        targetScore: 2500, 
        timeLimit: 60,
        itemCount: 12,
        probabilities: {
            [ITEM_TYPES.GOLD_SMALL]: 0.3,
            [ITEM_TYPES.GOLD_MEDIUM]: 0.25,
            [ITEM_TYPES.GOLD_LARGE]: 0.1,
            [ITEM_TYPES.STONE_SMALL]: 0.15,
            [ITEM_TYPES.STONE_MEDIUM]: 0.1,
            [ITEM_TYPES.STONE_LARGE]: 0.05,
            [ITEM_TYPES.DIAMOND]: 0.03,
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
            [ITEM_TYPES.GOLD_MEDIUM]: 0.25,
            [ITEM_TYPES.GOLD_LARGE]: 0.15,
            [ITEM_TYPES.STONE_SMALL]: 0.1,
            [ITEM_TYPES.STONE_MEDIUM]: 0.1,
            [ITEM_TYPES.STONE_LARGE]: 0.08,
            [ITEM_TYPES.DIAMOND]: 0.05,
            [ITEM_TYPES.BOMB]: 0.07
        }
    }
];

// 游戏主类
class GoldMinerGame {
    constructor() {
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // 游戏状态
        this.gameState = GAME_STATES.MENU;
        this.player = {
            score: 0,
            money: 0,
            position: { x: CANVAS_WIDTH / 2, y: 100 }
        };
        
        // 钩子状态
        this.hook = {
            angle: 0, // 当前角度（弧度）
            length: 0,
            maxLength: 400,
            speed: 5,
            state: 'idle', // idle, throwing, pulling, caught
            caughtItem: null
        };
        
        // 游戏对象
        this.items = [];
        this.level = 1;
        this.timeLeft = 0;
        this.levelStartTime = 0;
        
        // 图像资源
        this.images = {};
        
        // 鼠标状态
        this.mouse = {
            x: CANVAS_WIDTH / 2,
            y: 100,
            isDown: false
        };
        
        // 初始化
        this.init();
        this.setupEventListeners();
        this.gameLoop();
    }
    
    async init() {
        // 加载资源
        await this.loadResources();
    }
    
    async loadResources() {
        // 图片资源映射
        const imagePaths = {
            background: 'assets/images/background.png',
            hook: 'assets/images/hook.png',
            gold_small: 'assets/images/gold-small.png',
            gold_medium: 'assets/images/gold-medium.png',
            gold_large: 'assets/images/gold-large.png',
            stone_small: 'assets/images/stone-small.png',
            stone_medium: 'assets/images/stone-medium.png',
            stone_large: 'assets/images/stone-large.png',
            diamond: 'assets/images/diamond.png',
            bomb: 'assets/images/bomb.png'
        };
        
        // 默认颜色
        const defaultColors = {
            background: '#1a3c5c',
            hook: '#FF0000',
            gold_small: '#FFD700',
            gold_medium: '#FFD700',
            gold_large: '#FFD700',
            stone_small: '#808080',
            stone_medium: '#808080',
            stone_large: '#808080',
            diamond: '#00BFFF',
            bomb: '#FF0000'
        };
        
        // 加载图片
        for (const key in imagePaths) {
            this.images[key] = await Utils.loadImage(
                imagePaths[key], 
                defaultColors[key],
                {width: 50, height: 50}
            );
        }
    }
    
    setupEventListeners() {
        // 鼠标移动事件
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouse.x = e.clientX - rect.left;
            this.mouse.y = e.clientY - rect.top;
            
            // 更新钩子角度（仅当钩子空闲时）
            if (this.hook.state === 'idle') {
                this.updateHookAngle();
            }
        });
        
        // 鼠标点击事件
        this.canvas.addEventListener('mousedown', (e) => {
            if (e.button === 0) { // 左键
                this.mouse.isDown = true;
                
                if (this.gameState === GAME_STATES.PLAYING && this.hook.state === 'idle') {
                    this.throwHook();
                }
            }
        });
        
        this.canvas.addEventListener('mouseup', (e) => {
            if (e.button === 0) {
                this.mouse.isDown = false;
            }
        });
        
        // 键盘事件
        document.addEventListener('keydown', (e) => {
            switch(e.code) {
                case 'Escape':
                    if (this.gameState === GAME_STATES.PLAYING) {
                        this.showMenu();
                    }
                    break;
                case 'KeyR':
                    if (this.gameState === GAME_STATES.GAME_OVER) {
                        this.restartLevel();
                    }
                    break;
            }
        });
    }
    
    updateHookAngle() {
        // 计算钩子角度（从玩家位置指向鼠标位置）
        const dx = this.mouse.x - this.player.position.x;
        const dy = this.mouse.y - this.player.position.y;
        this.hook.angle = Math.atan2(dx, dy);
    }
    
    startLevel(level) {
        this.level = level;
        this.gameState = GAME_STATES.PLAYING;
        this.timeLeft = this.getCurrentLevelConfig().timeLimit;
        this.levelStartTime = Date.now();
        this.generateLevelItems();
        this.updateUI();
        
        // 重置钩子
        this.hook.state = 'idle';
        this.hook.length = 0;
        this.hook.caughtItem = null;
    }
    
    nextLevel() {
        if (this.level < LEVEL_CONFIG.length) {
            this.startLevel(this.level + 1);
        } else {
            // 所有关卡完成
            this.showLevelComplete(true);
        }
    }
    
    restartLevel() {
        this.startLevel(this.level);
    }
    
    showMenu() {
        this.gameState = GAME_STATES.MENU;
        this.player.score = 0;
        this.player.money = 0;
    }
    
    throwHook() {
        this.hook.state = 'throwing';
    }
    
    generateLevelItems() {
        this.items = [];
        const levelConfig = this.getCurrentLevelConfig();
        const numItems = levelConfig.itemCount;
        
        for (let i = 0; i < numItems; i++) {
            const itemType = this.getRandomItemType();
            const position = this.getValidPosition();
            this.items.push({
                type: itemType,
                position: position,
                value: ITEM_PROPERTIES[itemType].value,
                weight: ITEM_PROPERTIES[itemType].weight,
                size: ITEM_PROPERTIES[itemType].size,
                color: ITEM_PROPERTIES[itemType].color,
                caught: false
            });
        }
    }
    
    getRandomItemType() {
        const levelConfig = this.getCurrentLevelConfig();
        const probabilities = levelConfig.probabilities;
        
        // 确保概率总和为1
        const total = Object.values(probabilities).reduce((sum, prob) => sum + prob, 0);
        const normalizedProbabilities = {};
        Object.keys(probabilities).forEach(key => {
            normalizedProbabilities[key] = probabilities[key] / total;
        });
        
        const rand = Math.random();
        let cumulative = 0;
        
        for (const itemType in normalizedProbabilities) {
            cumulative += normalizedProbabilities[itemType];
            if (rand <= cumulative) {
                return itemType;
            }
        }
        
        return ITEM_TYPES.GOLD_SMALL;
    }
    
    getValidPosition() {
        const maxAttempts = 100;
        
        for (let i = 0; i < maxAttempts; i++) {
            const x = Utils.randomInt(100, CANVAS_WIDTH - 100);
            const y = Utils.randomInt(200, CANVAS_HEIGHT - 100);
            
            // 检查是否与其他物品重叠
            let valid = true;
            for (const item of this.items) {
                const dx = item.position.x - x;
                const dy = item.position.y - y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < item.size + 30) { // 30是安全距离
                    valid = false;
                    break;
                }
            }
            
            if (valid) {
                return { x, y };
            }
        }
        
        // 如果找不到有效位置，返回随机位置
        return {
            x: Utils.randomInt(100, CANVAS_WIDTH - 100),
            y: Utils.randomInt(200, CANVAS_HEIGHT - 100)
        };
    }
    
    updateHook() {
        switch(this.hook.state) {
            case 'throwing':
                this.hook.length += this.hook.speed * 2;
                
                // 检查碰撞
                this.checkCollision();
                
                // 如果达到最大长度或超出屏幕，开始收回
                const hookPos = this.getHookPosition();
                if (this.hook.length > this.hook.maxLength || 
                    hookPos.y < 0 || hookPos.x < 0 || hookPos.x > CANVAS_WIDTH) {
                    this.hook.state = 'pulling';
                }
                break;
                
            case 'pulling':
                if (this.hook.caughtItem) {
                    // 如果有物品，减慢收回速度
                    this.hook.length -= this.hook.speed * (1 / this.hook.caughtItem.weight);
                    
                    // 更新被捕获物品的位置
                    this.hook.caughtItem.position = this.getHookPosition();
                } else {
                    this.hook.length -= this.hook.speed * 2;
                }
                
                // 如果回到玩家位置，回到空闲状态
                if (this.hook.length <= 0) {
                    this.hook.length = 0;
                    this.hook.state = 'idle';
                    
                    // 如果捕获了物品，增加分数
                    if (this.hook.caughtItem) {
                        this.player.score += this.hook.caughtItem.value;
                        this.player.money += this.hook.caughtItem.value;
                        this.updateUI();
                        
                        // 移除被捕获的物品
                        this.items = this.items.filter(item => item !== this.hook.caughtItem);
                        this.hook.caughtItem = null;
                    }
                }
                break;
        }
    }
    
    getHookPosition() {
        return {
            x: this.player.position.x + this.hook.length * Math.sin(this.hook.angle),
            y: this.player.position.y + this.hook.length * Math.cos(this.hook.angle)
        };
    }
    
    checkCollision() {
        const hookPos = this.getHookPosition();
        const hookRadius = 10; // 钩子碰撞半径
        
        for (const item of this.items) {
            if (item.caught) continue;
            
            const dx = item.position.x - hookPos.x;
            const dy = item.position.y - hookPos.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < hookRadius + item.size / 2) {
                item.caught = true;
                this.hook.caughtItem = item;
                this.hook.state = 'pulling';
                break;
            }
        }
    }
    
    updateTime() {
        if (this.gameState === GAME_STATES.PLAYING) {
            const elapsedSeconds = Math.floor((Date.now() - this.levelStartTime) / 1000);
            this.timeLeft = Math.max(0, this.getCurrentLevelConfig().timeLimit - elapsedSeconds);
            
            // 检查时间结束
            if (this.timeLeft <= 0) {
                this.showGameOver();
            }
            
            // 检查关卡完成
            if (this.player.score >= this.getCurrentLevelConfig().targetScore) {
                this.showLevelComplete(false);
            }
            
            this.updateUI();
        }
    }
    
    getCurrentLevelConfig() {
        return LEVEL_CONFIG[this.level - 1];
    }
    
    updateUI() {
        document.getElementById('score').textContent = `分数: $${this.player.score}`;
        document.getElementById('money').textContent = `金钱: $${this.player.money}`;
        document.getElementById('level').textContent = `关卡: ${this.level}`;
        document.getElementById('target').textContent = `目标: $${this.getCurrentLevelConfig().targetScore}`;
        document.getElementById('time').textContent = `时间: ${this.timeLeft}秒`;
    }
    
    showLevelComplete(isAllComplete) {
        this.gameState = GAME_STATES.LEVEL_COMPLETE;
        
        const levelCompleteScreen = document.getElementById('level-complete-screen');
        const levelCompleteText = document.getElementById('level-complete-text');
        
        if (isAllComplete) {
            levelCompleteText.textContent = "恭喜！你已完成所有关卡！";
        } else {
            levelCompleteText.textContent = `关卡 ${this.level} 完成！`;
        }
    }
    
    showGameOver() {
        this.gameState = GAME_STATES.GAME_OVER;
        document.getElementById('final-score').textContent = `最终分数: $${this.player.score}`;
    }
    
    draw() {
        // 清除画布
        this.ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
        
        // 绘制背景
        if (this.images.background) {
            this.ctx.drawImage(this.images.background, 0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
        } else {
            // 默认背景
            this.ctx.fillStyle = '#1a3c5c';
            this.ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
            
            // 绘制地面
            this.ctx.fillStyle = '#8B4513';
            this.ctx.fillRect(0, CANVAS_HEIGHT - 100, CANVAS_WIDTH, 100);
        }
        
        // 绘制物品
        this.drawItems();
        
        // 绘制钩子和绳索
        this.drawHook();
        
        // 绘制玩家
        this.drawPlayer();
        
        // 绘制瞄准线（当钩子空闲时）
        if (this.hook.state === 'idle') {
            this.drawAimLine();
        }
    }
    
    drawItems() {
        for (const item of this.items) {
            const imageKey = item.type.replace('_', '-');
            
            if (this.images[imageKey]) {
                // 使用图片绘制物品
                this.ctx.drawImage(
                    this.images[imageKey],
                    item.position.x - item.size / 2,
                    item.position.y - item.size / 2,
                    item.size,
                    item.size
                );
            } else {
                // 使用颜色绘制物品
                this.ctx.fillStyle = item.color;
                this.ctx.beginPath();
                this.ctx.arc(item.position.x, item.position.y, item.size / 2, 0, Math.PI * 2);
                this.ctx.fill();
                this.ctx.strokeStyle = '#000';
                this.ctx.lineWidth = 2;
                this.ctx.stroke();
                
                // 如果是炸弹，绘制爆炸符号
                if (item.type === ITEM_TYPES.BOMB) {
                    this.ctx.fillStyle = '#000';
                    this.ctx.font = 'bold 16px Arial';
                    this.ctx.textAlign = 'center';
                    this.ctx.textBaseline = 'middle';
                    this.ctx.fillText('!', item.position.x, item.position.y);
                }
            }
            
            // 如果被钩住，显示价值
            if (item.caught) {
                this.ctx.fillStyle = '#FFF';
                this.ctx.font = '16px Arial';
                this.ctx.textAlign = 'center';
                this.ctx.textBaseline = 'middle';
                this.ctx.fillText(`$${item.value}`, item.position.x, item.position.y - item.size / 2 - 10);
            }
        }
    }
    
    drawHook() {
        const hookPos = this.getHookPosition();
        
        // 绘制绳索
        this.ctx.strokeStyle = '#8B4513';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(this.player.position.x, this.player.position.y);
        this.ctx.lineTo(hookPos.x, hookPos.y);
        this.ctx.stroke();
        
        // 绘制钩子
        if (this.images.hook) {
            // 旋转钩子图像
            this.ctx.save();
            this.ctx.translate(hookPos.x, hookPos.y);
            this.ctx.rotate(-this.hook.angle);
            this.ctx.drawImage(this.images.hook, -10, -10, 20, 20);
            this.ctx.restore();
        } else {
            // 使用颜色绘制钩子
            this.ctx.fillStyle = '#FF0000';
            this.ctx.beginPath();
            this.ctx.arc(hookPos.x, hookPos.y, 10, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.strokeStyle = '#000';
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
        }
        
        // 如果捕获了物品，绘制连接线
        if (this.hook.caughtItem) {
            this.ctx.strokeStyle = '#FFF';
            this.ctx.lineWidth = 1;
            this.ctx.beginPath();
            this.ctx.moveTo(hookPos.x, hookPos.y);
            this.ctx.lineTo(this.hook.caughtItem.position.x, this.hook.caughtItem.position.y);
            this.ctx.stroke();
        }
    }
    
    drawPlayer() {
        // 绘制玩家（矿工）
        this.ctx.fillStyle = '#8B4513';
        this.ctx.beginPath();
        this.ctx.arc(this.player.position.x, this.player.position.y, 30, 0, Math.PI * 2);
        this.ctx.fill();
        
        this.ctx.fillStyle = '#FFD700';
        this.ctx.beginPath();
        this.ctx.arc(this.player.position.x, this.player.position.y, 25, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 绘制矿工帽子
        this.ctx.fillStyle = '#8B0000';
        this.ctx.beginPath();
        this.ctx.arc(this.player.position.x, this.player.position.y - 15, 20, 0, Math.PI, true);
        this.ctx.fill();
    }
    
    drawAimLine() {
        // 绘制瞄准线
        const hookPos = this.getHookPosition();
        
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        this.ctx.lineWidth = 1;
        this.ctx.setLineDash([5, 5]);
        this.ctx.beginPath();
        this.ctx.moveTo(this.player.position.x, this.player.position.y);
        this.ctx.lineTo(hookPos.x, hookPos.y);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
    }
    
    gameLoop() {
        this.updateTime();
        
        if (this.gameState === GAME_STATES.PLAYING) {
            this.updateHook();
        }
        
        this.draw();
        
        setTimeout(() => {
            this.gameLoop();
        }, 1000 / FPS);
    }
}