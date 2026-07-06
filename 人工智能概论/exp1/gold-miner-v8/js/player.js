// 玩家系统
class Player {
    constructor() {
        this.score = 0;
        this.position = { x: CANVAS_WIDTH / 2, y: 100 };
    }
    
    addScore(points) {
        this.score += points;
        console.log(`增加分数: ${points}, 当前分数: ${this.score}`);
    }
    
    reset() {
        this.score = 0;
    }
    
    draw(ctx) {
        // 绘制玩家（矿工）
        ctx.fillStyle = '#8B4513';
        ctx.beginPath();
        ctx.arc(this.position.x, this.position.y, 30, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.fillStyle = '#FFD700';
        ctx.beginPath();
        ctx.arc(this.position.x, this.position.y, 25, 0, Math.PI * 2);
        ctx.fill();
        
        // 绘制矿工帽子
        ctx.fillStyle = '#8B0000';
        ctx.beginPath();
        ctx.arc(this.position.x, this.position.y - 15, 20, 0, Math.PI, true);
        ctx.fill();
        
        // 绘制矿工眼睛
        ctx.fillStyle = '#000';
        ctx.beginPath();
        ctx.arc(this.position.x - 8, this.position.y - 5, 3, 0, Math.PI * 2);
        ctx.arc(this.position.x + 8, this.position.y - 5, 3, 0, Math.PI * 2);
        ctx.fill();
        
        // 绘制矿工微笑
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(this.position.x, this.position.y + 5, 8, 0, Math.PI, false);
        ctx.stroke();
    }
}