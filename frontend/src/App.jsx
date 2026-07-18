import { useEffect, useState } from "react";
import { api } from "./api";
import Dashboard from "./Dashboard";
import Login from "./Login";
import "./App.css";

function App() {
  const [token, setToken] = useState(
    localStorage.getItem("access_token")
  );

  const [user, setUser] = useState(null);
  const [isLoadingUser, setIsLoadingUser] = useState(Boolean(token));

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get("/auth/me");
      setUser(response.data);
    } catch {
      localStorage.removeItem("access_token");
      setToken(null);
      setUser(null);
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
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  if (isLoadingUser || !user) {
    return <p className="loading-message">Loading...</p>;
  }

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

export default App;