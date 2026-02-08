interface Props {
  score: number;
  totalPayments: number;
  successfulPayments: number;
  totalSatsSpent: number;
}

export default function ReputationCard({ score, totalPayments, successfulPayments, totalSatsSpent }: Props) {
  const tierColor =
    score > 80 ? "text-yellow-400" : score > 60 ? "text-green-400" : score > 30 ? "text-blue-400" : "text-gray-400";
  const tierName = score > 80 ? "Gold" : score > 60 ? "Silver" : score > 30 ? "Bronze" : "Unrated";
  const discount = score > 80 ? 30 : score > 60 ? 20 : score > 30 ? 10 : 0;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
      <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
        On-Chain Reputation
      </h3>
      <div className="flex items-center gap-4 mb-4">
        {/* Score ring */}
        <div className="relative w-20 h-20">
          <svg className="w-20 h-20 -rotate-90" viewBox="0 0 36 36">
            <path
              className="text-gray-800"
              stroke="currentColor"
              strokeWidth="3"
              fill="none"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className={tierColor}
              stroke="currentColor"
              strokeWidth="3"
              fill="none"
              strokeDasharray={`${score}, 100`}
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-lg font-bold ${tierColor}`}>{score}</span>
          </div>
        </div>
        <div>
          <div className={`text-lg font-semibold ${tierColor}`}>{tierName} Tier</div>
          {discount > 0 && (
            <div className="text-sm text-green-400">{discount}% discount on all APIs</div>
          )}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3 text-center text-xs">
        <div className="bg-gray-800/50 rounded-lg p-2">
          <div className="text-white font-semibold">{totalPayments}</div>
          <div className="text-gray-500">Payments</div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-2">
          <div className="text-white font-semibold">
            {totalPayments > 0 ? Math.round((successfulPayments / totalPayments) * 100) : 0}%
          </div>
          <div className="text-gray-500">Success</div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-2">
          <div className="text-white font-semibold">{totalSatsSpent.toLocaleString()}</div>
          <div className="text-gray-500">Sats Spent</div>
        </div>
      </div>
      <div className="mt-3 text-xs text-gray-500 text-center">
        Powered by Stacks/Clarity smart contract
      </div>
    </div>
  );
}
