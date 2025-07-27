import React from 'react';
import { BarChart3, PieChart, TrendingUp, Users } from 'lucide-react';
import { AnalyticsData } from '../types';

interface AnalyticsProps {
  data: AnalyticsData;
}

const Analytics: React.FC<AnalyticsProps> = ({ data }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
      {/* Total Pain Points */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center">
          <div className="p-3 bg-blue-50 rounded-lg">
            <BarChart3 className="h-6 w-6 text-blue-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-600">Всего болей</p>
            <p className="text-2xl font-bold text-gray-900">{data.totalPainPoints}</p>
          </div>
        </div>
      </div>

      {/* Top Categories */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center mb-4">
          <PieChart className="h-5 w-5 text-orange-600 mr-2" />
          <h3 className="text-sm font-medium text-gray-900">Топ категории</h3>
        </div>
        <div className="space-y-2">
          {data.topCategories.slice(0, 3).map((category, index) => (
            <div key={index} className="flex justify-between items-center">
              <span className="text-sm text-gray-600">{category.name}</span>
              <span className="text-sm font-medium text-gray-900">{category.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Source Distribution */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center mb-4">
          <Users className="h-5 w-5 text-green-600 mr-2" />
          <h3 className="text-sm font-medium text-gray-900">По источникам</h3>
        </div>
        <div className="space-y-2">
          {data.sourceDistribution.map((source, index) => (
            <div key={index} className="flex justify-between items-center">
              <span className="text-sm text-gray-600">{source.source}</span>
              <span className="text-sm font-medium text-gray-900">{source.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Sentiment Distribution */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center mb-4">
          <TrendingUp className="h-5 w-5 text-purple-600 mr-2" />
          <h3 className="text-sm font-medium text-gray-900">Тональность</h3>
        </div>
        <div className="space-y-2">
          {data.sentimentDistribution.map((sentiment, index) => (
            <div key={index} className="flex justify-between items-center">
              <span className="text-sm text-gray-600">{sentiment.sentiment}</span>
              <span className="text-sm font-medium text-gray-900">{sentiment.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Analytics;