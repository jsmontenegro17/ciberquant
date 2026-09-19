// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import Workspace,{Pipeline,Context,type Overview} from './Workspace';
import * as client from '../../api/client';
import {marketApi} from '../../api/marketData';
import {researchApi} from '../../api/research';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
const dataset={source:'IQOPTION',broker:'IQOPTION',symbol:'EURUSD-OTC',market_type:'OTC',timeframe:'1m'};
function renderContext(){return render(<MemoryRouter><QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Context dataset={dataset} version={17}/></QueryClientProvider></MemoryRouter>);}
it('shows loading without stale evidence from another selection',()=>{
 vi.spyOn(client,'api').mockImplementation(()=>new Promise<never>(()=>{}));
 renderContext();expect(screen.getByText('Loading research evidence…')).toBeTruthy();
 expect(screen.queryByRole('list',{name:'Research pipeline'})).toBeNull();
});
it('surfaces ownership errors without fabricating evidence',async()=>{
 vi.spyOn(client,'api').mockRejectedValue(new Error('Resource not found'));
 renderContext();expect((await screen.findAllByRole('alert')).length).toBeGreaterThan(0);
 expect(screen.queryByRole('list',{name:'Research pipeline'})).toBeNull();
});
it.each(['READY','MISSING','RUNNING','FAILED','STALE','INCOMPATIBLE','UNAVAILABLE'])('renders pipeline %s without an execution recommendation',status=>{
 const data:Overview={dataset:{source:'IQOPTION',broker:'IQOPTION',symbol:'EURUSD-OTC',market_type:'OTC',timeframe:'1m'},version:{id:17},provider_health:[],evidence:{manual:null,validation:null},comparison_note:'Samples remain separate.',pipeline:[{name:'DATA',status,href:'/market-data',date:null,evidence:{id:1}}]};
 render(<MemoryRouter><Pipeline data={data}/></MemoryRouter>);
 expect(screen.getByText(status)).toBeTruthy();
 expect(screen.getByText(/StrategyVersion #17/)).toBeTruthy();
 expect(screen.getByRole('link',{name:'DATA'}).getAttribute('href')).toBe('/market-data');
 expect(screen.queryByText(/Buy now/)).toBeNull();
});
it('empty datasets and versions never auto-select a context',async()=>{
 vi.spyOn(marketApi,'coverage').mockResolvedValue({items:[],total:0,offset:0,limit:100});
 vi.spyOn(researchApi,'strategies').mockResolvedValue({items:[],total:0,offset:0,limit:20});
 render(<MemoryRouter><QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Workspace/></QueryClientProvider></MemoryRouter>);
 expect(await screen.findByText(/No datasets/)).toBeTruthy();
 expect(screen.getByText(/No context selected/)).toBeTruthy();
 expect(screen.getByRole('link',{name:'Import market data'}).getAttribute('href')).toBe('/market-data');
});
