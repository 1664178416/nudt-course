// 菜单系统
class MenuSystem {
    constructor(game) {
        this.game = game;
        this.setupMenuEventListeners();
    }
    
    setupMenuEventListeners() {
        // 开始菜单选项
        document.querySelectorAll('.menu-option[data-level]').forEach(option => {
            option.addEventListener('click', () => {
                const level = parseInt(option.getAttribute('data-level'));
                this.startLevel(level);
            });
        });
        
        // 下一关按钮
        document.getElementById('next-level-btn').addEventListener('click', () => {
            this.game.nextLevel();
            this.hideScreen('level-complete-screen');
        });
        
        // 返回菜单按钮（关卡完成界面）
        document.getElementById('back-to-menu-btn').addEventListener('click', () => {
            this.showMenu();
            this.hideScreen('level-complete-screen');
        });
        
        // 重新开始按钮
        document.getElementById('restart-btn').addEventListener('click', () => {
            this.game.restartLevel();
            this.hideScreen('game-over-screen');
        });
        
        // 返回菜单按钮（游戏结束界面）
        document.getElementById('menu-btn').addEventListener('click', () => {
            this.showMenu();
            this.hideScreen('game-over-screen');
        });
        
        // 重新开始按钮（游戏胜利界面）
        document.getElementById('win-restart-btn').addEventListener('click', () => {
            this.game.restartLevel();
            this.hideScreen('game-win-screen');
        });
        
        // 返回菜单按钮（游戏胜利界面）
        document.getElementById('win-menu-btn').addEventListener('click', () => {
            this.showMenu();
            this.hideScreen('game-win-screen');
        });
    }
    
    startLevel(level) {
        this.game.startLevel(level);
        this.hideScreen('start-menu');
    }
    
    showMenu() {
        this.game.showMenu();
        this.showScreen('start-menu');
    }
    
    showScreen(screenId) {
        document.getElementById(screenId).classList.remove('hidden');
    }
    
    hideScreen(screenId) {
        document.getElementById(screenId).classList.add('hidden');
    }
}