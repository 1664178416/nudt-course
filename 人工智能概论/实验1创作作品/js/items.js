// 物品系统
class Item {
    constructor(type, position) {
        this.type = type;
        this.position = position;
        this.baseValue = ITEM_PROPERTIES[type].value;
        this.value = this.calculateValue(); // 计算最终价值（处理特殊物品）
        this.weight = ITEM_PROPERTIES[type].weight;
        this.size = ITEM_PROPERTIES[type].size;
        this.color = ITEM_PROPERTIES[type].color;
        this.icon = ITEM_PROPERTIES[type].icon;
        this.caught = false;
        this.image = null;
        this.pulseTimer = 0;
        this.pulseState = 0;
    }
    
    // 计算物品价值（处理特殊物品）
    calculateValue() {
        switch(this.type) {
            case ITEM_TYPES.TREASURE_BOX:
                // 宝箱有随机价值
                return Utils.randomInt(500, 2000);
            default:
                return this.baseValue;
        }
    }
    
    async loadImage() {
        const imagePaths = {
            [ITEM_TYPES.GOLD_SMALL]: 'assets/images/gold-small.png',
            [ITEM_TYPES.GOLD_MEDIUM]: 'assets/images/gold-medium.png',
            [ITEM_TYPES.GOLD_LARGE]: 'assets/images/gold-large.png',
            [ITEM_TYPES.STONE_SMALL]: 'assets/images/stone-small.png',
            [ITEM_TYPES.STONE_MEDIUM]: 'assets/images/stone-medium.png',
            [ITEM_TYPES.STONE_LARGE]: 'assets/images/stone-large.png',
            [ITEM_TYPES.DIAMOND]: 'assets/images/diamond.png',
            [ITEM_TYPES.BOMB]: 'assets/images/bomb.png',
            [ITEM_TYPES.TREASURE_BOX]: 'assets/images/treasure-box.png',
            [ITEM_TYPES.GOLD_KEY]: 'assets/images/gold-key.png',
            [ITEM_TYPES.TIME_EXTENDER]: 'assets/images/time-extender.png',
            [ITEM_TYPES.DYNAMITE]: 'assets/images/dynamite.png',
            [ITEM_TYPES.MAGNET]: 'assets/images/magnet.png',
            [ITEM_TYPES.SUPER_GOLD]: 'assets/images/super-gold.png'
        };
        
        this.image = await Utils.loadImage(
            imagePaths[this.type], 
            this.color,
            {width: this.size, height: this.size}
        );
    }
    
    update() {
        // 特殊物品动画效果
        if ([ITEM_TYPES.DIAMOND, ITEM_TYPES.SUPER_GOLD, ITEM_TYPES.GOLD_KEY].includes(this.type)) {
            this.pulseTimer++;
            if (this.pulseTimer % 30 === 0) {
                this.pulseState = (this.pulseState + 1) % 2;
            }
        }
    }
    
