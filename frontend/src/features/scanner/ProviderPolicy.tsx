export function ProviderPolicy({provider,error}:{provider:string;error?:string}) {
  return <>
    {provider==='IQOPTION'&&<p className="researchWarning">IQ Option · Experimental · Solo PRACTICE (demostración) · Solo lectura. El seguimiento se detiene ante revisiones. NO SE GARANTIZA que una vela cerrada permanezca inmutable.</p>}
    {error==='DATA_CONFLICT'&&<p role="alert">CONFLICTO DE DATOS: seguimiento detenido. Sin reintento automático; requiere investigación del operador.</p>}
  </>;
}
