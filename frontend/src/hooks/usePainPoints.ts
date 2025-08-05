import { useState, useMemo, useEffect, useCallback } from 'react';
import { PainPoint, SearchFilters } from '../types';
import { mockPainPoints } from '../data/mockData';
import { apiService, mapApiPainPoint } from '../services/api';

export const usePainPoints = () => {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    sources: ['vk', 'telegram', 'pikabu'],
    dateFrom: '2025-01-10',
    dateTo: '2025-01-15',
    sentiment: '',
    category: 'Все категории'
  });

  const [apiPainPoints, setApiPainPoints] = useState<PainPoint[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useApi, setUseApi] = useState(true); // Переключатель между API и mock данными

  // Функция загрузки данных из API
  const loadPainPoints = useCallback(async () => {
    if (!useApi) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const results = await apiService.getResults();
      const mappedResults = results.map(mapApiPainPoint);
      setApiPainPoints(mappedResults);
    } catch (err) {
      console.error('Failed to load pain points:', err);
      setError('Не удалось загрузить данные. Показываем тестовые данные.');
      setUseApi(false); // Переключаемся на mock данные при ошибке
    } finally {
      setIsLoading(false);
    }
  }, [useApi]);

  // Загрузка данных при инициализации
  useEffect(() => {
    loadPainPoints();
  }, [useApi, loadPainPoints]);

  // Выбираем источник данных
  const sourcePainPoints = useApi ? apiPainPoints : mockPainPoints;

  const filteredPainPoints = useMemo(() => {
    return sourcePainPoints.filter((painPoint) => {
      // Query filter
      if (filters.query) {
        const query = filters.query.toLowerCase();
        if (!painPoint.text.toLowerCase().includes(query) &&
            !painPoint.keywords.some(keyword => keyword.toLowerCase().includes(query))) {
          return false;
        }
      }

      // Source filter
      if (filters.sources.length > 0 && !filters.sources.includes(painPoint.source)) {
        return false;
      }

      // Date filter
      if (filters.dateFrom && painPoint.date < filters.dateFrom) {
        return false;
      }
      if (filters.dateTo && painPoint.date > filters.dateTo) {
        return false;
      }

      // Sentiment filter
      if (filters.sentiment && painPoint.sentiment !== filters.sentiment) {
        return false;
      }

      // Category filter
      if (filters.category && filters.category !== 'Все категории' && painPoint.category !== filters.category) {
        return false;
      }

      return true;
    });
  }, [sourcePainPoints, filters]);

  const exportToCSV = () => {
    const topPainPoints = filteredPainPoints
      .sort((a, b) => b.mentions - a.mentions)
      .slice(0, 5);

    const csvContent = [
      ['Текст', 'Источник', 'Дата', 'Категория', 'Тональность', 'Упоминания', 'Автор'].join(','),
      ...topPainPoints.map(pp => [
        `"${pp.text.replace(/"/g, '""')}"`,
        pp.source,
        pp.date,
        pp.category,
        pp.sentiment,
        pp.mentions,
        pp.author
      ].join(','))
    ].join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'top_pain_points.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return {
    painPoints: filteredPainPoints,
    filters,
    setFilters,
    exportToCSV,
    isLoading,
    error,
    useApi,
    setUseApi,
    loadPainPoints
  };
};