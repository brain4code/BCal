import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types/index.ts';
import apiService from '../services/api.ts';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  console.log('=== AUTH PROVIDER LOADED ===');
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      console.log('=== INITIALIZE AUTH DEBUG ===');
      const token = localStorage.getItem('token');
      console.log('Token from localStorage:', token ? 'exists' : 'not found');
      
      if (token) {
        try {
          console.log('Fetching current user...');
          const userData = await apiService.getCurrentUser();
          console.log('User data from API:', userData);
          console.log('User role:', userData.role);
          setUser(userData);
        } catch (error) {
          console.error('Error fetching user:', error);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
      console.log('=== INITIALIZE AUTH COMPLETE ===');
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      console.log('=== LOGIN DEBUG ===');
      console.log('Logging in with email:', email);
      
      const tokenData = await apiService.login({ email, password });
      console.log('Token received:', tokenData);
      localStorage.setItem('token', tokenData.access_token);
      
      const userData = await apiService.getCurrentUser();
      console.log('User data received:', userData);
      console.log('User role:', userData.role);
      console.log('Setting user in state...');
      setUser(userData);
      console.log('=== LOGIN COMPLETE ===');
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };



  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
  };

  // Debug logging
  console.log('=== AUTH CONTEXT DEBUG ===');
  console.log('User:', user);
  console.log('User role:', user?.role);
  console.log('Is admin:', user?.role === 'admin');
  console.log('Is authenticated:', !!user);
  console.log('========================');



  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
