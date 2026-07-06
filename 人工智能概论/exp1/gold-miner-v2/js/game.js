// 游戏主类
class GoldMinerGame {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        
        // 游戏状态
        this.gameState = GAME_STATES.MENU;
        this.player = new Player();
        this.hook = new Hook(this.player.position);
        this.itemManager = new ItemManager();
        
        // 游戏参数
        this.level = 1;
        this.timeLeft = 0;
        this.levelStartTime = 0;
        
        // 鼠标状态
        this.mouse = {
            x: CANVAS_WIDTH / 2,
            y: 100,
            isDown: false
        };
        
        // 图像资源
        this.background = null;
        
        // 初始化
        this.init();
    }
    
    async init() {
        // 加载资源
        await this.loadResources();
        
        // 设置事件监听器
        this.setupEventListeners();
        
        // 开始游戏循环
        this.gameLoop();
    }
    
    async loadResources() {
        this.background = await Utils.loadImage(
            'assets/images/background.png', 
            '#1a3c5c',
            {width: CANVAS_WIDTH, height: CANVAS_HEIGHT}
        );
        
        await this.hook.loadImage();
    }
    
    setupEventListeners() {
        // 鼠标移动事件
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouse.x = e.clientX - rect.left;
            this.mouse.y = e.clientY - rect.top;
        });
        
        // 鼠标点击事件
        this.canvas.addEventListener('mousedown', (e) => {
            if (e.button === 0) { // 左键
                this.mouse.isDown = true;
                
                if (this.gameState === GAME_STATES.PLAYING) {
                    this.hook.throw();
                }
            }
        });
        
        this.canvas.addEventListener('mouseup', (e) => {
            if (e.button === 0) {
                this.mouse.isDown = false;
            }
        });
    }
    
    startLevel(level) {
        this.level = level;
        this.gameState = GAME_STATES.PLAYING;
        this.timeLeft = this.getCurrentLevelConfig().timeLimit;
        this.levelStartTime = Date.now();
        
        // 重置玩家分数（如果是从菜单开始）
        if (level === 1) {
            this.player.reset();
        }
        
        // 生成关卡物品
        this.itemManager.generateLevelItems(level);
        
        // 重置钩子
        this.hook.state = 'idle';
        this.hook.length = 0;
        this.hook.caughtItem = null;
        
        this.updateUI();
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
    }
    
    update() {
        if (this.gameState === GAME_STATES.PLAYING) {
            // 更新钩子
            this.hook.update(this.mouse);
            
            // 检查碰撞
            if (this.hook.state === 'throwing') {
                const caughtItem = this.itemManager.checkHookCollision(this.hook.getRect());
                if (caughtItem) {
                    this.hook.catchItem(caughtItem);
                }
            }
            
            // 检查钩子是否回到玩家位置
            if (this.hook.state === 'pulling' && this.hook.length <= 0) {
                const caughtItem = this.hook.releaseItem();
                if (caughtItem) {
                    this.player.addScore(caughtItem.value);
                    this.itemManager.removeItem(caughtItem);
                    this.updateUI();
                }
            }
            
            // 更新时间
            this.updateTime();
            
            // 检查游戏状态
            this.checkGameState();
        }
    }
    
    updateTime() {
        const elapsedSeconds = Math.floor((Date.now() - this.levelStartTime) / 1000);
        this.timeLeft = Math.max(0, this.getCurrentLevelConfig().timeLimit - elapsedSeconds);
        
        // 检查时间结束
        if (this.timeLeft <= 0) {
            this.showGameOver();
        }
        
        this.updateUI();
    }
    
    checkGameState() {
        // 检查关卡完成
        if (this.player.score >= this.getCurrentLevelConfig().targetScore) {
            this.showLevelComplete(false);
        }
    }
    
    getCurrentLevelConfig() {
        return LEVEL_CONFIG[this.level - 1];
    }
    
    updateUI() {
        document.getElementById('score').textContent = `分数: $${this.player.score}`;
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
        if (this.background) {
            this.ctx.drawImage(this.background, 0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
        } else {
            // 默认背景
            this.ctx.fillStyle = '#1a3c5c';
            this.ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
            
            // 绘制地面
            this.ctx.fillStyle = '#8B4513';
            this.ctx.fillRect(0, CANVAS_HEIGHT - 100, CANVAS_WIDTH, 100);
        }
        
        // 绘制物品
        this.itemManager.draw(this.ctx);
        
        // 绘制玩家
        this.player.draw(this.ctx);
        
        // 绘制钩子和瞄准线
        this.hook.draw(this.ctx);
        this.hook.drawAimLine(this.ctx, this.mouse);
    }
    
    gameLoop() {
        this.update();
        this.draw();
        
        setTimeout(() => {
            this.gameLoop();
        }, 1000 / FPS);
    }
}