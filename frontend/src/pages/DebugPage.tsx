import React from 'react';
import { useAuth } from '../contexts/AuthContext.tsx';

const DebugPage: React.FC = () => {
  const { user, isAdmin, isAuthenticated, loading } = useAuth();

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Debug Information</h1>
      
      <div className="bg-white shadow rounded-lg p-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold mb-2">Authentication Status</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Loading:</span> {loading ? 'Yes' : 'No'}
            </div>
            <div>
              <span className="font-medium">Authenticated:</span> {isAuthenticated ? 'Yes' : 'No'}
            </div>
            <div>
              <span className="font-medium">Is Admin:</span> {isAdmin ? 'Yes' : 'No'}
            </div>
          </div>
        </div>

        {user && (
          <div>
            <h2 className="text-lg font-semibold mb-2">User Information</h2>
            <div className="bg-gray-50 p-4 rounded">
              <pre className="text-sm overflow-auto">
                {JSON.stringify(user, null, 2)}
              </pre>
            </div>
          </div>
        )}

        <div>
          <h2 className="text-lg font-semibold mb-2">Local Storage</h2>
          <div className="bg-gray-50 p-4 rounded">
            <div className="text-sm">
              <div><strong>Token:</strong> {localStorage.getItem('token') ? 'Present' : 'Not found'}</div>
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">Admin Tab Logic</h2>
          <div className="bg-gray-50 p-4 rounded text-sm">
            <div>User role: <code>{user?.role || 'undefined'}</code></div>
            <div>Role === 'admin': <code>{user?.role === 'admin' ? 'true' : 'false'}</code></div>
            <div>isAdmin value: <code>{isAdmin ? 'true' : 'false'}</code></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DebugPage;
