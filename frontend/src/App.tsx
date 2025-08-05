import Header from './components/Header';
import SearchFilters from './components/SearchFilters';
import Analytics from './components/Analytics';
import PainPointCard from './components/PainPointCard';
import EmptyState from './components/EmptyState';
import { usePainPoints } from './hooks/usePainPoints';
import { mockAnalytics } from './data/mockData';

function App() {
  const { 
    painPoints, 
    filters, 
    setFilters, 
    exportToCSV, 
    isLoading, 
    error, 
    useApi, 
    setUseApi 
  } = usePainPoints();

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

        {error && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="text-yellow-800">
                  <p className="font-medium">Предупреждение</p>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
              <button
                onClick={() => setUseApi(!useApi)}
                className="ml-4 px-3 py-1 bg-yellow-100 text-yellow-800 rounded text-sm hover:bg-yellow-200"
              >
                {useApi ? 'Перейти к тестовым данным' : 'Попробовать API снова'}
              </button>
            </div>
          </div>
        )}

        <Analytics data={mockAnalytics} />

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span className="text-gray-600">Загружаем данные...</span>
            </div>
          </div>
        )}

        {!isLoading && painPoints.length > 0 ? (
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