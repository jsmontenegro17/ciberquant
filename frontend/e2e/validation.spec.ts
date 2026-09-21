import {test,expect} from '@playwright/test';
test('fixed TESTING version → preview → sealed development → explicit reveal → historical evidence',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/login');await page.getByLabel("Correo electrónico").fill('qa@example.com');await page.getByLabel("Contraseña").fill('browser-test-only');await page.getByRole('button',{name:"Iniciar sesión"}).click();
 await page.locator("aside").getByRole('link',{name:"Estrategias",exact:true}).click();await page.getByLabel("Nombre",{exact:true}).fill("Validación fixed fixture");await page.getByRole('button',{name:"Crear estrategia",exact:true}).click();await page.getByRole('link',{name:"Validación fixed fixture",exact:true}).first().click();
 await page.getByLabel("Valor 1",{exact:true}).fill('0');await page.getByRole('button',{name:"Crear versión",exact:true}).click();
 await page.getByRole('combobox',{name:"Estado",exact:true}).selectOption('TESTING');await page.getByRole('link',{name:"Validar v1",exact:true}).click();
 await page.getByRole('combobox',{name:"Conjunto de datos",exact:true}).selectOption({label:'VALIDATION_FIXTURE / DEMO / EURUSD / REGULAR / 1h'});
 await page.getByLabel("Fin global (UTC)").fill('2026-03-04T12:00:00Z');await page.getByLabel("Rendimiento %",{exact:true}).fill('83.5');
 await page.getByRole('button',{name:"Revisar plan fijo"}).click();await expect(page.getByRole('region',{name:"Vista previa del plan"})).toContainText('Instantánea de corte');
 await page.getByRole('button',{name:"Crear plan de validación"}).click();await expect(page).toHaveURL(/validation\/\d+/);
 await expect(page.getByText("PRUEBA FINAL — SEALED",{exact:true})).toBeVisible();await expect(page.getByText("EVIDENCIA PRELIMINAR",{exact:true})).toBeVisible();
 await expect(page.getByText("Partición 4 · Evaluable",{exact:true})).toBeVisible();expect(await page.getByRole('region',{name:"Prueba final",exact:true}).locator('table').count()).toBe(0);
 await page.screenshot({path:'test-results/req006-sealed.png',fullPage:true});
 await page.getByRole('button',{name:"Revelar prueba final",exact:true}).click();await expect(page.getByRole('dialog',{name:"Confirmar revelación"})).toBeVisible();
 const response=page.waitForResponse(r=>r.url().endsWith('/reveal-test')&&r.request().method()==='POST');await page.getByRole('button',{name:"Confirmar revelación irreversible"}).click();const result=await(await response).json();expect(result.status).toBe('COMPLETED');expect(result.verdict).toBe('PASS');
 await expect(page.getByRole('heading',{name:"Validación histórica aprobada (PASS)",exact:true})).toBeVisible();await expect(page.getByRole('region',{name:"Evidencia bootstrap"})).toBeVisible();
 await page.screenshot({path:'test-results/req006-revealed-desktop.png',fullPage:true});await page.setViewportSize({width:768,height:1024});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);await page.screenshot({path:'test-results/req006-revealed-tablet.png',fullPage:true});expect(errors).toEqual([]);
});
