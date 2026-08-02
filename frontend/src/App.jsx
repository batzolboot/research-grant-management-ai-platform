import { useEffect, useState } from "react";
import { api } from "./api";
import Dashboard from "./Dashboard";
import LandingPage from "./LandingPage";
import Login from "./Login";
import "./App.css";

function App() {
  const [token, setToken] = useState(
    localStorage.getItem("access_token")
  );

  const [user, setUser] = useState(null);
  const [page, setPage] = useState("landing");
  const [isLoadingUser, setIsLoadingUser] = useState(Boolean(token));
  const [demoError, setDemoError] = useState("");
  const [isDemoLoading, setIsDemoLoading] = useState(false);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get("/auth/me");
      setUser(response.data);
    } catch {
      localStorage.removeItem("access_token");
      setToken(null);
      setUser(null);
      setPage("landing");
    } finally {
      setIsLoadingUser(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, [token]);

  const handleLogin = (accessToken) => {
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
    setIsLoadingUser(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setToken(null);
    setUser(null);
    setPage("landing");
  };

  const handleDemoLogin = async () => {
    setDemoError("");
    setIsDemoLoading(true);

    const loginData = new URLSearchParams();
    loginData.append("username", "demo@example.com");
    loginData.append("password", "demo123");

    try {
      const response = await api.post(
        "/auth/login",
        loginData,
        {
          headers: {
            "Content-Type":
              "application/x-www-form-urlencoded",
          },
        }
      );

      handleLogin(response.data.access_token);
    } catch {
      setDemoError(
        "Demo account is not available yet."
      );
    } finally {
      setIsDemoLoading(false);
    }
  };

  if (token && (isLoadingUser || !user)) {
    return (
      <p className="loading-message">
        Loading application...
      </p>
    );
  }

  if (token && user) {
    return (
      <>
        <div className="top-bar">
          <span>
            {user.email} — {user.role}
          </span>

          <button type="button" onClick={handleLogout}>
            Logout
          </button>
        </div>

        <Dashboard user={user} />
      </>
    );
  }

  if (page === "login") {
    return (
      <Login
        onLogin={handleLogin}
        onBack={() => setPage("landing")}
      />
    );
  }

  return (
    <>
      <LandingPage
        onDemo={handleDemoLogin}
        onLogin={() => setPage("login")}
      />

      {isDemoLoading && (
        <p className="demo-status">
          Starting demo...
        </p>
      )}

      {demoError && (
        <p className="demo-error">
          {demoError}
        </p>
      )}
    </>
  );
}

export default App;