    draw(ctx) {
        // 保存当前状态
        ctx.save();
        
        // 特殊物品动画
        if (this.pulseState === 1) {
            ctx.globalAlpha = 0.8;
        }
        
        if (this.image) {
            // 使用图片绘制物品
            ctx.drawImage(
                this.image,
                this.position.x - this.size / 2,
                this.position.y - this.size / 2,
                this.size,
                this.size
            );
        } else {
            // 使用颜色和图标绘制物品
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.position.x, this.position.y, this.size / 2, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // 绘制图标
            ctx.fillStyle = '#FFF';
            ctx.font = `${this.size * 0.8}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(this.icon, this.position.x, this.position.y);
        }
        
        // 恢复状态
        ctx.restore();
        
        // 如果被钩住，显示价值
        if (this.caught) {
            ctx.fillStyle = '#FFF';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(`$${this.value}`, this.position.x, this.position.y - this.size / 2 - 10);
        }
    }
    
    getCircle() {
        return {
            x: this.position.x,
            y: this.position.y,
            radius: this.size / 2
        };
    }
}

// 物品管理器
class ItemManager {
    constructor() {
        this.items = [];
        this.level = 1;
        this.maxItems = 0;
        this.itemsCollected = 0;
        this.magnetActive = false;
        this.magnetPosition = null;
        this.magnetRadius = 200;
    }
    
    async generateLevelItems(level) {
        this.items = [];
        this.level = level;
        this.itemsCollected = 0;
        this.magnetActive = false;
        const levelConfig = LEVEL_CONFIG[level - 1];
        this.maxItems = levelConfig.itemCount;
        
        // 创建物品
        for (let i = 0; i < this.maxItems; i++) {
            const itemType = this.getRandomItemType(level);
            const position = this.getValidPosition();
            const item = new Item(itemType, position);
            await item.loadImage();
            this.items.push(item);
        }
        
        console.log(`生成了 ${this.items.length} 个物品`);
    }
    
    getRandomItemType(level) {
        const levelConfig = LEVEL_CONFIG[level - 1];
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
            const newCircle = {
                x: x,
                y: y,
                radius: 25
            };
            
            for (const item of this.items) {
                const itemCircle = item.getCircle();
                if (Utils.checkCircleCollision(newCircle, itemCircle)) {
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
    
    async addNewItem() {
        // 总是补充新物品，确保有足够的物品
        if (this.items.length < this.maxItems * 1.5) { // 允许超过初始数量50%
            const itemType = this.getRandomItemType(this.level);
            const position = this.getValidPosition();
            const item = new Item(itemType, position);
            await item.loadImage();
            this.items.push(item);
        }
    }
    
    checkHookCollision(hookCircle) {
        for (const item of this.items) {
            if (!item.caught && Utils.checkCircleCollision(hookCircle, item.getCircle())) {
                console.log(`捕获物品: ${item.type}, 价值: ${item.value}`);
                item.caught = true;
                return item;
            }
        }
        return null;
    }
    
    activateMagnet(position, duration = 5000) {
        this.magnetActive = true;
        this.magnetPosition = position;
        
        // 5秒后关闭磁铁效果
        setTimeout(() => {
            this.magnetActive = false;
            this.magnetPosition = null;
        }, duration);
    }
    
    updateMagnetEffect() {
        if (this.magnetActive && this.magnetPosition) {
            for (const item of this.items) {
                if (!item.caught) {
                    const distance = Utils.distance(item.position, this.magnetPosition);
                    if (distance < this.magnetRadius) {
                        // 计算吸引力
                        const angle = Math.atan2(
                            this.magnetPosition.x - item.position.x,
                            this.magnetPosition.y - item.position.y
                        );
                        const force = (1 - distance / this.magnetRadius) * 2;
                        
                        // 移动物品
                        item.position.x += Math.sin(angle) * force;
                        item.position.y += Math.cos(angle) * force;
                    }
                }
            }
        }
    }
    
    triggerDynamite(position) {
        const explosionRadius = 150;
        const destroyedItems = [];
        
        // 找到爆炸范围内的物品
        for (const item of this.items) {
            if (!item.caught) {
                const distance = Utils.distance(item.position, position);
                if (distance < explosionRadius) {
                    destroyedItems.push(item);
                    
                    // 显示爆炸效果
                    Utils.showPopup('💥', item.position.x, item.position.y);
                }
            }
        }
        
        // 移除被炸毁的物品
        this.items = this.items.filter(item => !destroyedItems.includes(item));
        
        // 补充新物品
        destroyedItems.forEach(async () => {
            await this.addNewItem();
        });
        
        return destroyedItems;
    }
    
    async removeItem(item) {
        this.items = this.items.filter(i => i !== item);
        this.itemsCollected++;
        
        // 每次移除物品后都补充一个新物品
        await this.addNewItem();
    }
    
    update() {
        // 更新所有物品
        this.items.forEach(item => item.update());
        
        // 处理磁铁效果
        this.updateMagnetEffect();
    }
    
    draw(ctx) {
        // 绘制所有物品
        this.items.forEach(item => item.draw(ctx));
        
        // 绘制磁铁范围（调试用）
        if (this.magnetActive && this.magnetPosition) {
            ctx.beginPath();
            ctx.arc(
                this.magnetPosition.x, 
                this.magnetPosition.y, 
                this.magnetRadius, 
                0, 
                Math.PI * 2
            );
            ctx.strokeStyle = 'rgba(0, 0, 205, 0.3)';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.setLineDash([]);
        }
    }
}