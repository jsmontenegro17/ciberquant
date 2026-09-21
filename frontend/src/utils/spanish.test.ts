import {expect,it} from 'vitest';
import {codeLabel,errorMessage,evidenceText} from './spanish';
it('labels codes without hiding their canonical identity or mixing candles with trades',()=>{
  expect(codeLabel('WIN')).toBe('Ganada (WIN)');
  expect(codeLabel('C')).toBe('Vela alcista (C)');
  expect(codeLabel('NEW_SERVER_CODE')).toBe('NEW_SERVER_CODE');
  expect(codeLabel(null)).toBe('—');
  expect(codeLabel(3)).toBe('3');
});
it('explains authentication and financial rejections without changing backend values',()=>{
  expect(errorMessage('Invalid credentials')).toBe('El correo o la contraseña no son correctos.');
  expect(errorMessage('Stake exceeds per-trade risk limit')).toBe('El importe supera el límite de riesgo por operación.');
  expect(errorMessage('UNKNOWN_DETAIL')).toContain('Detalle técnico: UNKNOWN_DETAIL');
});
it('translates known evidence descriptions and preserves unknown evidence verbatim',()=>{
  expect(evidenceText('20 closed candles')).toBe('20 velas cerradas');
  expect(evidenceText('cq-features-v1')).toBe('cq-features-v1');
});
