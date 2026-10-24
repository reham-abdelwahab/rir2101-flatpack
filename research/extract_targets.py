import json, sys
from playwright.sync_api import sync_playwright
CASES={'chair':('chair','CH1',[0,0,0,0,0]),'table':('table','TB1',[0,0,0,0,0]),'sofa_curved':('sofa','SF1',[0,-14,-20,-14,0])}
out={}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.goto("http://localhost:8765/tests/regress.html?base="); pg.wait_for_function("window.REGRESS",timeout=120000)
    for case,(a,mid,curve) in CASES.items():
        r=pg.evaluate("""([a,mid,curve])=>{const wc=document.getElementById('fc').contentWindow; const A=wc.eval('archetypes');
          const pc={...A[a]}; const piece={archetype:a,w:pc.w,d:pc.d,h:pc.h,subH:pc.subH,qty:1,method:'fold',curveOffsets:curve};
          const n=wc.nestAll([piece],{scale:10,sheetSize:'A3',thicknessMm:0.5,name:'T',id:'1',course:'RIR2101'});
          const r=FoldVerify.verifyModel(n.sheets.map(s=>s.svg),mid,{archetype:a,W:pc.w,D:pc.d,H:pc.h,sub:pc.subH,curve},wc.polygonClipping);
          return {ok:r.ok,assembled:r.assembled,target:r.assembledTarget,surfaces:r.surfaces,svgs:n.sheets.map(s=>s.svg),spec:{W:pc.w,D:pc.d,H:pc.h,sub:pc.subH,curve}}}""",[a,mid,curve])
        out[case]=r; print(case,r['ok'],r['assembled'],r['target'],len(r['surfaces']))
    b.close()
json.dump(out,open(sys.argv[1],'w'))
