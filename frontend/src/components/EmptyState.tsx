import React from 'react';
import { Search, AlertCircle } from 'lucide-react';

const EmptyState: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
      <div className="flex justify-center mb-4">
        <div className="p-3 bg-gray-100 rounded-full">
          <Search className="h-8 w-8 text-gray-400" />
        </div>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        Результаты не найдены
      </h3>
      <p className="text-gray-500 mb-6 max-w-md mx-auto">
        Попробуйте изменить параметры поиска или фильтры для получения результатов.
      </p>
      <div className="flex items-center justify-center text-sm text-gray-400">
        <AlertCircle className="h-4 w-4 mr-2" />
        <span>Совет: Используйте более общие ключевые слова</span>
      </div>
    </div>
  );
};

export default EmptyState;