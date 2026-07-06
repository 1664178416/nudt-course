import { EventEmitter } from '../utils/EventEmitter.js';

/**
 * Abstract base class for all sorting algorithms.
 * Provides common functionality for recording steps, comparisons, and swaps.
 * Concrete sorting algorithms must extend this class and implement the `sort` method.
 * @abstract
 * @extends EventEmitter
 */
export class SortingAlgorithm extends EventEmitter {
  /**
   * Reference to the ArrayData instance being sorted.
   * @private
   * @type {ArrayData}
   */
  #data = null;

  /**
   * Array of recorded steps for visualization.
   * Each step contains array snapshot, highlights, and statistics.
   * @private
   * @type {Object[]}
   */
  #steps = [];

  /**
   * Number of comparisons performed during sorting.
   * @private
   * @type {number}
   */
  #comparisons = 0;

  /**
   * Number of swaps performed during sorting.
   * @private
   * @type {number}
   */
  #swaps = 0;

  /**
   * Creates a new SortingAlgorithm instance.
   * Initializes steps array and statistics counters.
   */
  constructor() {
    super();
  }

  /**
   * Sorts the given array data and returns the recorded steps.
   * This is an abstract method that must be implemented by subclasses.
   * @abstract
   * @param {ArrayData} data - The ArrayData instance to sort
   * @return {Object[]} Array of recorded steps for visualization
   * @throws {Error} If called directly on the abstract base class
   */
  sort(data) {
    throw new Error('SortingAlgorithm.sort() is abstract and must be implemented by subclass');
  }

  /**
   * Records a step in the sorting process.
   * Creates a snapshot of current array state and statistics.
   * @protected
   * @param {string} description - Text description of this step
   * @param {Object[]} highlights - Array of highlight objects with index and color
   * @param {Object} [additionalStats={}] - Additional statistics to include
   */
  _step(description, highlights = [], additionalStats = {}) {
    if (!this.#data) {
      throw new Error('Cannot record step: data not initialized');
    }

    const step = {
      array: this.#data.getArray(), // Create a copy of current array
      highlights: [...highlights], // Create a copy of highlights
      stats: {
        comparisons: this.#comparisons,
        swaps: this.#swaps,
        description: description,
        ...additionalStats,
      },
    };

    this.#steps.push(step);
    this.emit('stepRecorded', step);
  }

  /**
   * Compares two elements in the array.
   * Increments comparison counter and returns the comparison result.
   * @protected
   * @param {number} i - Index of first element
   * @param {number} j - Index of second element
   * @return {boolean} True if array[i] > array[j] (for ascending sort)
   */
  _compare(i, j) {
    if (!this.#data) {
      throw new Error('Cannot compare: data not initialized');
    }

    const array = this.#data.getArray();

    if (i < 0 || i >= array.length || j < 0 || j >= array.length) {
      throw new Error(`Index out of bounds: i=${i}, j=${j}, array length=${array.length}`);
    }

    this.#comparisons++;
    return array[i] > array[j];
  }

  /**
   * Swaps two elements in the array.
   * Increments swap counter and calls data.swap().
   * @protected
   * @param {number} i - Index of first element
   * @param {number} j - Index of second element
   */
  _swap(i, j) {
    if (!this.#data) {
      throw new Error('Cannot swap: data not initialized');
    }

    const array = this.#data.getArray();

    if (i < 0 || i >= array.length || j < 0 || j >= array.length) {
      throw new Error(`Index out of bounds: i=${i}, j=${j}, array length=${array.length}`);
    }

    this.#swaps++;
    this.#data.swap(i, j);
  }

  /**
   * Resets the algorithm state for a new sort operation.
   * Clears steps and resets counters. Should be called at the beginning of each sort.
   * @protected
   */
  _reset() {
    this.#steps = [];
    this.#comparisons = 0;
    this.#swaps = 0;
    this.emit('reset');
  }

  /**
   * Sets the data reference and resets algorithm state.
   * Should be called by subclasses at the beginning of their sort implementation.
   * @protected
   * @param {ArrayData} data - The ArrayData instance to sort
   */
  _initialize(data) {
    this.#data = data;
    this._reset();
  }

  /**
   * Gets the total number of steps recorded.
   * @return {number} Number of steps
   */
  getStepCount() {
    return this.#steps.length;
  }

  /**
   * Gets the recorded steps.
   * @return {Object[]} Array of recorded steps
   */
  getSteps() {
    return [...this.#steps]; // Return a copy to prevent mutation
  }

  /**
   * Gets the current comparison count.
   * @return {number} Number of comparisons
   */
  getComparisonCount() {
    return this.#comparisons;
  }

  /**
   * Gets the current swap count.
   * @return {number} Number of swaps
   */
  getSwapCount() {
    return this.#swaps;
  }
}
