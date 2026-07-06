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
}