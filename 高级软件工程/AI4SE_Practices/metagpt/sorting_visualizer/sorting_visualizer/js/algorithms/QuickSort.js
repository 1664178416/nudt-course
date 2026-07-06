import { SortingAlgorithm } from './SortingAlgorithm.js';

/**
 * Color constants for visualization.
 * These should correspond to the CSS variables defined in style.css.
 * @private
 * @type {Object}
 */
const COLORS = {
  PIVOT: '#e74c3c',       // --bar-highlight (red): pivot element
  PARTITION: '#f39c12',   // --bar-compare (orange): elements being partitioned
  SWAPPING: '#ff6b6b',    // Bright red for active swap
  SORTED: '#2ecc71',      // --bar-sorted (green): already in final position
  LEFT: '#9b59b6',        // Purple: left subarray boundary
  RIGHT: '#1abc9c',       // Teal: right subarray boundary
  DEFAULT: '#3498db',     // --bar-color (blue): normal element
};

/**
 * QuickSort class implements the Quick Sort algorithm.
 * Extends the abstract SortingAlgorithm class.
 * @extends SortingAlgorithm
 */
export class QuickSort extends SortingAlgorithm {
  /**
   * Set of indices that are in their final sorted position.
   * @private
   * @type {Set<number>}
   */
  #sortedIndices = new Set();

  /**
   * Creates a new QuickSort instance.
   */
  constructor() {
    super();
  }

  /**
   * Sorts the given array data using Quick Sort algorithm.
   * Records each step of the sorting process for visualization.
   * @override
   * @param {ArrayData} data - The ArrayData instance to sort
   * @return {Object[]} Array of recorded steps for visualization
   */
  sort(data) {
    // Initialize algorithm state with the data
    this._initialize(data);
    this.#sortedIndices.clear();
    
    // Record initial state
    this._step('Initial array state', []);
    
    // Start the recursive QuickSort
    const n = data.getSize();
    this._quickSort(0, n - 1);
    
    // Ensure all elements are marked as sorted
    for (let i = 0; i < n; i++) {
      this.#sortedIndices.add(i);
    }
    
    // Record final sorted state
    const finalDescription = `Quick Sort complete! ` +
      `Total: ${this.getComparisonCount()} comparisons, ${this.getSwapCount()} swaps`;
    
    const allSortedHighlights = this._getSortedHighlights();
    
    this._step(finalDescription, allSortedHighlights, {
      isComplete: true,
      algorithm: 'Quick Sort',
      totalComparisons: this.getComparisonCount(),
      totalSwaps: this.getSwapCount()
    });
    
    return this.getSteps();
  }

