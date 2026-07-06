import { EventEmitter } from '../utils/EventEmitter.js';

/**
 * PlaybackController manages the playback of recorded sorting algorithm steps.
 * Controls the timing, navigation, and rendering of steps during visualization.
 * @extends EventEmitter
 */
export class PlaybackController extends EventEmitter {
  /**
   * Array of recorded steps from the sorting algorithm.
   * @private
   * @type {Object[]}
   */
  #steps = [];

  /**
   * Current step index being displayed.
   * @private
   * @type {number}
   */
  #currentStep = 0;

  /**
   * Speed of playback in milliseconds between steps.
   * @private
   * @type {number}
   */
  #speed = 200;

  /**
   * ID of the active timeout timer for playback.
   * @private
   * @type {number|null}
   */
  #timerId = null;

  /**
   * Whether playback is currently active.
   * @private
   * @type {boolean}
   */
  #isPlaying = false;

  /**
   * Reference to the Visualizer instance for rendering steps.
   * @private
   * @type {Visualizer|null}
   */
  #visualizer = null;

  /**
   * Creates a new PlaybackController instance.
   * @param {Visualizer} visualizer - The Visualizer instance to use for rendering
   */
  constructor(visualizer) {
    super();
    
    if (!visualizer || 
        typeof visualizer.render !== 'function' || 
        typeof visualizer.clear !== 'function') {
      throw new Error('Valid Visualizer instance with render and clear methods is required');
    }
    
    this.#visualizer = visualizer;
  }

