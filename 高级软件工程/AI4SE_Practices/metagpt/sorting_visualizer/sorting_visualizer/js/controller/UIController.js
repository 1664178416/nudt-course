## js/controller/UIController.js
```javascript
import { EventEmitter } from '../utils/EventEmitter.js';

/**
 * UIController manages all user interface interactions and updates.
 * Binds event listeners to UI elements and coordinates with Main and PlaybackController.
 * @extends EventEmitter
 */
export class UIController extends EventEmitter {
  /**
   * Creates a new UIController instance.
   * @param {Main} main - The Main application instance
   * @param {PlaybackController} playbackController - The PlaybackController instance
   */
  constructor(main, playbackController) {
    super();
    
    if (!main || typeof main.runVisualization !== 'function') {
      throw new Error('Valid Main instance with runVisualization method is required');
    }
    
    if (!playbackController || typeof playbackController.play !== 'function') {
      throw new Error('Valid PlaybackController instance is required');
    }
    
    /** @private {Main} */
    this.main = main;
    
    /** @private {PlaybackController} */
    this.playbackController = playbackController;
    
    /** @private {HTMLSelectElement} */
    this.algorithmSelect = null;
    
    /** @private {HTMLInputElement} */
    this.sizeSlider = null;
    
    /** @private {HTMLElement} */
    this.sizeValue = null;
    
    /** @private {HTMLButtonElement} */
    this.generateRandomBtn = null;
    
    /** @private {HTMLButtonElement} */
    this.generateReversedBtn = null;
    
    /** @private {HTMLInputElement} */
    this.customArrayInput = null;
    
    /** @private {HTMLButtonElement} */
    this.loadCustomBtn = null;
    
    /** @private {HTMLButtonElement} */
    this.playBtn = null;
    
    /** @private {HTMLButtonElement} */
    this.pauseBtn = null;
    
    /** @private {HTMLButtonElement} */
    this.prevBtn = null;
    
    /** @private {HTMLButtonElement} */
    this.nextBtn = null;
    
    /** @private {HTMLButtonElement} */
    this.resetBtn = null;
    
    /** @private {HTMLInputElement} */
    this.speedSlider = null;
    
    /** @private {HTMLElement} */
    this.speedValue = null;
    
    /** @private {HTMLElement} */
    this.statusIndicator = null;
    
    /** @private {HTMLElement} */
    this.stepCounter = null;
    
    /** @private {HTMLElement} */
    this.comparisonsCount = null;
    
    /** @private {HTMLElement} */
    this.swapsCount = null;
    
    /** @private {HTMLElement} */
    this.arraySize = null;
    
    /** @private {HTMLElement} */
    this.currentAlgorithm = null;
    
    /** @private {HTMLElement} */
    this.stepDescription = null;
    
    // Initialize UI elements and bind events
    this._initElements();
    this.bindEvents();
    
    // Listen to playback controller events
    this._setupPlaybackListeners();
  }
  
  /**
   * Initializes all UI element references.
   * @private
   */
  _initElements() {
    this.algorithmSelect = document.getElementById('algorithm-select');
    this.sizeSlider = document.getElementById('size-slider');
    this.sizeValue = document.getElementById('size-value');
    this.generateRandomBtn = document.getElementById('generate-random');
    this.generateReversedBtn = document.getElementById('generate-reversed');
    this.customArrayInput = document.getElementById('custom-array-input');
    this.loadCustomBtn = document.getElementById('load-custom');
    this.playBtn = document.getElementById('play-btn');
    this.pauseBtn = document.getElementById('pause-btn');
    this.prevBtn = document.getElementById('prev-btn');
    this.nextBtn = document.getElementById('next-btn');
    this.resetBtn = document.getElementById('reset-btn');
    this.speedSlider = document.getElementById('speed-slider');
    this.speedValue = document.getElementById('speed-value');
    this.statusIndicator = document.getElementById('status-indicator');
    this.stepCounter = document.getElementById('step-counter');
    this.comparisonsCount = document.getElementById('comparisons-count');
    this.swapsCount = document.getElementById('swaps-count');
    this.arraySize = document.getElementById('array-size');
    this.currentAlgorithm = document.getElementById('current-algorithm');
    this.stepDescription = document.getElementById('step-description');
    
    // Validate all required elements are found
    const elements = [
      this.algorithmSelect, this.sizeSlider, this.sizeValue, this.generateRandomBtn,
      this.generateReversedBtn, this.customArrayInput, this.loadCustomBtn, this.playBtn,
      this.pauseBtn, this.prevBtn, this.nextBtn, this.resetBtn, this.speedSlider,
      this.speedValue, this.statusIndicator, this.stepCounter, this.comparisonsCount,
      this.swapsCount, this.arraySize, this.currentAlgorithm, this.stepDescription
    ];
    
    for (const element of elements) {
      if (!element) {
        throw new Error('Required UI element not found. Check index.html structure.');
      }
    }
  }
  
  /**
   * Sets up event listeners for playback controller events.
   * @private
   */
  _setupPlaybackListeners() {
    this.playbackController.on('stepsLoaded', (data) => {
      this.updateInfoPanel({
        stats: { comparisons: 0, swaps: 0 },
        description: 'Steps loaded. Ready to play.'
      });
      // Use 1-based step display for user interface (step 1 of N)
      const displayCurrentStep = data.stepCount > 0 ? 1 : 0;
      this._updateStepCounter(displayCurrentStep, data.stepCount);
      this._updatePlaybackControls(data.stepCount > 0);
    });
    
    this.playbackController.on('stepChange', (data) => {
      // Convert 0-based index to 1-based for display
      const displayStep = data.currentStep + 1;
      this._updateStepCounter(displayStep, data.totalSteps);
      if (data.stepData) {
        this.updateInfoPanel(data.stepData);
      }
    });
    
    this.playbackController.on('playStateChange', (data) => {
      this._updatePlayState(data.isPlaying);
    });
    
    this.playbackController.on('reset', () => {
      this._updateStepCounter(0, this.playbackController.getTotalSteps());
      this._updatePlayState(false);
    });
    
    this.playbackController.on('speedChange', (data) => {
      this._updateSpeedDisplay(data.speed);
    });
    
    this.playbackController.on('playbackComplete', () => {
      this._updatePlayState(false);
      const totalSteps = this.playbackController.getTotalSteps();
      this._updateStepCounter(totalSteps, totalSteps);
      this._updateStatus('sorted');
    });
  }
  
  /**
   * Binds all event listeners to UI elements.
   */
  bindEvents() {
    // Algorithm selection
    this.algorithmSelect.addEventListener('change', () => this.onAlgorithmChange());
    
    // Array size control
    this.sizeSlider.addEventListener('input', () => this.onSizeChange());
    this.sizeSlider.addEventListener('change', () => this.onSizeChange());
    
    // Data generation buttons
    this.generateRandomBtn.addEventListener('click', () => this.onGenerateClick('random'));
    this.generateReversedBtn.addEventListener('click', () => this.onGenerateClick('reversed'));
    this.loadCustomBtn.addEventListener('click', () => this.onGenerateClick('custom'));
    
    // Playback control buttons
    this.playBtn.addEventListener('click', () => this.onPlaybackClick('play'));
    this.pauseBtn.addEventListener('click', () => this.onPlaybackClick('pause'));
    this.prevBtn.addEventListener('click', () => this.onPlaybackClick('prev'));
    this.nextBtn.addEventListener('click', () => this.onPlaybackClick('next'));
    this.resetBtn.addEventListener('click', () => this.onPlaybackClick('reset'));
    
    // Speed control
    this.speedSlider.addEventListener('input', () => this.onSpeedChange());
    this.speedSlider.addEventListener('change', () => this.onSpeedChange());
  }
  
  /**
   * Handles algorithm selection change.
   * Updates the current algorithm display and resets playback.
   */
  onAlgorithmChange() {
    const algorithmName = this.algorithmSelect.options[this.algorithmSelect.selectedIndex].text;
    this.currentAlgorithm.textContent = algorithmName;
    
    // Emit event for Main to handle
    this.emit('algorithmChange', {
      algorithmId: this.algorithmSelect.value,
      algorithmName: algorithmName
    });
    
    // Reset playback and update status
    this.playbackController.reset();
    this._updateStatus('idle');
    this._updatePlaybackControls(false);
  }
  
  /**
   * Handles array size slider change.
   * Updates the displayed size value.
   */
  onSizeChange() {
    const size = parseInt(this.sizeSlider.value);
    this.sizeValue.textContent = size;
    this.arraySize.textContent = size;
    
    // Emit event for Main to handle
    this.emit('sizeChange', { size: size });
  }
  
  /**
   * Handles data generation button clicks.
   * @param {string} type - The type of generation: 'random', 'reversed', or 'custom'
   */
  onGenerateClick(type) {
    switch (type) {
      case 'random':
        this.emit('generateRandom', { size: parseInt(this.sizeSlider.value) });
        break;
        
      case 'reversed':
        this.emit('generateReversed', { size: parseInt(this.sizeSlider.value) });
        break;
        
      case 'custom':
        const input = this.customArrayInput.value.trim();
        if (!input) {
          this._showInputError('Please enter numbers separated by commas.');
          return;
        }
        
        try {
          const numbers = input.split(',')
            .map(num => num.trim())
            .filter(num => num.length > 0)
            .map(num => {
              const parsed = parseFloat(num);
              if (isNaN(parsed)) {
                throw new Error(`"${num}" is not a valid number`);
              }
              return parsed;
            });
          
          if (numbers.length === 0) {
            throw new Error('No valid numbers found');
          }
          
          // Use the same maximum size as the size slider
          const maxSize = parseInt(this.sizeSlider.max) || 100;
          if (numbers.length > maxSize) {
            throw new Error(`Maximum array size is ${maxSize}`);
          }
          
          this.emit('generateCustom', { array: numbers });
          this._clearInputError();
        } catch (error) {
          this._showInputError(error.message);
        }
        break;
    }
    
    // Reset playback after generating new data
    this.playbackController.reset();
    this._updateStatus('idle');
    this._updatePlaybackControls(false);
  }
  
  /**
   * Handles playback control button clicks.
   * @param {string} action - The action to perform: 'play', 'pause', 'prev', 'next', 'reset'
   */
  onPlaybackClick(action) {
    switch (action) {
      case 'play':
        if (this.playbackController.getTotalSteps() === 0) {
          // No steps recorded yet, start visualization
          this._updateStatus('sorting');
          this.main.runVisualization();
        } else {
          // Resume playback
          this.playbackController.play();
          this._updateStatus('playing');
        }
        break;
        
      case 'pause':
        this.playbackController.pause();
        this._updateStatus('paused');
        break;
        
      case 'prev':
        this.playbackController.prev();
        this._updateStatus('paused');
        break;
        
      case 'next':
        this.playbackController.next();
        this._updateStatus('paused');
        break;
        
      case 'reset':
        this.playbackController.reset();
        this._updateStatus('idle');
        break;
    }
  }
  
  /**
   * Handles speed slider change.
   * Updates the playback speed.
   */
  onSpeedChange() {
    const speedLevel = parseInt(this.speedSlider.value); // 1-10
    // Map 1->500ms, 10->50ms (linear)
    const speedMs = 550 - speedLevel * 50;
    this.playbackController.setSpeed(speedMs);
    this._updateSpeedDisplay(speedMs);
  }
  
  /**
   * Updates the information panel with step data.
   * @param {Object} step - The step object containing stats and description
   */
  updateInfoPanel(step) {
    if (!step || !step.stats) {
      return;
    }
    
    // Update statistics
    this.comparisonsCount.textContent = step.stats.comparisons || 0;
    this.swapsCount.textContent = step.stats.swaps || 0;
    
    // Update step description
    if (step.stats.description) {
      this.stepDescription.textContent = step.stats.description;
    }
    
    // Update array size if provided in stats
    if (step.stats.arraySize) {
      this.arraySize.textContent = step.stats.arraySize;
    }
    
    // Update algorithm name if provided in stats
    if (step.stats.algorithm) {
      this.currentAlgorithm.textContent = step.stats.algorithm;
    }
  }
  
  /**
   * Updates the speed display value.
   * @param {number} speedMs - Speed in milliseconds
   * @private
   */
  _updateSpeedDisplay(speedMs) {
    // Convert ms to a friendly speed level (1-10) for display
    // speedMs range should be 50-500 (1->500ms, 10->50ms)
    const speedLevel = Math.max(1, Math.min(10, Math.round((550 - speedMs) / 50)));
    this.speedValue.textContent = speedLevel;
  }
  
  /**
   * Shows an error message for the custom array input.
   * @param {string} message - Error message to display
   * @private
   */
  _showInputError(message) {
    this._clearInputError();
    
    let errorEl = this.customArrayInput.parentNode.querySelector('.input-error');
    if (!errorEl) {
      errorEl = document.createElement('div');
      errorEl.className = 'input-error';
      this.customArrayInput.parentNode.appendChild(errorEl);
    }
    
    errorEl.textContent = message;
    errorEl.classList.add('active');
    this.customArrayInput.classList.add('error');
  }
  
  /**
   * Clears any displayed input error.
   * @private
   */
  _clearInputError() {
    const errorEl = this.customArrayInput.parentNode.querySelector('.input-error');
    if (errorEl) {
      errorEl.classList.remove('active');
      errorEl.textContent = '';
    }
    this.customArrayInput.classList.remove('error');
  }
  
  /**
   * Updates the visual state of a button based on disabled property.
   * @param {HTMLButtonElement} button - The button to update
   * @private
   */
  _updateButtonState(button) {
    if (button.disabled) {
      button.classList.add('disabled');
    } else {
      button.classList.remove('disabled');
    }
  }
  
  /**
   * Updates the step counter display.
   * @param {number} currentStep - Current step number (1-based display)
   * @param {number} totalSteps - Total number of steps
   * @private
   */
  _updateStepCounter(currentStep, totalSteps) {
    if (totalSteps === 0) {
      this.stepCounter.textContent = 'Step: 0/0';
    } else {
      this.stepCounter.textContent = `Step: ${currentStep}/${totalSteps}`;
    }
  }
  
  /**
   * Updates the playback control buttons state.
   * @param {boolean} hasSteps - Whether steps are loaded for playback
   * @private
   */
  _updatePlaybackControls(hasSteps) {
    const isPlaying = this.playbackController.isPlaying();
    const currentStep = this.playbackController.getCurrentStep();
    const totalSteps = this.playbackController.getTotalSteps();
    
    // Determine if steps are truly loaded and usable
    const stepsAvailable = hasSteps && totalSteps > 0;
    
    // Play/Pause buttons
    this.playBtn.disabled = (isPlaying || (stepsAvailable && currentStep === totalSteps));
    this.pauseBtn.disabled = !isPlaying;
    
    // Step navigation buttons
    this.prevBtn.disabled = !stepsAvailable || currentStep === 0;
    this.nextBtn.disabled = !stepsAvailable || currentStep === totalSteps - 1;
    
    // Reset button
    this.resetBtn.disabled = !stepsAvailable || (currentStep === 0 && !isPlaying);
    
    // Update button styles
    [this.playBtn, this.pauseBtn, this.prevBtn, this.nextBtn, this.resetBtn]
      .forEach(btn => this._updateButtonState(btn));
  }
  
  /**
   * Updates the status indicator with a new state.
   * @param {string} status - The status: 'idle', 'sorting', 'playing', 'paused', 'sorted'
   * @private
   */
  _updateStatus(status) {
    const statusTextMap = {
      'idle': 'Idle',
      'sorting': 'Sorting...',
      'playing': 'Playing',
      'paused': 'Paused',
      'sorted': 'Sorted'
    };
    
    this.statusIndicator.textContent = statusTextMap[status] || 'Unknown';
    
    // Remove all status classes
    this.statusIndicator.classList.remove(
      'status-idle', 'status-sorting', 'status-playing', 
      'status-paused',