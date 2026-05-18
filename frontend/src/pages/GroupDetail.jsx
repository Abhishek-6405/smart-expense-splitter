import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getGroup, getExpenses, createExpense, deleteExpense,
  getBalances, getSettleUp, parseExpense, parseBill, createSettlement
} from "../api";
import { useUser } from "../App";

const fmt = (paise) => `₹${(paise / 100).toFixed(2)}`;
const TABS = ["Expenses", "Balances", "Settle Up", "AI Parse"];

export default function GroupDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useUser();
  const [group, setGroup] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [balances, setBalances] = useState([]);
  const [settleUp, setSettleUp] = useState([]);
  const [tab, setTab] = useState("Expenses");
  const [loading, setLoading] = useState(true);
  const [showExpenseForm, setShowExpenseForm] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const g = await getGroup(id);
        setGroup(g.data);
        try { const e = await getExpenses(id); setExpenses(e.data); } catch {}
        try { const b = await getBalances(id); setBalances(b.data); } catch {}
        try { const s = await getSettleUp(id); setSettleUp(s.data); } catch {}
      } catch (err) {
        console.error("Group load error:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const refresh = async () => {
    try { const e = await getExpenses(id); setExpenses(e.data); } catch {}
    try { const b = await getBalances(id); setBalances(b.data); } catch {}
    try { const s = await getSettleUp(id); setSettleUp(s.data); } catch {}
  };

  const handleDelete = async (eid) => {
    await deleteExpense(id, eid);
    refresh();
  };

  const handleSettle = async (txn) => {
    await createSettlement(id, {
      from_user: txn.from_user_id,
      to_user: txn.to_user_id,
      amount_paise: txn.amount_paise,
    });
    refresh();
  };

  if (loading) return <div className="text-white/40 text-center mt-20">Loading...</div>;
  if (!group) return <div className="text-white/40 text-center mt-20">Group not found</div>;

  const filtered = expenses.filter((e) =>
    e.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <button className="btn-ghost mb-3 -ml-2" onClick={() => navigate("/")}>← Back</button>
      <h1 className="text-2xl font-bold mb-1">{group.name}</h1>
      {group.description && <p className="text-white/40 text-sm mb-4">{group.description}</p>}

      {/* Members */}
      <div className="flex gap-1.5 flex-wrap mb-5">
        {group.members?.map((m) => (
          <span
            key={m.id}
            className="text-xs px-2.5 py-1 rounded-full font-medium"
            style={{ backgroundColor: m.avatar_color + "22", color: m.avatar_color }}
          >
            {m.name}
          </span>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-card rounded-xl p-1 mb-5 border border-border">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 text-xs py-2 rounded-lg font-medium transition-all ${
              tab === t ? "bg-brand-500 text-white" : "text-white/40 hover:text-white"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* EXPENSES TAB */}
      {tab === "Expenses" && (
        <div>
          <div className="flex gap-2 mb-4">
            <input className="input flex-1" placeholder="Search expenses..." value={search} onChange={e => setSearch(e.target.value)} />
            <button className="btn-primary whitespace-nowrap" onClick={() => setShowExpenseForm(true)}>+ Add</button>
          </div>
          {filtered.length === 0 && (
            <div className="card text-center py-10">
              <p className="text-3xl mb-2">💸</p>
              <p className="text-white/40">No expenses yet</p>
            </div>
          )}
          <div className="space-y-3">
            {filtered.map((e) => (
              <div key={e.id} className="card">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold truncate">{e.description}</p>
                    <p className="text-white/40 text-xs mt-0.5">
                      Paid by <span className="text-white/70">{e.paid_by_user?.name}</span> · {new Date(e.date).toLocaleDateString("en-IN")}
                    </p>
                    <p className="text-xs text-white/30 mt-1">
                      Split: {e.shares?.map(s => `${s.user?.name} ${fmt(s.share_paise)}`).join(", ")}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="font-bold font-mono text-brand-500">{fmt(e.amount_paise)}</p>
                    <button
                      onClick={() => handleDelete(e.id)}
                      className="text-white/20 hover:text-rose-400 text-xs mt-1 transition-colors"
                    >
                      delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* BALANCES TAB */}
      {tab === "Balances" && (
        <div className="space-y-3">
          {balances.length === 0 && <div className="card text-center py-10 text-white/40">No balances yet</div>}
          {balances.map((b) => (
            <div key={b.user_id} className="card flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center font-bold"
                  style={{ backgroundColor: b.avatar_color + "33", color: b.avatar_color }}
                >
                  {b.user_name[0]}
                </div>
                <span className="font-medium">{b.user_name}</span>
              </div>
              <span className={b.net_balance_paise > 0 ? "badge-positive" : b.net_balance_paise < 0 ? "badge-negative" : "badge-neutral"}>
                {b.net_balance_paise > 0 ? "+" : ""}{fmt(b.net_balance_paise)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* SETTLE UP TAB */}
      {tab === "Settle Up" && (
        <div className="space-y-3">
          {settleUp.length === 0 && (
            <div className="card text-center py-10">
              <p className="text-3xl mb-2">✅</p>
              <p className="text-white/40">All settled up!</p>
            </div>
          )}
          {settleUp.map((txn, i) => (
            <div key={i} className="card">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="font-medium text-sm">
                    <span className="text-rose-400">{txn.from_user_name}</span>
                    <span className="text-white/30 mx-2">→</span>
                    <span className="text-emerald-400">{txn.to_user_name}</span>
                  </p>
                  <p className="font-bold font-mono text-brand-500 mt-0.5">{fmt(txn.amount_paise)}</p>
                </div>
                <button
                  className="text-xs bg-emerald-500/15 text-emerald-400 px-3 py-1.5 rounded-lg hover:bg-emerald-500/25 transition-all"
                  onClick={() => handleSettle(txn)}
                >
                  Mark Settled
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AI PARSE TAB */}
      {tab === "AI Parse" && <AIParseTab groupId={id} group={group} currentUser={currentUser} onSaved={refresh} />}

      {/* ADD EXPENSE MODAL */}
      {showExpenseForm && (
        <ExpenseModal
          group={group}
          currentUser={currentUser}
          onClose={() => setShowExpenseForm(false)}
          onSaved={() => { refresh(); setShowExpenseForm(false); }}
        />
      )}
    </div>
  );
}

// ---- Expense Modal ----
function ExpenseModal({ group, currentUser, onClose, onSaved }) {
  const [form, setForm] = useState({
    paid_by: currentUser?.id || "",
    amount_paise: "",
    description: "",
    date: new Date().toISOString().slice(0, 10),
    split_mode: "equal",
    shares: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const members = group.members || [];

  const amountRupees = parseFloat(form.amount_paise) || 0;
  const amountPaise = Math.round(amountRupees * 100);

  const computeShares = () => {
    if (form.split_mode === "equal") {
      const n = members.length;
      const base = Math.floor(amountPaise / n);
      const rem = amountPaise % n;
      return members.map((m, i) => ({ user_id: m.id, share_paise: base + (i < rem ? 1 : 0) }));
    }
    return form.shares;
  };

  const submit = async () => {
    setError("");
    const shares = computeShares();
    const total = shares.reduce((a, s) => a + s.share_paise, 0);
    if (total !== amountPaise) { setError(`Shares sum to ₹${total/100} but expense is ₹${amountPaise/100}`); return; }
    setLoading(true);
    try {
      await createExpense(group.id, { ...form, amount_paise: amountPaise, date: new Date(form.date).toISOString(), shares });
      onSaved();
    } catch (e) {
      setError(e.response?.data?.detail || "Error saving expense");
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-end" onClick={onClose}>
      <div className="bg-card border border-border rounded-t-3xl p-5 w-full max-w-lg mx-auto space-y-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Add Expense</h2>
          <button onClick={onClose} className="text-white/40 hover:text-white text-2xl leading-none">×</button>
        </div>

        <input className="input" placeholder="Description *" value={form.description} onChange={e => setForm(f => ({...f, description: e.target.value}))} />

        <input className="input" type="number" placeholder="Amount (₹)" value={form.amount_paise} onChange={e => setForm(f => ({...f, amount_paise: e.target.value}))} />

        <div>
          <label className="text-white/40 text-xs mb-1 block">Paid by</label>
          <select className="input" value={form.paid_by} onChange={e => setForm(f => ({...f, paid_by: e.target.value}))}>
            {members.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
        </div>

        <div>
          <label className="text-white/40 text-xs mb-1 block">Date</label>
          <input className="input" type="date" value={form.date} onChange={e => setForm(f => ({...f, date: e.target.value}))} />
        </div>

        <div>
          <label className="text-white/40 text-xs mb-1 block">Split Mode</label>
          <select className="input" value={form.split_mode} onChange={e => setForm(f => ({...f, split_mode: e.target.value, shares: []}))}>
            <option value="equal">Equal (all members)</option>
            <option value="custom">Custom</option>
          </select>
        </div>

        {form.split_mode === "custom" && (
          <div className="space-y-2">
            <p className="text-white/40 text-xs">Enter share per person (₹)</p>
            {members.map(m => (
              <div key={m.id} className="flex items-center gap-2">
                <span className="text-white/70 text-sm flex-1">{m.name}</span>
                <input
                  className="input w-28 text-right"
                  type="number"
                  placeholder="0"
                  onChange={e => {
                    const paise = Math.round(parseFloat(e.target.value || 0) * 100);
                    setForm(f => {
                      const existing = f.shares.filter(s => s.user_id !== m.id);
                      return {...f, shares: [...existing, { user_id: m.id, share_paise: paise }]};
                    });
                  }}
                />
              </div>
            ))}
          </div>
        )}

        {error && <p className="text-rose-400 text-sm bg-rose-500/10 rounded-xl px-3 py-2">{error}</p>}

        <button className="btn-primary w-full py-3" onClick={submit} disabled={loading || !form.description || !form.amount_paise}>
          {loading ? "Saving..." : "Save Expense"}
        </button>
      </div>
    </div>
  );
}

// ---- AI Parse Tab ----
function AIParseTab({ groupId, group, currentUser, onSaved }) {
  const [nlText, setNlText] = useState("");
  const [billText, setBillText] = useState("");
  const [result, setResult] = useState(null);
  const [billResult, setBillResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [billLoading, setBillLoading] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const handleNLParse = async () => {
    setError(""); setResult(null);
    setLoading(true);
    try {
      const res = await parseExpense({ text: nlText, group_id: groupId, current_user_id: currentUser?.id });
      if (!res.data.success) { setError(res.data.error || "Parse failed"); }
      else setResult(res.data);
    } catch { setError("AI service unavailable. Use manual entry."); }
    finally { setLoading(false); }
  };

  const handleSaveAI = async () => {
    if (!result) return;
    setSaving(true);
    try {
      await createExpense(groupId, {
        paid_by: result.payer_id,
        amount_paise: result.amount_paise,
        description: result.description,
        date: result.date || new Date().toISOString(),
        split_mode: result.split_mode || "custom",
        shares: result.shares.map(s => ({ user_id: s.user_id, share_paise: s.share_paise })),
      });
      setResult(null); setNlText("");
      onSaved();
      alert("Expense saved!");
    } catch (e) { setError(e.response?.data?.detail || "Save failed"); }
    finally { setSaving(false); }
  };

  const handleBillParse = async () => {
    setBillResult(null);
    setBillLoading(true);
    try {
      const res = await parseBill({ bill_text: billText, group_id: groupId });
      setBillResult(res.data);
    } catch { setBillResult({ success: false, error: "AI service unavailable" }); }
    finally { setBillLoading(false); }
  };

  return (
    <div className="space-y-6">
      {/* Natural Language */}
      <div className="card space-y-3">
        <h3 className="font-semibold text-brand-500">🧠 Natural Language Entry</h3>
        <p className="text-white/40 text-xs">Type an expense in plain English or Hinglish</p>
        <textarea
          className="input resize-none"
          rows={3}
          placeholder='e.g. "I paid 2400 for dinner last night, split equally between me, Aman, and Priya"'
          value={nlText}
          onChange={e => setNlText(e.target.value)}
        />
        <button className="btn-primary w-full" onClick={handleNLParse} disabled={loading || !nlText.trim()}>
          {loading ? "Parsing..." : "Parse with AI"}
        </button>

        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3">
            <p className="text-rose-400 text-sm">⚠️ {error}</p>
            <p className="text-white/30 text-xs mt-1">Falling back to manual entry</p>
          </div>
        )}

        {result && (
          <div className="bg-brand-500/10 border border-brand-500/30 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-brand-500 font-semibold text-sm">✓ Parsed ({Math.round(result.confidence * 100)}% confidence)</p>
            </div>
            <p className="text-white/70 text-sm"><span className="text-white/40">Description:</span> {result.description}</p>
            <p className="text-white/70 text-sm"><span className="text-white/40">Payer:</span> {result.payer_name}</p>
            <p className="text-white/70 text-sm"><span className="text-white/40">Amount:</span> ₹{(result.amount_paise/100).toFixed(2)}</p>
            <p className="text-white/70 text-sm"><span className="text-white/40">Shares:</span> {result.shares?.map(s => `${s.user_name} ₹${(s.share_paise/100).toFixed(2)}`).join(", ")}</p>
            <button className="btn-primary w-full mt-2" onClick={handleSaveAI} disabled={saving}>
              {saving ? "Saving..." : "✓ Confirm & Save"}
            </button>
          </div>
        )}
      </div>

      {/* Bill Parser */}
      <div className="card space-y-3">
        <h3 className="font-semibold text-brand-500">🧾 Bill Text Parser</h3>
        <p className="text-white/40 text-xs">Paste raw bill/receipt text</p>
        <textarea
          className="input resize-none"
          rows={4}
          placeholder={"Butter Chicken - 350\nNaan x2 - 60\nLassi - 80\nTotal: 490"}
          value={billText}
          onChange={e => setBillText(e.target.value)}
        />
        <button className="btn-primary w-full" onClick={handleBillParse} disabled={billLoading || !billText.trim()}>
          {billLoading ? "Parsing..." : "Parse Bill"}
        </button>

        {billResult && !billResult.success && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3">
            <p className="text-rose-400 text-sm">⚠️ {billResult.error}</p>
          </div>
        )}

        {billResult?.success && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 space-y-2">
            <p className="text-emerald-400 font-semibold text-sm">✓ Bill Parsed</p>
            {billResult.items?.map((item, i) => (
              <div key={i} className="flex justify-between text-sm">
                <span className="text-white/70">{item.item_name} {item.quantity > 1 && `×${item.quantity}`}</span>
                <span className="font-mono text-white/70">₹{(item.amount_paise/100).toFixed(2)}</span>
              </div>
            ))}
            <div className="border-t border-border pt-2 flex justify-between font-bold">
              <span>Total</span>
              <span className="font-mono text-brand-500">₹{((billResult.total_paise || 0)/100).toFixed(2)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}