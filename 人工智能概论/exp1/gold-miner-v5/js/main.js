// 程序入口
window.addEventListener('load', () => {
    const canvas = document.getElementById('game-canvas');
    const game = new GoldMinerGame(canvas);
    const menu = new MenuSystem(game);
});