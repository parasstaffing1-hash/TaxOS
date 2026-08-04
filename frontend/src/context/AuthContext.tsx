"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { API_BASE } from "@/lib/api";
import { isRecord, type AuthUser } from "@/lib/types";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function isAuthUser(value: unknown): value is AuthUser {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.email === "string" &&
    typeof value.is_active === "boolean" &&
    typeof value.created_at === "string"
  );
}

async function responseError(response: Response, fallback: string): Promise<Error> {
  const body: unknown = await response.json().catch(() => null);
  if (isRecord(body) && typeof body.detail === "string") {
    return new Error(body.detail);
  }
  return new Error(fallback);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadCurrentUser = async (): Promise<AuthUser | null> => {
    const response = await fetch(`${API_BASE}/auth/me`, { credentials: "include" });
    if (!response.ok) {
      return null;
    }

    const body: unknown = await response.json();
    return isAuthUser(body) ? body : null;
  };

  useEffect(() => {
    let active = true;

    void loadCurrentUser()
      .then((currentUser) => {
        if (active) {
          setUser(currentUser);
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    const form = new URLSearchParams({ username: email, password });
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
      credentials: "include",
    });
    if (!response.ok) {
      throw await responseError(response, "Unable to sign in.");
    }

    const currentUser = await loadCurrentUser();
    if (!currentUser) {
      throw new Error("Signed in, but the session could not be confirmed.");
    }
    setUser(currentUser);
  };

  const register = async (email: string, password: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      credentials: "include",
    });
    if (!response.ok) {
      throw await responseError(response, "Unable to create the account.");
    }
    await login(email, password);
  };

  const logout = async (): Promise<void> => {
    try {
      await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
