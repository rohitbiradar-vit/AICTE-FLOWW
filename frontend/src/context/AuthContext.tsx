import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiRequest } from '../api/client';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  designation?: string;
  region?: string;
  institution_id?: number;
  institution_name?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  switchRoleQuickLogin: (roleName: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('flowguard_token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('flowguard_user');
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        setUser(null);
      }
    }
    setLoading(false);
  }, [token]);

  const login = async (email: string, password: string) => {
    const res = await apiRequest<{
      access_token: string;
      token_type: string;
      role: string;
      user_id: number;
      full_name: string;
      institution_id?: number;
      institution_name?: string;
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });

    const userData: User = {
      id: res.user_id,
      email,
      full_name: res.full_name,
      role: res.role,
      institution_id: res.institution_id,
      institution_name: res.institution_name
    };

    localStorage.setItem('flowguard_token', res.access_token);
    localStorage.setItem('flowguard_user', JSON.stringify(userData));
    setToken(res.access_token);
    setUser(userData);
  };

  const switchRoleQuickLogin = async (roleEmail: string) => {
    await login(roleEmail, 'DemoPass123!');
  };

  const logout = () => {
    localStorage.removeItem('flowguard_token');
    localStorage.removeItem('flowguard_user');
    setToken(null);
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, switchRoleQuickLogin }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
