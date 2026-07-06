/**
 * EventEmitter class provides a simple event system for objects to communicate.
 * It allows subscribing to events and emitting events with data.
 * @class
 */
class EventEmitter {
  /**
   * Creates an instance of EventEmitter.
   */
  constructor() {
    /**
     * Map of event names to arrays of listener functions.
     * @private
     * @type {Map<string, Function[]>}
     */
    this._events = new Map();
  }

  /**
   * Subscribes to an event.
   * @param {string} event - The name of the event.
   * @param {Function} callback - The function to call when the event is emitted.
   */
  on(event, callback) {
    if (!this._events.has(event)) {
      this._events.set(event, []);
    }
    this._events.get(event).push(callback);
  }

  /**
   * Emits an event, calling all subscribed callbacks with provided arguments.
   * @param {string} event - The name of the event to emit.
   * @param {...any} args - Arguments to pass to the callback functions.
   */
  emit(event, ...args) {
    if (!this._events.has(event)) {
      return;
    }
    const callbacks = this._events.get(event);
    callbacks.forEach(callback => callback(...args));
  }
}

export { EventEmitter };
