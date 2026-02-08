import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar,
} from "recharts";
import type { AgentStatus, TaskHistory, TaskResult, ReputationData, WSMessage } from "../types";
import { useWebSocket } from "../hooks/useWebSocket";
import PaymentStream from "./PaymentStream";
import ReputationCard from "./ReputationCard";
import ApiCallHistory from "./ApiCallHistory";

const DEMO_QUERIES = [
  { query: "What's the weather in New Haven?", priority: "high" },
  { query: "Get me the BTC price", priority: "normal" },
  { query: "Latest crypto news", priority: "normal" },
  { query: "NVDA stock price", priority: "high" },
  { query: "Weather in Tokyo", priority: "normal" },
  { query: "STX stock price", priority: "critical" },
  { query: "News about AI", priority: "low" },
  { query: "ETH price", priority: "normal" },
];

export default function AgentDashboard() {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [tasks, setTasks] = useState<TaskHistory[]>([]);
  const [reputation, setReputation] = useState<ReputationData | null>(null);
  const [balanceHistory, setBalanceHistory] = useState<{ time: string; balance: number }[]>([]);
  const [taskInput, setTaskInput] = useState("");
  const [taskPriority, setTaskPriority] = useState("normal");
  const [running, setRunning] = useState(false);
  const [lastResult, setLastResult] = useState<TaskResult | null>(null);
  const [demoRunning, setDemoRunning] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([
        axios.get("/agent/status"),
        axios.get("/agent/tasks"),
      ]);
      setStatus(s.data);
      setTasks(t.data);
      // Update balance history
      setBalanceHistory((prev) => {
        const entry = { time: new Date().toLocaleTimeString(), balance: s.data.wallet.balance_sats };
        const next = [...prev, entry];
        return next.slice(-30);
      });
      // Load reputation
      if (s.data.agent_id) {
        const r = await axios.get(`/reputation/${s.data.agent_id}`);
        setReputation(r.data);
      }
    } catch {}
  }, []);

  useEffect(() => {
    loadData();
    const id = setInterval(loadData, 8000);
    return () => clearInterval(id);
  }, [loadData]);

  const { connected } = useWebSocket(
    useCallback(() => { loadData(); }, [loadData])
  );

  const runTask = async (query: string, priority: string) => {
    setRunning(true);
    try {
      const resp = await axios.post("/agent/task", { query, priority });
      setLastResult(resp.data);
      await loadData();
    } catch {}
    setRunning(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskInput.trim()) return;
    await runTask(taskInput, taskPriority);
    setTaskInput("");
  };

  const runDemo = async () => {
    setDemoRunning(true);
    for (const q of DEMO_QUERIES) {
      await runTask(q.query, q.priority);
      await new Promise((r) => setTimeout(r, 600));
    }
    setDemoRunning(false);
  };

  const fundAgent = async () => {
    await axios.post("/agent/fund", { amount_sats: 5000 });
    await loadData();
  };

  const pnlColor = status
    ? status.wallet.balance_sats >= status.wallet.initial_balance
      ? "text-green-400"
      : "text-red-400"
    : "text-gray-400";

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-bitcoin text-2xl font-bold">&#x20BF;</span>
            <h1 className="text-xl font-bold text-white">BitAgent</h1>
            <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">
              AI Agent OS
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className={`text-xs flex items-center gap-1.5 ${connected ? "text-green-400" : "text-red-400"}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-green-400" : "bg-red-400"}`} />
              {connected ? "WebSocket Live" : "Disconnected"}
            </span>
            <button
              onClick={fundAgent}
              className="px-3 py-1 text-xs bg-bitcoin/20 text-bitcoin rounded-lg hover:bg-bitcoin/30 transition"
            >
              + Fund 5000 sats
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Top row: Wallet stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: "Balance", value: `${status?.wallet.balance_sats.toLocaleString() ?? "..."} sats`, color: pnlColor },
            { label: "Total Spent", value: `${status?.wallet.total_spent.toLocaleString() ?? 0} sats`, color: "text-red-400" },
            { label: "API Calls", value: String(status?.total_api_calls ?? 0), color: "text-blue-400" },
            { label: "Payments", value: String(status?.successful_payments ?? 0), color: "text-lightning" },
            { label: "Reputation", value: `${status?.reputation_score ?? 50}/100`, color: "text-yellow-400" },
          ].map((s) => (
            <div key={s.label} className="bg-gray-900 rounded-xl border border-gray-800 p-4">
              <div className="text-xs text-gray-500 uppercase tracking-wider">{s.label}</div>
              <div className={`text-xl font-bold mt-1 ${s.color}`}>{s.value}</div>
            </div>
          ))}
        </div>

        {/* Task input + demo */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
              Agent Task Control
            </h3>
            <button
              onClick={runDemo}
              disabled={demoRunning}
              className="px-4 py-1.5 text-sm bg-lightning/20 text-lightning rounded-lg hover:bg-lightning/30 transition disabled:opacity-50"
            >
              {demoRunning ? "Running Demo..." : "Run Full Demo"}
            </button>
          </div>
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              placeholder="Ask the agent anything... e.g. weather in New Haven"
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-lightning"
            />
            <select
              value={taskPriority}
              onChange={(e) => setTaskPriority(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
            <button
              type="submit"
              disabled={running || !taskInput.trim()}
              className="px-6 py-2 bg-bitcoin text-white rounded-lg font-medium text-sm hover:bg-bitcoin/90 transition disabled:opacity-50"
            >
              {running ? "Running..." : "Execute"}
            </button>
          </form>

          {/* Last result */}
          {lastResult && (
            <div className="mt-3 p-3 bg-gray-800/50 rounded-lg text-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-300 font-medium">&ldquo;{lastResult.query}&rdquo;</span>
                <span className={lastResult.has_result ? "text-green-400" : "text-red-400"}>
                  {lastResult.has_result ? "Data Received" : "No Data"}
                </span>
              </div>
              <div className="space-y-1">
                {lastResult.actions.map((a, i) => (
                  <div key={i} className="text-xs text-gray-400">
                    [{a.action}] {a.detail}
                  </div>
                ))}
              </div>
              {lastResult.cost_sats > 0 && (
                <div className="mt-1 text-xs text-lightning">
                  Cost: {lastResult.cost_sats} sats | Balance: {lastResult.agent_balance} sats
                </div>
              )}
            </div>
          )}
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left column (2/3) */}
          <div className="xl:col-span-2 space-y-6">
            {/* Balance chart */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">
                Balance Over Time
              </h3>
              {balanceHistory.length < 2 ? (
                <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
                  Execute tasks to see balance changes
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={balanceHistory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 11 }} />
                    <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: 8 }}
                      formatter={(v: number) => [`${v.toLocaleString()} sats`, "Balance"]}
                    />
                    <Line type="monotone" dataKey="balance" stroke="#f7931a" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Payment stream */}
            <PaymentStream />

            {/* Task history */}
            <ApiCallHistory tasks={tasks} />
          </div>

          {/* Right column (1/3) */}
          <div className="space-y-6">
            {/* Reputation */}
            <ReputationCard
              score={reputation?.score ?? status?.reputation_score ?? 50}
              totalPayments={reputation?.total_payments ?? status?.successful_payments ?? 0}
              successfulPayments={reputation?.successful_payments ?? status?.successful_payments ?? 0}
              totalSatsSpent={reputation?.total_sats_spent ?? status?.wallet.total_spent ?? 0}
            />

            {/* How L402 works */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
                L402 Protocol Flow
              </h3>
              <div className="space-y-3 text-xs">
                {[
                  { step: "1", label: "Agent calls API", desc: "GET /api/weather/new-haven", color: "text-blue-400" },
                  { step: "2", label: "Server returns 402", desc: "Payment Required + Lightning invoice", color: "text-yellow-400" },
                  { step: "3", label: "Agent decides", desc: "Evaluates budget, priority, price", color: "text-purple-400" },
                  { step: "4", label: "Lightning payment", desc: "Pays invoice, gets preimage", color: "text-lightning" },
                  { step: "5", label: "Data received", desc: "Authorization: L402 macaroon:preimage", color: "text-green-400" },
                ].map((s) => (
                  <div key={s.step} className="flex gap-3 items-start">
                    <span className={`${s.color} font-bold w-5`}>{s.step}</span>
                    <div>
                      <div className="text-gray-200 font-medium">{s.label}</div>
                      <div className="text-gray-500">{s.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick actions */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
                Quick Queries
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { q: "Weather in NYC", p: "normal" },
                  { q: "BTC price", p: "high" },
                  { q: "Crypto news", p: "normal" },
                  { q: "ETH price", p: "low" },
                  { q: "STX stock", p: "critical" },
                  { q: "AI news", p: "normal" },
                ].map((item) => (
                  <button
                    key={item.q}
                    onClick={() => runTask(item.q, item.p)}
                    disabled={running}
                    className="p-2 text-xs bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-300 transition disabled:opacity-50 text-left"
                  >
                    {item.q}
                    <span className="block text-gray-500 mt-0.5">{item.p}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
