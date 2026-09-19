import {api} from './client'; import type {Account} from '../types'; export const accountsApi={list:()=>api<Account[]>('/accounts'),ledger:(id:number)=>api<any[]>(`/accounts/${id}/ledger`)};
