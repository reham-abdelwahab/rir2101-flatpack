import json
from playwright.sync_api import sync_playwright
FV=open('tests/fold_verify.js').read()
CASES=[('chair','flat',[0,0,0,0,0]),('chair','arched',[0,-14,-20,-14,0]),('chair','sloped',[-15,-8,0,8,15]),
       ('sofa','flat',[0,0,0,0,0]),('table','flat',[0,0,0,0,0]),('bed','flat',[0,0,0,0,0]),('cabinet','flat',[0,0,0,0,0])]
JS="""(args)=>{ const [cases, scale]=args; const ID={chair:'CH1',sofa:'SF1',table:'TB1',bed:'BD1',cabinet:'CB1'}; const out=[];
  for (const [a,v,curve] of cases){ const A=archetypes[a], f=10/scale;
    const p={...newPiece(a,'fold'), curveOffsets:curve};
    const n=nestAll([p],{scale, sheetSize:'A4', thicknessMm:0.5, name:'REVIEW', id:'0', course:'RIR2101'});
    const r=FoldVerify.verifyModel(n.sheets.map(s=>s.svg), ID[a], {archetype:a, W:p.w*f, D:p.d*f, H:p.h*f, sub:p.subH*f, curve, trace:true}, polygonClipping);
    out.push({type:'fold', archetype:a, variant:v, scale, size:[p.w,p.d,p.h], ok:r.ok, valley:r.valley, tabs:[r.tabsMated,r.tabs], assembled:r.assembled, order:r.order, notes:r.notes, trace:r.trace}); }
  return out; }"""
WJS="""()=>{ const out=[]; for (const a of ['chair','table','sofa','bed','cabinet']) for (const scale of [10,20]) {
  const cfg={...v4Cfg(), scale, sheetSize:'A4', thicknessMm:1.5}; const p={...newPiece(a,'waffle')};
  const w=waffleForPiece(p,cfg); const res=w.res, plan=waffleAssemblyPlan(res);
  out.push({type:'waffle', archetype:a, scale, size:[p.w,p.d,p.h], t:res.t, valid:w.validation.ok, plan,
    ribs:res.ribs.map(r=>({name:r.name, dir:r.dir, pos:+r.pos.toFixed(3), poly:(function rd(x){return typeof x[0]==='number'?[+x[0].toFixed(3),+x[1].toFixed(3)]:x.map(rd)})(r.poly)}))}); }
  return out; }"""
data={'generated':'2026-10-24','versions':{}}
with sync_playwright() as pw:
    b=pw.chromium.launch()
    for ver,url in [('v4.3.0','http://localhost:8765/index.html'),('v4.2.4','http://localhost:8765/v4.2.4/index.html')]:
        pg=b.new_page(); pg.goto(url); pg.wait_for_timeout(2000); pg.add_script_tag(content=FV)
        cases=CASES if ver=='v4.3.0' else [c for c in CASES if c[1]=='flat']
        fold=pg.evaluate(JS,[cases,20])
        data['versions'][ver]={'fold':fold}
        if ver=='v4.3.0': data['versions'][ver]['waffle']=pg.evaluate(WJS)
        print(ver, [(c['archetype'],c['variant'],c['ok'],len(c['valley'])) for c in fold])
    b.close()
json.dump(data,open('/home/claude/foldview/data.json','w'),separators=(',',':'))
import os; print(os.path.getsize('/home/claude/foldview/data.json'))
