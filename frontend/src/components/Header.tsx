import React from 'react';
import { Search, TrendingUp, Brain } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <div className="flex items-center">
              <Brain className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">PainFinder AI</h1>
                <p className="text-sm text-gray-500">Поиск болей российских предпринимателей</p>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center text-sm text-gray-600">
              <TrendingUp className="h-4 w-4 mr-1" />
              <span>467 болей найдено</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;