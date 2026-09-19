// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,cleanup,fireEvent,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {ScannerCard,Scanner} from './Scanner';
import {scannerApi} from '../../api/scanner';
import {marketApi} from '../../api/marketData';
import {researchApi} from '../../api/research';
import type {WatchItem} from '../../api/scanner';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
const item:WatchItem={id:1,watchlist_id:1,provider:'REPLAY',dataset:{source:'FIXTURE',broker:'DEMO',symbol:'EURUSD',market_type:'REGULAR',timeframe:'1m'},strategy_version_id:1,research_mode:false,enabled:true,state:'ACTIVE',latest:{state:'MATCH',mode:'REPLAY',research_direction:'PUT',validation_state:'HISTORICALLY_VALIDATED',dataset_validation_state:'HISTORICALLY_VALIDATED',current_payout:'79',validation_payout:'84',current_break_even:'55.8',payout_warning:true,signal_context:{rsi_14:'73.14'},health:{status:'CONNECTED',clock_delta_seconds:0}}};
it('renders neutral MATCH, private dataset, payout mismatch, Replay and exact context',()=>{
 const toggle=vi.fn();render(<ScannerCard item={item} onToggle={toggle}/>);
 expect(screen.getByText(/CONDITIONS MATCHED/)).toBeTruthy();
 expect(screen.getByText(/REPLAY MODE/)).toBeTruthy();
 expect(screen.getByText('PAYOUT BELOW VALIDATION ASSUMPTION')).toBeTruthy();
 expect(screen.getByText(/Research signal — no order sent/)).toBeTruthy();
 expect(screen.getByText(/rsi_14/)).toBeTruthy();
 expect(screen.getByText(/CONNECTED/)).toBeTruthy();
 expect(screen.queryByText(/TAKE PUT NOW/)).toBeNull();
 fireEvent.click(screen.getByRole('button',{name:'Pause item'}));expect(toggle).toHaveBeenCalledOnce();
});
it.each(['NO_MATCH','STALE','PROVIDER_DOWN','INSUFFICIENT_HISTORY','UNAVAILABLE'])('renders %s without a positive signal',state=>{
 render(<ScannerCard item={{...item,state,latest:{...item.latest,state,payout_warning:false}}} onToggle={()=>{}}/>);
 expect(screen.queryByText(/CONDITIONS MATCHED/)).toBeNull();
 expect(screen.getAllByText(new RegExp(state)).length).toBeGreaterThan(0);
});
it('labels degraded suspension and explicit research filter without treating them as safe',()=>{
 render(<ScannerCard item={{...item,state:'SUSPENDED_DEGRADED',research_mode:true,latest:{state:'UNAVAILABLE',validation_state:'DEGRADED'}}} onToggle={()=>{}}/>);
 expect(screen.getByText('DEGRADED — normal scanning suspended.')).toBeTruthy();
 expect(screen.getByText(/RESEARCH FILTER/)).toBeTruthy();
});

it('creates a watchlist, selects full dataset/version, surfaces compatibility rejection and separates forming/history',async()=>{
 const page=<T,>(items:T[])=>({items,total:items.length,offset:0,limit:20});
 vi.spyOn(scannerApi,'providers').mockResolvedValue({items:[{provider:'REPLAY',enabled:true,mode:'REPLAY',capabilities:{forming_candle:false}}]});
 vi.spyOn(scannerApi,'lists').mockResolvedValue(page([{id:1,name:'Research desk',enabled:true}]));
 vi.spyOn(scannerApi,'items').mockResolvedValue(page([{...item,latest:{state:'NO_MATCH'}}]));
 vi.spyOn(scannerApi,'events').mockResolvedValue(page([{id:1,dataset:item.dataset,strategy_version_id:1,signal_time:'2026-01-01T00:01:00Z',state:'MATCH',mode:'REPLAY',direction:'PUT',current_payout:'79',validation_state_snapshot:'HISTORICALLY_VALIDATED',evidence:{},paper_outcome:{result:'WIN',evidence:{entry_price:'101',expiry_price:'100',unit_pnl:'.79'}}}]));
 vi.spyOn(scannerApi,'snapshot').mockResolvedValue({item,subscription:{status:'CONNECTED',health:{server_time:'2026-01-01T00:02:00Z'},snapshot:{forming_state:'FORMING',forming:{close:'110'}}}});
 vi.spyOn(scannerApi,'createList').mockResolvedValue({id:1,name:'Research desk',enabled:true});
 vi.spyOn(scannerApi,'createItem').mockRejectedValue(new Error('HISTORICALLY_VALIDATED on the exact dataset required'));
 vi.spyOn(marketApi,'coverage').mockResolvedValue(page([{...item.dataset,candle_count:100,first_candle:'2026-01-01',last_candle:'2026-01-02'}]));
 vi.spyOn(researchApi,'strategies').mockResolvedValue(page([{id:1,name:'Fixed research',description:'',status:'TESTING'}]));
 vi.spyOn(researchApi,'versions').mockResolvedValue(page([{id:1,strategy_id:1,version:1,trade_direction:'PUT',indicator_specs:[],condition_tree:{left:{type:'FIELD',field:'close',bars_ago:0},operator:'GT',right:{type:'NUMBER',value:'0'}},strategy_dsl_version:'cq-strategy-dsl-v1',feature_engine_version:'cq-features-v1',definition_sha256:'hash',created_at:'2026-01-01',validation_state:'HISTORICALLY_VALIDATED'}]));
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}})}><Scanner/></QueryClientProvider>);
 fireEvent.change(screen.getByLabelText('Watchlist name'),{target:{value:'Research desk'}});
 fireEvent.click(screen.getByRole('button',{name:'Create watchlist'}));
 await waitFor(()=>expect(scannerApi.createList).toHaveBeenCalledWith('Research desk',expect.anything()));
 fireEvent.change(await screen.findByRole('combobox',{name:'Existing dataset'}),{target:{value:JSON.stringify(item.dataset)}});
 fireEvent.change(screen.getByRole('combobox',{name:'Strategy'}),{target:{value:'1'}});
 await screen.findByRole('option',{name:'v1 · HISTORICALLY_VALIDATED'});
 fireEvent.change(screen.getByRole('combobox',{name:'Immutable version'}),{target:{value:'1'}});
 fireEvent.click(screen.getByRole('button',{name:'Create watch item / start provider'}));
 await screen.findByText('HISTORICALLY_VALIDATED on the exact dataset required');
 expect(scannerApi.createItem).toHaveBeenCalledWith({list:1,body:{provider:'REPLAY',dataset:item.dataset,strategy_version_id:1,research_mode:false}},expect.anything());
 fireEvent.click(screen.getByRole('button',{name:'Inspect snapshot #1'}));
 expect(await screen.findByText(/FORMING is provisional/)).toBeTruthy();
 expect(screen.queryByText(/CONDITIONS MATCHED/)).toBeNull();
 expect(screen.getByText('REPLAY PAPER OBSERVATION · WIN')).toBeTruthy();
});
