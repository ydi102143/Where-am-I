// --- API helpers ---
async function fetchPlan(minutes=90){ const r=await fetch(`/v1/plan/today?minutes_available=${encodeURIComponent(minutes)}`); if(!r.ok) throw new Error("plan failed"); return r.json(); }
async function updateTask(taskId, payload){ const r=await fetch(`/v1/tasks/${taskId}`, { method:"PATCH", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)}); if(!r.ok) throw new Error("update failed"); return r.json(); }
async function postReflect(payload){ const r=await fetch("/v1/reflect",{ method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)}); if(!r.ok) throw new Error("reflect failed"); return r.json(); }
async function fetchReflectSummary(days=7){ const r=await fetch(`/v1/reflect/recent?days=${days}`); if(!r.ok) throw new Error("summary failed"); return r.json(); }
async function fetchAnalyze(days=7){ const r=await fetch(`/v1/reflect/analyze?days=${days}`); if(!r.ok) throw new Error("analyze failed"); return r.json(); }
async function fetchWeekly(){ const r=await fetch("/v1/review/weekly"); if(!r.ok) throw new Error("weekly fetch failed"); return r.json(); }
async function runWeekly(){ const r=await fetch("/v1/review/weekly/run", { method:"POST" }); if(!r.ok) throw new Error("weekly run failed"); return r.json(); }
async function fetchGoals(){ const r=await fetch("/v1/goals"); if(!r.ok) throw new Error("goals fetch failed"); return r.json(); }
async function runPlan(goalId){ const r=await fetch(`/v1/goals/${goalId}/plan`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({ minutes_per_day:90, max_tasks:8, dry_run:false })}); if(!r.ok) throw new Error("plan run failed"); return r.json(); }
async function fetchIntegration(){ const r=await fetch("/v1/integration"); if(r.status===404) return null; if(!r.ok) throw new Error("integration fetch failed"); return r.json(); }
async function saveIntegration(url){ const r=await fetch("/v1/integration", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({ kind:"gcal_ics", value:url })}); if(!r.ok) throw new Error("integration save failed"); return r.json(); }
async function fetchAvailableMinutes(params){ const q=new URLSearchParams(params); const r=await fetch(`/v1/plan/available_minutes?${q.toString()}`); if(!r.ok) throw new Error("available minutes failed"); return r.json(); }

function el(html){ const t=document.createElement("template"); t.innerHTML=html.trim(); return t.content.firstElementChild; }
function toast(msg){ const box=document.createElement("div"); box.className="toast"; box.textContent=msg; document.body.appendChild(box); setTimeout(()=> box.classList.add("show"), 10); setTimeout(()=> { box.classList.remove("show"); box.remove(); }, 1800); }
function todayISO(){ const d=new Date(); const tz=d.getTimezoneOffset(); const local=new Date(d.getTime()-tz*60000); return local.toISOString().slice(0,10); }

function cardHTML(it){
  const due = it.due ? new Date(it.due).toLocaleDateString("ja-JP") : "—";
  const disabledStart = (it.status === "doing" || it.status === "done") ? "disabled" : "";
  const disabledDone  = (it.status === "done") ? "disabled" : "";
  return `
    <article class="card" data-task-id="${it.task_id}">
      <div class="row">
        <h3 class="title">${it.title}</h3>
        <span class="badge ${it.status}">${it.status}</span>
      </div>
      <div class="meta">
        <span>Impact: ${it.impact}</span>
        <span>Effort: ${it.effort_min}分</span>
        <span>期限: ${due}</span>
        <span class="score">Score: ${it.score}</span>
      </div>
      <p class="coach">${it.coach_line}</p>
      <div class="actions">
        <button class="btn start" ${disabledStart} data-action="start">開始</button>
        <button class="btn done" ${disabledDone} data-action="done">完了</button>
        <a class="btn ghost" href="/v1/tasks/${it.task_id}" target="_blank" rel="noopener">JSON</a>
      </div>
    </article>
  `;
}

function bindCardActions(card){
  const badge = card.querySelector(".badge");
  const btnStart = card.querySelector('button[data-action="start"]');
  const btnDone  = card.querySelector('button[data-action="done"]');
  const taskId = card.dataset.taskId;
  if(btnStart){
    btnStart.onclick = async ()=>{
      btnStart.disabled = true;
      try{ await updateTask(taskId, { status:"doing" }); badge.textContent="doing"; badge.classList.remove("pending","done"); badge.classList.add("doing"); toast("ステータス: 開始"); }
      catch(e){ console.error(e); btnStart.disabled=false; toast("開始に失敗しました"); }
    };
  }
  if(btnDone){
    btnDone.onclick = async ()=>{
      btnDone.disabled = true;
      try{ await updateTask(taskId, { status:"done" }); badge.textContent="done"; badge.classList.remove("pending","doing"); badge.classList.add("done"); toast("完了！おつかれさま🎉"); await load(); }
      catch(e){ console.error(e); btnDone.disabled=false; toast("完了に失敗しました"); }
    };
  }
}

function render(items){
  const wrap=document.querySelector("#cards"); const empty=document.querySelector("#empty");
  wrap.innerHTML=""; if(!items || items.length===0){ empty.style.display="block"; return; } empty.style.display="none";
  items.forEach(it=>{ const node=el(cardHTML(it)); wrap.appendChild(node); bindCardActions(node); });
}

async function load(){
  const minutes = Number(document.querySelector("#minutes").value || 90);
  try{ const data = await fetchPlan(minutes); render(data); }
  catch(e){ console.error(e); alert("取得に失敗しました"); }
}

