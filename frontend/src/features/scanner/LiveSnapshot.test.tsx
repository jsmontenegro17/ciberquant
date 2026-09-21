// @vitest-environment jsdom
import {afterEach,it,expect} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import {LiveSnapshot,utcTime} from './LiveSnapshot';
import {ScannerCard} from './Scanner';
import type {WatchItem} from '../../api/scanner';
afterEach(cleanup);
const item:WatchItem={id:1,watchlist_id:1,provider:'IQOPTION',dataset:{source:'IQOPTION',broker:'IQOPTION',symbol:'EURUSD-OTC',market_type:'OTC',timeframe:'1m'},strategy_version_id:1,research_mode:true,enabled:true,state:'ACTIVE',latest:{state:'MATCH'}};
const candle={open:'1.123456789012345678',high:'1.2',low:'1.1',close:'1.15',open_time:'2026-09-21T17:00:00Z'};
const subscription={status:'CONNECTED',health:{status:'CONNECTED',market_open:false,last_received:'2026-09-21T17:01:00Z'},snapshot:{last_closed:candle,forming:candle,payout:null}};
it('separates connected from open and preserves exact price text without raw JSON',()=>{
 const {container}=render(<LiveSnapshot item={item} subscription={subscription}/>);
 expect(screen.getByText('Conectado · mercado cerrado')).toBeTruthy();
 expect(screen.getAllByText(candle.open)).toHaveLength(2);
 expect(screen.getAllByRole('img')).toHaveLength(2);
 expect(container.querySelector('pre')).toBeNull();
 expect(screen.getByText(/no un gráfico histórico/)).toBeTruthy();
 expect(screen.getByText('No disponible')).toBeTruthy();
});
it.each(['conflict','disconnected','paused'])('does not display live candles or active matches when %s',reason=>{
 const next={...item,enabled:reason!=='paused',state:reason==='paused'?'ACTIVE':'PROVIDER_DOWN',latest:{state:'MATCH',...(reason==='conflict'?{error:'DATA_CONFLICT'}:{})}};
 render(<><LiveSnapshot item={next} subscription={{...subscription,status:reason==='disconnected'?'DISCONNECTED':'CONNECTED'}}/><ScannerCard item={next} onToggle={()=>{}}/></>);
 expect(screen.queryByRole('img')).toBeNull();
 expect(screen.queryByText(/CONDICIONES CUMPLIDAS/)).toBeNull();
});
it('handles missing candles and unknown market status without inventing zeros',()=>{
 render(<LiveSnapshot item={item} subscription={{status:'CONNECTED',health:{},snapshot:{forming:{close:'1.15'}}}}/>);
 expect(screen.getByText('Conectado · apertura sin confirmar')).toBeTruthy();
 expect(screen.queryByRole('img')).toBeNull();
 expect(screen.getAllByText('Sin vela disponible para mostrar en vivo.')).toHaveLength(2);
});
it('formats timestamps explicitly in UTC and handles invalid values',()=>{
 expect(utcTime('2026-09-21T17:00:00Z')).toContain('UTC');
 expect(utcTime('bad')).toBe('Sin registro');
});
