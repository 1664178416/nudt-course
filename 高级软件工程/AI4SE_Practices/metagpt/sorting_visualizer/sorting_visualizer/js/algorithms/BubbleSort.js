import { SortingAlgorithm } from './SortingAlgorithm.js';

/**
 * Color constants for visualization.
 * These should correspond to the CSS variables defined in style.css.
 * @private
 * @type {Object}
 */
const COLORS = {
  COMPARING: '#f39c12', // --bar-compare
  SWAPPING: '#e74c3c',  // --bar-highlight
  SORTED: '#2ecc71',    // --bar-sorted
  DEFAULT: '#3498db',   // --bar-color
};

/**
 * BubbleSort class implements the Bubble Sort algorithm.
 * Extends the abstract SortingAlgorithm class.
 * @extends SortingAlgorithm
 */
export class BubbleSort extends SortingAlgorithm {
  /**
   * Sorts the given array data using Bubble Sort algorithm.
   * Records each step of the sorting process for visualization.
   * @override
   * @param {ArrayData} data - The ArrayData instance to sort
   * @return {Object[]} Array of recorded steps for visualization
   */
  sort(data) {
    // Initialize algorithm state with the data
    this._initialize(data);
    
    const n = data.getSize();
    const steps = [];
    let didEarlyExit = false;
    
    // Record initial state
    this._step('Initial array state', []);
    
    // Outer loop for each pass
    for (let i = 0; i < n - 1; i++) {
      let swappedInThisPass = false;
      
      // Record the beginning of a new pass
      this._step(`Starting pass ${i + 1}`, []);
      
      // Inner loop for comparisons in current pass
      for (let j = 0; j < n - i - 1; j++) {
        // Get fresh array snapshot for accurate description
        const currentArray = data.getArray();
        
        // Record comparison step with fresh array data
        this._step(
          `Comparing elements at indices ${j} and ${j + 1}: ` +
          `${currentArray[j]} vs ${currentArray[j + 1]}`,
          [
            { index: j, color: COLORS.COMPARING },
            { index: j + 1, color: COLORS.COMPARING }
          ]
        );
        
        // Compare adjacent elements
        if (this._compare(j, j + 1)) {
          // Get fresh array snapshot after comparison but before swap
          const preSwapArray = data.getArray();
          
          // Record swap step with accurate pre-swap values
          this._step(
            `Swapping ${preSwapArray[j]} and ${preSwapArray[j + 1]} - ` +
            `${preSwapArray[j]} > ${preSwapArray[j + 1]}`,
            [
              { index: j, color: COLORS.SWAPPING },
              { index: j + 1, color: COLORS.SWAPPING }
            ]
          );
          
          // Perform the swap
          this._swap(j, j + 1);
          swappedInThisPass = true;
        }
      }
      
      // Mark the last element of this pass as sorted
      const newlySortedIndex = n - i - 1;
      this._step(
        `Pass ${i + 1} complete. Element at index ${newlySortedIndex} is now in final position`,
        [{ index: newlySortedIndex, color: COLORS.SORTED }]
      );
      
      // If no swaps occurred in this pass, array is already sorted
      if (!swappedInThisPass) {
        didEarlyExit = true;
        
        // Mark all remaining unsorted elements as sorted immediately
        const remainingIndices = [];
        for (let k = 0; k < newlySortedIndex; k++) {
          remainingIndices.push({ index: k, color: COLORS.SORTED });
        }
        
        if (remainingIndices.length > 0) {
          this._step(
            'No swaps in this pass - array is already sorted. Marking remaining elements.',
            remainingIndices
          );
        }
        break; // Exit outer loop immediately
      }
    }
    
    // Record final sorted state
    const exitReason = didEarlyExit ? 'Sorted (stopped early - already sorted)' : 'Sorting complete';
    const finalDescription = `${exitReason}! ` +
      `Total: ${this.getComparisonCount()} comparisons, ${this.getSwapCount()} swaps`;
    
    // Mark all elements as sorted in final step
    const allSortedIndices = Array.from({ length: n }, (_, i) => ({
      index: i,
      color: COLORS.SORTED
    }));
    
    this._step(finalDescription, allSortedIndices, {
      isComplete: true,
      algorithm: 'Bubble Sort'
    });
    
    return this.getSteps();
  }
}
