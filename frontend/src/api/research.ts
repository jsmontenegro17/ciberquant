import { api } from './client';
import type { Dataset, Page } from './marketData';
import type { Spec } from './features';
export type FieldType = 'NUMBER' | 'STRING' | 'BOOLEAN';
export interface FieldOperand {type:'FIELD';field:string;bars_ago:number}
export type Operand = FieldOperand | {type:FieldType;value:string|boolean};
export interface Condition {left:FieldOperand;operator:string;right:Operand}
export interface Group {operator:'AND'|'OR';conditions:(Condition|Group)[]}
export interface VersionBody {trade_direction:'CALL'|'PUT';indicator_specs:Spec[];condition_tree:Condition|Group}
export interface Version extends VersionBody {id:number;strategy_id:number;version:number;strategy_dsl_version:string;feature_engine_version:string;definition_sha256:string;created_at:string;validation_state?:string;latest_validation_attempt?:string|null}
export interface Strategy {id:number;name:string;description:string;status:string;latest_version?:Version|null;last_backtest?:{id:number;status:string}|null}
export interface DslDefinitions {strategy_dsl_version:string;feature_engine_version:string;backtest_engine_version:string;operators:string[];group_operators:('AND'|'OR')[];base_fields:Record<string,FieldType>;max_bars_ago:number;max_depth:number;max_nodes:number;entry_model:string;statuses:string[]}
export interface RunInput {strategy_version_id:number;dataset:Dataset;signal_start:string;signal_end:string;as_of_candle_id:number|null;payout_percent:string;expiry_bars:number;overlap_policy:string}
export interface BacktestRun extends RunInput {id:number;status:string;entry_model:string;backtest_engine_version:string;strategy_dsl_version:string;feature_engine_version:string;config_sha256:string;strategy_snapshot:VersionBody&{name:string;version:number;definition_sha256:string};config_snapshot:Record<string,unknown>;metrics:Record<string,string|number|null>|null;equity_curve:{sequence_no:number;time:string|null;equity:string}[]|null;error_summary:string|null}
export interface BacktestTrade {id:number;sequence_no:number;signal_time:string;entry_time:string;expiry_time:string;direction:string;entry_price:string;expiry_price:string;result:string;unit_pnl:string;signal_context:Record<string,string|boolean|null>}
const post = <T,>(path:string,body:unknown) => api<T>(path,{method:'POST',body:JSON.stringify(body)});
export const researchApi = {
  definitions:()=>api<DslDefinitions>('/strategies/definitions'),
  fields:(specs:Spec[])=>post<Record<string,FieldType>>('/strategies/fields',specs),
  strategies:(offset=0)=>api<Page<Strategy>>(`/strategies?offset=${offset}`),
  create:(name:string,description:string)=>post<Strategy>('/strategies',{name,description}),
  strategy:(id:number)=>api<Strategy>(`/strategies/${id}`),
  status:(id:number,status:string)=>api<Strategy>(`/strategies/${id}`,{method:'PATCH',body:JSON.stringify({status})}),
  versions:(id:number,offset=0)=>api<Page<Version>>(`/strategies/${id}/versions?offset=${offset}`),
  version:(id:number,body:VersionBody)=>post<Version>(`/strategies/${id}/versions`,body),
  run:(body:RunInput)=>post<BacktestRun>('/backtests',body),
  runs:(offset=0)=>api<Page<BacktestRun>>(`/backtests?offset=${offset}`),
  result:(id:number)=>api<BacktestRun>(`/backtests/${id}`),
  trades:(id:number,offset=0)=>api<Page<BacktestTrade>>(`/backtests/${id}/trades?offset=${offset}`),
};
