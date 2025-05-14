import { expect, test, describe } from 'vitest';
import { Counter, createCounter } from 'pkg/component';

describe('Counter', () => {
    test('initializes with default value', () => {
        const counter = new Counter();
        expect(counter.getValue()).toBe(0);
    });

    test('initializes with provided value', () => {
        const counter = new Counter(10);
        expect(counter.getValue()).toBe(10);
    });

    test('increment increases count by 1', () => {
        const counter = new Counter(5);
        expect(counter.increment()).toBe(6);
        expect(counter.getValue()).toBe(6);
    });

    test('decrement decreases count by 1', () => {
        const counter = new Counter(5);
        expect(counter.decrement()).toBe(4);
        expect(counter.getValue()).toBe(4);
    });

    test('reset changes count to specified value', () => {
        const counter = new Counter(5);
        counter.reset(10);
        expect(counter.getValue()).toBe(10);
    });

    test('reset without argument resets to 0', () => {
        const counter = new Counter(5);
        counter.reset();
        expect(counter.getValue()).toBe(0);
    });
});

describe('createCounter', () => {
    test('creates a counter with default value', () => {
        const counter = createCounter();
        expect(counter.getValue()).toBe(0);
    });

    test('creates a counter with specified value', () => {
        const counter = createCounter(15);
        expect(counter.getValue()).toBe(15);
    });
});
