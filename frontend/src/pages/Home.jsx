import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getGroups } from "../api";

export default function Home() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getGroups()
      .then((r) => setGroups(r.data))
      .finally(() => setLoading(false));
  }, []);

  const colors = ["#6366f1", "#ec4899", "#14b8a6", "#f97316", "#8b5cf6", "#22c55e"];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Your Groups</h1>
          <p className="text-white/40 text-sm mt-0.5">Track shared expenses</p>
        </div>
        <button className="btn-primary" onClick={() => navigate("/groups/new")}>
          + New
        </button>
      </div>

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse h-20 bg-card/50" />
          ))}
        </div>
      )}

      {!loading && groups.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-4xl mb-3">👥</p>
          <p className="text-white/60">No groups yet.</p>
          <p className="text-white/30 text-sm mt-1">Create one to get started</p>
        </div>
      )}

      <div className="space-y-3">
        {groups.map((g, i) => (
          <div
            key={g.id}
            className="card cursor-pointer hover:border-brand-500/50 transition-all"
            onClick={() => navigate(`/groups/${g.id}`)}
          >
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg flex-shrink-0"
                style={{ backgroundColor: colors[i % colors.length] + "33", border: `1px solid ${colors[i % colors.length]}55` }}
              >
                <span style={{ color: colors[i % colors.length] }}>
                  {g.name[0]}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold truncate">{g.name}</p>
                <p className="text-white/40 text-sm">
                  {g.members?.length || 0} members · {g.currency}
                </p>
              </div>
              <span className="text-white/20 text-xl">›</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}