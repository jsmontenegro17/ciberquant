// @vitest-environment jsdom
import {afterEach, expect, it, vi} from 'vitest';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {MemoryRouter, Route, Routes} from 'react-router-dom';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {GettingStarted, StartHint} from './GettingStarted';
import {Login} from '../auth/Login';
import {authApi} from '../../api/auth';

afterEach(()=>{cleanup();vi.restoreAllMocks();});
it('explains separate workflows without issuing requests or inventing data',()=>{
  const fetch=vi.spyOn(globalThis,'fetch');
  render(<MemoryRouter><GettingStarted/></MemoryRouter>);
  expect(screen.getByRole('heading',{name:'Empieza por aquí'})).toBeTruthy();
  expect(screen.getByRole('heading',{name:'Quiero investigar con IQ Option'})).toBeTruthy();
  expect(screen.getByRole('heading',{name:'Quiero llevar un diario de mis operaciones'})).toBeTruthy();
  expect(screen.getByText(/no tiene un formulario para crearlas/)).toBeTruthy();
  expect(screen.getByText(/no envía órdenes/i)).toBeTruthy();
  expect(fetch).not.toHaveBeenCalled();
});
it('keeps guidance accessible from the summary',()=>{
  render(<MemoryRouter><StartHint/></MemoryRouter>);
  expect(screen.getByRole('link',{name:'Ver primeros pasos'}).getAttribute('href')).toBe('/start');
});
it('uses Spanish labels and takes a successful login to the guide',async()=>{
  vi.spyOn(authApi,'login').mockResolvedValue({id:1,email:'demo@example.com',name:'Usuario',role:'USER',status:'ACTIVE'});
  render(<QueryClientProvider client={new QueryClient()}><MemoryRouter initialEntries={['/login']}><Routes>
    <Route path="/login" element={<Login/>}/><Route path="/start" element={<GettingStarted/>}/>
  </Routes></MemoryRouter></QueryClientProvider>);
  fireEvent.change(screen.getByLabelText('Correo electrónico'),{target:{value:'demo@example.com'}});
  fireEvent.change(screen.getByLabelText('Contraseña'),{target:{value:'test-only'}});
  fireEvent.click(screen.getByRole('button',{name:'Iniciar sesión'}));
  expect(await screen.findByRole('heading',{name:'Empieza por aquí'})).toBeTruthy();
  expect(authApi.login).toHaveBeenCalledWith('demo@example.com','test-only');
});
