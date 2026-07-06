/**
 * @fileoverview Core 2048 game logic including move mechanics and merge operations.
 * @class GameLogic
 */

class GameLogic {
    /**
     * Creates a GameLogic instance with a copy of the current game grid.
     * @param {number[][]} grid - 4x4 grid representation (0 = empty).
     */
    constructor(grid) {
        /** @private {number[][]} */
        this.grid_ = grid.map(row => [...row]);
        
        /** @private {number} */
        this.scoreDelta_ = 0;
    }

    /**
     * Checks if a move in given direction is possible.
     * @param {string} direction - 'up', 'down', 'left', or 'right'.
     * @return {boolean} True if any tile can move/merge in that direction.
     */
    canMove(direction) {
        const grid = this.grid_;
        
        switch (direction) {
            case 'left':
                return this.canMoveLeft_(grid);
            case 'right':
                return this.canMoveRight_(grid);
            case 'up':
                return this.canMoveUp_(grid);
            case 'down':
                return this.canMoveDown_(grid);
            default:
                return false;
        }
    }

    /**
     * Executes a move in specified direction.
     * @param {string} direction - 'up', 'down', 'left', or 'right'.
     * @return {{movedGrid: number[][], scoreDelta: number}} Resultant grid and points earned.
     */
    move(direction) {
        this.scoreDelta_ = 0;
        // Save deep copy of current state
        const originalGrid = this.grid_.map(row => [...row]);
        
        switch (direction) {
            case 'left':
                this.moveLeft_();
                break;
            case 'right':
                this.moveRight_();
                break;
            case 'up':
                this.moveUp_();
                break;
            case 'down':
                this.moveDown_();
                break;
            default:
                console.warn(`Invalid direction: ${direction}`);
                return { movedGrid: originalGrid, scoreDelta: 0 };
        }
        
        // Check if grid actually changed
        const moved = !this.gridsEqual_(originalGrid, this.grid_);
        
        return {
            movedGrid: this.grid_,
            scoreDelta: moved ? this.scoreDelta_ : 0
        };
    }

    /**
     * Moves all tiles left.
     * @private
     */
    moveLeft_() {
        for (let r = 0; r < 4; r++) {
            this.grid_[r] = this.compressAndMergeRow_(this.grid_[r], 'left');
        }
    }

    /**
     * Moves all tiles right.
     * @private
     */
    moveRight_() {
        for (let r = 0; r < 4; r++) {
            this.grid_[r] = this.compressAndMergeRow_(this.grid_[r], 'right');
        }
    }

    /**
     * Moves all tiles up.
     * @private
     */
    moveUp_() {
        this.transposeGrid_();
        this.moveLeft_();
        this.transposeGrid_();
    }

    /**
     * Moves all tiles down.
     * @private
     */
    moveDown_() {
        this.transposeGrid_();
        this.moveRight_();
        this.transposeGrid_();
    }

    /**
     * Processes a single row/column through compress and merge operations.
     * @param {number[]} line - Array of 4 numbers.
     * @param {string} direction - 'left' or 'right'.
     * @return {number[]} Processed line.
     * @private
     */
    compressAndMergeRow_(line, direction) {
        let processed = [...line];
        
        // Reverse for right direction to process from right to left
        if (direction === 'right') {
            processed.reverse();
        }
        
        // Remove zeros
        processed = processed.filter(cell => cell !== 0);
        
        // Merge adjacent equal values, skip next after merge
        for (let i = 0; i < processed.length - 1; i++) {
            if (processed[i] === processed[i + 1]) {
                processed[i] *= 2;
                this.scoreDelta_ += processed[i];
                processed.splice(i + 1, 1);
            }
        }
        
        // Pad with zeros
        while (processed.length < 4) {
            processed.push(0);
        }
        
        // Reverse back for right direction
        if (direction === 'right') {
            processed.reverse();
        }
        
        return processed;
    }

    /**
     * Transposes the 4x4 grid in place (rows ↔ columns).
     * @private
     */
    transposeGrid_() {
        for (let r = 0; r < 4; r++) {
            for (let c = r + 1; c < 4; c++) {
                [this.grid_[r][c], this.grid_[c][r]] = [this.grid_[c][r], this.grid_[r][c]];
            }
        }
    }

    /**
     * Checks if left move is possible.
     * @param {number[][]} grid - The grid to check.
     * @return {boolean}
     * @private
     */
    canMoveLeft_(grid) {
        for (let r = 0; r < 4; r++) {
            for (let c = 0; c < 4; c++) {
                if (grid[r][c] !== 0) {
                    // Check if can move into an empty space to the left
                    if (c > 0 && grid[r][c - 1] === 0) return true;
                    // Check if can merge with same tile to the left
                    if (c > 0 && grid[r][c - 1] === grid[r][c]) return true;
                }
            }
        }
        return false;
    }

    /**
     * Checks if right move is possible.
     * @param {number[][]} grid - The grid to check.
     * @return {boolean}
     * @private
     */
    canMoveRight_(grid) {
        for (let r = 0; r < 4; r++) {
            for (let c = 3; c >= 0; c--) {
                if (grid[r][c] !== 0) {
                    if (c < 3 && grid[r][c + 1] === 0) return true;
                    if (c < 3 && grid[r][c + 1] === grid[r][c]) return true;
                }
            }
        }
        return false;
    }

    /**
     * Checks if up move is possible.
     * @param {number[][]} grid - The grid to check.
     * @return {boolean}
     * @private
     */
    canMoveUp_(grid) {
        // Transpose and check left (which becomes up)
        const transposed = this.transposeCopy_(grid);
        return this.canMoveLeft_(transposed);
    }

    /**
     * Checks if down move is possible.
     * @param {number[][]} grid - The grid to check.
     * @return {boolean}
     * @private
     */
    canMoveDown_(grid) {
        // Transpose and check right (which becomes down)
        const transposed = this.transposeCopy_(grid);
        return this.canMoveRight_(transposed);
    }

    /**
     * Returns a transposed copy of a grid.
     * @param {number[][]} grid - Original grid.
     * @return {number[][]} Transposed copy.
     * @private
     */
    transposeCopy_(grid) {
        const result = Array.from({ length: 4 }, () => Array(4).fill(0));
        for (let r = 0; r < 4; r++) {
            for (let c = 0; c < 4; c++) {
                result[c][r] = grid[r][c];
            }
        }
        return result;
    }

    /**
     * Compares two grids for equality.
     * @param {number[][]} grid1
     * @param {number[][]} grid2
     * @return {boolean}
     * @private
     */
    gridsEqual_(grid1, grid2) {
        for (let r = 0; r < 4; r++) {
            for (let c = 0; c < 4; c++) {
                if (grid1[r][c] !== grid2[r][c]) return false;
            }
        }
        return true;
    }
}
