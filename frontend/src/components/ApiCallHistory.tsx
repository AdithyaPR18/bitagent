import type { TaskHistory } from "../types";

interface Props {
  tasks: TaskHistory[];
}

const ACTION_ICONS: Record<string, string> = {
  decide: "\u{1F914}",
  query: "\u{1F50D}",
  pay: "\u26A1",
  respond: "\u2705",
};

export default function ApiCallHistory({ tasks }: Props) {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
      <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
        Agent Task History
      </h3>
      {tasks.length === 0 ? (
        <p className="text-sm text-gray-500">No tasks executed yet.</p>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {[...tasks].reverse().map((task, i) => (
            <div
              key={i}
              className={`p-3 rounded-lg border ${
                task.has_result
                  ? "bg-green-950/30 border-green-800/50"
                  : "bg-gray-800/30 border-gray-700/50"
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-sm text-white font-medium">
                  &ldquo;{task.query}&rdquo;
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    task.priority === "critical"
                      ? "bg-red-900/50 text-red-400"
                      : task.priority === "high"
                      ? "bg-orange-900/50 text-orange-400"
                      : task.priority === "low"
                      ? "bg-gray-700 text-gray-400"
                      : "bg-blue-900/50 text-blue-400"
                  }`}
                >
                  {task.priority}
                </span>
              </div>
              <div className="space-y-1">
                {task.actions.map((a, j) => (
                  <div key={j} className="text-xs text-gray-400 flex gap-1.5">
                    <span>{ACTION_ICONS[a.action] || "\u2022"}</span>
                    <span>{a.detail}</span>
                  </div>
                ))}
              </div>
              <div className="mt-2 flex gap-3 text-xs text-gray-500">
                <span>{task.endpoint}</span>
                {task.cost_sats > 0 && (
                  <span className="text-lightning font-medium">{task.cost_sats} sats</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
