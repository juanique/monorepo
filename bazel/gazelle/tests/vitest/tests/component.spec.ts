import { expect, test, describe } from 'vitest';
import { nested } from "tests/lib/nested/nested"
import { Component } from './lib/component';

describe('Component', () => {
  test('returns the correct message', () => {
    expect(Component()).toBe('Component rendered');
    nested()
  });

  test('has the correct properties', () => {
    const component = { name: 'test-component', render: Component };
    expect(component).toHaveProperty('name');
    expect(component).toHaveProperty('render');
  });
});
