const arrayContainer = document.getElementById('array-container');
const startButton = document.getElementById('start-button');

let array = Array.from({ length: 20 }, () => Math.floor(Math.random() * 100));
drawArray();

startButton.addEventListener('click', async () => {
    // 禁用按钮防止重复点击
    startButton.disabled = true;
    
    // 复制一份原始数组进行排序
    const arr = array.slice();
    await bubbleSortVisualization(arr);
    
    // 排序完成后重新启用按钮
    startButton.disabled = false;
});

function drawArray(arr = array) {
    arrayContainer.innerHTML = '';
    arr.forEach(value => {
        const bar = document.createElement('div');
        bar.style.height = `${value}px`;
        bar.classList.add('bar');
        arrayContainer.appendChild(bar);
    });
}

async function bubbleSortVisualization(arr) {
    const bars = document.querySelectorAll('.bar');
    const len = arr.length;
    
    for (let i = 0; i < len; i++) {
        for (let j = 0; j < len - i - 1; j++) {
            // 高亮当前正在比较的两个条形图
            bars[j].style.backgroundColor = 'red';
            bars[j + 1].style.backgroundColor = 'red';
            
            // 等待一小段时间以便观察
            await sleep(300);
            
            if (arr[j] > arr[j + 1]) {
                // 交换数组中的值
                [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
                
                // 更新条形图高度
                bars[j].style.height = `${arr[j]}px`;
                bars[j + 1].style.height = `${arr[j + 1]}px`;
            }
            
            // 恢复颜色
            bars[j].style.backgroundColor = 'teal';
            bars[j + 1].style.backgroundColor = 'teal';
        }
        // 标记已排序的元素
        bars[len - i - 1].style.backgroundColor = 'green';
    }
    
    // 更新全局数组
    array = arr;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}