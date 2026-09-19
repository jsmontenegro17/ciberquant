import { api } from "./client";
export type RiskPreview = {
  trading_account_id: number;
  current_balance: string;
  currency: string;
  risk_per_trade_percent: string;
  suggested_stake: string;
  max_loss_amount: string;
  max_operations: number;
  minimum_payout_percent: string;
  profit_target_amount: string | null;
};
export const riskPreview = (id: number) =>
  api<RiskPreview>(`/accounts/${id}/risk-preview`);
