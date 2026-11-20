(function(){
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];

  /* ---------- theme ---------- */
  const root=document.documentElement;
  const saved=localStorage.getItem('theme');
  root.dataset.theme = saved || (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');

  function syncThemeUI(){
    const isDark = root.dataset.theme === 'dark';
    $$('[data-theme-label]').forEach(el=>el.textContent = isDark ? 'Light' : 'Dark');
    $$('[data-theme-sun]').forEach(el=>el.style.display = isDark ? '' : 'none');
    $$('[data-theme-moon]').forEach(el=>el.style.display = isDark ? 'none' : '');
  }
  syncThemeUI();

  window.toast=(m)=>{
    const t=$('#toast'); if(!t) return;
    t.textContent=m; t.classList.add('on');
    clearTimeout(t._tid);
    t._tid=setTimeout(()=>t.classList.remove('on'),2200);
  };

  /* ---------- CAPTCHA controller ---------- */
  function refreshCaptcha(btn, modeOverride){
    const box = btn ? btn.closest('[data-captcha-box]') : $('[data-captcha-box]');
    if(!box) return;
    const img = box.querySelector('img[data-captcha-img]');
    const input = box.querySelector('input[name="captcha"]');
    if(!img) return;
    const mode = modeOverride || box.dataset.mode || 'text';
    box.dataset.mode = mode;
    box.querySelectorAll('[data-captcha-mode]').forEach(b=>b.classList.toggle('active', b.dataset.captchaMode===mode));
    if(input){
      input.placeholder = mode==='math' ? 'Enter numeric result (e.g. 25)' : 'Type the 6 characters shown above';
      input.value = '';
    }
    const rbtn = box.querySelector('[data-captcha-refresh]');
    if(rbtn){ rbtn.classList.add('spinning'); setTimeout(()=>rbtn.classList.remove('spinning'),550); }
    const theme = root.dataset.theme || 'light';
    img.src = `/captcha.svg?mode=${encodeURIComponent(mode)}&theme=${encodeURIComponent(theme)}&t=${Date.now()}`;
  }

  /* ---------- sidebar & dropdowns ---------- */
  function closeSidebar(){
    $('#sidebar')?.classList.remove('open');
    $('#sidebarBackdrop')?.classList.remove('open');
  }
  function closeUserMenu(){
    const dd = $('#userDropdown'), tr = $('#userMenuBtn');
    if(dd) dd.classList.remove('open');
    if(tr) tr.setAttribute('aria-expanded','false');
  }

  document.addEventListener('click',e=>{
    // Theme toggle
    if(e.target.closest('#themeBtn, [data-theme-toggle]')){
      root.dataset.theme = root.dataset.theme==='dark'?'light':'dark';
      localStorage.setItem('theme',root.dataset.theme);
      syncThemeUI();
      Charts.retheme();
      if($('[data-captcha-box]')) refreshCaptcha(null);
      return;
    }
    // Mobile sidebar toggle
    if(e.target.closest('#menuBtn, [data-open-menu]')){
      const sb = $('#sidebar');
      const open = sb?.classList.toggle('open');
      $('#sidebarBackdrop')?.classList.toggle('open', !!open);
      return;
    }
    if(e.target.closest('#sidebarBackdrop') || (!e.target.closest('#sidebar') && $('#sidebar')?.classList.contains('open'))){
      closeSidebar();
    }
    // User dropdown
    const umBtn = e.target.closest('#userMenuBtn');
    if(umBtn){
      const dd = $('#userDropdown');
      const open = dd?.classList.toggle('open');
      umBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      return;
    }
    if(!e.target.closest('.user-menu')) closeUserMenu();

    // Flash dismiss
    const fClose = e.target.closest('[data-flash-close]');
    if(fClose){ fClose.closest('.flash')?.remove(); return; }

    // Print button
    const p = e.target.closest('[data-print]');
    if(p){ window.print(); return; }

    // Password show/hide toggle
    const pwBtn = e.target.closest('[data-toggle-pw]');
    if(pwBtn){
      const wrap = pwBtn.closest('.input-wrap');
      const inp = wrap?.querySelector('input');
      if(inp){
        const show = inp.type === 'password';
        inp.type = show ? 'text' : 'password';
        pwBtn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
        const eOn = pwBtn.querySelector('[data-eye-on]'), eOff = pwBtn.querySelector('[data-eye-off]');
        if(eOn) eOn.style.display = show ? 'none' : '';
        if(eOff) eOff.style.display = show ? '' : 'none';
      }
      return;
    }

    // CAPTCHA refresh & mode switch
    const capRef = e.target.closest('[data-captcha-refresh]');
    if(capRef){ refreshCaptcha(capRef); return; }
    const capMode = e.target.closest('[data-captcha-mode]');
    if(capMode){ refreshCaptcha(capMode, capMode.dataset.captchaMode); return; }

    // Demo credential quick-fill
    const demoBtn = e.target.closest('[data-demo-user]');
    if(demoBtn){
      const idEl = $('#identifier'), pwEl = $('#password'), capEl = $('#captcha');
      if(idEl) idEl.value = demoBtn.dataset.demoUser || '';
      if(pwEl) pwEl.value = demoBtn.dataset.demoPass || '';
      if(capEl) capEl.focus();
      window.toast(`Filled ${demoBtn.dataset.demoUser} credentials — enter CAPTCHA to sign in`);
      return;
    }

    // Privacy Consent Banner controls
    const openConsent = e.target.closest('[data-open-consent]');
    if(openConsent){
      $('#consentBanner')?.classList.add('open');
      $('#consentBackdrop')?.classList.add('open');
      $('#consentFloatBtn')?.classList.add('hidden');
      return;
    }
    if(e.target.closest('#closeConsentBtn')){
      $('#consentBanner')?.classList.remove('open');
      $('#consentBackdrop')?.classList.remove('open');
      $('#consentFloatBtn')?.classList.remove('hidden');
      return;
    }
    const togPurp = e.target.closest('#togglePurposesBtn');
    if(togPurp){
      const panel = $('#consentPurposes');
      if(panel){
        const willOpen = panel.hidden;
        panel.hidden = !willOpen;
        togPurp.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
        togPurp.textContent = willOpen ? 'Hide Purposes' : 'Show Purposes';
      }
      return;
    }
    const preset = e.target.closest('[data-reason-preset]');
    if(preset){
      const rInp = $('#consentReason');
      if(rInp){ rInp.value = preset.dataset.reasonPreset || ''; rInp.focus(); }
      $$('.reason-chip').forEach(c=>c.classList.toggle('active', c===preset));
      return;
    }
    const consentBtn = e.target.closest('[data-consent-action]');
    if(consentBtn){
      submitConsent(consentBtn.dataset.consentAction);
      return;
    }
  });

  async function submitConsent(decision){
    const banner = $('#consentBanner');
    if(!banner) return;
    const btns = $$('[data-consent-action]', banner);
    btns.forEach(b=>b.disabled = true);
    const reason = ($('#consentReason')?.value || '').trim();
    const payload = {
      decision,
      reason,
      analytics: !!$('#permAnalytics')?.checked,
      personalization: !!$('#permPersonalization')?.checked,
      diagnostics: !!$('#permDiagnostics')?.checked,
    };
    try{
      const res = await fetch('/api/consent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': banner.dataset.csrf || '',
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if(!res.ok){
        window.toast(data.error || 'Could not save privacy preferences.');
        return;
      }
      banner.classList.remove('open');
      $('#consentBackdrop')?.classList.remove('open');
      $('#consentFloatBtn')?.classList.remove('hidden');
      const labels = {
        accepted_all: 'All permissions accepted & saved.',
        rejected_all: 'Optional permissions rejected (essential only).',
        custom: 'Custom privacy preferences saved.',
      };
      window.toast(labels[decision] || 'Privacy preferences saved.');
      if(location.pathname === '/account'){
        setTimeout(()=>location.reload(), 450);
      }
    } catch(err){
      window.toast('Network error while saving privacy preferences.');
    } finally{
      btns.forEach(b=>b.disabled = false);
    }
  }

  document.addEventListener('keydown', e=>{
    if(e.key === 'Escape'){ closeSidebar(); closeUserMenu(); }
  });

  /* ---------- password strength meter ---------- */
  function bindPasswordMeters(){
    $$('[data-pw-meter]').forEach(input=>{
      const meterId = input.dataset.pwMeter;
      const meter = document.getElementById(meterId);
      if(!meter) return;
      const bars = meter.querySelector('.pw-bars');
      const update = ()=>{
        const v = input.value || '';
        const rules = {
          len: v.length >= 8,
          upper: /[A-Z]/.test(v),
          lower: /[a-z]/.test(v),
          num: /[0-9]/.test(v),
          spec: /[^A-Za-z0-9]/.test(v),
        };
        let passed = Object.values(rules).filter(Boolean).length;
        let score = 0;
        if(v.length > 0){
          score = passed <= 2 ? 1 : (passed === 3 ? 2 : (passed === 4 ? 3 : 4));
        }
        if(bars) bars.dataset.score = String(score);
        Object.entries(rules).forEach(([k,ok])=>{
          const el = meter.querySelector(`[data-rule="${k}"]`);
          if(el) el.classList.toggle('ok', ok);
        });
      };
      input.addEventListener('input', update);
      update();
    });
  }

  /* ---------- filter auto-submit ---------- */
  $$('form[data-auto] select').forEach(s=>s.addEventListener('change',()=>s.form.submit()));

  /* ---------- charts ---------- */
  const PAL=['#158a59','#e5a135','#0c4a3e','#d6455d','#2ea877','#3b82c4','#c2578f','#84a92c','#e07a1f','#5b6b7a','#1fb072','#a855f7','#f43f5e','#22c55e'];
  const css=v=>getComputedStyle(root).getPropertyValue(v).trim();
  const Charts={list:{},
    defaults(){ if(!window.Chart)return;
      Chart.defaults.color=css('--muted');
      Chart.defaults.borderColor=css('--line');
      Chart.defaults.font.family=getComputedStyle(document.body).fontFamily;
      Chart.defaults.font.size=12;
      Chart.defaults.plugins.tooltip.padding=11;
      Chart.defaults.plugins.tooltip.cornerRadius=10;
      Chart.defaults.maintainAspectRatio=false;
      Chart.defaults.responsive=true;
      Chart.defaults.plugins.legend.labels.usePointStyle=true;
      Chart.defaults.plugins.legend.labels.boxWidth=8;
    },
    prep(cfg){
      cfg=JSON.parse(JSON.stringify(cfg)); const o=cfg.options=cfg.options||{};
      const byPoint=o.colorByPoint, noGrid=o.noGrid, click=o.clickPostId; delete o.colorByPoint; delete o.noGrid; delete o.clickPostId;
      (cfg.data.datasets||[]).forEach((d,i)=>{
        if(cfg.type==='doughnut'||cfg.type==='pie'){
          d.backgroundColor=d.backgroundColor||cfg.data.labels.map((_,j)=>PAL[j%PAL.length]);
          d.borderColor=css('--surface'); d.borderWidth=2;
        }
        else if(byPoint&&cfg.data.datasets.length===1){
          d.backgroundColor=cfg.data.labels.map((_,j)=>PAL[j%PAL.length]); d.borderRadius=6;
        }
        else {
          const c=PAL[i%PAL.length]; d.backgroundColor=d.backgroundColor||c; d.borderColor=d.borderColor||c;
          if(cfg.type==='bar')d.borderRadius=6;
        }
      });
      if(noGrid){o.scales=o.scales||{};['x','y'].forEach(a=>{o.scales[a]=Object.assign({grid:{display:false}},o.scales[a]||{})})}
      o.plugins=o.plugins||{}; o.interaction=o.interaction||{mode:cfg.type==='scatter'?'nearest':'index',intersect:cfg.type==='scatter'};
      if(cfg.type==='scatter'){
        o.plugins.tooltip=Object.assign({callbacks:{label:function(c){const r=c.raw;return c.dataset.label+(r.id?' \u00b7 '+r.id:'')+' ('+r.x+', '+r.y+')'}}},o.plugins.tooltip||{});
      }
      if(click){ o.onClick=(e,els,ch)=>{ if(!els.length)return; const r=ch.data.datasets[els[0].datasetIndex].data[els[0].index]; if(r.id) location.href='/posts/'+r.id; }; o.onHover=(e,els)=>{e.native.target.style.cursor=els.length?'pointer':'default'} }
      return cfg;
    },
    make(id,cfg){ const el=document.getElementById(id); if(!el||!window.Chart)return;
      this.defaults(); if(this.list[id])this.list[id].destroy();
      const c=new Chart(el,this.prep(cfg)); c._src=cfg; this.list[id]=c; el.setAttribute('role','img'); return c; },
    retheme(){ this.defaults(); Object.entries(this.list).forEach(([id,c])=>this.make(id,c._src)); },
    init(){ $$('script[type="application/json"][data-chart]').forEach(s=>this.make(s.dataset.chart,JSON.parse(s.textContent))); }
  };
  window.Charts=Charts;
  document.addEventListener('DOMContentLoaded',()=>{
    Charts.init();
    bindPasswordMeters();
    document.body.classList.add('ready');

    // Register PWA Service Worker for mobile installability
    if('serviceWorker' in navigator){
      navigator.serviceWorker.register('/sw.js').catch(()=>{});
    }
  });

  // PWA Install App prompt handler
  let deferredInstall = null;
  window.addEventListener('beforeinstallprompt', (e)=>{
    e.preventDefault();
    deferredInstall = e;
    const btn = $('#installAppBtn');
    if(btn) btn.style.display = 'inline-flex';
  });
  document.addEventListener('click', async (e)=>{
    const btn = e.target.closest('#installAppBtn');
    if(!btn || !deferredInstall) return;
    deferredInstall.prompt();
    const res = await deferredInstall.userChoice;
    if(res && res.outcome === 'accepted') window.toast('App installed to your device!');
    deferredInstall = null;
    btn.style.display = 'none';
  });
})();
