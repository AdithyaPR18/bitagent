import { useEffect, useState } from "react";
import type { PaymentRecord } from "../types";
import axios from "axios";

export default function PaymentStream() {
  const [payments, setPayments] = useState<PaymentRecord[]>([]);

  useEffect(() => {
    const load = () =>
      axios.get("/payments/history").then((r) => setPayments(r.data)).catch(() => {});
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
      <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
        Lightning Payment Stream
      </h3>
      {payments.length === 0 ? (
        <p className="text-sm text-gray-500">No payments yet. Run a task to see payments flow.</p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {[...payments].reverse().map((p, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-2 rounded-lg bg-gray-800/50 text-sm"
            >
              <div className="flex items-center gap-2">
                <span className="text-lightning font-bold text-lg">&#9889;</span>
                <div>
                  <span className="text-white font-mono">{p.amount_sats} sats</span>
                  <span className="text-gray-500 ml-2 text-xs">{p.endpoint}</span>
                </div>
              </div>
              <span className="text-xs text-gray-500">
                {new Date(p.timestamp * 1000).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
