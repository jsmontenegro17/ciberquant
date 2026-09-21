import { codeLabel } from '../../utils/spanish';
import {useState} from 'react';
import {useQuery,useMutation} from '@tanstack/react-query';
import {featureApi,type Spec} from '../../api/features';
import {researchApi,type Condition,type Group,type Version,type VersionBody,type Operand} from '../../api/research';
import {Failure} from '../market-data/Shared';
const initial:Condition={left:{type:'FIELD',field:'close',bars_ago:0},operator:'GT',right:{type:'NUMBER',value:'0'}};

export function VersionBuilder({strategyId,copy,onSaved}:{strategyId:number;copy?:Version;onSaved:()=>void}) {
  const [specs,setSpecs]=useState<Spec[]>(copy?.indicator_specs??[]);
  const [direction,setDirection]=useState<'CALL'|'PUT'>(copy?.trade_direction??'CALL');
  const original=copy?.condition_tree;
  const [group,setGroup]=useState<'AND'|'OR'>(original && 'conditions' in original?original.operator:'AND');
  const [conditions,setConditions]=useState<Condition[]>(original && !('conditions' in original)?[original]:original && 'conditions' in original && original.conditions.every(c=>'left' in c)? original.conditions as Condition[]:[initial]);
  const defs=useQuery({queryKey:['strategy-definitions'],queryFn:researchApi.definitions});
  const features=useQuery({queryKey:['feature-definitions'],queryFn:featureApi.definitions});
  const fields=useQuery({queryKey:['strategy-fields',specs],queryFn:()=>researchApi.fields(specs),retry:false});
  const save=useMutation({mutationFn:(body:VersionBody)=>researchApi.version(strategyId,body),onSuccess:onSaved});
  const change=(i:number,next:Condition)=>setConditions(conditions.map((c,n)=>n===i?next:c));
  const updateSpec=(i:number,next:Spec)=>setSpecs(specs.map((s,n)=>n===i?next:s));
  const fieldNames=Object.keys(fields.data??{});
  const featureDefs=features.data;
  return <section className="panel formPanel"><h2>Crear versión inmutable</h2>
    <p>Guardar crea una versión nueva. Las definiciones y ejecuciones anteriores no cambian.</p>
    {copy && <p>Copia de v{copy.version}. El editor admite grupos simples; las definiciones anidadas se crean mediante la API tipada.</p>}
    <Failure error={defs.error}/><Failure error={features.error}/><Failure error={fields.error}/><Failure error={save.error}/>
    <form onSubmit={e=>{e.preventDefault();save.mutate({trade_direction:direction,indicator_specs:specs,condition_tree:{operator:group,conditions} as Group});}}>
      <label>Dirección de operación<select value={direction} onChange={e=>setDirection(e.target.value as 'CALL'|'PUT')}><option value={"CALL"}>{codeLabel("CALL")}</option><option value={"PUT"}>{codeLabel("PUT")}</option></select></label>
      <h3>Indicadores declarados</h3>
      {specs.map((s,i)=>{const d=featureDefs?.supported_indicators.find(d=>d.type===s.type);return <div className="grid compact" key={i}>
        <label>Indicador {i+1}<select value={s.type} onChange={e=>{const d=featureDefs!.supported_indicators.find(d=>d.type===e.target.value)!;updateSpec(i,{type:d.type,...d.parameters});}}>{featureDefs?.supported_indicators.map(d=><option key={d.type} value={d.type}>{codeLabel(d.type)}</option>)}</select></label>
        <label>Período {i+1}<input type="number" required min={d?.constraints.period.min} max={d?.constraints.period.max} step="1" value={s.period} onChange={e=>updateSpec(i,{...s,period:Number(e.target.value)})}/></label>
        {d?.constraints.stddev_multiplier && <label>Multiplicador {i+1}<input type="number" required min="0.000001" step="0.000001" max={d.constraints.stddev_multiplier.max} value={s.stddev_multiplier} onChange={e=>updateSpec(i,{...s,stddev_multiplier:e.target.value})}/></label>}
        <button type="button" className="secondary" onClick={()=>setSpecs(specs.filter((_,n)=>n!==i))}>Quitar indicador {i+1}</button>
      </div>;})}
      <button type="button" disabled={!featureDefs||specs.length>=Math.min(12,featureDefs.max_indicator_specs)} onClick={()=>{const d=featureDefs!.supported_indicators[0];setSpecs([...specs,{type:d.type,...d.parameters}]);}}>Añadir indicador</button>
      <label>Grupo principal<select value={group} onChange={e=>setGroup(e.target.value as 'AND'|'OR')}>{defs.data?.group_operators.map(o=><option key={o} value={o}>{codeLabel(o)}</option>)}</select></label>
      {conditions.map((c,i)=>{const ft=fields.data?.[c.left.field]??'NUMBER';const types=['FIELD',ft];return <fieldset key={i}><legend>Condición {i+1}</legend><div className="grid compact">
        <label>Campo {i+1}<select disabled={!fields.data||fields.isFetching} value={c.left.field} onChange={e=>{const field=e.target.value;const type=fields.data?.[field];if(!type)return;change(i,{left:{...c.left,field},operator:type==='NUMBER'?'GT':'EQ',right:{type,value:type==='BOOLEAN'?false:type==='STRING'?'C':'0'}});}}>{fieldNames.map(f=><option key={f} value={f}>{codeLabel(f)}</option>)}</select></label>
        <label>Velas anteriores {i+1}<input required type="number" min="0" max={defs.data?.max_bars_ago??50} step="1" value={c.left.bars_ago} onChange={e=>change(i,{...c,left:{...c.left,bars_ago:Number(e.target.value)}})}/></label>
        <label>Operador {i+1}<select value={c.operator} onChange={e=>change(i,{...c,operator:e.target.value})}>{defs.data?.operators.filter(o=>ft==='NUMBER'||['EQ','NE'].includes(o)).map(o=><option key={o} value={o}>{codeLabel(o)}</option>)}</select></label>
        <label>Tipo de operando {i+1}<select value={c.right.type} onChange={e=>{const t=e.target.value;const right:Operand=t==='FIELD'?{type:'FIELD',field:c.left.field,bars_ago:0}:{type:ft,value:ft==='BOOLEAN'?false:ft==='STRING'?'C':'0'};change(i,{...c,right});}}>{types.map(t=><option key={t} value={t}>{codeLabel(t)}</option>)}</select></label>
        {c.right.type==='FIELD'?<><label>Campo derecho {i+1}<select value={c.right.field} onChange={e=>change(i,{...c,right:{...c.right as Extract<Operand,{type:'FIELD'}>,field:e.target.value}})}>{fieldNames.filter(f=>fields.data![f]===ft).map(f=><option key={f} value={f}>{codeLabel(f)}</option>)}</select></label><label>Velas anteriores del lado derecho {i+1}<input type="number" required min="0" max={defs.data?.max_bars_ago??50} value={c.right.bars_ago} onChange={e=>change(i,{...c,right:{...c.right as Extract<Operand,{type:'FIELD'}>,bars_ago:Number(e.target.value)}})}/></label></>:
          <label>Valor {i+1}{ft==='NUMBER'?<input required value={String(c.right.value)} onChange={e=>change(i,{...c,right:{type:'NUMBER',value:e.target.value}})}/>:<select value={String(c.right.value)} onChange={e=>change(i,{...c,right:{type:ft,value:ft==='BOOLEAN'?e.target.value==='true':e.target.value}})}>{(ft==='BOOLEAN'?['false','true']:['C','P','D']).map(v=><option key={v} value={v}>{codeLabel(v)}</option>)}</select>}</label>}
        <button type="button" className="secondary" disabled={conditions.length===1} onClick={()=>setConditions(conditions.filter((_,n)=>n!==i))}>Quitar condición {i+1}</button>
      </div></fieldset>;})}
      <button type="button" disabled={conditions.length>=(defs.data?.max_nodes??50)-1} onClick={()=>setConditions([...conditions,{...initial}])}>Añadir condición</button>
      <button disabled={save.isPending||!defs.data||!fields.data||fields.isFetching||fields.isError}>Crear versión</button>
    </form>
  </section>;
}
