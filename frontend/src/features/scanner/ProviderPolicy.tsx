export function ProviderPolicy({provider,error}:{provider:string;error?:string}) {
  return <>
    {provider==='IQOPTION'&&<p className="researchWarning">IQ Option · Experimental · PRACTICE-only · Read-only. Finality: fail-closed on revision. Immutable closed-candle finality NOT GUARANTEED.</p>}
    {error==='DATA_CONFLICT'&&<p role="alert">DATA CONFLICT — subscription stopped. No automatic retry; explicit operational investigation required.</p>}
  </>;
}
