// 钩子系统
class Hook {
    constructor(playerPosition) {
        this.playerPosition = playerPosition;
        this.angle = 0; // 当前角度（弧度）
        this.length = 0;
        this.maxLength = 400;
        this.speed = 5;
        this.state = 'idle'; // idle, throwing, pulling, caught
        this.caughtItem = null;
        this.image = null;
    }
    
    async loadImage() {
        this.image = await Utils.loadImage(
            'assets/images/hook.png', 
            '#FF0000',
            {width: 20, height: 20}
        );
    }
    
    update(mousePosition) {
        // 更新钩子角度（仅当钩子空闲时）
        if (this.state === 'idle') {
            this.updateAngle(mousePosition);
        }
        
        // 根据状态更新钩子
        switch(this.state) {
            case 'throwing':
                this.updateThrowing();
                break;
                
            case 'pulling':
                this.updatePulling();
                break;
        }
    }
    
    updateAngle(mousePosition) {
        // 计算钩子角度（从玩家位置指向鼠标位置）
        const dx = mousePosition.x - this.playerPosition.x;
        const dy = mousePosition.y - this.playerPosition.y;
        this.angle = Math.atan2(dx, dy);
    }
    
    updateThrowing() {
        this.length += this.speed * 2;
        
        // 如果达到最大长度或超出屏幕，开始收回
        const hookPos = this.getPosition();
        if (this.length > this.maxLength || 
            hookPos.y < 0 || hookPos.x < 0 || hookPos.x > CANVAS_WIDTH) {
            this.state = 'pulling';
        }
    }
    
    updatePulling() {
        if (this.caughtItem) {
            // 如果有物品，减慢收回速度
            this.length -= this.speed * (1 / this.caughtItem.weight);
            
            // 更新被捕获物品的位置
            this.caughtItem.position = this.getPosition();
        } else {
            this.length -= this.speed * 2;
        }
        
        // 如果回到玩家位置，回到空闲状态
        if (this.length <= 0) {
            this.length = 0;
            this.state = 'idle';
        }
    }
    
    throw() {
        if (this.state === 'idle') {
            this.state = 'throwing';
            return true;
        }
        return false;
    }
    
    getPosition() {
        return {
            x: this.playerPosition.x + this.length * Math.sin(this.angle),
            y: this.playerPosition.y + this.length * Math.cos(this.angle)
        };
    }
    
    getRect() {
        const pos = this.getPosition();
        return {
            x: pos.x - 10,
            y: pos.y - 10,
            width: 20,
            height: 20
        };
    }
    
    catchItem(item) {
        this.caughtItem = item;
        this.state = 'pulling';
    }
    
    releaseItem() {
        const item = this.caughtItem;
        this.caughtItem = null;
        return item;
    }
    
    draw(ctx) {
        const hookPos = this.getPosition();
        
        // 绘制绳索
        ctx.strokeStyle = '#8B4513';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(this.playerPosition.x, this.playerPosition.y);
        ctx.lineTo(hookPos.x, hookPos.y);
        ctx.stroke();
        
        // 绘制钩子
        if (this.image) {
            // 旋转钩子图像
            ctx.save();
            ctx.translate(hookPos.x, hookPos.y);
            ctx.rotate(-this.angle);
            ctx.drawImage(this.image, -10, -10, 20, 20);
            ctx.restore();
        } else {
            // 使用颜色绘制钩子
            ctx.fillStyle = '#FF0000';
            ctx.beginPath();
            ctx.arc(hookPos.x, hookPos.y, 10, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 2;
            ctx.stroke();
        }
        
        // 如果捕获了物品，绘制连接线
        if (this.caughtItem) {
            ctx.strokeStyle = '#FFF';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(hookPos.x, hookPos.y);
            ctx.lineTo(this.caughtItem.position.x, this.caughtItem.position.y);
            ctx.stroke();
        }
    }
    
    drawAimLine(ctx, mousePosition) {
        if (this.state === 'idle') {
            // 绘制瞄准线
            const hookPos = this.getPosition();
            
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(this.playerPosition.x, this.playerPosition.y);
            ctx.lineTo(hookPos.x, hookPos.y);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // 绘制鼠标位置指示器
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.beginPath();
            ctx.arc(mousePosition.x, mousePosition.y, 5, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}