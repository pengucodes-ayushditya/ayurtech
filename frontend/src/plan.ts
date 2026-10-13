import type { Food, Meal, Nutrition } from './types';
export function previewNutrition(items: Meal[], foods: Food[]): Nutrition {
  const total: Nutrition = { calories: 0, protein: 0, carbs: 0, fat: 0 };
  for (const item of items) {
    const food = foods.find((f) => f.id === item.food_id);
    if (food)
      for (const k of Object.keys(total) as (keyof Nutrition)[])
        total[k] += (food.nutrition[k] * item.grams) / food.unit;
  }
  return total;
}
