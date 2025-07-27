import React from 'react';
import { ExternalLink, MessageCircle, Calendar, Hash } from 'lucide-react';
import { PainPoint } from '../types';

interface PainPointCardProps {
  painPoint: PainPoint;
}

const PainPointCard: React.FC<PainPointCardProps> = ({ painPoint }) => {
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'negative': return 'text-red-600 bg-red-50';
      case 'neutral': return 'text-yellow-600 bg-yellow-50';
      case 'positive': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getSentimentLabel = (sentiment: string) => {
    switch (sentiment) {
      case 'negative': return 'Негативная';
      case 'neutral': return 'Нейтральная';
      case 'positive': return 'Позитивная';
      default: return 'Неопределённая';
    }
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'vk': return 'bg-blue-500';
      case 'telegram': return 'bg-sky-500';
      case 'pikabu': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getSourceLabel = (source: string) => {
    switch (source) {
      case 'vk': return 'VK';
      case 'telegram': return 'Telegram';
      case 'pikabu': return 'Pikabu';
      default: return source;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSourceColor(painPoint.source)} text-white`}>
              {getSourceLabel(painPoint.source)}
            </span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(painPoint.sentiment)}`}>
              {getSentimentLabel(painPoint.sentiment)}
            </span>
            <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
              {painPoint.category}
            </span>
          </div>
          <div className="flex items-center text-gray-500 text-sm">
            <MessageCircle className="h-4 w-4 mr-1" />
            <span>{painPoint.mentions}</span>
          </div>
        </div>

        {/* Content */}
        <p className="text-gray-900 mb-4 leading-relaxed">
          {painPoint.text}
        </p>

        {/* Keywords */}
        <div className="flex flex-wrap gap-2 mb-4">
          {painPoint.keywords.map((keyword, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-md"
            >
              <Hash className="h-3 w-3 mr-1" />
              {keyword}
            </span>
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t">
          <div className="flex items-center space-x-4">
            <span className="font-medium">{painPoint.author}</span>
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-1" />
              <span>{new Date(painPoint.date).toLocaleDateString('ru-RU')}</span>
            </div>
          </div>
          <a
            href={painPoint.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center text-blue-600 hover:text-blue-800 transition-colors"
          >
            <ExternalLink className="h-4 w-4 mr-1" />
            Источник
          </a>
        </div>
      </div>
    </div>
  );
};

export default PainPointCard;