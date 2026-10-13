export type User = { id: string; name: string; email: string; role: 'dietitian' | 'patient' };
export type Nutrition = { calories: number; protein: number; carbs: number; fat: number };
export type Food = {
  id: string;
  name: string;
  unit: number;
  nutrition: Nutrition;
  properties: { thermal: string; digestibility: string };
  rasas: string[];
  allergens: string[];
  source: string;
  dosha_impact: Record<string, string>;
};
export type Meal = {
  meal: string;
  food_id: string;
  grams: number;
  name?: string;
  nutrition?: Nutrition;
};
export type Plan = {
  id: string;
  version: number;
  title: string;
  notes: string;
  status: string;
  items: Meal[];
  totals: Nutrition;
  created_at: string;
};
export type Assessment = {
  id: string;
  kind: string;
  result: string;
  scores: Record<string, number>;
  created_at: string;
};
export type CheckIn = { day: string; adherence: number; energy: number; note: string };
export type Patient = {
  id: string;
  name: string;
  age: number;
  gender: string;
  email: string;
  allergies: string[];
  notes: string;
  status: string;
  portal_active: boolean;
  created_at: string;
  plans?: Plan[];
  assessments?: Assessment[];
  checkins?: CheckIn[];
};
export type Dashboard = {
  active_patients: number;
  published_plans: number;
  assessed_patients: number;
  needs_plan: number;
  events: { id: string; action: string; created_at: string }[];
};
