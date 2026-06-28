<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js"></script>

<style>
  :root{
    --paper:#F5F2EC; --card:#FBFAF6; --ink:#1E2230; --ink-soft:#565C6B;
    --rule:#E4DFD4; --pen:#D63A2F; --pen-soft:#FBE9E6; --good:#1B8A5A;
    --warn:#C9821F; --blue:#2E5C8A; --chip:#EFEBE2;
    --display:'Newsreader',Georgia,serif; --ui:'Inter',system-ui,sans-serif;
    --mono:'IBM Plex Mono',ui-monospace,monospace;
    --shadow:0 1px 2px rgba(30,34,48,.04),0 8px 24px rgba(30,34,48,.06);
  }
  *{box-sizing:border-box}
  html,body{margin:0}
  body{background:var(--paper);color:var(--ink);font-family:var(--ui);
    -webkit-font-smoothing:antialiased;line-height:1.5}
  .wrap{max-width:1180px;margin:0 auto;padding:28px 22px 64px}

  /* Header */
  header{display:flex;align-items:flex-end;justify-content:space-between;
    gap:20px;border-bottom:1.5px solid var(--ink);padding-bottom:16px;margin-bottom:26px}
  .brand .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.18em;
    text-transform:uppercase;color:var(--pen);font-weight:600;margin-bottom:6px}
  .brand h1{font-family:var(--display);font-weight:600;font-size:34px;line-height:1;
    margin:0;letter-spacing:-.01em}
  .brand h1 .mark{position:relative;white-space:nowrap}
  .brand h1 .mark::after{content:"";position:absolute;left:-2px;right:-2px;bottom:3px;
    height:9px;background:var(--pen);opacity:.22;border-radius:2px;z-index:-1;transform:rotate(-1deg)}
  .brand p{margin:8px 0 0;color:var(--ink-soft);font-size:14px;max-width:46ch}
  .meta{font-family:var(--mono);font-size:11px;color:var(--ink-soft);text-align:right;
    line-height:1.7}
  .meta b{color:var(--ink)}

  /* Layout */
  .grid{display:grid;grid-template-columns:minmax(340px,420px) 1fr;gap:26px;align-items:start}
  @media(max-width:880px){.grid{grid-template-columns:1fr}}

  .card{background:var(--card);border:1px solid var(--rule);border-radius:14px;
    box-shadow:var(--shadow)}
  .pad{padding:20px}
  .panel-label{font-family:var(--mono);font-size:11px;letter-spacing:.14em;
    text-transform:uppercase;color:var(--ink-soft);font-weight:600;margin:0 0 12px;
    display:flex;align-items:center;gap:8px}
  .panel-label .dot{width:6px;height:6px;border-radius:50%;background:var(--pen)}

  /* Input panel */
  .field{margin-bottom:16px}
  .field label{display:block;font-size:13px;font-weight:600;margin-bottom:6px}
  .field .hint{font-weight:400;color:var(--ink-soft);font-size:12px}
  textarea,input[type=text]{width:100%;font-family:var(--ui);font-size:13.5px;color:var(--ink);
    background:#fff;border:1px solid var(--rule);border-radius:9px;padding:11px 12px;resize:vertical;
    outline:none;transition:border-color .15s,box-shadow .15s}
  textarea{min-height:230px;line-height:1.55}
  textarea:focus,input[type=text]:focus{border-color:var(--pen);box-shadow:0 0 0 3px var(--pen-soft)}
  .uploadrow{display:flex;gap:8px;align-items:center;margin-top:8px}
  .filebtn{font-family:var(--ui);font-size:12.5px;font-weight:600;color:var(--ink);
    background:var(--chip);border:1px solid var(--rule);border-radius:8px;padding:8px 12px;
    cursor:pointer;transition:background .15s}
  .filebtn:hover{background:#E7E1D5}
  .filename{font-size:12px;color:var(--ink-soft);font-family:var(--mono)}

  .analyze{width:100%;margin-top:6px;font-family:var(--ui);font-weight:600;font-size:15px;
    color:#fff;background:var(--pen);border:none;border-radius:10px;padding:13px;cursor:pointer;
    display:flex;align-items:center;justify-content:center;gap:9px;transition:transform .08s,background .15s}
  .analyze:hover{background:#bf3127}
  .analyze:active{transform:translateY(1px)}
  .analyze:disabled{background:#cdb6b3;cursor:not-allowed}
  .pen-ic{width:16px;height:16px}

  /* Results */
  #results{min-height:300px}
  .empty{border:1.5px dashed var(--rule);border-radius:14px;padding:54px 28px;text-align:center;
    background:repeating-linear-gradient(-12deg,transparent,transparent 22px,#F0ECE3 22px,#F0ECE3 23px)}
  .empty h2{font-family:var(--display);font-weight:500;font-size:23px;margin:0 0 8px}
  .empty p{color:var(--ink-soft);font-size:14px;margin:0 auto;max-width:42ch}

  /* working state */
  .working{display:flex;flex-direction:column;gap:12px;padding:30px 26px}
  .step{display:flex;align-items:center;gap:11px;font-size:14px;color:var(--ink-soft);
    opacity:.4;transition:opacity .3s,color .3s}
  .step.on{opacity:1;color:var(--ink)}
  .step.done{opacity:1;color:var(--good)}
  .step .box{width:18px;height:18px;border:1.5px solid var(--rule);border-radius:5px;flex:none;
    display:flex;align-items:center;justify-content:center;font-size:11px}
  .step.on .box{border-color:var(--pen)}
  .step.done .box{border-color:var(--good);background:var(--good);color:#fff}
  .spin{width:11px;height:11px;border:2px solid var(--pen);border-top-color:transparent;
    border-radius:50%;animation:sp .7s linear infinite}
  @keyframes sp{to{transform:rotate(360deg)}}

  .res-section{animation:rise .45s ease both}
  @keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
  .res-section + .res-section{margin-top:18px}
  h3.sec{font-family:var(--display);font-weight:600;font-size:19px;margin:0 0 4px}
  .sec-sub{color:var(--ink-soft);font-size:12.5px;margin:0 0 14px}

  /* score */
  .scorehead{display:flex;align-items:center;gap:22px;flex-wrap:wrap}
  .gauge{position:relative;width:104px;height:104px;flex:none}
  .gauge svg{transform:rotate(-90deg)}
  .gauge .val{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
    justify-content:center}
  .gauge .num{font-family:var(--display);font-weight:600;font-size:30px;line-height:1}
  .gauge .of{font-family:var(--mono);font-size:10px;color:var(--ink-soft);margin-top:2px}
  .verdict{flex:1;min-width:200px}
  .verdict .tag{display:inline-block;font-family:var(--mono);font-size:11px;font-weight:600;
    text-transform:uppercase;letter-spacing:.08em;padding:4px 9px;border-radius:6px;margin-bottom:8px}
  .verdict p{margin:0;font-size:13.5px;color:var(--ink-soft)}
  .verdict .role{color:var(--ink);font-weight:600}
  .bars{margin-top:18px;display:grid;gap:11px}
  .bar .top{display:flex;justify-content:space-between;font-size:12.5px;margin-bottom:5px}
  .bar .top b{font-weight:600}
  .bar .top span{font-family:var(--mono);color:var(--ink-soft)}
  .track{height:7px;background:var(--chip);border-radius:5px;overflow:hidden}
  .fill{height:100%;border-radius:5px;width:0;transition:width .9s cubic-bezier(.2,.8,.2,1)}
  .bar .note{font-size:11.5px;color:var(--ink-soft);margin-top:4px}

  /* chips */
  .chips{display:flex;flex-wrap:wrap;gap:7px}
  .chip{font-size:12.5px;font-weight:500;padding:5px 11px;border-radius:20px;
    background:var(--chip);border:1px solid var(--rule)}
  .chip.add{background:var(--pen-soft);border-color:#F2C9C3;color:#9e2a22;cursor:default}
  .add-grid{display:grid;gap:9px}
  .add-row{display:flex;gap:11px;align-items:baseline;font-size:13px}
  .add-row .k{font-weight:600;color:#9e2a22;flex:none;min-width:max-content}
  .add-row .why{color:var(--ink-soft)}

  /* summary box */
  .summary{background:#fff;border:1px solid var(--rule);border-left:3px solid var(--pen);
    border-radius:8px;padding:15px 16px;font-size:14px;line-height:1.6;font-family:var(--display)}
  .copybtn{margin-top:10px;font-family:var(--ui);font-size:12px;font-weight:600;color:var(--ink);
    background:var(--chip);border:1px solid var(--rule);border-radius:7px;padding:7px 12px;cursor:pointer}
  .copybtn:hover{background:#E7E1D5}

  /* redline bullets — signature */
  .redline{display:grid;gap:14px}
  .rl{background:#fff;border:1px solid var(--rule);border-radius:9px;padding:13px 15px}
  .rl .orig{font-size:13px;color:#a4534d;text-decoration:line-through;
    text-decoration-color:var(--pen);text-decoration-thickness:1.5px;margin-bottom:7px}
  .rl .new{font-size:13.5px;line-height:1.5;position:relative;padding-left:18px}
  .rl .new::before{content:"›";position:absolute;left:2px;top:-1px;color:var(--good);
    font-weight:700;font-size:16px}

  /* ATS issues */
  .issues{display:grid;gap:11px}
  .issue{display:flex;gap:12px;padding:12px 14px;background:#fff;border:1px solid var(--rule);
    border-radius:9px}
  .sev{width:9px;height:9px;border-radius:50%;flex:none;margin-top:5px}
  .sev.high{background:var(--pen)} .sev.medium{background:var(--warn)} .sev.low{background:var(--blue)}
  .issue .body b{font-size:13px}
  .issue .body .fix{font-size:12.5px;color:var(--ink-soft);margin-top:3px}
  .issue .body .fix em{font-style:normal;color:var(--good);font-weight:600}

  .wins{list-style:none;padding:0;margin:0;display:grid;gap:8px}
  .wins li{display:flex;gap:10px;font-size:13.5px;align-items:baseline}
  .wins li::before{content:"✓";color:var(--good);font-weight:700;flex:none}

  .toolbar{display:flex;gap:10px;margin-top:22px;flex-wrap:wrap}
  .tb{font-family:var(--ui);font-weight:600;font-size:13px;border-radius:9px;padding:10px 16px;
    cursor:pointer;border:1px solid var(--rule);background:var(--card)}
  .tb.primary{background:var(--ink);color:#fff;border-color:var(--ink)}
  .tb:hover{filter:brightness(.97)}

  .err{background:var(--pen-soft);border:1px solid #F2C9C3;color:#9e2a22;border-radius:9px;
    padding:14px 16px;font-size:13.5px}
  .footnote{font-size:11.5px;color:var(--ink-soft);margin-top:26px;font-family:var(--mono);
    border-top:1px solid var(--rule);padding-top:14px;line-height:1.7}

  @media print{
    body{background:#fff}
    .inputcol,.toolbar,header .meta,.footnote{display:none}
    .grid{grid-template-columns:1fr}
    .card{box-shadow:none;border:none}
  }
</style>

<div class="wrap">
  <header>
    <div class="brand">
      <div class="eyebrow">AI Career Assistant · Agent 01</div>
      <h1>Redline <span class="mark">Resume Agent</span></h1>
      <p>Paste your resume and I'll mark it up like an editor with a red pen — find your skills, flag the gaps, rewrite the weak lines, and score it for ATS.</p>
    </div>
    <div class="meta">
      model · <b>claude-sonnet</b><br/>
      output · <b>ATS report</b><br/>
      export · <b>PDF</b>
    </div>
  </header>

  <div class="grid">
    <!-- INPUT -->
    <div class="inputcol">
      <div class="card pad">
        <p class="panel-label"><span class="dot"></span>Your resume</p>
        <div class="field">
          <label>Resume text
            <span class="hint">— paste it, or upload a PDF / DOCX below</span></label>
          <textarea id="resume" placeholder="Paste your full resume here…&#10;&#10;Name, summary, experience bullets, skills, education — all of it."></textarea>
          <div class="uploadrow">
            <button class="filebtn" id="pick">⬆ Upload PDF / DOCX</button>
            <input type="file" id="file" accept=".pdf,.docx" hidden />
            <span class="filename" id="fname"></span>
          </div>
        </div>
        <div class="field">
          <label>Target role or job description
            <span class="hint">— optional, sharpens the scoring</span></label>
          <input type="text" id="target" placeholder="e.g. Data Analyst, or paste a job posting" />
        </div>
        <button class="analyze" id="run">
          <svg class="pen-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l7.586 7.586"/><circle cx="11" cy="11" r="2"/></svg>
          Mark up my resume
        </button>
      </div>
      <p class="footnote">
        How it works · text is sent to Claude, which returns a structured ATS report.<br/>
        Nothing is stored — refresh and it's gone.
      </p>
    </div>

    <!-- RESULTS -->
    <div id="results">
      <div class="empty">
        <h2>The page is blank until you mark it up.</h2>
        <p>Drop in a resume on the left and I'll return extracted skills, missing keywords, a rewritten summary, line-by-line edits, and an ATS score.</p>
      </div>
    </div>
  </div>
</div>

<script>
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

  const $ = s => document.querySelector(s);
  const resumeEl = $("#resume"), targetEl = $("#target"),
        runBtn = $("#run"), results = $("#results"),
        fileInput = $("#file"), fname = $("#fname");

  $("#pick").onclick = () => fileInput.click();
  fileInput.onchange = async (e) => {
    const f = e.target.files[0]; if(!f) return;
    fname.textContent = "reading " + f.name + "…";
    try{
      let text = "";
      if(f.name.toLowerCase().endsWith(".pdf")){
        const buf = await f.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({data:buf}).promise;
        for(let i=1;i<=pdf.numPages;i++){
          const page = await pdf.getPage(i);
          const c = await page.getTextContent();
          text += c.items.map(it=>it.str).join(" ") + "\n";
        }
      } else if(f.name.toLowerCase().endsWith(".docx")){
        const buf = await f.arrayBuffer();
        const r = await mammoth.extractRawText({arrayBuffer:buf});
        text = r.value;
      } else { throw new Error("Use a PDF or DOCX file."); }
      resumeEl.value = text.trim();
      fname.textContent = "✓ loaded " + f.name;
    }catch(err){
      fname.textContent = "couldn't read that — paste the text instead";
    }
  };

  const steps = [
    "Reading the document",
    "Extracting skills & keywords",
    "Checking ATS compatibility",
    "Rewriting weak lines",
    "Scoring the resume"
  ];

  function showWorking(){
    results.innerHTML = `<div class="card"><div class="working" id="work">
      ${steps.map((s,i)=>`<div class="step" data-i="${i}">
        <span class="box">${i+1}</span><span>${s}</span></div>`).join("")}
    </div></div>`;
    let i=0;
    const stepEls = [...document.querySelectorAll(".step")];
    stepEls[0].classList.add("on");
    stepEls[0].querySelector(".box").innerHTML = '<span class="spin"></span>';
    const timer = setInterval(()=>{
      if(i < stepEls.length-1){
        stepEls[i].classList.remove("on"); stepEls[i].classList.add("done");
        stepEls[i].querySelector(".box").textContent="✓";
        i++;
        stepEls[i].classList.add("on");
        stepEls[i].querySelector(".box").innerHTML = '<span class="spin"></span>';
      }
    }, 1100);
    return ()=>{ clearInterval(timer);
      stepEls.forEach(e=>{e.classList.remove("on");e.classList.add("done");
        e.querySelector(".box").textContent="✓";}); };
  }

  const PROMPT = (resume, target) => `You are an expert resume reviewer and ATS (applicant tracking system) specialist. Analyze the resume below.

${target ? "TARGET ROLE / JOB DESCRIPTION:\n"+target+"\n\n" : ""}RESUME:
"""
${resume}
"""

Return ONLY a valid JSON object (no markdown, no commentary, no code fences) with EXACTLY this shape:
{
  "detectedRole": "the role this resume targets, short",
  "atsScore": <integer 0-100>,
  "verdict": "one encouraging but honest sentence about the resume's current state",
  "scoreBreakdown": [
    {"label":"Keywords & skills","score":<int>,"max":25,"note":"short reason"},
    {"label":"Impact & metrics","score":<int>,"max":25,"note":"short reason"},
    {"label":"Formatting & ATS parse","score":<int>,"max":25,"note":"short reason"},
    {"label":"Clarity & structure","score":<int>,"max":25,"note":"short reason"}
  ],
  "extractedSkills": [up to 14 skills found in the resume],
  "suggestedSkills": [up to 6 {"skill":"...","why":"why it helps for this role, <12 words"}],
  "professionalSummary": "a strong rewritten 2-3 sentence professional summary tailored to the role",
  "improvedBullets": [up to 5 {"original":"a real weak bullet from the resume","improved":"stronger version with action verb + metric"}],
  "atsIssues": [up to 5 {"severity":"high|medium|low","issue":"the problem","fix":"the specific fix"}],
  "quickWins": [3-5 short actionable improvements]
}
The four scoreBreakdown scores must sum to atsScore. Be specific to THIS resume — quote real content. Output JSON only.`;

  async function analyze(){
    const resume = resumeEl.value.trim();
    if(resume.length < 60){
      results.innerHTML = `<div class="card pad"><div class="err">
        I need a bit more to work with — paste your resume (or upload a file) first.</div></div>`;
      return;
    }
    runBtn.disabled = true;
    const stop = showWorking();
    try{
      const res = await fetch("https://api.anthropic.com/v1/messages",{
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
          model:"claude-sonnet-4-6", max_tokens:4096,
          messages:[{role:"user", content: PROMPT(resume, targetEl.value.trim())}]
        })
      });
      const data = await res.json();
      let txt = (data.content||[]).filter(b=>b.type==="text").map(b=>b.text).join("");
      txt = txt.replace(/```json|```/g,"").trim();
      const s = txt.indexOf("{"), e = txt.lastIndexOf("}");
      if(s>=0 && e>=0) txt = txt.slice(s, e+1);
      const r = JSON.parse(txt);
      stop();
      setTimeout(()=>render(r), 350);
    }catch(err){
      stop();
      results.innerHTML = `<div class="card pad"><div class="err">
        Something went wrong reading the analysis (${(err&&err.message)||err}).
        Try again, or shorten the resume slightly.</div></div>`;
    }finally{
      runBtn.disabled = false;
    }
  }

  function scoreColor(pct){
    if(pct>=75) return "var(--good)";
    if(pct>=50) return "var(--warn)";
    return "var(--pen)";
  }
  function esc(s){return (s||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}

  function render(r){
    const score = Math.max(0,Math.min(100, r.atsScore|0));
    const col = scoreColor(score);
    const C = 2*Math.PI*44, off = C*(1-score/100);
    const tagBg = score>=75? "var(--good)" : score>=50? "var(--warn)" : "var(--pen)";
    const tagTxt = score>=75? "Strong" : score>=50? "Needs work" : "Major gaps";

    const bars = (r.scoreBreakdown||[]).map(b=>{
      const pct = Math.round((b.score/(b.max||25))*100);
      return `<div class="bar">
        <div class="top"><b>${esc(b.label)}</b><span>${b.score}/${b.max||25}</span></div>
        <div class="track"><div class="fill" style="background:${scoreColor(pct)}" data-w="${pct}"></div></div>
        ${b.note?`<div class="note">${esc(b.note)}</div>`:""}
      </div>`;}).join("");

    const found = (r.extractedSkills||[]).map(s=>`<span class="chip">${esc(s)}</span>`).join("");
    const add = (r.suggestedSkills||[]).map(s=>
      `<div class="add-row"><span class="k">+ ${esc(s.skill)}</span><span class="why">${esc(s.why||"")}</span></div>`).join("");
    const bullets = (r.improvedBullets||[]).map(b=>
      `<div class="rl"><div class="orig">${esc(b.original)}</div><div class="new">${esc(b.improved)}</div></div>`).join("");
    const issues = (r.atsIssues||[]).map(i=>
      `<div class="issue"><span class="sev ${i.severity||'low'}"></span>
        <div class="body"><b>${esc(i.issue)}</b>
        <div class="fix"><em>Fix:</em> ${esc(i.fix)}</div></div></div>`).join("");
    const wins = (r.quickWins||[]).map(w=>`<li>${esc(w)}</li>`).join("");

    results.innerHTML = `
      <div class="card pad res-section" style="animation-delay:0s">
        <div class="scorehead">
          <div class="gauge">
            <svg width="104" height="104" viewBox="0 0 104 104">
              <circle cx="52" cy="52" r="44" fill="none" stroke="var(--chip)" stroke-width="9"/>
              <circle cx="52" cy="52" r="44" fill="none" stroke="${col}" stroke-width="9"
                stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C}" id="ring"/>
            </svg>
            <div class="val"><span class="num">${score}</span><span class="of">/ 100 ATS</span></div>
          </div>
          <div class="verdict">
            <span class="tag" style="background:${tagBg};color:#fff">${tagTxt}</span>
            <p><span class="role">Read as: ${esc(r.detectedRole||"—")}.</span> ${esc(r.verdict||"")}</p>
          </div>
        </div>
        <div class="bars">${bars}</div>
      </div>

      <div class="card pad res-section" style="animation-delay:.06s">
        <h3 class="sec">Skills you've already got</h3>
        <p class="sec-sub">Pulled straight from your resume.</p>
        <div class="chips">${found||"<span class='sec-sub'>None detected — add a skills section.</span>"}</div>
      </div>

      <div class="card pad res-section" style="animation-delay:.12s">
        <h3 class="sec">Skills worth adding</h3>
        <p class="sec-sub">Common for this role and missing (or buried) here.</p>
        <div class="add-grid">${add||"<span class='sec-sub'>Good coverage already.</span>"}</div>
      </div>

      <div class="card pad res-section" style="animation-delay:.18s">
        <h3 class="sec">A sharper summary</h3>
        <p class="sec-sub">Drop this at the top of your resume.</p>
        <div class="summary" id="summary">${esc(r.professionalSummary||"")}</div>
        <button class="copybtn" id="copySum">Copy summary</button>
      </div>

      ${bullets?`<div class="card pad res-section" style="animation-delay:.24s">
        <h3 class="sec">Line-by-line redlines</h3>
        <p class="sec-sub">Your phrasing, struck through — my rewrite below it.</p>
        <div class="redline">${bullets}</div>
      </div>`:""}

      ${issues?`<div class="card pad res-section" style="animation-delay:.3s">
        <h3 class="sec">ATS flags</h3>
        <p class="sec-sub">Things that trip up applicant tracking systems.</p>
        <div class="issues">${issues}</div>
      </div>`:""}

      ${wins?`<div class="card pad res-section" style="animation-delay:.36s">
        <h3 class="sec">Quick wins</h3>
        <p class="sec-sub">Five-minute fixes, biggest impact first.</p>
        <ul class="wins">${wins}</ul>
      </div>`:""}

      <div class="toolbar">
        <button class="tb primary" onclick="window.print()">⤓ Save report as PDF</button>
        <button class="tb" id="again">Analyze another</button>
      </div>`;

    requestAnimationFrame(()=>{
      setTimeout(()=>{ const ring=$("#ring"); if(ring) ring.style.transition="stroke-dashoffset 1s ease",ring.style.strokeDashoffset=off; },150);
      document.querySelectorAll(".fill").forEach(f=>setTimeout(()=>f.style.width=f.dataset.w+"%",200));
    });
    const cs=$("#copySum");
    if(cs) cs.onclick=()=>{navigator.clipboard.writeText($("#summary").textContent);cs.textContent="Copied ✓";setTimeout(()=>cs.textContent="Copy summary",1500);};
    const ag=$("#again");
    if(ag) ag.onclick=()=>{results.scrollIntoView({behavior:"smooth"});resumeEl.focus();};
  }

  runBtn.onclick = analyze;
</script>
