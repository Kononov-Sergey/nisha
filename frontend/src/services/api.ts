import { PainPoint } from '../types';

export interface SearchRequest {
  keywords: string[];
  platforms?: string[];
  date_from?: string;
  date_to?: string;
}

export interface ApiPainPoint {
  id: number;
  source: string;
  author: string;
  text: string;
  url?: string;
  pain_keywords: string[];
  sentiment_score: number;
  pain_intensity: number;
  created_at: string;
}

export interface ExportResponse {
  filename: string;
  content: string;
}

const API_BASE_URL = '/api';

class ApiService {
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async searchPains(request: SearchRequest): Promise<ApiPainPoint[]> {
    return this.makeRequest<ApiPainPoint[]>('/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getResults(
    platform?: string,
    minIntensity?: number,
    limit: number = 50
  ): Promise<ApiPainPoint[]> {
    const params = new URLSearchParams();
    if (platform) params.append('platform', platform);
    if (minIntensity !== undefined) params.append('min_intensity', minIntensity.toString());
    params.append('limit', limit.toString());

    return this.makeRequest<ApiPainPoint[]>(`/results?${params.toString()}`);
  }

  async exportTopPains(): Promise<ExportResponse> {
    return this.makeRequest<ExportResponse>('/export');
  }
}

// Функция для преобразования API данных в формат фронтенда
export function mapApiPainPoint(apiPoint: ApiPainPoint): PainPoint {
  return {
    id: apiPoint.id.toString(),
    text: apiPoint.text,
    source: apiPoint.source as 'vk' | 'telegram' | 'pikabu',
    author: apiPoint.author,
    date: apiPoint.created_at.split('T')[0], // Преобразуем datetime в date
    category: 'Общее', // Пока используем дефолтную категорию
    sentiment: apiPoint.sentiment_score > 0 ? 'positive' : 
               apiPoint.sentiment_score < -0.3 ? 'negative' : 'neutral',
    mentions: Math.round(apiPoint.pain_intensity * 10), // Приблизительное количество упоминаний
    sentiment_score: apiPoint.sentiment_score,
    keywords: apiPoint.pain_keywords,
    url: apiPoint.url || ''
  };
}

export const apiService = new ApiService();