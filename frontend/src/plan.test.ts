import { describe, it, expect } from 'vitest';
import { previewNutrition } from './plan';
import type { Food } from './types';
const food: Food = {
  id: 'rice',
  name: 'Rice',
  unit: 100,
  nutrition: { calories: 130, protein: 2.7, carbs: 28, fat: 0.3 },
  properties: { thermal: 'Cold', digestibility: 'Easy' },
  rasas: ['Sweet'],
  allergens: [],
  source: 'Demo',
  dosha_impact: {},
};
describe('nutrition preview', () => {
  it('scales the demo unit to grams', () => {
    expect(
      previewNutrition([{ meal: 'Lunch', food_id: 'rice', grams: 150 }], [food]).calories,
    ).toBe(195);
  });
  it('adds portions across meals', () => {
    expect(
      previewNutrition(
        [
          { meal: 'Lunch', food_id: 'rice', grams: 100 },
          { meal: 'Dinner', food_id: 'rice', grams: 100 },
        ],
        [food],
      ).carbs,
    ).toBe(56);
  });
  it('starts at zero for an empty plan', () => {
    expect(previewNutrition([], [])).toEqual({ calories: 0, protein: 0, carbs: 0, fat: 0 });
  });
});
