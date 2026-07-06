import { EventEmitter } from './EventEmitter.js';

/**
 * ArrayData class manages the core data array for sorting visualization.
 * It provides methods to generate, modify, and track the state of the array.
 * Emits events when data or state changes.
 * @extends EventEmitter
 */
class ArrayData extends EventEmitter {
  /**
   * Creates a new ArrayData instance.
   * Initializes with empty array, zero size, and 'idle' state.
   */
  constructor() {
    super();
    
    /** @private {number[]} */
    this.array = [];
    
    /** @private {number} */
    this.size = 0;
    
    /** @private {string} */
    this.state = 'idle';
  }
  
  /**
   * Generates a random array of specified size.
   * Emits 'dataChange' event after generation.
   * @param {number} size - The size of array to generate
   */
  generateRandom(size) {
    if (size <= 0) {
      throw new Error('Array size must be positive');
    }
    
    this.array = [];
    this.size = size;
    
    // Generate random numbers between 1 and 100
    for (let i = 0; i < size; i++) {
      this.array.push(Math.floor(Math.random() * 100) + 1);
    }
    
    this.setState('idle');
    this.emit('dataChange', {
      array: [...this.array],
      state: this.state
    });
  }
  
  /**
   * Generates a reversed sorted array of specified size.
   * Emits 'dataChange' event after generation.
   * @param {number} size - The size of array to generate
   */
  generateReversed(size) {
    if (size <= 0) {
      throw new Error('Array size must be positive');
    }
    
    this.array = [];
    this.size = size;
    
    // Generate reversed array from size down to 1
    for (let i = 0; i < size; i++) {
      this.array.push(size - i);
    }
    
    this.setState('idle');
    this.emit('dataChange', {
      array: [...this.array],
      state: this.state
    });
  }
  
  /**
   * Sets a custom array provided by the user.
   * Emits 'dataChange' event after setting.
   * @param {number[]} arr - The custom array to set
   */
  setCustomArray(arr) {
    if (!Array.isArray(arr)) {
      throw new Error('Input must be an array');
    }
    
    if (arr.length === 0) {
      throw new Error('Array cannot be empty');
    }
    
    // Validate all elements are finite numbers
    for (let i = 0; i < arr.length; i++) {
      if (typeof arr[i] !== 'number' || !Number.isFinite(arr[i])) {
        throw new Error(`Element at index ${i} is not a valid finite number`);
      }
    }
    
    this.array = [...arr];
    this.size = arr.length;
    
    this.setState('idle');
    this.emit('dataChange', {
      array: [...this.array],
      state: this.state
    });
  }
  
  /**
   * Gets a copy of the current array.
   * @return {number[]} Copy of the current array
   */
  getArray() {
    return [...this.array];
  }
  
  /**
   * Gets the current array size.
   * @return {number} Current array size
   */
  getSize() {
    return this.size;
  }
  
  /**
   * Swaps two elements in the array.
   * Emits 'dataChange' event after swap.
   * @param {number} i - First index
   * @param {number} j - Second index
   */
  swap(i, j) {
    if (i < 0 || i >= this.size || j < 0 || j >= this.size) {
      throw new Error('Index out of bounds');
    }
    
    // Swap elements using destructuring
    [this.array[i], this.array[j]] = [this.array[j], this.array[i]];
    
    this.emit('dataChange', {
      array: [...this.array],
      state: this.state
    });
  }
  
  /**
   * Sets the state of the array and emits 'stateChange' event.
   * @param {string} state - New state string
   */
  setState(state) {
    if (typeof state !== 'string') {
      throw new Error('State must be a string');
    }
    
    this.state = state;
    this.emit('stateChange', {
      state: this.state,
      array: [...this.array]
    });
  }
  
  /**
   * Gets the current state of the array.
   * @return {string} Current state
   */
  getState() {
    return this.state;
  }
}

export { ArrayData };
