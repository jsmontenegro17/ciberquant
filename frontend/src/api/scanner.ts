import {api} from './client';
import type {Dataset,Page} from './marketData';
export interface Watchlist {id:number;name:string;enabled:boolean}
export interface Provider {provider:string;enabled:boolean;mode:string;capabilities:Record<string,boolean>;warning?:string}
export interface Evidence {state?:string;mode?:string;strategy_name?:string;version?:number;research_direction?:string;validation_state?:string;dataset_validation_state?:string;validation_payout?:string|null;current_payout?:string|null;current_break_even?:string|null;payout_warning?:boolean;signal_time?:string;signal_open?:string;latency_ms?:number|null;next_entry_boundary?:string;error?:string;features?:unknown;signal_context?:unknown;health?:Record<string,unknown>}
export interface WatchItem {id:number;watchlist_id:number;provider:string;dataset:Dataset;strategy_version_id:number;research_mode:boolean;enabled:boolean;state:string;latest:Evidence|null}
export interface ScannerEvent {id:number;dataset:Dataset;strategy_version_id:number;signal_time:string;state:string;mode:string;direction:string;current_payout:string|null;validation_state_snapshot:string;evidence:Evidence;paper_outcome:{result:string;evidence:Record<string,unknown>}|null}
export interface ItemInput {provider:string;dataset:Dataset;strategy_version_id:number;research_mode:boolean;research_payout?:string;research_expiry?:number}
const post=<T,>(path:string,body:unknown)=>api<T>(path,{method:'POST',body:JSON.stringify(body)});
export const scannerApi={
 providers:()=>api<{items:Provider[]}>('/live/providers'),
 lists:()=>api<Page<Watchlist>>('/scanner/watchlists?limit=100'),
 createList:(name:string)=>post<Watchlist>('/scanner/watchlists',{name}),
 createItem:({list,body}:{list:number;body:ItemInput})=>post<WatchItem>(`/scanner/watchlists/${list}/items`,body),
 items:(research:boolean,offset=0)=>api<Page<WatchItem>>(`/scanner/items?include_research=${research}&offset=${offset}`),
 toggle:({id,enabled}:{id:number;enabled:boolean})=>api<WatchItem>(`/scanner/items/${id}`,{method:'PATCH',body:JSON.stringify({enabled})}),
 events:(offset=0)=>api<Page<ScannerEvent>>(`/scanner/events?offset=${offset}`),
 snapshot:(id:number)=>api<{item:WatchItem;subscription:{status:string;health:Record<string,unknown>;snapshot:Record<string,unknown>}|null}>(`/live/snapshot?item_id=${id}`),
};
