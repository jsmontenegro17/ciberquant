import {test,expect} from '@playwright/test';
test('fixed TESTING version → preview → sealed development → explicit reveal → historical evidence',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/login');await page.getByLabel('Email').fill('qa@example.com');await page.getByLabel('Password').fill('browser-test-only');await page.getByRole('button',{name:'Sign in'}).click();
 await page.getByRole('link',{name:'Strategy Lab',exact:true}).click();await page.getByLabel('Name',{exact:true}).fill('Validation fixed fixture');await page.getByRole('button',{name:'Create strategy',exact:true}).click();await page.getByRole('link',{name:'Validation fixed fixture',exact:true}).first().click();
 await page.getByLabel('Value 1',{exact:true}).fill('0');await page.getByRole('button',{name:'Create version',exact:true}).click();
 await page.getByRole('combobox',{name:'Status',exact:true}).selectOption('TESTING');await page.getByRole('link',{name:'Validate v1',exact:true}).click();
 await page.getByRole('combobox',{name:'Dataset',exact:true}).selectOption({label:'VALIDATION_FIXTURE / DEMO / EURUSD / REGULAR / 1h'});
 await page.getByLabel('Overall end (UTC)').fill('2026-03-04T12:00:00Z');await page.getByLabel('Payout %',{exact:true}).fill('83.5');
 await page.getByRole('button',{name:'Preview frozen plan'}).click();await expect(page.getByRole('region',{name:'Plan preview'})).toContainText('As-of snapshot');
 await page.getByRole('button',{name:'Create Validation Plan'}).click();await expect(page).toHaveURL(/validation\/\d+/);
 await expect(page.getByText('FINAL TEST — SEALED',{exact:true})).toBeVisible();await expect(page.getByText('PRELIMINARY EVIDENCE',{exact:true})).toBeVisible();
 await expect(page.getByText('Fold 4 · Evaluable',{exact:true})).toBeVisible();expect(await page.getByRole('region',{name:'Final test',exact:true}).locator('table').count()).toBe(0);
 await page.screenshot({path:'test-results/req006-sealed.png',fullPage:true});
 await page.getByRole('button',{name:'Reveal Final Test',exact:true}).click();await expect(page.getByRole('dialog',{name:'Confirm reveal'})).toBeVisible();
 const response=page.waitForResponse(r=>r.url().endsWith('/reveal-test')&&r.request().method()==='POST');await page.getByRole('button',{name:'Confirm irreversible reveal'}).click();const result=await(await response).json();expect(result.status).toBe('COMPLETED');expect(result.verdict).toBe('PASS');
 await expect(page.getByRole('heading',{name:'Historical validation PASS',exact:true})).toBeVisible();await expect(page.getByRole('region',{name:'Bootstrap evidence'})).toBeVisible();
 await page.screenshot({path:'test-results/req006-revealed-desktop.png',fullPage:true});await page.setViewportSize({width:768,height:1024});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);await page.screenshot({path:'test-results/req006-revealed-tablet.png',fullPage:true});expect(errors).toEqual([]);
});
