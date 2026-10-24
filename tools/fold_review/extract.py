import json
from playwright.sync_api import sync_playwright
FV=open('tests/fold_verify.js').read()
B='http://localhost:8765/'
CASES=[('chair','flat',[0,0,0,0,0]),('chair','arched',[0,-14,-20,-14,0]),('chair','sloped',[-15,-8,0,8,15]),
       ('sofa','flat',[0,0,0,0,0]),('table','flat',[0,0,0,0,0]),('bed','flat',[0,0,0,0,0]),('cabinet','flat',[0,0,0,0,0])]
JS=r"""(args)=>{ const [cases, scale]=args; const ID={chair:'CH1',sofa:'SF1',table:'TB1',bed:'BD1',cabinet:'CB1'}; const out=[];
  for (const [a,v,curve] of cases){ const f=10/scale, p={...newPiece(a,'fold'), curveOffsets:curve};
    const n=nestAll([p],{scale, sheetSize:'A4', thicknessMm:0.5, name:'REVIEW', id:'0', course:'RIR2101'}), svgs=n.sheets.map(s=>s.svg);
    const W=p.w*f, D=p.d*f, H=p.h*f;
    const r=FoldVerify.verifyModel(svgs, ID[a], {archetype:a, W, D, H, sub:p.subH*f, curve, trace:true}, polygonClipping);
    const sides=[];
    if ((a==='chair'||a==='sofa') && r.trace) {
      // place every side profile by its PRINTED side facing out (x = 0 → printed normal −x, x = W → +x), not by the post rule
      const backS=(r.surfaces||[]).filter(s=>/BACK/.test(s.face)); const backY=backS.length? backS[0].P3.reduce((s2,X)=>s2+X[1],0)/backS[0].P3.length : null;
      FoldVerify.parseModel(svgs, ID[a]).filter(P=>/LEFT|RIGHT/.test(P.name)).forEach(P=>{
        const LR=P.localRing, x0=Math.min(...LR.map(q=>q[0])), x1=Math.max(...LR.map(q=>q[0])), y0=Math.min(...LR.map(q=>q[1])), y1=Math.max(...LR.map(q=>q[1]));
        const left=/LEFT/.test(P.name), X=left?0:W, s=left?1:-1;
        // local (u, v↓) → world (X, s·u…, z = y1 − v); printed normal = −s·x̂ (same convention as the folded faces)
        const M=[0,0,-s,X, s,0,0,(s>0?-x0:x1), 0,-1,0,y1];
        const tallU=LR.filter(q=>Math.abs(q[1]-y0)<0.05).map(q=>q[0]), postU=(Math.min(...tallU)+Math.max(...tallU))/2, postY=s>0?postU-x0:x1-postU;
        const postAtBack = backY==null ? null : Math.abs(postY-backY) < D/2;
        const postLeft=Math.min(...tallU)-x0 < (x1-x0)/2, oldFlip = postLeft === (backY!=null && backY>D/2), oldS = oldFlip?-1:1;
        sides.push({name:P.name, X, s, M, ring:LR.map(q=>[+q[0].toFixed(3),+q[1].toFixed(3)]), postAtBack, oldRuleAgrees: oldS===s});
      });
    }
    out.push({type:'fold', archetype:a, variant:v, scale, size:[p.w,p.d,p.h], ok:r.ok, valley:r.valley, tabs:[r.tabsMated,r.tabs], assembled:r.assembled, order:r.order, notes:r.notes, trace:r.trace, sides}); }
  return out; }"""
WJS=r"""()=>{ const out=[]; for (const a of ['chair','table','sofa','bed','cabinet']) for (const scale of [10,20]) {
  const cfg={...v4Cfg(), scale, sheetSize:'A4', thicknessMm:1.5}; const p={...newPiece(a,'waffle')};
  const w=waffleForPiece(p,cfg); const res=w.res, plan=waffleAssemblyPlan(res);
  out.push({type:'waffle', archetype:a, scale, size:[p.w,p.d,p.h], t:res.t, valid:w.validation.ok, plan,
    ribs:res.ribs.map(r=>({name:r.name, dir:r.dir, pos:+r.pos.toFixed(3), poly:(function rd(x){return typeof x[0]==='number'?[+x[0].toFixed(3),+x[1].toFixed(3)]:x.map(rd)})(r.poly)}))}); }
  return out; }"""
data={'generated':'2026-10-24','versions':{}}
with sync_playwright() as pw:
    b=pw.chromium.launch()
    for ver,url,allc,waf in [('v4.3.1',B+'index.html',True,True),('v4.3.0',B+'_v430.html',False,False),('v4.2.4',B+'v4.2.4/index.html',False,False)]:
        pg=b.new_page(); pg.goto(url); pg.wait_for_timeout(2000); pg.add_script_tag(content=FV)
        tv=pg.evaluate("()=>TOOL_VERSION"); assert tv==ver[1:], (tv,ver)
        cases=CASES if allc else [c for c in CASES if c[1]=='flat' and c[0] in ('chair','sofa','table','bed','cabinet')]
        fold=pg.evaluate(JS,[cases,20]); data['versions'][ver]={'fold':fold}
        if waf: data['versions'][ver]['waffle']=pg.evaluate(WJS)
        for c in fold:
            print(ver, c['archetype'], c['variant'], 'ok' if c['ok'] else 'FAIL', [(s['name'], 'post@back' if s['postAtBack'] else 'post@FRONT', 'old-rule-same' if s['oldRuleAgrees'] else 'old-rule-DIFFERS') for s in c['sides']])
    b.close()
json.dump(data,open('tools/fold_review/data.json','w'),separators=(',',':'))