// Reflect
async function loadSummary(){
  try{ const d=await fetchReflectSummary(7); document.querySelector("#r-count").textContent=d.count??0; document.querySelector("#r-avg").textContent=(d.avg_mood??"—"); document.querySelector("#r-latest-date").textContent=d.latest_date||"—"; document.querySelector("#r-latest-text").textContent=d.latest_text||"—"; }
  catch(e){ console.error(e); }
}
async function onSubmitReflect(ev){
  ev.preventDefault();
  const dateStr=document.querySelector("#r-date").value||todayISO();
  const mood=Number(document.querySelector("#r-mood").value||3);
  const text=(document.querySelector("#r-text").value||"").trim();
  const status=document.querySelector("#r-status");
  status.textContent="保存中…";
  try{ await postReflect({ date:dateStr, mood, text }); status.textContent="保存しました"; document.querySelector("#r-text").value=""; await loadSummary(); await loadAnalyze(); await loadWeekly(); }
  catch(e){ console.error(e); status.textContent="保存に失敗しました"; }
  finally{ setTimeout(()=> status.textContent="", 2000); }
}
function initReflectUI(){
  const dateEl=document.querySelector("#r-date"); if(dateEl) dateEl.value=todayISO();
  const form=document.querySelector("#reflect-form"); form?.addEventListener("submit", onSubmitReflect);
  loadSummary();
}

// Analyze section
function renderAnalyze(data){
  const sumEl=document.querySelector("#rv-summary"); const ul=document.querySelector("#rv-improve");
  if(!data || (data.count??0)===0){ sumEl.textContent="まだデータが少ないため、要約は表示できません。今日の振り返りを保存してみよう。"; ul.innerHTML=""; return; }
  sumEl.textContent=data.summary || "小さく始めて前進。粒度は30分に調整。";
  ul.innerHTML=(data.improvements||[]).slice(0,3).map(t=>`<li>${t}</li>`).join("");
}
async function loadAnalyze(){ try{ const d=await fetchAnalyze(7); renderAnalyze(d); } catch(e){ console.error(e); document.querySelector("#rv-summary").textContent="要約の取得に失敗しました。"; } }
document.getElementById("rv-reload")?.addEventListener("click", loadAnalyze);

// Weekly
function renderWeekly(data){
  const sum=document.querySelector("#wk-summary"); const ul=document.querySelector("#wk-improve"); const meta=document.querySelector("#wk-meta");
  if(!data || data.exists===false){ sum.textContent="まだ生成されていません。『手動生成』を押すか、日曜21時をお待ちください。"; ul.innerHTML=""; meta.textContent=""; return; }
  sum.textContent=data.summary || "小さく始めて前進。粒度を30分に調整。";
  ul.innerHTML=(data.improvements||[]).slice(0,3).map(t=>`<li>${t}</li>`).join("");
  const range=data.range?`${data.range.start}〜${data.range.end}`:""; meta.textContent=`対象: ${range} / 生成日: ${data.date} / 入力メモ件数: ${data.count ?? 0}`;
}
async function loadWeekly(){ try{ const d=await fetchWeekly(); renderWeekly(d); } catch(e){ console.error(e); document.querySelector("#wk-summary").textContent="取得に失敗しました。"; } }
document.getElementById("wk-reload")?.addEventListener("click", loadWeekly);
document.getElementById("wk-run")?.addEventListener("click", async ()=>{ try{ const res=await runWeekly(); renderWeekly({ exists:true, ...res }); } catch(e){ console.error(e); alert("手動生成に失敗しました"); } });

// ICS modal & calendar
function openIcsModal(prefill=""){ const m=document.getElementById("ics-modal"); m.style.display="block"; document.getElementById("ics-url").value=prefill||""; }
function closeIcsModal(){ document.getElementById("ics-modal").style.display="none"; }
async function getFromCalendar(){
  try{
    const integ=await fetchIntegration(); if(!integ){ openIcsModal(""); return; }
    const iso=(new Date()).toISOString().slice(0,10);
    const res=await fetchAvailableMinutes({ date_str: iso, work_start:"07:00", work_end:"23:00" });
    const min=res.available_minutes ?? 0; document.getElementById("minutes").value=Math.max(15, Math.min(600, min)); toast(`今日の空き時間: ${min}分 を適用しました`); await load();
  }catch(e){ console.error(e); alert("カレンダー取得に失敗しました。ICS設定を確認してください。"); }
}
document.getElementById("get-from-cal")?.addEventListener("click", getFromCalendar);
document.getElementById("ics-close")?.addEventListener("click", closeIcsModal);
document.getElementById("ics-save")?.addEventListener("click", async ()=>{
  const url=(document.getElementById("ics-url").value||"").trim();
  if(!url){ alert("URLを入力してください"); return; }
  try{ await saveIntegration(url); closeIcsModal(); toast("ICSを保存しました。『カレンダーから取得』を再度押してください。"); }
  catch(e){ console.error(e); alert("保存に失敗しました"); }
});

// Generate tasks button
async function generateTasks(){
  try{
    const goals=await fetchGoals();
    if(!goals || goals.length===0){ alert("Goalがありません。先にGoalを作成してください。"); return; }
    const latest=goals[0];
    const res=await runPlan(latest.id);
    toast(`タスクを ${res.created_count} 件生成しました`); await load();
  }catch(e){ console.error(e); alert("自動生成に失敗しました"); }
}
document.getElementById("gen-tasks")?.addEventListener("click", generateTasks);

document.querySelector("#reload").onclick = load;
window.addEventListener("DOMContentLoaded", ()=>{ load(); initReflectUI(); loadAnalyze(); loadWeekly(); });
