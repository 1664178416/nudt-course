## js/main.js
```javascript
import { ArrayData } from './visualizer/ArrayData.js';
import { SortingAlgorithm } from './algorithms/SortingAlgorithm.js';
import { Visualizer } from './visualizer/Visualizer.js';
import { PlaybackController } from './controller/PlaybackController.js';
import { UIController } from './controller/UIController.js';
import { BubbleSort } from './algorithms/BubbleSort.js';
import { SelectionSort } from './algorithms/SelectionSort.js';
import { InsertionSort } from './algorithms/InsertionSort.js';
import { QuickSort } from './algorithms/QuickSort.js';
import { MergeSort } from './algorithms/MergeSort.js';

/**
 * Main application class that coordinates all modules.
 * Acts as the entry point and central coordinator for the sorting visualizer.
 */
export class Main {
  /**
   * Creates a new Main application instance.
   */
  constructor() {
    /**
     * Current array data instance.
     * @private
     * @type {ArrayData}
     */
    this.arrayData = null;
    
    /**
     * Current sorting algorithm instance.
     * @private
     * @type {SortingAlgorithm|null}
     */
    this.currentAlgorithm = null;
    
    /**
     * Visualizer instance for rendering.
     * @private
     * @type {Visualizer|null}
     */
    this.visualizer = null;
    
    /**
     * Playback controller for step management.
     * @private
     * @type {PlaybackController|null}
     */
    this.playbackController = null;
    
    /**
     * UI controller for user interactions.
     * @private
     * @type {UIController|null}
     */
    this.uiController = null;
    
    /**
     * Default array size for initialization.
     * @private
     * @type {number}
     */
    this.defaultSize = 30;
    
    /**
     * Mapping of algorithm IDs to their classes.
     * @private
     * @type {Object}
     */
    this.algorithmMap = {
      'bubble': BubbleSort,
      'selection': SelectionSort,
      'insertion': InsertionSort,
      'quick': QuickSort,
      'merge': MergeSort
    };
    
    /**
     * Mapping of algorithm IDs to display names.
     * @private
     * @type {Object}
     */
    this.algorithmNames = {
      'bubble': 'Bubble Sort',
      'selection': 'Selection Sort',
      'insertion': 'Insertion Sort',
      'quick': 'Quick Sort',
      'merge': 'Merge Sort'
    };
    
    // Bind methods to maintain proper context
    this.handleAlgorithmChange = this.handleAlgorithmChange.bind(this);
    this.handleSizeChange = this.handleSizeChange.bind(this);
    this.handleGenerateRandom = this.handleGenerateRandom.bind(this);
    this.handleGenerateReversed = this.handleGenerateReversed.bind(this);
    this.handleGenerateCustom = this.handleGenerateCustom.bind(this);
    this.runVisualization = this.runVisualization.bind(this);
  }
  
  /**
   * Initializes the application.
   * Sets up all modules and establishes connections between them.
   */
  init() {
    try {
      // Step 1: Initialize array data with default random values
      this.arrayData = new ArrayData();
      this.arrayData.generateRandom(this.defaultSize);
      
      // Step 2: Initialize visualizer with canvas element
      const canvas = document.getElementById('visualization-canvas');
      if (!canvas) {
        throw new Error('Canvas element not found');
      }
      this.visualizer = new Visualizer(canvas);
      
      // Step 3: Initialize playback controller with visualizer
      this.playbackController = new PlaybackController(this.visualizer);
      
      // Step 4: Initialize UI controller
      this.uiController = new UIController(this, this.playbackController);
      
      // Step 5: Set up event listeners for UI events
      this.setupEventListeners();
      
      // Step 6: Set initial algorithm (default is Bubble Sort)
      this.setAlgorithm('bubble');
      
      // Step 7: Render initial array state
      this.renderInitialState();
      
      console.log('Sorting Algorithm Visualizer initialized successfully');
    } catch (error) {
      console.error('Failed to initialize application:', error);
      this.showError(`Initialization failed: ${error.message}`);
    }
  }
  
  /**
   * Sets up event listeners for UI controller events.
   * @private
   */
  setupEventListeners() {
    if (!this.uiController) {
      throw new Error('UIController not initialized');
    }
    
    // Listen for algorithm selection changes
    this.uiController.on('algorithmChange', this.handleAlgorithmChange);
    
    // Listen for array size changes
    this.uiController.on('sizeChange', this.handleSizeChange);
    
    // Listen for data generation events
    this.uiController.on('generateRandom', this.handleGenerateRandom);
    this.uiController.on('generateReversed', this.handleGenerateReversed);
    this.uiController.on('generateCustom', this.handleGenerateCustom);
    
    // Listen for array data changes
    this.arrayData.on('dataChange', (data) => {
      this.updateArrayInfo();
      this.renderArray();
    });
    
    // Listen for array state changes
    this.arrayData.on('stateChange', (data) => {
      // Update UI status indicator based on array state
      this.updateStatusIndicator(data.state);
    });
  }
  
  /**
   * Handles algorithm selection change from UI.
   * @param {Object} eventData - Event data containing algorithmId and algorithmName
   */
  handleAlgorithmChange(eventData) {
    const { algorithmId } = eventData;
    this.setAlgorithm(algorithmId);
    
    // Reset playback when algorithm changes
    if (this.playbackController) {
      this.playbackController.reset();
    }
    
    // Update algorithm name in UI
    if (this.uiController) {
      this.uiController.updateInfoPanel({
        stats: {
          algorithm: this.algorithmNames[algorithmId] || 'Unknown Algorithm'
        }
      });
    }
    
    // Update status to idle
    this.updateStatusIndicator('idle');
  }
  
  /**
   * Handles array size change from UI.
   * @param {Object} eventData - Event data containing new size
   */
  handleSizeChange(eventData) {
    const { size } = eventData;
    
    // Store the current array type to regenerate with same type
    const algorithmSelect = document.getElementById('algorithm-select');
    const currentAlgorithm = algorithmSelect ? algorithmSelect.value : 'bubble';
    
    // Regenerate array with new size
    this.handleGenerateRandom({ size });
    
    // Reset playback
    if (this.playbackController) {
      this.playbackController.reset();
    }
    
    // Update status to idle
    this.updateStatusIndicator('idle');
  }
  
  /**
   * Handles random array generation request.
   * @param {Object} eventData - Event data containing size
   */
  handleGenerateRandom(eventData) {
    const size = eventData.size || this.defaultSize;
    
    try {
      this.arrayData.generateRandom(size);
      
      // Update UI info
      this.updateArrayInfo();
      
      // Reset playback
      if (this.playbackController) {
        this.playbackController.reset();
      }
      
      // Render the new array
      this.renderArray();
    } catch (error) {
      this.showError(`Failed to generate random array: ${error.message}`);
    }
  }
  
  /**
   * Handles reversed array generation request.
   * @param {Object} eventData - Event data containing size
   */
  handleGenerateReversed(eventData) {
    const size = eventData.size || this.defaultSize;
    
    try {
      this.arrayData.generateReversed(size);
      
      // Update UI info
      this.updateArrayInfo();
      
      // Reset playback
      if (this.playbackController) {
        this.playbackController.reset();
      }
      
      // Render the new array
      this.renderArray();
    } catch (error) {
      this.showError(`Failed to generate reversed array: ${error.message}`);
    }
  }
  
  /**
   * Handles custom array generation request.
   * @param {Object} eventData - Event data containing custom array
   */
  handleGenerateCustom(eventData) {
    const { array } = eventData;
    
    try {
      this.arrayData.setCustomArray(array);
      
      // Update UI info
      this.updateArrayInfo();
      
      // Reset playback
      if (this.playbackController) {
        this.playbackController.reset();
      }
      
      // Render the new array
      this.renderArray();
    } catch (error) {
      this.showError(`Failed to load custom array: ${error.message}`);
    }
  }
  
  /**
   * Sets the current sorting algorithm.
   * @param {string} algorithmId - The ID of the algorithm to set
   * @private
   */
  setAlgorithm(algorithmId) {
    const AlgorithmClass = this.algorithmMap[algorithmId];
    
    if (!AlgorithmClass) {
      console.warn(`Unknown algorithm: ${algorithmId}, defaulting to Bubble Sort`);
      this.currentAlgorithm = new BubbleSort();
      return;
    }
    
    this.currentAlgorithm = new AlgorithmClass();
    console.log(`Algorithm set to: ${this.algorithmNames[algorithmId]}`);
  }
  
  /**
   * Runs the visualization by executing the current algorithm.
   * Records steps and loads them into the playback controller.
   */
  runVisualization() {
    if (!this.currentAlgorithm) {
      this.showError('No algorithm selected');
      return;
    }
    
    if (!this.arrayData) {
      this.showError('No data available');
      return;
    }
    
    try {
      // Save the initial state of the array
      const initialArray = this.arrayData.getArray();
      
      // Set array state to 'sorting'
      this.arrayData.setState('sorting');
      
      // Execute the algorithm directly on the main array data
      console.log('Starting algorithm execution...');
      const steps = this.currentAlgorithm.sort(this.arrayData);
      console.log(`Algorithm completed. Generated ${steps.length} steps`);
      
      // Restore the array to its initial state for playback
      // The steps contain snapshots, so we don't need to keep the sorted array
      this.arrayData.setCustomArray(initialArray);
      this.arrayData.setState('idle');
      
      // Load steps into playback controller
      if (this.playbackController) {
        this.playbackController.loadSteps(steps);
        console.log('Steps loaded into playback controller');
      } else {
        throw new Error('Playback controller not available');
      }
    } catch (error) {
      console.error('Failed to run visualization:', error);
      this.showError(`Algorithm execution failed: ${error.message}`);
      this.arrayData.setState('idle');
    }
  }
  
  /**
   * Renders the current array state.
   * @private
   */
  renderArray() {
    if (!this.visualizer || !this.arrayData) {
      return;
    }
    
    const array = this.arrayData.getArray();
    const stats = {
      comparisons: 0,
      swaps: 0,
      arraySize: array.length,
      algorithm: this.getCurrentAlgorithmName(),
      description: 'Initial array'
    };
    
    this.visualizer.render(array, [], stats);
  }
  
  /**
   * Renders the initial state of the application.
   * @private
   */
  renderInitialState() {
    this.renderArray();
    this.updateArrayInfo();
  }
  
  /**
   * Updates array information in the UI.
   * @private
   */
  updateArrayInfo() {
    if (!this.arrayData || !this.uiController) {
      return;
    }
    
    const array = this.arrayData.getArray();
    const stats = {
      comparisons: 0,
      swaps: 0,
      arraySize: array.length,
      algorithm: this.getCurrentAlgorithmName(),
      description: 'Array ready for sorting'
    };
    
    this.uiController.updateInfoPanel({ stats });
  }
  
  /**
   * Updates the status indicator in the UI.
   * @param {string} status - The status to display
   * @private
   */
  updateStatusIndicator(status) {
    if (!this.uiController) {
      return;
    }
    
    // Map internal states to UI controller statuses
    const statusMap = {
      'idle': 'idle',
      'sorting': 'sorting',
      'sorted': 'sorted'
    };
    
    const uiStatus = statusMap[status] || 'idle';
