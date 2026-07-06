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
        this.keysCollected = 0; // 收集的钥匙数量
        
        // 鼠标状态
        this.mouse = {
            x: CANVAS_WIDTH / 2,
            y: 100,
            isDown: false
        };
        
        // 图像资源
        this.background = null;
        this.backgroundLayer1 = null;
        this.backgroundLayer2 = null;
        
        // 初始化进度条
        this.createProgressUI();
        
        // 初始化
        this.init();
    }
    
    createProgressUI() {
        // 创建进度条容器
        const progressContainer = document.createElement('div');
        progressContainer.className = 'progress-container';
        progressContainer.id = 'progress-container';
        
        // 创建进度条
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        progressBar.id = 'progress-bar';
        
        progressContainer.appendChild(progressBar);
        
        // 创建关卡指示器
        const levelIndicator = document.createElement('div');
        levelIndicator.className = 'level-indicator';
        levelIndicator.id = 'level-indicator';
        levelIndicator.textContent = '关卡 1';
        
        // 添加到游戏容器
        const gameContainer = document.getElementById('game-container');
        gameContainer.appendChild(levelIndicator);
        gameContainer.appendChild(progressContainer);
    }
    
    updateProgressBar() {
        const currentLevelConfig = this.getCurrentLevelConfig();
        const progress = Math.min(100, (this.player.score / currentLevelConfig.targetScore) * 100);
        document.getElementById('progress-bar').style.width = `${progress}%`;
        document.getElementById('level-indicator').textContent = `关卡 ${this.level}`;
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
        
        this.backgroundLayer1 = await Utils.loadImage(
            'assets/images/background-layer1.png', 
            'transparent',
            {width: CANVAS_WIDTH, height: CANVAS_HEIGHT}
        );
        
        this.backgroundLayer2 = await Utils.loadImage(
            'assets/images/background-layer2.png', 
            'transparent',
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
            this.keysCollected = 0;
        }
        
        // 生成关卡物品
        this.itemManager.generateLevelItems(level);
        
        // 重置钩子
        this.hook.state = 'idle';
        this.hook.length = 0;
        this.hook.caughtItem = null;
        
        this.updateUI();
        this.updateProgressBar();
        
        // 隐藏所有屏幕
        this.hideAllScreens();
    }
    
    nextLevel() {
        if (this.level < LEVEL_CONFIG.length) {
            this.startLevel(this.level + 1);
        } else {
            // 所有关卡完成
            this.showGameWin();
        }
    }
    
    restartLevel() {
        this.startLevel(this.level);
    }
    
    showMenu() {
        this.gameState = GAME_STATES.MENU;
        this.showScreen('start-menu');
    }
    
    handleSpecialItem(item) {
        switch(item.type) {
            case ITEM_TYPES.TIME_EXTENDER:
                // 增加10秒时间
                this.timeLeft += 10;
                if (this.timeLeft > this.getCurrentLevelConfig().timeLimit) {
                    this.timeLeft = this.getCurrentLevelConfig().timeLimit;
                }
                Utils.showPopup('+10秒!', this.player.position.x, this.player.position.y - 50);
                break;
                
            case ITEM_TYPES.DYNAMITE:
                // 触发爆炸，清除周围物品
                const destroyedItems = this.itemManager.triggerDynamite(this.player.position);
                const totalValue = destroyedItems.reduce((sum, item) => sum + Math.max(0, item.value), 0);
                this.player.addScore(totalValue);
                Utils.showPopup(`炸毁 +$${totalValue}`, this.player.position.x, this.player.position.y - 50);
                break;
                
            case ITEM_TYPES.MAGNET:
                // 激活磁铁效果5秒
                this.itemManager.activateMagnet(this.player.position);
                Utils.showPopup('磁铁激活!', this.player.position.x, this.player.position.y - 50);
                break;
                
            case ITEM_TYPES.GOLD_KEY:
                // 收集钥匙
                this.keysCollected++;
                Utils.showPopup(`钥匙 x${this.keysCollected}`, this.player.position.x, this.player.position.y - 50);
                break;
                
            case ITEM_TYPES.BOMB:
                // 炸弹惩罚
                Utils.showPopup(`-$${Math.abs(item.value)}`, this.player.position.x, this.player.position.y - 50);
                break;
        }
    }
    
    update() {
        if (this.gameState === GAME_STATES.PLAYING) {
            // 更新物品
            this.itemManager.update();
            
            // 更新钩子
            this.hook.update(this.mouse);
            
            // 检查碰撞
            if (this.hook.state === 'throwing') {
                const caughtItem = this.itemManager.checkHookCollision(this.hook.getCircle());
                if (caughtItem) {
                    this.hook.catchItem(caughtItem);
                }
            }
            
            // 检查钩子是否回到玩家位置
            if (this.hook.state === 'pulling' && this.hook.length <= 100) {
                const caughtItem = this.hook.releaseItem();
                if (caughtItem) {
                    // 处理特殊物品效果
                    this.handleSpecialItem(caughtItem);
                    
                    // 只有有价值的物品才添加到分数
                    if (caughtItem.value > 0) {
                        this.player.addScore(caughtItem.value);
                    } else if (caughtItem.value < 0) {
                        this.player.addScore(caughtItem.value); // 炸弹扣分
                    }

                    this.itemManager.removeItem(caughtItem);
                    this.updateUI();
                    this.updateProgressBar();
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
        
        // 时间不足10秒时添加视觉提示
        const timeElement = document.getElementById('time');
        if (this.timeLeft <= 10) {
            timeElement.style.color = 'red';
            timeElement.style.animation = 'pulse 1s infinite alternate';
        } else {
            timeElement.style.color = 'white';
            timeElement.style.animation = 'none';
        }
        
        // 检查时间结束
        if (this.timeLeft <= 0 && this.gameState === GAME_STATES.PLAYING) {
            this.showGameOver();
        }
        
        this.updateUI();
    }
    
    checkGameState() {
        // 检查关卡完成
        if (this.player.score >= this.getCurrentLevelConfig().targetScore) {
            this.showLevelComplete();
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
    
    showLevelComplete() {
        this.gameState = GAME_STATES.LEVEL_COMPLETE;
        
        const levelCompleteScreen = document.getElementById('level-complete-screen');
        const levelCompleteText = document.getElementById('level-complete-text');
        
        let bonusText = '';
        if (this.keysCollected > 0) {
            const keyBonus = this.keysCollected * 200;
            this.player.addScore(keyBonus);
            bonusText = `钥匙奖励: +$${keyBonus}\n`;
        }
        
        const timeLeftBonus = this.timeLeft * 10;
        this.player.addScore(timeLeftBonus);
        bonusText += `剩余时间奖励: +$${timeLeftBonus}`;
        
        if (this.level < LEVEL_CONFIG.length) {
            levelCompleteText.textContent = `关卡 ${this.level} 完成！\n${bonusText}\n总分: $${this.player.score}`;
        } else {
            levelCompleteText.textContent = `恭喜！你已完成所有关卡！\n${bonusText}\n总分: $${this.player.score}`;
        }
        
        this.hideAllScreens();
        levelCompleteScreen.classList.remove('hidden');
    }
    
    showGameOver() {
        this.gameState = GAME_STATES.GAME_OVER;
        document.getElementById('final-score').textContent = `最终分数: $${this.player.score}`;
        
        this.hideAllScreens();
        document.getElementById('game-over-screen').classList.remove('hidden');
    }
    
    showGameWin() {
        this.gameState = GAME_STATES.GAME_WIN;
        document.getElementById('win-score').textContent = `最终分数: $${this.player.score}`;
        
        this.hideAllScreens();
        document.getElementById('game-win-screen').classList.remove('hidden');
    }
    
    hideAllScreens() {
        const screens = document.querySelectorAll('.screen');
        screens.forEach(screen => {
            screen.classList.add('hidden');
        });
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
        }
        
        // 绘制背景层
        if (this.backgroundLayer1) {
            this.ctx.drawImage(this.backgroundLayer1, 0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
        }
        
        // 绘制物品
        this.itemManager.draw(this.ctx);
        
        // 绘制玩家
        this.player.draw(this.ctx);
        
        // 绘制钩子和瞄准线
        this.hook.draw(this.ctx);
        this.hook.drawAimLine(this.ctx, this.mouse);
        
        // 绘制前景层
        if (this.backgroundLayer2) {
            this.ctx.drawImage(this.backgroundLayer2, 0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
        }
        
        // 绘制钥匙数量
        if (this.keysCollected > 0) {
            this.ctx.fillStyle = '#FFD700';
            this.ctx.font = '20px Arial';
            this.ctx.textAlign = 'left';
            this.ctx.textBaseline = 'top';
            this.ctx.fillText(`🔑 x${this.keysCollected}`, 20, 65);
        }
    }
    
    gameLoop() {
        this.update();
        this.draw();
        
        requestAnimationFrame(() => this.gameLoop());
    }
}