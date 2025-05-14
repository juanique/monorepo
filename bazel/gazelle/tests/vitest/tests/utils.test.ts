import { expect, test, describe } from 'vitest';
import { add, subtract, multiply } from './lib/utils';

describe('Math utils', () => {
  test('add works correctly', () => {
    expect(add(2, 3)).toBe(5);
    expect(add(-1, 1)).toBe(0);
    expect(add(0, 0)).toBe(0);
  });

  test('subtract works correctly', () => {
    expect(subtract(5, 2)).toBe(3);
    expect(subtract(1, 1)).toBe(0);
    expect(subtract(0, 5)).toBe(-5);
  });

  test('multiply works correctly', () => {
    expect(multiply(2, 3)).toBe(6);
    expect(multiply(-2, 3)).toBe(-6);
    expect(multiply(0, 5)).toBe(0);
  });
});
