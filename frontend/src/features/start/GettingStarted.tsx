import { Link } from 'react-router-dom';

export function StartHint() {
  return <section className="panel" aria-label="Ayuda para empezar">
    <h2>¿Por dónde empiezo?</h2>
    <p>CiberQuant te ayuda a estudiar estrategias y registrar operaciones. No opera por ti.</p>
    <Link className="button" to="/start">Ver primeros pasos</Link>
  </section>;
}

export function GettingStarted() {
  return <div className="stack">
    <section className="panel">
      <div className="eyebrow">BIENVENIDO A CIBERQUANT</div>
      <h2>Empieza por aquí</h2>
      <p>Esta es una herramienta para investigar: observar precios, definir una idea y comprobar qué ocurrió con ella. No es un robot que compra o vende y no promete ganancias.</p>
      <p>Si acabas de entrar y ves pantallas vacías, no significa que algo esté roto. Todavía necesitas elegir datos y definir qué quieres estudiar.</p>
    </section>
    <section className="panel" aria-labelledby="research-start">
      <h2 id="research-start">Quiero investigar con IQ Option</h2>
      <p>No necesitas crear una cuenta de operaciones ni introducir un saldo para usar este camino.</p>
      <ol className="startSteps">
        <li><h3>Comprueba la fuente de precios</h3><p>Abre <Link to="/scanner">Seguimiento en vivo</Link> y revisa IQ Option en «Proveedores». Habilitado significa que está configurado; la recepción continua se comprueba al activar un seguimiento.</p></li>
        <li><h3>Define qué quieres observar</h3><p>En <Link to="/strategies">Estrategias</Link>, crea un nombre y una descripción de tu idea. Después abre la estrategia y crea una versión con sus condiciones. Crear el nombre no crea las reglas automáticamente.</p><p>Una versión es una copia fija de las reglas. Si cambias la idea, creas otra versión para no alterar resultados anteriores. La condición inicial del editor es un ejemplo técnico, no una estrategia recomendada.</p></li>
        <li><h3>Crea un seguimiento de investigación</h3><p>Vuelve a <Link to="/scanner">Seguimiento en vivo</Link>. Crea una lista, selecciona IQ Option, escribe la identidad exacta del activo y elige tu estrategia y versión. Por ejemplo, EURUSD-OTC, mercado OTC y temporalidad 1m identifican velas de un minuto; su disponibilidad debe verificarse.</p><p>Para una idea sin validación usa la opción explícita de investigación. El vencimiento y el rendimiento alternativo son supuestos de simulación, no ganancias garantizadas. El seguimiento normal exige validación histórica compatible; no se activa solo por crear una estrategia.</p></li>
        <li><h3>Observa y revisa la evidencia</h3><p>Espera velas cerradas y consulta el estado, los eventos y las observaciones simuladas. Una coincidencia solo indica que se cumplieron tus reglas; no es una orden. En <Link to="/workspace">Área de investigación</Link> podrás reunir la evidencia del mismo activo y versión cuando exista.</p></li>
      </ol>
      <p className="researchWarning">IQ Option es una integración no oficial y experimental: solo PRACTICE (demostración) y lectura. No envía órdenes ni sincroniza tu saldo como cuenta de CiberQuant. Si aparece DATA_CONFLICT, el seguimiento se detiene porque el proveedor revisó datos; no lo fuerces ni borres la evidencia.</p>
    </section>
    <section className="panel">
      <h2>Quiero probar una idea con datos históricos</h2>
      <ol className="startSteps">
        <li>Consulta <Link to="/market-data">Datos de mercado</Link>. Si no hay datos, un administrador puede importar un CSV con el formato requerido. No se descargan históricos automáticamente al entrar.</li>
        <li>Explora <Link to="/cataloger">Patrones de velas</Link> e <Link to="/features">Indicadores</Link> para entender los datos. No son recomendaciones para operar.</li>
        <li>Define tu estrategia en <Link to="/strategies">Estrategias</Link> y ejecuta una prueba histórica desde su versión.</li>
        <li>Revisa <Link to="/backtests">Pruebas históricas</Link> y después <Link to="/validation">Validación</Link>. Un resultado positivo en los mismos datos usados para diseñar la idea no demuestra que funcionará en el futuro.</li>
      </ol>
    </section>
    <section className="panel">
      <h2>Quiero llevar un diario de mis operaciones</h2>
      <p>Este camino es independiente de la investigación y de IQ Option.</p>
      <ol className="startSteps">
        <li>Revisa <Link to="/accounts">Cuentas</Link>. Necesitas una cuenta asignada y un perfil de riesgo. Esta versión permite consultar cuentas, pero no tiene un formulario para crearlas; si no tienes ninguna, solicita su configuración al administrador.</li>
        <li>En <Link to="/sessions">Sesiones</Link>, inicia una sesión de operaciones. El servidor determina sus límites de riesgo.</li>
        <li>Registra manualmente las operaciones que realmente hayas realizado. No se importan automáticamente del bróker.</li>
        <li>Anota tus observaciones en <Link to="/journal">Diario</Link> y consulta tus resultados en <Link to="/dashboard">Resumen</Link>.</li>
      </ol>
    </section>
    <section className="panel">
      <h2>Palabras que verás en la aplicación</h2>
      <dl>
        <dt>Vela</dt><dd>Resume apertura, máximo, mínimo y cierre de un precio durante un intervalo.</dd>
        <dt>Temporalidad</dt><dd>Duración de cada vela: 1m significa un minuto.</dd>
        <dt>Conjunto de datos</dt><dd>Una combinación exacta de fuente, bróker, símbolo, mercado y temporalidad. OTC y regular se mantienen separados.</dd>
        <dt>Prueba histórica</dt><dd>Aplica reglas a datos del pasado bajo supuestos explícitos; no ejecuta operaciones reales.</dd>
        <dt>Simulación en vivo</dt><dd>Observa qué habría ocurrido después de una señal. No mueve dinero ni escribe operaciones en tu diario.</dd>
        <dt>C / P / D</dt><dd>Vela alcista / bajista / doji exacto. No significan operación ganada o perdida.</dd>
        <dt>Códigos y evidencia técnica</dt><dd>Identificadores como CALL, PUT, PASS y DATA_CONFLICT, y el contenido JSON de auditoría, conservan sus códigos originales para no alterar la trazabilidad.</dd>
      </dl>
    </section>
  </div>;
}
