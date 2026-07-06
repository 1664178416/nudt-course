import { SortingAlgorithm } from './SortingAlgorithm.js';

/**
 * Color constants for visualization.
 * These should correspond to the CSS variables defined in style.css.
 * @private
 * @type {Object}
 */
const COLORS = {
  KEY: '#f39c12',        // --bar-compare (orange): current key being inserted
  COMPARING: '#e74c3c',  // --bar-highlight (red): element being compared with key
  SHIFTING: '#ff6b6b',   // Bright red for elements being shifted
  SORTED: '#2ecc71',     // --bar-sorted (green): already in final sorted position
  DEFAULT: '#3498db',    // --bar-color (blue): normal element
};

/**
 * InsertionSort class implements the Insertion Sort algorithm.
 * Extends the abstract SortingAlgorithm class.
 * @extends SortingAlgorithm
 */
export class InsertionSort extends SortingAlgorithm {
  /**
   * Sorts the given array data using Insertion Sort algorithm.
   * Records each step of the sorting process for visualization.
   * @override
   * @param {ArrayData} data - The ArrayData instance to sort
   * @return {Object[]} Array of recorded steps for visualization
   */
  sort(data) {
    // Initialize algorithm state with the data
    this._initialize(data);
    
    const n = data.getSize();
    const sortedIndices = new Set(); // Track indices that are in their final position
    
    // Record initial state
    this._step('Initial array state', []);
    
    // Start from the second element (index 1)
    for (let i = 1; i < n; i++) {
      // Store the original key value for description purposes
      const originalArray = data.getArray();
      const keyValue = originalArray[i];
      let j = i; // j is the current position of the key as it moves left
      
      // Record the start of processing this element
      this._step(
        `Select element at index ${i} as key (value: ${keyValue})`,
        [
          { index: i, color: COLORS.KEY },
          ...this._getSortedHighlights(sortedIndices)
        ],
        { currentIteration: i }
      );
      
      // Move the key leftwards until we find its correct position
      while (j > 0) {
        const compareIndex = j - 1;
        const currentArray = data.getArray();
        
        // Record comparison step
        this._step(
          `Comparing element at index ${compareIndex} (value: ${currentArray[compareIndex]}) ` +
          `with key (value: ${keyValue}) at position ${j}`,
          [
            { index: j, color: COLORS.KEY },
            { index: compareIndex, color: COLORS.COMPARING },
            ...this._getSortedHighlights(sortedIndices)
          ]
        );
        
        // If the element to the left is GREATER than the key, shift it right
        // We use the base class's _compare method which returns array[i] > array[j]
        // Since we're comparing array[compareIndex] with the key at position j,
        // we check if the left element is greater than the element at j
        if (this._compare(compareIndex, j)) {
          // Record shift step
          const preSwapArray = data.getArray();
          this._step(
            `Element ${preSwapArray[compareIndex]} > ${preSwapArray[j]}. ` +
            `Shifting ${preSwapArray[compareIndex]} right to index ${j}`,
            [
              { index: compareIndex, color: COLORS.SHIFTING },
              { index: j, color: COLORS.SHIFTING },
              ...this._getSortedHighlights(sortedIndices)
            ]
          );
          
          // Perform the shift (swap the elements)
          this._swap(compareIndex, j);
          j--; // Move the key position one step left
          
          // Record position update after shift
          if (j > 0) {
            this._step(
              `Key ${keyValue} moved to index ${j}`,
              [
                { index: j, color: COLORS.KEY },
                ...this._getSortedHighlights(sortedIndices)
              ]
            );
          }
        } else {
          // Found correct position: left element <= key
          const currentArray = data.getArray();
          this._step(
            `Element ${currentArray[compareIndex]} ≤ ${currentArray[j]}. ` +
            `Key ${keyValue} found correct position at index ${j}`,
            [
              { index: j, color: COLORS.SORTED },
              ...this._getSortedHighlights(sortedIndices)
            ]
          );
          break;
        }
      }
      
      // Handle case where key moved all the way to index 0
      if (j === 0) {
        this._step(
          `Key ${keyValue} is the smallest element. Now at index 0.`,
          [
            { index: 0, color: COLORS.SORTED },
            ...this._getSortedHighlights(sortedIndices)
          ]
        );
      }
      
      // Mark the key's final position as sorted
      sortedIndices.add(j);
      
      // Mark all elements from 0 to i as sorted (they are in relative order)
      // This is more accurate than just adding j, as elements 0..i-1 were already sorted
      for (let k = 0; k <= i; k++) {
        sortedIndices.add(k);
      }
      
      this._step(
        `Insertion complete. Elements 0 through ${i} are now in sorted order.`,
        this._getSortedHighlights(sortedIndices),
        { sortedCount: sortedIndices.size }
      );
    }
    
    // Record final sorted state
    const finalDescription = `Insertion Sort complete! ` +
      `Total: ${this.getComparisonCount()} comparisons, ${this.getSwapCount()} swaps`;
    
    // Mark all elements as sorted
    const allSortedHighlights = Array.from({ length: n }, (_, idx) => ({
      index: idx,
      color: COLORS.SORTED
    }));
    
    this._step(finalDescription, allSortedHighlights, {
      isComplete: true,
      algorithm: 'Insertion Sort',
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