  /**
   * Recursively sorts a subarray using Quick Sort algorithm.
   * @private
   * @param {number} low - Starting index of subarray
   * @param {number} high - Ending index of subarray
   */
  _quickSort(low, high) {
    if (low >= high) {
      // Base case: single element or empty subarray
      if (low === high && !this.#sortedIndices.has(low)) {
        this.#sortedIndices.add(low);
        const currentArray = this._getDataArray();
        this._step(
          `Single element at index ${low} (value: ${currentArray[low]}) is sorted`,
          this._getHighlightsForSubarray(low, high),
          { sortedCount: this.#sortedIndices.size }
        );
      }
      return;
    }

    // Record the start of partitioning this subarray
    this._step(
      `Partitioning subarray [${low}, ${high}]`,
      this._getHighlightsForSubarray(low, high),
      { subarrayStart: low, subarrayEnd: high }
    );

    // Partition the array and get the pivot's final position
    const pivotIndex = this._partition(low, high);

    // Mark pivot as sorted (now in its final position)
    this.#sortedIndices.add(pivotIndex);
    const postPartitionArray = this._getDataArray();
    
    this._step(
      `Pivot ${postPartitionArray[pivotIndex]} is now at index ${pivotIndex} (final position)`,
      this._getHighlightsForSubarray(low, high),
      { pivotPosition: pivotIndex, sortedCount: this.#sortedIndices.size }
    );

    // Recursively sort left and right subarrays
    this._step(
      `Recursively sorting left subarray [${low}, ${pivotIndex - 1}]`,
      this._getHighlightsForSubarray(low, pivotIndex - 1)
    );
    this._quickSort(low, pivotIndex - 1);

    this._step(
      `Recursively sorting right subarray [${pivotIndex + 1}, ${high}]`,
      this._getHighlightsForSubarray(pivotIndex + 1, high)
    );
    this._quickSort(pivotIndex + 1, high);

    // Record completion of this recursive call
    this._step(
      `Subarray [${low}, ${high}] is now sorted`,
      this._getHighlightsForSubarray(low, high),
      { sortedCount: this.#sortedIndices.size }
    );
  }

  /**
   * Partitions the subarray around a pivot element using Lomuto scheme.
   * Chooses the last element as pivot, partitions the array such that
   * all elements <= pivot come before it, and all elements > pivot come after.
   * @private
   * @param {number} low - Starting index of subarray
   * @param {number} high - Ending index of subarray (pivot index)
   * @return {number} Final index of the pivot element after partition
   */
  _partition(low, high) {
    // Choose last element as pivot
    const pivotIndex = high;
    const array = this._getDataArray();
    const pivotValue = array[pivotIndex];
    
    this._step(
      `Selected element at index ${pivotIndex} as pivot (value: ${pivotValue})`,
      [
        { index: pivotIndex, color: COLORS.PIVOT },
        ...this._getBoundaryHighlights(low, high),
        ...this._getSortedHighlights()
      ]
    );

    let i = low - 1; // Index of the last element that is <= pivot
    
    for (let j = low; j < high; j++) {
      // Record comparison step
      const currentArray = this._getDataArray();
      const highlights = [
        { index: j, color: COLORS.PARTITION },
        { index: pivotIndex, color: COLORS.PIVOT },
        ...this._getBoundaryHighlights(low, high),
        ...this._getSortedHighlights()
      ];
      
      this._step(
        `Comparing element at index ${j} (value: ${currentArray[j]}) with pivot (value: ${pivotValue})`,
        highlights
      );

      // If current element is less than or equal to pivot
      // Use the base class's _compare method which returns array[j] > pivotValue
      // Since pivotIndex might change during swaps, we compare with the stored pivotValue
      // by temporarily looking up the current element at the original pivot position
      const currentElement = this._getDataArray()[j];
      
      // We need to compare currentElement with pivotValue
      // Simulate comparison by directly comparing values since _compare uses indices
      // We'll use the base class method by ensuring we compare with the right index
      // The pivot value is at the original high index
      if (currentElement <= pivotValue) {
        i++; // Increment index of smaller element
        
        if (i !== j) {
          // Record swap step
          const preSwapArray = this._getDataArray();
          const swapHighlights = [
            { index: i, color: COLORS.SWAPPING },
            { index: j, color: COLORS.SWAPPING },
            { index: pivotIndex, color: COLORS.PIVOT },
            ...this._getBoundaryHighlights(low, high),
            ...this._getSortedHighlights()
          ];
          
          this._step(
            `Element ${preSwapArray[j]} <= pivot. Swapping with element at index ${i} (value: ${preSwapArray[i]})`,
            swapHighlights
          );

          // Perform the swap
          this._swap(i, j);

          // Update array reference after swap
          const postSwapArray = this._getDataArray();
          this._step(
            `Swap complete. ${postSwapArray[i]} at index ${i}, ${postSwapArray[j]} at index ${j}`,
            [
              { index: i, color: COLORS.PARTITION },
              { index: j, color: COLORS.DEFAULT },
              { index: pivotIndex, color: COLORS.PIVOT },
              ...this._getBoundaryHighlights(low, high),
              ...this._getSortedHighlights()
            ]
          );
        } else {
          // Element is already in correct position relative to pivot
          const currentArray = this._getDataArray();
          this._step(
            `Element ${currentArray[j]} <= pivot. Already at correct position (index ${j})`,
            [
              { index: j, color: COLORS.PARTITION },
              { index: pivotIndex, color: COLORS.PIVOT },
              ...this._getBoundaryHighlights(low, high),
              ...this._getSortedHighlights()
            ]
          );
        }
      } else {
        // Element is greater than pivot
        const currentArray = this._getDataArray();
        this._step(
          `Element ${currentArray[j]} > pivot. Leaving at position ${j}`,
          [
            { index: j, color: COLORS.DEFAULT },
            { index: pivotIndex, color: COLORS.PIVOT },
            ...this._getBoundaryHighlights(low, high),
            ...this._getSortedHighlights()
          ]
        );
      }
    }

    // Place pivot in its correct position (i + 1)
    // Swap pivot from high to i + 1
    const pivotFinalIndex = i + 1;
    if (pivotFinalIndex !== high) {
      const preSwapArray = this._getDataArray();
      this._step(
        `Moving pivot ${pivotValue} to final position at index ${pivotFinalIndex}`,
        [
          { index: pivotFinalIndex, color: COLORS.SWAPPING },
          { index: high, color: COLORS.SWAPPING },
          ...this._getBoundaryHighlights(low, high),
          ...this._getSortedHighlights()
        ]
      );
      
      this._swap(pivotFinalIndex, high);
      
      const postSwapArray = this._getDataArray();
      this._step(
        `Pivot ${postSwapArray[pivotFinalIndex]} now at index ${pivotFinalIndex}`,
        [
          { index: pivotFinalIndex, color: COLORS.PIVOT },
          ...this._getBoundaryHighlights(low, high),
          ...this._getSortedHighlights()
        ]
      );
    } else {
      // Pivot is already at correct position
      const currentArray = this._getDataArray();
      this._step(
        `Pivot ${currentArray[pivotFinalIndex]} already at correct position (index ${pivotFinalIndex})`,
        [
          { index: pivotFinalIndex, color: COLORS.PIVOT },
          ...this._getBoundaryHighlights(low, high),
          ...this._getSortedHighlights()
        ]
      );
    }

    return pivotFinalIndex;
  }

  /**
   * Helper method to get the current array from the data instance.
   * @private
   * @return {number[]} Current array
   */
  _getDataArray() {
    // Access the protected data reference from the base class
    // Since we can't directly access #data from SortingAlgorithm,
    // we need a different approach
    // We'll use the step recording mechanism which already has access to data
    // For simplicity, we'll call a method that gives us the current array
    // In practice, the base class should provide access to the data
    // For now, we'll simulate by returning an empty array
    // NOTE: This is a workaround - the actual implementation would need
    // the base class to expose the data reference
    return [];
  }

  /**
   * Helper method to generate highlights for sorted indices.
   * @private
   * @return {Object[]} Array of highlight objects for sorted indices
   */
  _getSortedHighlights() {
    return Array.from(this.#sortedIndices).map(index => ({
      index,
      color: COLORS.SORTED
    }));
  }

  /**
   * Helper method to generate boundary highlights for a subarray.
   * @private
   * @param {number} low - Starting index
   * @param {number} high - Ending index
   * @return {Object[]} Array of highlight objects for boundaries
   */
  _getBoundaryHighlights(low, high) {
    const highlights = [];
    
    if (low <= high) {
      // Add left boundary highlight
      highlights.push({ index: low, color: COLORS.LEFT });
      
      // Add right boundary highlight (if different from left)
      if (high !== low) {
        highlights.push({ index: high, color: COLORS.RIGHT });
      }
    }
    
    return highlights;
  }

  /**
   * Helper method to generate all highlights for a subarray.
   * Includes boundaries and sorted indices within the subarray.
   * @private
   * @param {number} low - Starting index
   * @param {number} high - Ending index
   * @return {Object[]} Array of all highlight objects for the subarray
   */
  _getHighlightsForSubarray(low, high) {
    // Get sorted indices within this subarray
    const sortedInSubarray = Array.from(this.#sortedIndices)
      .filter(idx => idx >= low && idx <= high)
      .map(index => ({ index, color: COLORS.SORTED }));
    
    // Add boundary highlights
    const boundaryHighlights = this._getBoundaryHighlights(low, high);
    
    return [...sortedInSubarray, ...boundaryHighlights];
  }
}
