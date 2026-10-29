/* EchoTime mechanism lab. All numerical results are saved by the Python builder.
   This file only chooses states and draws their data. No external dependencies. */
"use strict";
(() => {
  const scriptURL = new URL(document.currentScript.src);
  const assetURL = name => new URL(name, scriptURL).href;
  const $ = id => document.getElementById(id);
  const C = { a: "#5ad6d5", b: "#ff9d86", gold: "#ffd16d", muted: "#acbdcc", grid: "#30495e", text: "#f1f5f8" };
  let DATA, methods, active, timer = null, inspection = 32;
  const esc = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const fmt = (value, digits = 5) => Math.abs(value) < 5e-10 ? "0" : Number(value.toFixed(digits)).toString();
  const text = (x, y, value, fill = C.muted, size = 11, anchor = "start") => `<text x="${x}" y="${y}" fill="${fill}" font-size="${size}" text-anchor="${anchor}" font-family="system-ui,sans-serif">${esc(value)}</text>`;
  const line = (x1,y1,x2,y2,color,width=1,extra="") => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}" ${extra}/>`;
  const circle = (x,y,color,r=3) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${color}"/>`;
  function bounds(values, zero = true) {
    const f = values.filter(v => v !== null && Number.isFinite(v));
    let lo = Math.min(...f), hi = Math.max(...f);
    if (zero) { lo = Math.min(0,lo); hi = Math.max(0,hi); }
    const pad = Math.max((hi-lo)*.14,.05);
    return [lo-pad,hi+pad];
  }
  function shell(width,height,content,label) {
    return `<svg class="plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(label)}"><title>${esc(label)}</title>${content}</svg>`;
  }
  function poly(values, px, py, color, width=2.1) {
    let parts = [], current = [];
    values.forEach((v,i) => {
      if (v === null) { if (current.length) parts.push(current); current = []; }
      else current.push(`${px(i)},${py(v)}`);
    });
    if (current.length) parts.push(current);
    return parts.map(points=>`<polyline points="${points.join(" ")}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round"/>`).join("");
  }
  function axes(w,h,xaxis,ylim,{left=48,right=w-17,top=28,bottom=h-37,ylabel="",xlabel=""}={}) {
    const [lo,hi]=ylim;
    const px=i=>left+i*(right-left)/Math.max(xaxis.length-1,1);
    const py=v=>bottom-(v-lo)*(bottom-top)/(hi-lo);
    let s="";
    for (const fraction of [0,.5,1]) {
      const val=lo+(hi-lo)*fraction, yy=py(val);
      s+=line(left,yy,right,yy,C.grid)+text(left-7,yy+3,fmt(val,2),C.muted,10,"end");
    }
    const ticks=[0,Math.floor((xaxis.length-1)/2),xaxis.length-1];
    for(const i of [...new Set(ticks)])s+=text(px(i),bottom+16,fmt(xaxis[i],1),C.muted,10,"middle");
    s+=text(left,14,ylabel,C.muted,10)+text((left+right)/2,h-6,xlabel,C.muted,10,"middle");
    return {s,px,py,left,right,top,bottom};
  }
  function mappingIndex(id) {
    if (["dft","acf"].includes(id))return null;
    if (["paa","sax"].includes(id))return Math.floor(inspection/8);
    if (id==="derivative")return Math.min(inspection,62);
    return inspection;
  }
  function comparisonPlot(method,result,w=540) {
    if (method.kind==="alignment")return alignmentPlot(method,result,w);
    const a=method.a,b=result.b,h=240;
    const limits=bounds([...a,...b]);
    const p=axes(w,h,method.axis,limits,{ylabel:method.ylabel,xlabel:method.xlabel});
    let s=p.s;
    if (method.id==="sax") {
      method.breakpoints.forEach(v=>{s+=line(p.left,p.py(v),p.right,p.py(v),C.muted,1,'stroke-dasharray="3 4" opacity="0.6"');});
    }
    if (["rmse","zrmse","derivative","paa"].includes(method.id)) {
      a.forEach((v,i)=>{if(b[i]!==null)s+=line(p.px(i),p.py(v),p.px(i),p.py(b[i]),C.gold,1,'opacity="0.35"');});
    }
    s+=poly(a,p.px,p.py,C.a)+poly(b,p.px,p.py,C.b);
    if (a.length<=33)a.forEach((v,i)=>{s+=circle(p.px(i),p.py(v),C.a,2.5)+circle(p.px(i),p.py(b[i]),C.b,2.5);});
    if(method.id==="sax") {
      a.forEach((v,i)=>{s+=text(p.px(i)-5,p.py(v)-9,"abcd"[method.symbols_a[i]],C.a,12,"middle");
        s+=text(p.px(i)+5,p.py(b[i])+15,"abcd"[result.symbols_b[i]],C.b,12,"middle");});
    }
    const selected=mappingIndex(method.id);
    if(selected!==null) {
      const xx=p.px(selected);
      s+=line(xx,p.top,xx,p.bottom,C.gold,1,'stroke-dasharray="3 4"');
      s+=circle(xx,p.py(a[selected]),C.gold,4);
      if(b[selected]!==null)s+=circle(xx,p.py(b[selected]),C.gold,4);
    }
    if(method.id==="sbd") {
      const count=b.filter(v=>v===null).length;
      s+=text(p.right,p.top+9,`${count} zero-padded positions shown as gaps`,C.muted,10,"end");
    }
    return shell(w,h,s,`${method.title}: the actual features compared for A and B. ${method.ylabel}. ${method.xlabel}.`);
  }
  function alignmentPlot(method,result,w=540) {
    const h=275,a=method.a,b=result.b,right=w-17;
    const [lo,hi]=bounds([...a,...b]);
    const px=i=>48+i*(right-48)/63;
    const pyA=v=>105-(v-lo)*75/(hi-lo),pyB=v=>233-(v-lo)*75/(hi-lo);
    let s=text(48,15,"A · raw amplitude",C.a,11)+text(48,145,"B · raw amplitude",C.b,11);
    for (const [py,offset] of [[pyA,0],[pyB,128]]) {
      for(const v of [lo,(lo+hi)/2,hi])s+=line(48,py(v),right,py(v),C.grid)+text(41,py(v)+3,fmt(v,2),C.muted,9,"end");
      s+=text(48,122+offset,"0",C.muted,10)+text(right,122+offset,"63",C.muted,10,"end");
    }
    for(const [i,j] of result.pairs) {
      const selected=i===inspection;
      s+=line(px(i),pyA(a[i]),px(j),pyB(b[j]),selected?C.gold:"#8d8061",selected?2.2:1,`opacity="${selected?1:.3}"`);
    }
    s+=poly(a,px,pyA,C.a)+poly(b,px,pyB,C.b);
    s+=line(px(inspection),27,px(inspection),238,C.gold,1,'stroke-dasharray="3 4" opacity="0.7"');
    s+=circle(px(inspection),pyA(a[inspection]),C.gold,4);
    for(const [i,j] of result.pairs)if(i===inspection)s+=circle(px(j),pyB(b[j]),C.gold,4);
    s+=text(w/2,270,"Original sample indices · separate rows",C.muted,10,"middle");
    return shell(w,h,s,`${method.title}: actual ordered index pairs. A is the top trace and B is the bottom trace; both use the same amplitude scale.`);
  }
  function contributionPlot(method,result,w=540) {
    const values=result.contribution,axis=result.contribution_axis||method.axis;
    const h=163;
    const ylim=method.id==="lcss"?[-.08,1.15]:bounds(values);
    const xlabel=method.id==="sbd"?"Linear lag in samples":method.id==="derivative"?"Interval start":method.id==="dft"?"Frequency bin":method.id==="acf"?"Lag":(["paa","sax"].includes(method.id)?"Block index":"A sample index");
    const p=axes(w,h,axis,ylim,{ylabel:method.contribution_unit,xlabel,top:28,bottom:h-34});
    let s=p.s;
    const selected=mappingIndex(method.id);
    if(method.id==="sbd") {
      s+=poly(values,p.px,p.py,C.a);
      const winner=axis.indexOf(result.best_lag);
      s+=line(p.px(winner),p.top,p.px(winner),p.bottom,C.gold,1.7)+circle(p.px(winner),p.py(values[winner]),C.gold,4);
    } else {
      const width=Math.max(2,Math.min(21,(p.right-p.left)/values.length*.72));
      values.forEach((v,i)=>{
        const yy=p.py(v),zero=p.py(0),height=Math.max(.8,Math.abs(yy-zero));
        s+=`<rect x="${p.px(i)-width/2}" y="${Math.min(yy,zero)}" width="${width}" height="${height}" fill="${i===selected?C.gold:C.b}" opacity="${i===selected?1:.75}"/>`;
      });
    }
    return shell(w,h,s,method.contribution+". "+method.contribution_unit+".");
  }
  function highlightRawPairs() {
    let all=[];
    for(const id of [$("left-method").value,$("right-method").value]) {
      const result=active.methods[id];
      if(result.pairs)all=all.concat(result.pairs.filter(pair=>pair[0]===inspection));
    }
    return all.filter((pair,i)=>all.findIndex(p=>p[0]===pair[0]&&p[1]===pair[1])===i);
  }
  function rawPlot() {
    const w=Math.max(300,$("raw-plot").clientWidth||1150),h=250,axis=Array.from({length:64},(_,i)=>i);
    const p=axes(w,h,axis,DATA.raw_ylim_by_transform[$("perturbation").value],{left:49,right:w-18,top:28,bottom:213,ylabel:w<500?"Raw amplitude · fixed within this perturbation":"Raw amplitude · fixed scale within this perturbation",xlabel:"Original sample index"});
    let s=p.s;
    if($("perturbation").value==="spike") {
      const xx=p.px(40),xr=p.px(48);
      s+=`<rect x="${xx}" y="${p.top}" width="${xr-xx}" height="${p.bottom-p.top}" fill="${C.b}" opacity="0.08"/>`;
    }
    s+=poly(DATA.x,p.px,p.py,C.a,2.5)+poly(active.y,p.px,p.py,C.b,2.5);
    for(const [i,j] of highlightRawPairs())s+=line(p.px(i),p.py(DATA.x[i]),p.px(j),p.py(active.y[j]),C.gold,2,'opacity="0.9"')+circle(p.px(j),p.py(active.y[j]),C.gold,4);
    s+=line(p.px(inspection),p.top,p.px(inspection),p.bottom,C.gold,1,'stroke-dasharray="4 4"');
    s+=circle(p.px(inspection),p.py(DATA.x[inspection]),C.gold,4)+circle(p.px(inspection),p.py(active.y[inspection]),C.gold,4);
    $("raw-plot").innerHTML=shell(w,h,s,`The shared raw A/B pair. ${active.parameters.label}. Fixed amplitude scale. Selected A index ${inspection}.`);
    $("inspect-output").textContent=`i=${inspection} · A=${fmt(DATA.x[inspection],4)} · B=${fmt(active.y[inspection],4)} (same timestamp)`;
  }
  function card(side) {
    const id=$(side+"-method").value,method=methods[id],result=active.methods[id];
    const width=Math.max(260,($(side+"-card").clientWidth||580)-40);
    const closeness=method.direction==="lower"?"Lower means closer under this rule":"Higher means closer under this rule";
    let inspectionDetail="";
    if(result.pairs) {
      const js=result.pairs.filter(pair=>pair[0]===inspection).map(pair=>pair[1]);
      inspectionDetail=`Selected A[${inspection}] → ${js.length?js.map(j=>`B[${j}]`).join(", "):"no matched B point"}. `;
    } else if(["dft","acf"].includes(id))inspectionDetail="Each plotted feature combines many input samples. ";
    else if(["paa","sax"].includes(id))inspectionDetail=`Selected sample belongs to block ${Math.floor(inspection/8)}. `;
    else if(id==="derivative")inspectionDetail=`Selected interval: ${Math.min(inspection,62)} → ${Math.min(inspection,62)+1}. `;
    const description=`<div class="score-row"><strong class="score">${fmt(result.value,6)}</strong><span class="unit">${esc(method.unit)}</span></div>
      <div class="value-label">${esc(method.result)} · ${esc(closeness)}</div>
      <p class="preprocessing"><strong>Input handling:</strong> ${esc(method.preprocess)}</p>
      <p class="keeps">${esc(method.keeps)}</p><p class="allows">${esc(method.allows)}</p>
      <div class="plot-title">What this method actually compares</div><div class="plot-wrap">${comparisonPlot(method,result,width)}</div>
      <p class="detail">${esc(inspectionDetail+(result.detail||""))}</p>
      <div class="plot-title">${esc(method.contribution)}</div><div class="plot-wrap">${contributionPlot(method,result,width)}</div>
      <p class="caution">${esc(method.caution)}</p><p class="math">${esc(method.formula)}</p>
      <p class="parameters"><strong>Fixed parameters:</strong> ${esc(method.parameters)}</p>
      <div class="sources">${method.sources.map(source=>`<a href="${esc(source.url)}">${esc(source.title)}</a>`).join("")}</div>`;
    $(side+"-card").querySelector(".method-body").innerHTML=description;
  }
  function refresh() {
    const kind=$("perturbation").value,level=Number($("strength").value);
    active=DATA.states[kind][level];
    const perturbation=DATA.perturbations.find(p=>p.id===kind);
    $("strength-label").textContent=perturbation.strength+" · "+fmt(active.parameters.amount,3)+" "+perturbation.unit;
    $("strength-output").value=`${level}/20`;
    $("strength").setAttribute("aria-valuetext",active.parameters.label+`, level ${level} of 20`);
    $("transform-description").textContent=perturbation.description+" Current: "+active.parameters.label+".";
    $("insight").textContent=perturbation.observe;
    rawPlot(); card("left"); card("right");
    $("values-table").innerHTML=DATA.methods.map(method=>`<tr><td>${esc(method.title)}</td><td>${fmt(active.methods[method.id].value,8)}</td><td>${esc(method.unit)}</td><td>${method.direction}</td></tr>`).join("");
  }
  function stop() {
    if(timer!==null)window.clearInterval(timer);
    timer=null;$("play").textContent="Play levels";$("play").setAttribute("aria-pressed","false");
  }
  function initialize(data) {
    DATA=data;methods=Object.fromEntries(DATA.methods.map(method=>[method.id,method]));
    $("perturbation").innerHTML=DATA.perturbations.map(item=>`<option value="${esc(item.id)}">${esc(item.title)}</option>`).join("");
    const options=DATA.methods.map(method=>`<option value="${esc(method.id)}">${esc(method.title)}</option>`).join("");
    $("left-method").innerHTML=options;$("right-method").innerHTML=options;
    $("left-method").value="rmse";$("right-method").value="zrmse";
    $("perturbation").addEventListener("change",()=>{stop();refresh();});
    $("strength").addEventListener("input",()=>{stop();refresh();});
    ["left-method","right-method"].forEach(id=>$(id).addEventListener("change",refresh));
    $("inspect").addEventListener("input",()=>{inspection=Number($("inspect").value);rawPlot();card("left");card("right");});
    $("reset").addEventListener("click",()=>{stop();$("strength").value="0";refresh();});
    $("play").setAttribute("aria-pressed","false");
    $("play").addEventListener("click",()=>{
      if(timer!==null){stop();return;}
      $("play").textContent="Pause";$("play").setAttribute("aria-pressed","true");
      if(Number($("strength").value)===20)$("strength").value="0";
      refresh();
      timer=window.setInterval(()=>{
        const next=Number($("strength").value)+1;
        if(next>20){stop();return;}
        $("strength").value=String(next);refresh();
      },550);
    });
    document.addEventListener("visibilitychange",()=>{if(document.hidden)stop();});
    window.addEventListener("resize",()=>{rawPlot();card("left");card("right");});
    $("download").addEventListener("click",()=>{
      const snapshot={schema_version:DATA.schema_version,provenance:DATA.provenance,x:DATA.x,
        perturbation:DATA.perturbations.find(p=>p.id===$("perturbation").value),method_definitions:DATA.methods,state:active};
      const url=URL.createObjectURL(new Blob([JSON.stringify(snapshot,null,2)],{type:"application/json"}));
      const link=document.createElement("a");link.href=url;link.download=`echotime-${$("perturbation").value}-${$("strength").value}.json`;link.click();
      window.setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    $("loading").classList.add("hidden");$("interface").classList.remove("hidden");refresh();
    document.documentElement.dataset.labReady="true";
  }
  function unpack(payload) {
    if(payload.encoding!=="array-pool-v1")throw new Error("Unsupported data encoding");
    function visit(value) {
      if(Array.isArray(value))return value.map(visit);
      if(value && typeof value==="object") {
        if(Object.keys(value).length===1 && Object.prototype.hasOwnProperty.call(value,"$array"))return payload.arrays[value.$array];
        return Object.fromEntries(Object.entries(value).map(([key,entry])=>[key,visit(entry)]));
      }
      return value;
    }
    return visit(payload.data);
  }
  // Start static, including under prefers-reduced-motion. Explicit user action
  // is required for both autoplay controls; a still PNG is always available.
  let gifPlaying=false;
  $("gif-toggle").addEventListener("click",()=>{
    gifPlaying=!gifPlaying;
    $("comparison-image").src=assetURL(gifPlaying?"mechanism-comparison.gif":"mechanism-comparison.png");
    $("gif-toggle").textContent=gifPlaying?"Show still image":"Play GIF";
    $("gif-toggle").setAttribute("aria-pressed",String(gifPlaying));
  });
  fetch(assetURL("states.json"))
    .then(response=>{if(!response.ok)throw new Error(`Data response ${response.status}`);return response.json();})
    .then(unpack).then(initialize)
    .catch(error=>{
      $("loading").className="error";
      $("loading").textContent="The saved numerical states could not be loaded. Serve the exported site over HTTP (for example: python -m http.server). The static walkthrough and downloadable files remain available. "+error.message;
    });
})();
