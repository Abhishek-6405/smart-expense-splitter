import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createGroup } from "../api";
import { useUser } from "../App";

export default function NewGroup() {
  const { users, currentUser } = useUser();
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const toggle = (uid) =>
    setSelected((s) =>
      s.includes(uid) ? s.filter((x) => x !== uid) : [...s, uid]
    );

  const submit = async () => {
    if (!name.trim() || selected.length < 1) return;
    const memberIds = selected.includes(currentUser?.id)
      ? selected
      : [currentUser?.id, ...selected];
    setLoading(true);
    try {
      const res = await createGroup({
        name,
        description: desc,
        created_by: currentUser?.id,
        member_ids: memberIds,
      });
      navigate(`/groups/${res.data.id}`);
    } catch (e) {
      alert(e.response?.data?.detail || "Error creating group");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button className="btn-ghost mb-4 -ml-2" onClick={() => navigate("/")}>
        ← Back
      </button>
      <h1 className="text-2xl font-bold mb-6">New Group</h1>

      <div className="space-y-4">
        <div>
          <label className="text-white/50 text-sm mb-1.5 block">Group Name *</label>
          <input
            className="input"
            placeholder="e.g. Goa Trip 2025"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div>
          <label className="text-white/50 text-sm mb-1.5 block">Description</label>
          <input
            className="input"
            placeholder="Optional"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
          />
        </div>

        <div>
          <label className="text-white/50 text-sm mb-2 block">
            Add Members ({selected.length} selected)
          </label>
          <div className="space-y-2">
            {users.map((u) => {
              const isMe = u.id === currentUser?.id;
              const sel = selected.includes(u.id) || isMe;
              return (
                <div
                  key={u.id}
                  onClick={() => !isMe && toggle(u.id)}
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                    sel
                      ? "border-brand-500/60 bg-brand-500/10"
                      : "border-border bg-card hover:border-border/80"
                  } ${isMe ? "opacity-60 cursor-default" : ""}`}
                >
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
                    style={{ backgroundColor: u.avatar_color + "44" }}
                  >
                    <span style={{ color: u.avatar_color }}>{u.name[0]}</span>
                  </div>
                  <span className="flex-1 font-medium">
                    {u.name} {isMe && <span className="text-white/30 text-xs">(you)</span>}
                  </span>
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                      sel ? "border-brand-500 bg-brand-500" : "border-border"
                    }`}
                  >
                    {sel && <span className="text-white text-xs">✓</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <button
          className="btn-primary w-full py-3 mt-2"
          onClick={submit}
          disabled={loading || !name.trim()}
        >
          {loading ? "Creating..." : "Create Group"}
        </button>
      </div>
    </div>
  );
}