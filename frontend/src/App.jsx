import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useState, useEffect, createContext, useContext } from "react";
import { getUsers } from "./api";
import Home from "./pages/Home";
import GroupDetail from "./pages/GroupDetail";
import NewGroup from "./pages/NewGroup";

export const UserContext = createContext(null);
export const useUser = () => useContext(UserContext);

export default function App() {
  const [users, setUsers] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    getUsers().then((r) => {
      setUsers(r.data);
      if (r.data.length > 0) setCurrentUser(r.data[0]);
    });
  }, []);

  return (
    <UserContext.Provider value={{ currentUser, setCurrentUser, users }}>
      <BrowserRouter>
        <div className="min-h-screen">
          {/* Top Nav */}
          <nav className="sticky top-0 z-50 bg-surface/80 backdrop-blur border-b border-border px-4 py-3 flex items-center justify-between">
            <span className="font-bold text-lg tracking-tight">
              <span className="text-brand-500">Split</span>Smart
            </span>
            <select
              className="bg-card border border-border text-white text-sm rounded-xl px-3 py-1.5 focus:outline-none focus:border-brand-500"
              value={currentUser?.id || ""}
              onChange={(e) =>
                setCurrentUser(users.find((u) => u.id === e.target.value))
              }
            >
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          </nav>

          <div className="max-w-lg mx-auto px-4 py-6">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/groups/new" element={<NewGroup />} />
              <Route path="/groups/:id" element={<GroupDetail />} />
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    </UserContext.Provider>
  );
}