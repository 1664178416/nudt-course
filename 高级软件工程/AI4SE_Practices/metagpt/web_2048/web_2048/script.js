/**
 * @fileoverview UI rendering and main application entry point for 2048 game.
 * Follows Google JavaScript Style Guide with modular, maintainable code.
 * @module script
 */

import { Game } from './game.js';
import { InputHandler } from './input-handler.js';

/**
 * UI class responsible for all DOM manipulation and visual updates.
 */
class UI {
  /**
   * Creates a UI instance bound to a Game instance.
   * @param {Game} game - The game instance to render.
   */
  constructor(game) {
    /** @private {Game} */
    this.game_ = game;

    /** @private {HTMLElement} */
    this.gridContainer_ = document.getElementById('grid-container');

    /** @private {HTMLElement} */
    this.scoreElement_ = document.getElementById('current-score');

    /** @private {HTMLElement} */
    this.bestScoreElement_ = document.getElementById('best-score');

    /** @private {HTMLElement} */
    this.gameOverMsg_ = document.getElementById('game-over-msg');

    /** @private {HTMLElement} */
    this.winMsg_ = document.getElementById('win-msg');

    /** @private {Object<string, HTMLElement>} */
    this.tileElements_ = {};

    // Initialize empty grid structure
    this.initializeGrid_();
  }

  /**
   * Initializes the empty grid cells in the DOM.
   * @private
   */
  initializeGrid_() {
    this.gridContainer_.innerHTML = '';
    for (let row = 0; row < 4; row++) {
      for (let col = 0; col < 4; col++) {
        const cell = document.createElement('div');
        cell.className = 'grid-cell';
        cell.dataset.row = row.toString();
        cell.dataset.col = col.toString();
        this.gridContainer_.appendChild(cell);
      }
    }
  }

  /**
   * Updates the entire game grid based on current game state.
   * Removes all existing tiles and recreates them from current grid state.
   */
  updateGrid() {
    const grid = this.game_.getGrid();
    
    // 1. Remove all existing tile elements
    Object.values(this.tileElements_).forEach(tile => tile.remove());
    this.tileElements_ = {};
    
    // 2. Create new tile elements based on current grid
    for (let row = 0; row < 4; row++) {
      for (let col = 0; col < 4; col++) {
        const value = grid[row][col];
        if (value !== 0) {
          this.createTile_(row, col, value);
        }
      }
    }
  }

  /**
   * Creates a new tile element at specified position.
   * @param {number} row - Row index (0-3).
   * @param {number} col - Column index (0-3).
   * @param {number} value - Tile value (2, 4, 8, etc.).
   * @private
   */
  createTile_(row, col, value) {
    const tileKey = `${row}-${col}`;
    const tileElement = document.createElement('div');
    
    // Set tile class and content
    tileElement.className = `tile ${this.getTileClass_(value)}`;
    tileElement.textContent = value;
    
    // Position the tile using CSS variables
    const computedStyle = getComputedStyle(document.documentElement);
    const tileSize = parseInt(computedStyle.getPropertyValue('--tile-size'), 10) || 100;
    const gridGap = parseInt(computedStyle.getPropertyValue('--grid-gap'), 10) || 15;
    
    tileElement.style.left = `${col * (tileSize + gridGap) + gridGap}px`;
    tileElement.style.top = `${row * (tileSize + gridGap) + gridGap}px`;
    
    // Add appear animation for new tiles
    tileElement.classList.add('tile-appear');
    
    // Calculate animation duration from CSS custom property
    // --transition-duration-normal defaults to 0.15s (150ms)
    const transitionDuration = getComputedStyle(document.documentElement)
      .getPropertyValue('--transition-duration-normal')
      .trim();
    const appearDuration = transitionDuration ? 
      parseFloat(transitionDuration) * 1000 : 150; // Default to 150ms
    
    setTimeout(() => {
      tileElement.classList.remove('tile-appear');
    }, appearDuration);
    
    this.gridContainer_.appendChild(tileElement);
    this.tileElements_[tileKey] = tileElement;
  }

  /**
   * Gets the CSS class for a tile based on its value.
   * For values up to 2048, returns 'tile-{value}'.
   * For larger values, returns 'tile-super'.
   * @param {number} value - Tile value.
   * @return {string} CSS class name.
   * @private
   */
  getTileClass_(value) {
    if (value <= 2048) {
      return `tile-${value}`;
    }
    return 'tile-super';
  }

  /**
   * Updates score displays including current score and best score.
   * Highlights best score if it was just updated.
   */
  updateScores() {
    const currentScore = this.game_.getScore();
    const bestScore = this.game_.getBestScore();
    
    this.scoreElement_.textContent = currentScore.toLocaleString();
    this.bestScoreElement_.textContent = bestScore.toLocaleString();
    
    // Highlight best score if current score equals best score (and not zero)
    if (currentScore === bestScore && currentScore > 0) {
      this.bestScoreElement_.parentElement.classList.add('new-best');
      setTimeout(() => {
        this.bestScoreElement_.parentElement.classList.remove('new-best');
      }, 500);
    }
  }

  /**
   * Shows the game over message overlay.
   * Note: InputHandler should call this when gameOver condition is detected.
   */
  showGameOverMessage() {
    this.gameOverMsg_.classList.remove('hidden');
    this.gameOverMsg_.classList.add('visible');
  }

  /**
   * Hides the game over message overlay.
   * Note: InputHandler should call this on game restart.
   */
  hideGameOverMessage() {
    this.gameOverMsg_.classList.remove('visible');
    this.gameOverMsg_.classList.add('hidden');
  }

  /**
   * Shows the win message overlay.
   * Note: InputHandler should call this when win condition is detected.
   */
  showWinMessage() {
    this.winMsg_.classList.remove('hidden');
    this.winMsg_.classList.add('visible');
  }

  /**
   * Hides the win message overlay.
   * Note: InputHandler should call this on game restart.
   */
  hideWinMessage() {
    this.winMsg_.classList.remove('visible');
    this.winMsg_.classList.add('hidden');
  }

  /**
   * Plays a visual animation when player wins.
   * Note: InputHandler should call this when win condition is detected,
   * typically after showWinMessage().
   */
  showWinAnimation() {
    // Pulse animation on all tiles
    Object.values(this.tileElements_).forEach(tile => {
      tile.classList.add('tile-pulse');
      setTimeout(() => {
        tile.classList.remove('tile-pulse');
      }, 1000);
    });
  }

  /**
   * Plays a shake animation to indicate invalid move.
   * Note: InputHandler should call this when move is invalid.
   */
  showInvalidMoveAnimation() {
    this.gridContainer_.classList.add('shake');
    setTimeout(() => {
      this.gridContainer_.classList.remove('shake');
    }, 300);
  }
}

/**
 * Main application class that initializes and coordinates game components.
 */
class Main {
  /**
   * Creates and initializes the 2048 game application.
   */
  constructor() {
    /** @private {Game} */
    this.game_ = new Game();

    /** @private {UI} */
    this.ui_ = new UI(this.game_);

    /** @private {InputHandler} */
    this.inputHandler_ = new InputHandler(this.game_, this.ui_);

    // Perform initial render
    this.ui_.updateGrid();
    this.ui_.updateScores();
  }

  /**
   * Initializes the application (alternative constructor pattern).
   * @return {Main} The initialized Main instance.
   */
  static init() {
    return new Main();
  }
}

// Initialize the game when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
  Main.init();
});

export { UI, Main };
