import { SortingAlgorithm } from './SortingAlgorithm.js';

/**
 * Color constants for visualization.
 * These should correspond to the CSS variables defined in style.css.
 * @private
 * @type {Object}
 */
const COLORS = {
  CANDIDATE: '#f39c12',  // --bar-compare (orange): current minimum candidate
  COMPARING: '#e74c3c',  // --bar-highlight (red): element being compared
  SWAPPING: '#ff6b6b',   // Bright red for active swap
  SORTED: '#2ecc71',     // --bar-sorted (green): already in final position
  DEFAULT: '#3498db',    // --bar-color (blue): normal element
};

/**
 * SelectionSort class implements the Selection Sort algorithm.
 * Extends the abstract SortingAlgorithm class.
 * @extends SortingAlgorithm
 */
export class SelectionSort extends SortingAlgorithm {
  /**
   * Sorts the given array data using Selection Sort algorithm.
   * Records each step of the sorting process for visualization.
   * @override
   * @param {ArrayData} data - The ArrayData instance to sort
   * @return {Object[]} Array of recorded steps for visualization
   */
  sort(data) {
    // Initialize algorithm state with the data
    this._initialize(data);
    
    const n = data.getSize();
    const sortedIndices = new Set(); // Track sorted indices
    
    // Record initial state
    this._step('Initial array state', []);
    
    // Outer loop: boundary between sorted and unsorted portions
    for (let i = 0; i < n - 1; i++) {
      // Assume the minimum is the first element of unsorted portion
      let minIndex = i;
      const currentArray = data.getArray();
      
      // Highlight sorted portion and current minimum candidate
      const highlights = [
        { index: minIndex, color: COLORS.CANDIDATE },
        ...this._getSortedHighlights(sortedIndices)
      ];
      
      this._step(
        `Starting iteration ${i + 1}. Minimum candidate at index ${minIndex} (value: ${currentArray[minIndex]})`,
        highlights,
        { currentIteration: i + 1 }
      );
      
      // Inner loop: find the minimum in the unsorted portion
      for (let j = i + 1; j < n; j++) {
        const currentArray = data.getArray();
        const comparisonHighlights = [
          { index: minIndex, color: COLORS.CANDIDATE },
          { index: j, color: COLORS.COMPARING },
          ...this._getSortedHighlights(sortedIndices)
        ];
        
        this._step(
          `Comparing candidate (index ${minIndex}, value: ${currentArray[minIndex]}) ` +
          `with element at index ${j} (value: ${currentArray[j]})`,
          comparisonHighlights
        );
        
        // CORRECTED: Compare if current candidate is greater than element at j
        if (this._compare(minIndex, j)) {
          // Found new minimum - element at j is smaller than current candidate
          const previousMin = minIndex;
          minIndex = j;
          const newArray = data.getArray();
          
          this._step(
            `New minimum found at index ${minIndex} (value: ${newArray[minIndex]})`,
            [
              { index: previousMin, color: COLORS.DEFAULT },
              { index: minIndex, color: COLORS.CANDIDATE },
              ...this._getSortedHighlights(sortedIndices)
            ]
          );
        }
      }
      
      // Now minIndex contains the actual minimum element in unsorted portion
      if (minIndex !== i) {
        const preSwapArray = data.getArray();
        const preSwapHighlights = [
          { index: i, color: COLORS.SWAPPING },
          { index: minIndex, color: COLORS.SWAPPING },
          ...this._getSortedHighlights(sortedIndices)
        ];
        
        this._step(
          `Swapping minimum element (index ${minIndex}, value: ${preSwapArray[minIndex]}) ` +
          `with first unsorted element (index ${i}, value: ${preSwapArray[i]})`,
          preSwapHighlights
        );
        
        // Perform the swap
        this._swap(i, minIndex);
        
        // Update sorted indices after swap
        sortedIndices.add(i);
        const postSwapHighlights = [
          { index: i, color: COLORS.SORTED },
          { index: minIndex, color: COLORS.DEFAULT },
          ...this._getSortedHighlights(sortedIndices)
        ];
        
        const postSwapArray = data.getArray();
        this._step(
          `Swap complete. ${postSwapArray[i]} now at index ${i} (final position)`,
          postSwapHighlights
        );
      } else {
        // Element is already at correct position
        sortedIndices.add(i);
        const currentArray = data.getArray();
        const highlights = [
          { index: i, color: COLORS.SORTED },
          ...this._getSortedHighlights(sortedIndices)
        ];
        
        this._step(
          `Minimum element already at correct position (index ${i}, value: ${currentArray[i]})`,
          highlights
        );
      }
      
      // Record progress after each iteration
      const sortedCount = sortedIndices.size;
      this._step(
        `Iteration ${i + 1} complete. ${sortedCount} elements in final position`,
        this._getSortedHighlights(sortedIndices),
        { sortedCount }
      );
    }
    
    // Mark the last element as sorted (it's automatically in correct position)
    sortedIndices.add(n - 1);
    
    // Record final sorted state
    const finalDescription = `Selection Sort complete! ` +
      `Total: ${this.getComparisonCount()} comparisons, ${this.getSwapCount()} swaps`;
    
    const allSortedHighlights = this._getSortedHighlights(sortedIndices);
    
    this._step(finalDescription, allSortedHighlights, {
      isComplete: true,
      algorithm: 'Selection Sort',
      totalComparisons: this.getComparisonCount(),
      totalSwaps: this.getSwapCount()
    });
    
    return this.getSteps();
  }

  /**
   * Helper method to generate highlights for sorted indices.
   * @private
   * @param {Set<number>} sortedIndices - Set of indices that are sorted
   * @return {Object[]} Array of highlight objects for sorted indices
   */
  _getSortedHighlights(sortedIndices) {
    return Array.from(sortedIndices).map(index => ({
      index,
      color: COLORS.SORTED
    }));
  }
}
