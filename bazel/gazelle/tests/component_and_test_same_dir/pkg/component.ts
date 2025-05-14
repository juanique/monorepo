/**
 * A Counter component that manages state
 */
export class Counter {
    private count: number;

    constructor(initialCount: number = 0) {
        this.count = initialCount;
    }

    increment(): number {
        return ++this.count;
    }

    decrement(): number {
        return --this.count;
    }

    getValue(): number {
        return this.count;
    }

    reset(value: number = 0): void {
        this.count = value;
    }
}

/**
 * Utility function that creates a counter with an optional initial value
 */
export function createCounter(initialValue?: number): Counter {
    return new Counter(initialValue);
}
