export interface PainPoint {
  id: string;
  text: string;
  source: 'vk' | 'telegram' | 'pikabu';
  date: string;
  sentiment: 'negative' | 'neutral' | 'positive';
  sentiment_score: number;
  category: string;
  mentions: number;
  author: string;
  url: string;
  keywords: string[];
}

export interface SearchFilters {
  query: string;
  sources: string[];
  dateFrom: string;
  dateTo: string;
  sentiment: string;
  category: string;
}

export interface AnalyticsData {
  totalPainPoints: number;
  topCategories: Array<{ name: string; count: number }>;
  sourceDistribution: Array<{ source: string; count: number }>;
  sentimentDistribution: Array<{ sentiment: string; count: number }>;
  trends: Array<{ date: string; count: number }>;
}