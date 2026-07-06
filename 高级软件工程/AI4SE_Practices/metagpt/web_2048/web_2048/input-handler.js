/**
 * @fileoverview Input handler for 2048 game supporting keyboard, button, and touch inputs.
 * Follows Google JavaScript Style Guide with modular, maintainable code.
 * @module input-handler
 */

import { Game } from './game.js';
import { UI } from './script.js';

/**
 * Input handler class responsible for binding and processing all user inputs.
 * Converts keyboard presses, button clicks, and touch gestures into game commands.
 */
class InputHandler {
  /**
   * Creates an InputHandler instance bound to game and UI.
   * @param {Game} game - Game instance to control.
   * @param {UI} ui - UI instance to update.
   */
  constructor(game, ui) {
    /** @private {Game} */
    this.game_ = game;

    /** @private {UI} */
    this.ui_ = ui;

    /** @private {number|null} */
    this.touchStartX_ = null;

    /** @private {number|null} */
    this.touchStartY_ = null;

    /** @private {boolean} */
    this.keyCooldown_ = false;

    /** @private {number} */
    this.KEY_COOLDOWN_TIME_MS_ = 100;

    /** @private {number} */
    this.MIN_SWIPE_DISTANCE_ = 20;

    // Bind all event listeners
    this.bindKeyboardEvents_();
    this.bindButtonEvents_();
    this.bindTouchEvents_();
  }

  /**
   * Binds keyboard arrow key events for game control.
   * Uses cooldown to prevent rapid repeated key presses.
   * @private
   */
  bindKeyboardEvents_() {
    document.addEventListener('keydown', (event) => {
      // Prevent default behavior for arrow keys to avoid page scrolling
      const keyHandled = this.handleKeyDown_(event);
      if (keyHandled) {
        event.preventDefault();
      }
    });

    // Also bind keyup to reset cooldown flag
    document.addEventListener('keyup', () => {
      this.keyCooldown_ = false;
    });
  }

  /**
   * Handles keydown event and maps to game directions.
   * @param {KeyboardEvent} event - Keyboard event object.
   * @return {boolean} True if key was handled as a game command.
   * @private
   */
  handleKeyDown_(event) {
    if (this.keyCooldown_) {
      return false;
    }

    let direction = null;
    
    switch (event.key) {
      case 'ArrowUp':
      case 'w':
      case 'W':
        direction = 'up';
        break;
      case 'ArrowDown':
      case 's':
      case 'S':
        direction = 'down';
        break;
      case 'ArrowLeft':
      case 'a':
      case 'A':
        direction = 'left';
        break;
      case 'ArrowRight':
      case 'd':
      case 'D':
        direction = 'right';
        break;
      default:
        return false;
    }

    this.handleMove_(direction);
    this.keyCooldown_ = true;
    
    // Reset cooldown after delay
    setTimeout(() => {
      this.keyCooldown_ = false;
    }, this.KEY_COOLDOWN_TIME_MS_);
    
    return true;
  }

  /**
   * Binds button events for game control (restart button).
   * @private
   */
  bindButtonEvents_() {
    const restartButton = document.getElementById('restart-button');
    if (restartButton) {
      restartButton.addEventListener('click', () => this.handleRestart_());
    }

    // Bind keyboard shortcuts for restart (R key)
    document.addEventListener('keydown', (event) => {
      if (event.key === 'r' || event.key === 'R') {
        this.handleRestart_();
      }
    });
  }

  /**
   * Binds touch events for swipe-based game control on mobile devices.
   * @private
   */
  bindTouchEvents_() {
    const gameBoard = document.querySelector('.game-board');
    if (!gameBoard) {
      return;
    }

    gameBoard.addEventListener('touchstart', (event) => {
      // Only handle single touch
      if (event.touches.length !== 1) {
        return;
      }
      
      const touch = event.touches[0];
      this.touchStartX_ = touch.clientX;
      this.touchStartY_ = touch.clientY;
      
      // Prevent scrolling when touching game board
      event.preventDefault();
    }, { passive: false });

    gameBoard.addEventListener('touchend', (event) => {
      if (this.touchStartX_ === null || this.touchStartY_ === null) {
        return;
      }

      const touch = event.changedTouches[0];
      const touchEndX = touch.clientX;
      const touchEndY = touch.clientY;

      const direction = this.calculateSwipeDirection_(
        this.touchStartX_,
        this.touchStartY_,
        touchEndX,
        touchEndY
      );

      if (direction) {
        this.handleMove_(direction);
      }

      // Reset touch start coordinates
      this.touchStartX_ = null;
      this.touchStartY_ = null;
      
      event.preventDefault();
    }, { passive: false });

    // Prevent context menu on long press
    gameBoard.addEventListener('contextmenu', (event) => {
      event.preventDefault();
    });
  }

  /**
   * Calculates swipe direction based on touch start and end coordinates.
   * @param {number} startX - Touch start X coordinate.
   * @param {number} startY - Touch start Y coordinate.
   * @param {number} endX - Touch end X coordinate.
   * @param {number} endY - Touch end Y coordinate.
   * @return {string|null} Direction ('up', 'down', 'left', 'right') or null if swipe too short.
   * @private
   */
  calculateSwipeDirection_(startX, startY, endX, endY) {
    const dx = endX - startX;
    const dy = endY - startY;

    // Calculate absolute distance
    const absDx = Math.abs(dx);
    const absDy = Math.abs(dy);

    // Check if swipe distance is sufficient
    if (Math.max(absDx, absDy) < this.MIN_SWIPE_DISTANCE_) {
      return null;
    }

    // Determine primary direction (horizontal vs vertical)
    if (absDx > absDy) {
      // Horizontal swipe
      return dx > 0 ? 'right' : 'left';
    } else {
      // Vertical swipe
      return dy > 0 ? 'down' : 'up';
    }
  }

  /**
   * Handles a move command in specified direction.
   * @param {string} direction - One of 'up', 'down', 'left', 'right'.
   * @private
   */
  handleMove_(direction) {
    // Validate direction parameter
    const validDirections = ['up', 'down', 'left', 'right'];
    if (!validDirections.includes(direction)) {
      console.warn(`Invalid direction: ${direction}`);
      return;
    }

    // Attempt to move in game
    const moved = this.game_.move(direction);

    if (moved) {
      // Update UI to reflect new game state
      this.ui_.updateGrid();
      this.ui_.updateScores();

      // Check for win condition
      if (this.game_.hasWon()) {
        this.ui_.showWinMessage();
        this.ui_.showWinAnimation();
      }

      // Check for game over condition
      if (this.game_.isGameOver()) {
        this.ui_.showGameOverMessage();
      }
    } else {
      // Play invalid move animation
      this.ui_.showInvalidMoveAnimation();
    }
  }

  /**
   * Handles game restart command.
   * @private
   */
  handleRestart_() {
    // Reset game state
    this.game_.resetGame();
    
    // Update UI
    this.ui_.hideGameOverMessage();
    this.ui_.hideWinMessage();
    this.ui_.updateGrid();
    this.ui_.updateScores();
  }
}

export { InputHandler };
