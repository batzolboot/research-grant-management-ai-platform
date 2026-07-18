import { useState } from "react";
import Dashboard from "./Dashboard";
import Login from "./Login";
import "./App.css";

function App() {
  const [token, setToken] = useState(
    localStorage.getItem("access_token")
  );

  const handleLogin = (accessToken) => {
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setToken(null);
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <>
      <div className="top-bar">
        <button type="button" onClick={handleLogout}>
          Logout
        </button>
      </div>

      <Dashboard />
    </>
  );
}

export default App;