import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const {chromium}=await import('/home/hblu/Documents/Codex/ml-generative-15-20/tools/node_modules/playwright/index.mjs');
const release=path.dirname(fileURLToPath(import.meta.url));
const bank=JSON.parse(await fs.readFile(release+'/lessons.json','utf8'));
const base=process.env.BASE_URL||'http://127.0.0.1:8795/ml-check';
const checks=[],errors=[];
const browser=await chromium.launch({executablePath:'/opt/google/chrome/chrome',headless:true,args:['--no-sandbox']});
try{
 for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:950}});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url())});
  for(const lesson of bank.lessons)for(const phase of ['A','B']){
   await page.goto(base+'/lessons/'+lesson.lesson_id+'?phase='+phase,{waitUntil:'networkidle'});
   const text=await page.locator('body').innerText();
   const questions=lesson.questions.filter(q=>q.phase===phase);
   const ok=questions.every(q=>text.includes(q.prompt)&&q.options.every(o=>text.includes(o))) &&
    lesson.questions.every(q=>!text.includes(q.explanation)) && await page.locator('input[type=radio]').count()===20 &&
    await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1);
   checks.push({lesson:lesson.lesson_id,phase,width,passed:ok});
  }
  await page.close();
 }
}finally{await browser.close()}
const result={host:'hblu-5090',base,passed:checks.length===128&&checks.every(c=>c.passed)&&errors.length===0,checks,errors};
await fs.writeFile(release+'/'+(process.env.BASE_URL?'live-browser':'build-browser')+'.json',JSON.stringify(result,null,2)+'\n');
console.log({passed:result.passed,checks:checks.length,failed:checks.filter(c=>!c.passed),errors});
if(!result.passed)process.exitCode=1;
