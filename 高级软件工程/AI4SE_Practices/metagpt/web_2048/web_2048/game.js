/**
 * @fileoverview Main game state management for 2048 game.
 * @class Game
 */

import { GameLogic } from './game-logic.js';

/**
 * Main game class managing grid state, score, and game status.
 */
class Game {
  /**
   * Creates a new Game instance and initializes the grid.
   * @constructor
   */
  constructor() {
    /** @private {number[][]} 4x4 grid where 0 represents empty cell */
    this.grid_ = [];

    /** @private {number} Current game score */
    this.score_ = 0;

    /** @private {number} Best score from localStorage */
    this.bestScore_ = 0;

    /** @private {boolean} Whether game is over */
    this.gameOver_ = false;

    /** @private {boolean} Whether player has won (reached 2048) */
    this.won_ = false;

    /** @private {string} LocalStorage key for best score */
    this.STORAGE_KEY_ = 'bestScore';

    // Load best score and set up initial game state
    this.loadBestScore_();
    this.resetGame();
  }

  /**
   * Initializes an empty 4x4 grid.
   * @private
   */
  initializeGrid_() {
    this.grid_ = Array.from({ length: 4 }, () => Array(4).fill(0));
  }

  /**
   * Loads best score from localStorage.
   * @private
   */
  loadBestScore_() {
    const stored = localStorage.getItem(this.STORAGE_KEY_);
    this.bestScore_ = stored ? parseInt(stored, 10) : 0;
  }

  /**
   * Saves best score to localStorage.
   * @private
   */
  saveBestScore_() {
    localStorage.setItem(this.STORAGE_KEY_, this.bestScore_.toString());
  }

  /**
   * Finds all empty cells in the grid.
   * @return {Array<{row: number, col: number}>} List of empty cell positions.
   * @private
   */
  findEmptyCells_() {
    const emptyCells = [];
    for (let row = 0; row < 4; row++) {
      for (let col = 0; col < 4; col++) {
        if (this.grid_[row][col] === 0) {
          emptyCells.push({ row, col });
        }
      }
    }
    return emptyCells;
  }

  /**
   * Adds a random tile (2 or 4) to an empty cell.
   * @return {Array<number>|null} Position [row, col, value] of added tile,
   *     or null if no empty cells.
   */
  addRandomTile() {
    const emptyCells = this.findEmptyCells_();
    if (emptyCells.length === 0) {
      return null;
    }

    const randomIndex = Math.floor(Math.random() * emptyCells.length);
    const { row, col } = emptyCells[randomIndex];
    // 90% chance for 2, 10% chance for 4
    const value = Math.random() < 0.9 ? 2 : 4;

    this.grid_[row][col] = value;
    return [row, col, value];
  }

  /**
   * Executes a move in the specified direction.
   * @param {string} direction - One of 'up', 'down', 'left', 'right'.
   * @return {boolean} True if the move was successful and changed the grid.
   */
  move(direction) {
    if (this.gameOver_ || this.won_) {
      return false;
    }

    const gameLogic = new GameLogic(this.grid_);
    const result = gameLogic.move(direction);

    // Check if grid actually changed
    if (!this.gridsEqual_(this.grid_, result.movedGrid)) {
      this.grid_ = result.movedGrid;
      this.score_ += result.scoreDelta;

      // Add a new random tile after successful move
      this.addRandomTile();

      // Update best score if current score exceeds it
      if (this.score_ > this.bestScore_) {
        this.bestScore_ = this.score_;
        this.saveBestScore_();
      }

      // Check game status
      this.checkWinCondition_();
      this.checkGameOverCondition_();

      return true;
    }

    return false;
  }

  /**
   * Checks if player has won by reaching 2048.
   * @private
   */
  checkWinCondition_() {
    if (this.won_) return;

    for (let row = 0; row < 4; row++) {
      for (let col = 0; col < 4; col++) {
        if (this.grid_[row][col] === 2048) {
          this.won_ = true;
          return;
        }
      }
    }
  }

  /**
   * Checks if game is over (no valid moves available).
   * @private
   */
  checkGameOverCondition_() {
    const gameLogic = new GameLogic(this.grid_);
    const hasValidMove = 
      gameLogic.canMove('up') ||
      gameLogic.canMove('down') ||
      gameLogic.canMove('left') ||
      gameLogic.canMove('right');
    
    this.gameOver_ = !hasValidMove;
  }

  /**
   * Compares two grids for equality.
   * @param {number[][]} grid1 - First grid.
   * @param {number[][]} grid2 - Second grid.
   * @return {boolean} True if grids are identical.
   * @private
   */
  gridsEqual_(grid1, grid2) {
    for (let row = 0; row < 4; row++) {
      for (let col = 0; col < 4; col++) {
        if (grid1[row][col] !== grid2[row][col]) {
          return false;
        }
      }
    }
    return true;
  }

  /**
   * Checks if game is over.
   * @return {boolean} True if game over.
   */
  isGameOver() {
    return this.gameOver_;
  }

  /**
   * Checks if player has won.
   * @return {boolean} True if player has reached 2048.
   */
  hasWon() {
    return this.won_;
  }

  /**
   * Gets current score.
   * @return {number} Current score.
   */
  getScore() {
    return this.score_;
  }

  /**
   * Gets best score.
   * @return {number} Best score.
   */
  getBestScore() {
    return this.bestScore_;
  }

  /**
   * Updates best score if current score exceeds it.
   */
  updateBestScore() {
    if (this.score_ > this.bestScore_) {
      this.bestScore_ = this.score_;
      this.saveBestScore_();
    }
  }

  /**
   * Resets game to initial state.
   */
  resetGame() {
    this.initializeGrid_();
    this.score_ = 0;
    this.gameOver_ = false;
    this.won_ = false;
    
    // Add two initial tiles
    this.addRandomTile();
    this.addRandomTile();
  }

  /**
   * Gets current grid state.
   * @return {number[][]} Copy of current grid.
   */
  getGrid() {
    return this.grid_.map(row => [...row]);
  }
}

export { Game };
