export interface WalletStats {
  agent_id: string;
  balance_sats: number;
  initial_balance: number;
  total_spent: number;
  total_received: number;
  total_transactions: number;
  hourly_spend: number;
  is_low_balance: boolean;
  uptime_hours: number;
}

export interface AgentStatus {
  agent_id: string;
  wallet: WalletStats;
  reputation_score: number;
  total_api_calls: number;
  successful_payments: number;
  tasks_completed: number;
  uptime_hours: number;
}

export interface TaskAction {
  action: "decide" | "query" | "pay" | "respond";
  detail: string;
  timestamp: number;
}

export interface TaskResult {
  query: string;
  priority: string;
  endpoint: string;
  cost_sats: number;
  completed: boolean;
  has_result: boolean;
  result: unknown;
  actions: TaskAction[];
  agent_balance: number;
  reputation_score: number;
}

export interface TaskHistory {
  query: string;
  priority: string;
  endpoint: string;
  cost_sats: number;
  completed: boolean;
  actions: TaskAction[];
  has_result: boolean;
}

export interface PaymentRecord {
  endpoint: string;
  amount_sats: number;
  payment_hash: string;
  timestamp: number;
  agent_id: string;
}

export interface ReputationData {
  score: number;
  total_payments: number;
  successful_payments: number;
  total_sats_spent: number;
  registered_at: number;
  last_updated: number;
  discount_multiplier: number;
}

export interface CreditScore {
  credit_score: number;
  will_pay: boolean;
  will_pay_probability: number;
  discount_multiplier: number;
  pricing_tier: string;
}

export interface WSMessage {
  type: string;
  query?: string;
  cost?: number;
  success?: boolean;
  reputation?: number;
  balance?: number;
  amount?: number;
  timestamp?: number;
  agent?: AgentStatus;
  wallet?: WalletStats;
}
