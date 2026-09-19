// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,cleanup,fireEvent} from '@testing-library/react';
import {ScannerCard} from './Scanner';
import type {WatchItem} from '../../api/scanner';
afterEach(cleanup);
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
