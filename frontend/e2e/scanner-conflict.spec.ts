import {test,expect} from '@playwright/test';

test('conflicted research appears automatically with a plain-language next step',async({page})=>{
 const item={id:901,watchlist_id:1,provider:'IQOPTION',dataset:{source:'IQOPTION',broker:'IQOPTION',symbol:'EURUSD-OTC',market_type:'OTC',timeframe:'1m'},strategy_version_id:1,research_mode:true,research_payout:'84',research_expiry:1,enabled:true,state:'PROVIDER_DOWN',latest:{error:'DATA_CONFLICT',state:'PROVIDER_DOWN'}};
 await page.route('**/api/v1/scanner/items?*',route=>route.fulfill({json:{items:[item],total:1,limit:20,offset:0}}));
 await page.route('**/api/v1/live/snapshot?item_id=901',route=>route.fulfill({json:{item,subscription:{status:'DISCONNECTED',health:{error:'DATA_CONFLICT'},snapshot:{}}}}));
 await page.route('**/api/v1/scanner/events?*',route=>route.fulfill({json:{items:[],total:0,limit:20,offset:0}}));
 await page.goto('/login');
 await page.getByLabel('Correo electrónico').fill('qa@example.com');
 await page.getByLabel('Contraseña').fill('browser-test-only');
 await page.getByRole('button',{name:'Iniciar sesión'}).click();
 await page.getByRole('link',{name:'Ver mis estrategias y su estado'}).click();
 await expect(page.getByText('Detenido para proteger tus resultados')).toBeVisible();
 await expect(page.getByText(/no se guardó el segundo precio/)).toBeVisible();
 await expect(page.getByRole('button',{name:'Requiere revisión técnica'})).toBeDisabled();
 await expect(page.locator('pre:visible')).toHaveCount(0);
 await expect(page.getByRole('img')).toHaveCount(0);
 await expect(page.getByText(/CONDICIONES CUMPLIDAS/)).toHaveCount(0);
 await page.screenshot({path:'test-results/req010-conflict-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await page.screenshot({path:'test-results/req010-conflict-mobile.png',fullPage:true});
});
