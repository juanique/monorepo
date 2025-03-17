import { sum } from './utils';

describe('sum', () => {
    it('adds two numbers correctly', () => {
        expect(sum(1, 2)).toBe(3);
    });
});
