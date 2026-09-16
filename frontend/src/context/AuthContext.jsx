import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  const fetchMe = useCallback(async () => {
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      localStorage.setItem('user', JSON.stringify(res.data));
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    if (token && storedUser) {
      // eslint-disable-next-line react/set-state-in-effect -- rehydrate session from storage on mount
      setUser(JSON.parse(storedUser));
      fetchMe();
    } else {
      setLoading(false);
    }
  }, [fetchMe]);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    const { access_token } = res.data;
    localStorage.setItem('token', access_token);
    await fetchMe();
  };

  const register = async (data) => {
    await api.post('/auth/register', data);
  };

  const loginWithOtp = async (email, code) => {
    const res = await api.post('/auth/login/verify', { email, code });
    const { access_token } = res.data;
    localStorage.setItem('token', access_token);
    await fetchMe();
  };

  return (
    <AuthContext.Provider value={{ user, setUser, login, register, logout, loading, loginWithOtp, fetchMe }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react/only-export-components -- hook co-located with its provider by design
export function useAuth() {
  return useContext(AuthContext);
}