  /**
   * Loads new steps for playback and resets to initial state.
   * Emits 'stepsLoaded' event with step count.
   * @param {Object[]} steps - Array of step objects to load
   */
  loadSteps(steps) {
    if (!Array.isArray(steps)) {
      throw new Error('Steps must be an array');
    }

    // Create a deep copy of steps to prevent external mutation
    this.#steps = steps.map(step => ({
      ...step,
      array: [...step.array],
      highlights: [...step.highlights],
      stats: { ...step.stats }
    }));
    
    this.#currentStep = 0;
    this.#isPlaying = false;
    
    // Clear any active playback
    this.#clearTimer();
    
    // Emit event before rendering to allow UI updates
    this.emit('stepsLoaded', {
      stepCount: this.#steps.length,
      currentStep: this.#currentStep
    });

    // Render the first step if available
    if (this.#steps.length > 0) {
      this.#renderCurrentStep();
      // Emit step change event for initial state
      this.emit('stepChange', {
        currentStep: this.#currentStep,
        totalSteps: this.#steps.length,
        stepData: this.getCurrentStepData()
      });
    } else {
      this.#visualizer.clear();
    }
  }

  /**
   * Starts or resumes playback of steps.
   * Emits 'playStateChange' event with current state.
   * If already playing or no steps available, does nothing.
   */
  play() {
    if (this.#isPlaying || this.#steps.length === 0) {
      return;
    }

    // If at the last step, reset to beginning and render immediately
    if (this.#currentStep >= this.#steps.length - 1) {
      this.#currentStep = 0;
      this.#renderCurrentStep();
      this.emit('stepChange', {
        currentStep: this.#currentStep,
        totalSteps: this.#steps.length,
        stepData: this.getCurrentStepData()
      });
    }

    this.#isPlaying = true;
    this.emit('playStateChange', { isPlaying: this.#isPlaying });
    
    // Start the playback sequence
    this.#scheduleNextStep();
  }

  /**
   * Pauses the current playback.
   * Emits 'playStateChange' event with current state.
   */
  pause() {
    if (!this.#isPlaying) {
      return;
    }

    this.#isPlaying = false;
    this.#clearTimer();
    this.emit('playStateChange', { isPlaying: this.#isPlaying });
  }

  /**
   * Advances to the next step if available.
   * If playing, pauses playback first.
   * Emits 'stepChange' event with new step index.
   */
  next() {
    // Pause if currently playing
    if (this.#isPlaying) {
      this.pause();
    }

    if (this.#currentStep < this.#steps.length - 1) {
      this.#currentStep++;
      this.#renderCurrentStep();
      this.emit('stepChange', {
        currentStep: this.#currentStep,
        totalSteps: this.#steps.length,
        stepData: this.getCurrentStepData()
      });
    }
  }

  /**
   * Goes back to the previous step if available.
   * If playing, pauses playback first.
   * Emits 'stepChange' event with new step index.
   */
  prev() {
    // Pause if currently playing
    if (this.#isPlaying) {
      this.pause();
    }

    if (this.#currentStep > 0) {
      this.#currentStep--;
      this.#renderCurrentStep();
      this.emit('stepChange', {
        currentStep: this.#currentStep,
        totalSteps: this.#steps.length,
        stepData: this.getCurrentStepData()
      });
    }
  }

  /**
   * Resets playback to the first step.
   * Pauses playback if active.
   * Emits 'reset' event.
   */
  reset() {
    this.pause();
    
    if (this.#steps.length > 0 && this.#currentStep !== 0) {
      this.#currentStep = 0;
      this.#renderCurrentStep();
      this.emit('stepChange', {
        currentStep: this.#currentStep,
        totalSteps: this.#steps.length,
        stepData: this.getCurrentStepData()
      });
    }
    
    this.emit('reset');
  }

  /**
   * Sets the playback speed.
   * If currently playing, reschedules the next step with new speed.
   * @param {number} speed - New speed in milliseconds between steps (1-1000)
   */
  setSpeed(speed) {
    if (typeof speed !== 'number' || speed <= 0 || speed > 1000) {
      throw new Error('Speed must be a number between 1 and 1000 milliseconds');
    }

    const oldSpeed = this.#speed;
    this.#speed = speed;
    
    // Reschedule if currently playing and speed actually changed
    if (this.#isPlaying && oldSpeed !== speed) {
      this.#clearTimer();
      this.#scheduleNextStep();
    }

    this.emit('speedChange', { speed: this.#speed });
  }

  /**
   * Gets the current playback speed.
   * @return {number} Current speed in milliseconds
   */
  getSpeed() {
    return this.#speed;
  }

  /**
   * Gets whether playback is currently active.
   * @return {boolean} True if currently playing
   */
  isPlaying() {
    return this.#isPlaying;
  }

  /**
   * Gets the current step index.
   * @return {number} Current step index (0-based)
   */
  getCurrentStep() {
    return this.#currentStep;
  }

  /**
   * Gets the total number of loaded steps.
   * @return {number} Total step count
   */
  getTotalSteps() {
    return this.#steps.length;
  }

  /**
   * Gets the current step data.
   * @return {Object|null} Current step object or null if no steps
   */
  getCurrentStepData() {
    if (this.#steps.length === 0 || this.#currentStep >= this.#steps.length) {
      return null;
    }
    
    const step = this.#steps[this.#currentStep];
    return {
      ...step,
      array: [...step.array],
      highlights: [...step.highlights],
      stats: { ...step.stats }
    };
  }

  /**
   * Clears the active timer if one exists.
   * @private
   */
  #clearTimer() {
    if (this.#timerId !== null) {
      clearTimeout(this.#timerId);
      this.#timerId = null;
    }
  }

  /**
   * Schedules the next step for automatic playback.
   * @private
   */
  #scheduleNextStep() {
    if (!this.#isPlaying) {
      return;
    }

    this.#timerId = setTimeout(() => {
      // Check if we should continue playing
      if (!this.#isPlaying) {
        return;
      }

      // Move to next step if available
      if (this.#currentStep < this.#steps.length - 1) {
        this.#currentStep++;
        this.#renderCurrentStep();
        this.emit('stepChange', {
          currentStep: this.#currentStep,
          totalSteps: this.#steps.length,
          stepData: this.getCurrentStepData()
        });
        
        // Schedule next step
        this.#scheduleNextStep();
      } else {
        // Reached the end
        this.#isPlaying = false;
        this.#timerId = null;
        this.emit('playStateChange', { isPlaying: this.#isPlaying });
        this.emit('playbackComplete');
      }
    }, this.#speed);
  }

  /**
   * Renders the current step using the visualizer.
   * @private
   */
  #renderCurrentStep() {
    if (this.#steps.length === 0 || this.#currentStep >= this.#steps.length) {
      return;
    }

    const step = this.#steps[this.#currentStep];
    
    // Validate step structure
    if (!step || 
        !Array.isArray(step.array) || 
        !Array.isArray(step.highlights) || 
        !step.stats || 
        typeof step.stats !== 'object') {
      console.error('Invalid step structure at index', this.#currentStep, ':', step);
      return;
    }

    try {
      this.#visualizer.render(step.array, step.highlights, step.stats);
    } catch (error) {
      console.error('Failed to render step:', error);
    }
  }

  /**
   * Cleans up resources before disposal.
   */
  dispose() {
    this.pause();
    this.#steps = [];
    this.#visualizer = null;
    this.#clearTimer();
  }
}
