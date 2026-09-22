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
it('exposes approved fail-closed policy and stopped conflict without ACTIVE or MATCH',()=>{
 render(<ScannerCard item={{...item,provider:'IQOPTION',state:'PROVIDER_DOWN',latest:{state:'PROVIDER_DOWN',error:'DATA_CONFLICT'}}} onToggle={()=>{}}/>);
 expect(screen.getByText(/NO SE GARANTIZA que una vela cerrada permanezca inmutable/)).toBeTruthy();
 expect(screen.getByText(/CONFLICTO DE DATOS: seguimiento detenido/)).toBeTruthy();
 expect(screen.queryByText(/CONDICIONES CUMPLIDAS/)).toBeNull();
 expect(screen.queryByText(/ACTIVE/)).toBeNull();
});
it('labels unofficial IQ and observed product without claiming execution',()=>{
 render(<ScannerCard item={{...item,provider:'IQOPTION',latest:{...item.latest,payout_product:'binary'}}} onToggle={()=>{}}/>);
 expect(screen.getByText(/INTEGRACIÓN COMUNITARIA NO OFICIAL/)).toBeTruthy();
 expect(screen.getByText(/Producto: binary/)).toBeTruthy();
 expect(screen.getByText(/no garantiza una cotización ejecutable/)).toBeTruthy();
});
it.each([null,'87'])('truthfully displays research90/3 vs validation84/1 with provider payout %s',provider=>{
 render(<ScannerCard item={{...item,research_mode:true,research_payout:'90',research_expiry:3,latest:{...item.latest,current_payout:provider,validation_payout:'84',validation_expiry:1,payout_snapshot:provider??'90',payout_source:provider?'PROVIDER':'RESEARCH_ASSUMPTION',expiry_bars:3,expiry_source:'RESEARCH_ASSUMPTION'}}} onToggle={()=>{}}/>);
 expect(screen.getByText("Supuesto de vencimiento de investigación: 3 velas")).toBeTruthy();
 expect(screen.getByText(/Rendimiento de la validación histórica: 84% · Vencimiento de validación histórica: 1 velas — solo referencia/)).toBeTruthy();
 if(provider){
  expect(screen.getByText(/Rendimiento actual del proveedor: 87%/)).toBeTruthy();
  expect(screen.getByText("Supuesto alternativo de investigación: 90% — no se usa mientras esté disponible el rendimiento del proveedor.")).toBeTruthy();
  expect(screen.queryByText("Supuesto de rendimiento de investigación: 90%")).toBeNull();
 }else{
  expect(screen.getByText("Supuesto de rendimiento de investigación: 90%")).toBeTruthy();
  expect(screen.queryByText(/no se usa mientras esté disponible/)).toBeNull();
 }
 expect(screen.getByText(/Vencimiento simulado: 3 velas · RESEARCH_ASSUMPTION/)).toBeTruthy();
});
const item:WatchItem={id:1,watchlist_id:1,provider:'REPLAY',dataset:{source:'FIXTURE',broker:'DEMO',symbol:'EURUSD',market_type:'REGULAR',timeframe:'1m'},strategy_version_id:1,research_mode:false,enabled:true,state:'ACTIVE',latest:{state:'MATCH',mode:'REPLAY',research_direction:'PUT',validation_state:'HISTORICALLY_VALIDATED',dataset_validation_state:'HISTORICALLY_VALIDATED',current_payout:'79',validation_payout:'84',current_break_even:'55.8',payout_warning:true,signal_context:{rsi_14:'73.14'},health:{status:'CONNECTED',clock_delta_seconds:0}}};
it('renders neutral MATCH, private dataset, payout mismatch, Replay and exact context',()=>{
 const toggle=vi.fn();render(<ScannerCard item={item} onToggle={toggle}/>);
 expect(screen.getByText(/CONDICIONES CUMPLIDAS/)).toBeTruthy();
 expect(screen.getByText(/MODO REPRODUCCIÓN/)).toBeTruthy();
 expect(screen.getByText("RENDIMIENTO INFERIOR AL SUPUESTO DE VALIDACIÓN")).toBeTruthy();
 expect(screen.getByText(/Señal de investigación: no se envió ninguna orden/)).toBeTruthy();
 expect(screen.getByText(/rsi_14/)).toBeTruthy();
 expect(screen.getByText(/CONNECTED/)).toBeTruthy();
 expect(screen.queryByText(/TAKE PUT NOW/)).toBeNull();
 fireEvent.click(screen.getByRole('button',{name:"Pausar seguimiento"}));expect(toggle).toHaveBeenCalledOnce();
});
it.each(['NO_MATCH','STALE','PROVIDER_DOWN','INSUFFICIENT_HISTORY','UNAVAILABLE'])('renders %s without a positive signal',state=>{
 render(<ScannerCard item={{...item,state,latest:{...item.latest,state,payout_warning:false}}} onToggle={()=>{}}/>);
 expect(screen.queryByText(/CONDICIONES CUMPLIDAS/)).toBeNull();
 expect(screen.getAllByText(new RegExp(state)).length).toBeGreaterThan(0);
});
it('labels degraded suspension and explicit research filter without treating them as safe',()=>{
 render(<ScannerCard item={{...item,state:'SUSPENDED_DEGRADED',research_mode:true,latest:{state:'UNAVAILABLE',validation_state:'DEGRADED'}}} onToggle={()=>{}}/>);
 expect(screen.getByText("DEGRADADO: seguimiento normal suspendido.")).toBeTruthy();
 expect(screen.getByText(/INVESTIGACIÓN: sin validar/)).toBeTruthy();
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
 await waitFor(()=>expect(scannerApi.items).toHaveBeenCalledWith(true,0));
 await waitFor(()=>expect(scannerApi.snapshot).toHaveBeenCalledWith(1));
 fireEvent.click(screen.getByText('Configurar un nuevo seguimiento'));
 expect((screen.getByRole('checkbox',{name:'Crear en modo investigación (sin validación histórica)'}) as HTMLInputElement).checked).toBe(false);
 fireEvent.change(screen.getByLabelText("Nombre de la lista"),{target:{value:'Research desk'}});
 fireEvent.click(screen.getByRole('button',{name:"Crear lista de seguimiento"}));
 await waitFor(()=>expect(scannerApi.createList).toHaveBeenCalledWith('Research desk',expect.anything()));
 fireEvent.change(await screen.findByRole('combobox',{name:"Datos existentes"}),{target:{value:JSON.stringify(item.dataset)}});
 fireEvent.change(screen.getByRole('combobox',{name:"Estrategia"}),{target:{value:'1'}});
 await screen.findByRole('option',{name:'v1 · HISTORICALLY_VALIDATED'});
 fireEvent.change(screen.getByRole('combobox',{name:"Versión inmutable"}),{target:{value:'1'}});
 fireEvent.click(screen.getByRole('button',{name:"Crear seguimiento e iniciar proveedor"}));
 await screen.findByText('HISTORICALLY_VALIDATED on the exact dataset required');
 expect(scannerApi.createItem).toHaveBeenCalledWith({list:1,body:{provider:'REPLAY',dataset:item.dataset,strategy_version_id:1,research_mode:false}},expect.anything());
 fireEvent.click(screen.getByRole('button',{name:"Ver velas y conexión · n.º1"}));
 expect(await screen.findByText(/La vela en formación es provisional/)).toBeTruthy();
 expect(screen.queryByText(/CONDICIONES CUMPLIDAS/)).toBeNull();
 expect(screen.getByText('OBSERVACIÓN SIMULADA EN REPRODUCCIÓN · Ganada (WIN)')).toBeTruthy();
});
