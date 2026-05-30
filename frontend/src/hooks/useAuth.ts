"use client";

import { useState, useEffect, useRef } from "react";

interface AuthState {
  token: string | null;
  role: string | null;
  isLoaded: boolean;
}

const initialState: AuthState = {
  token: null,
  role: null,
  isLoaded: false,
};

export function useAuth() {
  const [auth, setAuth] = useState<AuthState>(initialState);
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    const token = localStorage.getItem("access_token");
    const role = localStorage.getItem("user_role");

    setAuth({
      token,
      role,
      isLoaded: true,
    });
  }, []);

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_role");
    setAuth({ token: null, role: null, isLoaded: true });
    window.location.href = "/login";
  };

  return {
    token: auth.token,
    role: auth.role,
    isLoaded: auth.isLoaded,
    isLoggedIn: !!auth.token,
    isAdmin: auth.role === "admin",
    isModerator: auth.role === "moderator" || auth.role === "admin",
    logout,
  };
}
