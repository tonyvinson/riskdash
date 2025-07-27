import React, { useState } from 'react';
import KSIManager from './components/KSIManager/KSIManager';
import TenantOnboarding from './components/TenantOnboarding/TenantOnboarding';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [notification, setNotification] = useState(null);

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleOnboardingComplete = (result) => {
    showNotification(`Tenant onboarded successfully! Tenant ID: ${result.tenant_id}`);
    setCurrentView('dashboard');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'onboarding':
        return <TenantOnboarding onComplete={handleOnboardingComplete} />;
      case 'dashboard':
      default:
        return <KSIManager />;
    }
  };

  return (
    <div className="App min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                🛡️ Riskuity KSI Validator
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setCurrentView('dashboard')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'dashboard'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setCurrentView('onboarding')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'onboarding'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                New Tenant
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 max-w-sm p-4 rounded-md shadow-lg z-50 ${
          notification.type === 'success' 
            ? 'bg-green-50 border border-green-200 text-green-700'
            : 'bg-red-50 border border-red-200 text-red-700'
        }`}>
          {notification.message}
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto">
        {renderCurrentView()}
      </main>
    </div>
  );
}

export default App;
