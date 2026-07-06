// 物品系统
class Item {
    constructor(type, position) {
        this.type = type;
        this.position = position;
        this.value = ITEM_PROPERTIES[type].value;
        this.weight = ITEM_PROPERTIES[type].weight;
        this.size = ITEM_PROPERTIES[type].size;
        this.color = ITEM_PROPERTIES[type].color;
        this.caught = false;
        this.image = null;
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
            [ITEM_TYPES.BOMB]: 'assets/images/bomb.png'
        };
        
        this.image = await Utils.loadImage(
            imagePaths[this.type], 
            this.color,
            {width: this.size, height: this.size}
        );
    }
    
    draw(ctx) {
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
            // 使用颜色绘制物品
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.position.x, this.position.y, this.size / 2, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // 特殊物品的标识
            if (this.type === ITEM_TYPES.BOMB) {
                // 炸弹绘制"X"标记
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(this.position.x - this.size/3, this.position.y - this.size/3);
                ctx.lineTo(this.position.x + this.size/3, this.position.y + this.size/3);
                ctx.moveTo(this.position.x + this.size/3, this.position.y - this.size/3);
                ctx.lineTo(this.position.x - this.size/3, this.position.y + this.size/3);
                ctx.stroke();
            } else if (this.type === ITEM_TYPES.DIAMOND) {
                // 钻石绘制特殊形状
                ctx.fillStyle = '#FFFFFF';
                ctx.font = 'bold 12px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('💎', this.position.x, this.position.y);
            } else if (this.type.includes('stone')) {
                // 石头绘制纹理
                ctx.fillStyle = '#606060';
                ctx.beginPath();
                ctx.arc(this.position.x - 3, this.position.y - 3, 3, 0, Math.PI * 2);
                ctx.arc(this.position.x + 4, this.position.y + 2, 4, 0, Math.PI * 2);
                ctx.arc(this.position.x - 2, this.position.y + 4, 3, 0, Math.PI * 2);
                ctx.fill();
            } else if (this.type.includes('gold')) {
                // 黄金绘制光泽
                ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
                ctx.beginPath();
                ctx.arc(this.position.x - this.size/4, this.position.y - this.size/4, this.size/5, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        
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
    }
    
    async generateLevelItems(level) {
        this.items = [];
        this.level = level;
        this.itemsCollected = 0;
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
        console.log(`物品类型: ${this.items.map(item => item.type)}`);
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
        // 如果物品数量少于最大数量，添加一个新物品
        if (this.items.length < this.maxItems) {
            const itemType = this.getRandomItemType(this.level);
            const position = this.getValidPosition();
            const item = new Item(itemType, position);
            await item.loadImage();
            this.items.push(item);
            console.log(`补充了新物品: ${itemType}`);
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
    
    removeItem(item) {
        this.items = this.items.filter(i => i !== item);
        this.itemsCollected++;
        
        // 每当收集一个物品，有30%的概率补充一个新物品
        if (Math.random() < 0.3) {
            this.addNewItem();
        }
    }
    
    draw(ctx) {
        for (const item of this.items) {
            item.draw(ctx);
        }
    }
}