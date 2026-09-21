// @vitest-environment jsdom
import {afterEach,beforeEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,cleanup,waitFor,within} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter,Route,Routes} from 'react-router-dom';
import type {ReactNode} from 'react';
import {validationApi,type ValidationRun,type Protocol} from '../../api/validation';
import {marketApi} from '../../api/marketData';
import {ValidationDetail,ValidationSetup,ValidationList} from './Validation';
vi.mock('../../api/validation',()=>({validationApi:{definitions:vi.fn(),preview:vi.fn(),create:vi.fn(),list:vi.fn(),detail:vi.fn(),segments:vi.fn(),reveal:vi.fn()}}));
vi.mock('../../api/marketData',async original=>({...await original<typeof import('../../api/marketData')>(),marketApi:{coverage:vi.fn()}}));
const dataset={source:'FIXTURE',broker:'DEMO',symbol:'EURUSD',market_type:'REGULAR',timeframe:'1h'};
const protocol:Protocol={validation_engine_version:'cq-validation-v1',split:[60,20,20],fold_count:4,minimum_resolved:100,minimum_active_days:10,minimum_fold_resolved:20,minimum_evaluable_folds:3,minimum_positive_folds:3,bootstrap:{iterations:2000,blocks:'UTC signal day'},verdict_gates:[]};
const input={strategy_version_id:1,dataset,overall_start:'2026-01-01T00:00:00Z',overall_end:'2026-03-01T00:00:00Z',as_of_candle_id:1500,payout_percent:'84',expiry_bars:1,overlap_policy:'ALLOW'};
const boundaries=['TRAIN','VALIDATION','TEST'].map(segment_type=>({segment_type,fold_number:0,signal_start:input.overall_start,signal_end:input.overall_end}));
const metrics={trades_executed:100,resolved_trades:100,total_unit_pnl:'84',edge_percentage_points:'20'};
const run:ValidationRun={...input,id:1,status:'SEALED',verdict:'PENDING_TEST',validation_state:'NOT_VALIDATED',latest_validation_attempt:'PENDING_TEST',validation_engine_version:'cq-validation-v1',config_sha256:'hash',config_snapshot:{...input,definition_sha256:'definition',protocol,boundaries},development_summary:{TRAIN:metrics,VALIDATION:metrics},walk_forward_summary:[1,2,3,4].map(fold_number=>({...metrics,fold_number,evaluable:true})) as ValidationRun['walk_forward_summary'],test_summary:null,bootstrap_summary:null,temporal_stability:{VALIDATION:[]},holdout_warnings:{prior_validation_count:0,prior_revealed_holdout_count:0,overlapping_holdout_count:0,replay_count:0},gates:null,test_revealed_at:null,created_at:'2026-09-19',error_summary:null};
function mount(ui:ReactNode,path='/validation/1'){return render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}})}><MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter></QueryClientProvider>);}
beforeEach(()=>{vi.resetAllMocks();vi.mocked(validationApi.detail).mockResolvedValue(run);vi.mocked(validationApi.segments).mockResolvedValue([]);vi.mocked(validationApi.definitions).mockResolvedValue(protocol);vi.mocked(marketApi.coverage).mockResolvedValue({items:[{...dataset,candle_count:1500,first_candle:input.overall_start,last_candle:input.overall_end}],total:1,offset:0,limit:20});});
afterEach(cleanup);
it('shows development and four folds with computationally sealed test, no hidden metrics',async()=>{
 mount(<Routes><Route path='/validation/:id' element={<ValidationDetail/>}/></Routes>);
 await screen.findByText("PRUEBA FINAL — SEALED");
 expect(screen.getByText("EVIDENCIA PRELIMINAR")).toBeTruthy();
 expect(screen.getAllByText(/Partición \d · Evaluable/)).toHaveLength(4);
 const card=screen.getByRole('region',{name:"Prueba final"});
 expect(within(card).queryByRole('table')).toBeNull();
 expect(screen.queryByRole('region',{name:"Evidencia bootstrap"})).toBeNull();
 expect(validationApi.reveal).not.toHaveBeenCalled();
});
it.each(['PASS','FAIL','INCONCLUSIVE'])('confirms explicit reveal and explains %s with gates',async verdict=>{
 vi.mocked(validationApi.reveal).mockResolvedValue({...run,status:'COMPLETED',verdict,validation_state:verdict==='PASS'?'HISTORICALLY_VALIDATED':'NOT_VALIDATED',test_revealed_at:'2026-09-19',test_summary:metrics,bootstrap_summary:{point_estimate:'.84',lower_95:'.8',upper_95:'.9',block_count:12,iterations:2000,seed:'seed'},gates:{test_resolved:verdict!=='INCONCLUSIVE',test_pnl:verdict==='PASS'}});
 mount(<Routes><Route path='/validation/:id' element={<ValidationDetail/>}/></Routes>);
 fireEvent.click(await screen.findByRole('button',{name:"Revelar prueba final"}));
 expect(validationApi.reveal).not.toHaveBeenCalled();
 expect(screen.getByRole('dialog',{name:"Confirmar revelación"}).textContent).toContain('deja de considerarse no observada');
 fireEvent.click(screen.getByRole('button',{name:"Confirmar revelación irreversible"}));
 await screen.findByText("PRUEBA FINAL — REVEALED");
 expect(validationApi.reveal).toHaveBeenCalledTimes(1);
 expect(screen.getByRole('heading',{name:verdict==='PASS'?"Validación histórica aprobada (PASS)":verdict})).toBeTruthy();
 expect(screen.getByRole('region',{name:"Evidencia bootstrap"})).toBeTruthy();
 expect(screen.queryByRole('button',{name:"Revelar prueba final"})).toBeNull();
});
it('shows reused holdout, replay and degraded state without profitability claim',async()=>{
 vi.mocked(validationApi.detail).mockResolvedValue({...run,validation_state:'DEGRADED',holdout_warnings:{prior_validation_count:2,prior_revealed_holdout_count:2,overlapping_holdout_count:2,replay_count:1}});
 mount(<Routes><Route path='/validation/:id' element={<ValidationDetail/>}/></Routes>);
 await screen.findByText(/MUESTRA RESERVADA REUTILIZADA/);expect(screen.getByText(/REPRODUCCIÓN:/)).toBeTruthy();expect(screen.getByText(/Reservada \(SEALED\) · DEGRADED/)).toBeTruthy();
});
it('previews exact frozen plan and submits the preview snapshot',async()=>{
 vi.mocked(validationApi.preview).mockResolvedValue({config_snapshot:run.config_snapshot,config_sha256:'hash'});vi.mocked(validationApi.create).mockResolvedValue(run);
 mount(<Routes><Route path='/validation/new' element={<ValidationSetup/>}/><Route path='/validation/:id' element={<p>Created plan</p>}/></Routes>,'/validation/new?version=1');
 await screen.findByRole('option',{name:'FIXTURE / DEMO / EURUSD / REGULAR / 1h'});
 fireEvent.change(screen.getByLabelText("Conjunto de datos"),{target:{value:JSON.stringify(dataset)}});
 fireEvent.click(screen.getByRole('button',{name:"Revisar plan fijo"}));
 await screen.findByRole('region',{name:"Vista previa del plan"});
 fireEvent.click(screen.getByRole('button',{name:"Crear plan de validación"}));
 await screen.findByText("Created plan");
 expect(validationApi.create).toHaveBeenCalledWith(input,expect.anything());
});
it('invalidates preview when inputs change',async()=>{
 vi.mocked(validationApi.preview).mockResolvedValue({config_snapshot:run.config_snapshot,config_sha256:'hash'});
 mount(<ValidationSetup/>,'/validation/new?version=1');await screen.findByRole('option',{name:'FIXTURE / DEMO / EURUSD / REGULAR / 1h'});
 fireEvent.change(screen.getByLabelText("Conjunto de datos"),{target:{value:JSON.stringify(dataset)}});fireEvent.click(screen.getByRole('button',{name:"Revisar plan fijo"}));await screen.findByRole('region',{name:"Vista previa del plan"});
 fireEvent.change(screen.getByLabelText("Rendimiento %"),{target:{value:'80'}});expect(screen.queryByRole('button',{name:"Crear plan de validación"})).toBeNull();
});
it('renders API failure without fabricating results',async()=>{
 vi.mocked(validationApi.detail).mockRejectedValue(new Error('API unavailable'));
 mount(<Routes><Route path='/validation/:id' element={<ValidationDetail/>}/></Routes>);
 await screen.findByText('API unavailable');expect(screen.queryByText("Validación histórica aprobada (PASS)")).toBeNull();
});
it('lists private validation attempts without ranking',async()=>{
 vi.mocked(validationApi.list).mockResolvedValue({items:[run],total:1,limit:20,offset:0});mount(<ValidationList/>);
 await waitFor(()=>expect(screen.getByRole('link',{name:"Plan n.º1 / versión n.º1"})).toBeTruthy());
});
