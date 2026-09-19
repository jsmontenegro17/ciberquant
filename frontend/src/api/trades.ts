import {api} from './client'; import type {Trade} from '../types'; export const tradesApi={create:(body:object)=>api<Trade>('/trades',{method:'POST',body:JSON.stringify(body)})};
