import React from 'react';
import Header from './components/Header';
import SearchFilters from './components/SearchFilters';
import Analytics from './components/Analytics';
import PainPointCard from './components/PainPointCard';
import EmptyState from './components/EmptyState';
import { usePainPoints } from './hooks/usePainPoints';
import { mockAnalytics } from './data/mockData';

function App() {
  const { painPoints, filters, setFilters, exportToCSV } = usePainPoints();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Найди свою нишу
          </h2>
          <p className="text-lg text-gray-600">
            Анализируй "боли" российских предпринимателей в социальных сетях и находи неудовлетворённые потребности
          </p>
        </div>

        <SearchFilters 
          filters={filters}
          onFiltersChange={setFilters}
          onExport={exportToCSV}
        />

        <Analytics data={mockAnalytics} />

        {painPoints.length > 0 ? (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-gray-900">
                Найдено {painPoints.length} болей
              </h3>
              <div className="text-sm text-gray-500">
                Отсортировано по количеству упоминаний
              </div>
            </div>
            
            <div className="grid grid-cols-1 gap-6">
              {painPoints.map((painPoint) => (
                <PainPointCard key={painPoint.id} painPoint={painPoint} />
              ))}
            </div>
          </div>
        ) : (
          <EmptyState />
        )}
      </main>

      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500">
            <p className="mb-2">PainFinder AI - MVP для поиска болей российских предпринимателей</p>
            <p className="text-sm">Данные получены из VK API, TgStat, и веб-скрейпинга Pikabu</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;