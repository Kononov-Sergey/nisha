import React from 'react';
import { Search, Filter, Calendar, Download } from 'lucide-react';
import { SearchFilters as SearchFiltersType } from '../types';
import { categories, sources } from '../data/mockData';

interface SearchFiltersProps {
  filters: SearchFiltersType;
  onFiltersChange: (filters: SearchFiltersType) => void;
  onExport: () => void;
}

const SearchFilters: React.FC<SearchFiltersProps> = ({ filters, onFiltersChange, onExport }) => {
  const handleInputChange = (field: keyof SearchFiltersType, value: string | string[]) => {
    onFiltersChange({ ...filters, [field]: value });
  };

  const handleSourceToggle = (sourceId: string) => {
    const newSources = filters.sources.includes(sourceId)
      ? filters.sources.filter(s => s !== sourceId)
      : [...filters.sources, sourceId];
    handleInputChange('sources', newSources);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-4">
        {/* Search Query */}
        <div className="lg:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Поисковый запрос
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={filters.query}
              onChange={(e) => handleInputChange('query', e.target.value)}
              placeholder="Введите ключевые слова..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Category Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Категория
          </label>
          <select
            value={filters.category}
            onChange={(e) => handleInputChange('category', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {categories.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>

        {/* Sentiment Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Тональность
          </label>
          <select
            value={filters.sentiment}
            onChange={(e) => handleInputChange('sentiment', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Все</option>
            <option value="negative">Негативная</option>
            <option value="neutral">Нейтральная</option>
            <option value="positive">Позитивная</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-end">
        {/* Date Filters */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              От
            </label>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => handleInputChange('dateFrom', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              До
            </label>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => handleInputChange('dateTo', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Source Filters */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Источники
          </label>
          <div className="flex space-x-2">
            {sources.map((source) => (
              <button
                key={source.id}
                onClick={() => handleSourceToggle(source.id)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filters.sources.includes(source.id)
                    ? `${source.color} text-white`
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {source.label}
              </button>
            ))}
          </div>
        </div>

        {/* Export Button */}
        <div className="flex justify-end">
          <button
            onClick={onExport}
            className="flex items-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
          >
            <Download className="h-4 w-4 mr-2" />
            Экспорт CSV
          </button>
        </div>
      </div>
    </div>
  );
};

export default SearchFilters;