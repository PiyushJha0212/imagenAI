const API_BASE = "http://127.0.0.1:8000";

function setMessage(text, type = 'info') {
    const el = document.getElementById('message');
    el.textContent = text;
    el.className = type;
}

function showSpinner(show) {
    const s = document.getElementById('spinner');
    const img = document.getElementById('result');
    if (show) {
        s.hidden = false;
        img.src = '';
        img.style.display = 'none';
    } else {
        s.hidden = true;
        img.style.display = '';
    }
}

async function generate() {
    const product = document.getElementById("product").value.trim();
    const use_case = document.getElementById("use_case").value;
    const platformEl = document.getElementById("platform");
    let platform = platformEl ? platformEl.value : '';
    const template = document.getElementById('template') ? document.getElementById('template').value : 'sale_poster';
    // derive platform from template to enforce template constraints
    function mapTemplateToPlatform(t) {
        const tt = (t || '').toLowerCase();
        if (tt.includes('banner')) return 'banner';
        if (tt.includes('instagram')) return 'instagram';
        if (tt.includes('poster') || tt.includes('sale') || tt.includes('event')) return 'poster';
        return 'poster';
    }
    platform = mapTemplateToPlatform(template);
    if (platformEl) platformEl.value = platform;
    const style = document.getElementById("style").value;
    let width = parseInt(document.getElementById('width').value || '384', 10);
    let steps = parseInt(document.getElementById('steps').value || '20', 10);
    const preset = document.getElementById('preset').value;
    const perfToggle = document.getElementById('perfToggle') && document.getElementById('perfToggle').checked;
    // apply preset: map presets to sensible steps/width per layout
    (function applyPreset(){
        const defaults = { banner: 960, poster: 512, instagram: 640 };
        const base = defaults[platform] || 640;
        if (preset === 'fast') { steps = 8; width = Math.max(256, Math.round(base * 0.6)); }
        else if (preset === 'quality') { steps = 40; width = Math.min(1024, Math.round(base * 1.2)); }
        else { steps = 20; width = base; }
        // reflect in hidden inputs so export uses same values
        const win = document.getElementById('width'); if (win) win.value = width;
        const sin = document.getElementById('steps'); if (sin) sin.value = steps;
    })();
    const btn = document.getElementById('generateBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    // Profile selection: performance toggle overrides profile to 'fast'
    let profile = document.getElementById('profile').value || 'balanced';
    if (perfToggle) {
        profile = 'fast';
        // reflect in select UI
        const psel = document.getElementById('profile'); if (psel) psel.value = 'fast';
    }

    const exactCheckbox = document.getElementById('exactAspect');
    const exact = (exactCheckbox && exactCheckbox.checked) || (profile === 'high'); // exact if checked or high-quality

    // If exact is requested, use standard layout sizes to ensure precise aspect ratios
    function layoutSizeFor(platform) {
        if (!platform) return 640;
        platform = platform.toLowerCase();
        if (platform === 'banner') return 960; // 3:1 -> backend will compute height
        if (platform === 'poster') return 512; // 2:3 width -> backend computes height
        return 640; // instagram / square
    }

    if (exact) {
        width = layoutSizeFor(platform);
        // reflect width in input so user sees it
        const win = document.getElementById('width'); if (win) win.value = width;
    }
    const guidance = parseFloat(document.getElementById('guidance').value || '7');
    const negative_prompt = document.getElementById('negative_prompt').value.trim();
    const seedVal = document.getElementById('seed').value;
    const seed = seedVal ? parseInt(seedVal, 10) : null;

    if (!product) {
        setMessage('Please enter a product or title.', 'warning');
        return;
    }

    setMessage('Sending request to the generator...', 'info');
    btn.disabled = true;
    showSpinner(true);
    downloadBtn.style.display = 'none';

    try {
        const resp = await fetch(API_BASE + "/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product, use_case, platform, style, template, width, steps, guidance_scale: guidance, negative_prompt, seed, profile, exact })
        });

        if (!resp.ok) {
            const txt = await resp.text();
            throw new Error(`Server error ${resp.status}: ${txt}`);
        }

        const data = await resp.json();

        // Support a few response shapes: { image_data: base64 } or { image_path: '/path' } or { url: 'http...' }
        let src = '';
        if (data.image_data) {
            src = 'data:image/png;base64,' + data.image_data;
        } else if (data.url) {
            src = data.url;
        } else if (data.image_path) {
            if (/^https?:\/\//i.test(data.image_path)) src = data.image_path;
            else if (data.image_path.startsWith('/')) src = API_BASE + data.image_path;
            else src = API_BASE + '/' + data.image_path;
        } else {
            throw new Error('Unexpected response from server');
        }

        const img = document.getElementById('result');
        img.src = src;
        img.onload = () => {
            showSpinner(false);
            setMessage('Design generated — preview shown below.', 'success');
            downloadBtn.style.display = '';
            // prepare download
            downloadBtn.onclick = () => {
                const a = document.createElement('a');
                a.href = src;
                a.download = (product.replace(/\s+/g, '_') || 'design') + '.png';
                document.body.appendChild(a);
                a.click();
                a.remove();
            };
            // enable overlay editing when an image is present
            try { enableOverlayControls(); } catch(e) { /* ignore if helper missing */ }
            // Update overlay preview values
            updateOverlayFromInputs();
            updatePreviewLayout(platform);
        };

    } catch (err) {
        console.error(err);
        setMessage('Error: ' + (err.message || err), 'error');
        showSpinner(false);
    } finally {
        btn.disabled = false;
    }
}

// Preview layout mapping — adjust container height to simulate aspect ratios without re-generating
function updatePreviewLayout(platform) {
    const container = document.getElementById('imageContainer');
    if (!container) return;
    if (platform === 'banner') {
        container.style.height = '180px';
    } else if (platform === 'poster') {
        container.style.height = '680px';
    } else {
        container.style.height = '420px';
    }
}

function updateOverlayFromInputs() {
    const title = document.getElementById('titleText').value || '';
    const cta = document.getElementById('ctaText').value || '';
    const color = document.getElementById('ctaColor').value || '#111827';
    const pos = document.getElementById('position').value || 'bottom-left';
    const titleColor = document.getElementById('titleColor') ? document.getElementById('titleColor').value : '#ffffff';
    const logoEl = document.getElementById('overlayLogo');
    const logoInput = document.getElementById('logoInput');
    const logoScale = parseInt(document.getElementById('logoScale')?.value || '120', 10);

    const overlay = document.getElementById('overlay');
    const titleEl = document.getElementById('overlayTitle');
    const btn = document.getElementById('overlayBtn');

    titleEl.textContent = title;
    btn.textContent = cta;
    btn.style.background = color;
    titleEl.style.color = titleColor;

    // logo preview handling
    if (logoInput && logoInput.files && logoInput.files[0]) {
        const file = logoInput.files[0];
        const url = URL.createObjectURL(file);
        logoEl.src = url;
        logoEl.hidden = false;
        // scale in preview by setting height (px)
        logoEl.style.height = logoScale + 'px';
    } else {
        logoEl.src = '';
        logoEl.hidden = true;
    }
    btn.style.pointerEvents = cta ? 'auto' : 'none';

    // position handling
    titleEl.style.left = '';
    titleEl.style.right = '';
    titleEl.style.top = '';
    titleEl.style.bottom = '';
    btn.style.left = '';
    btn.style.right = '';
    btn.style.top = '';
    btn.style.bottom = '';

    switch (pos) {
        case 'bottom-left':
            titleEl.style.left = '20px'; titleEl.style.bottom = '80px';
            btn.style.left = '20px'; btn.style.bottom = '20px';
            break;
        case 'bottom-right':
            titleEl.style.right = '20px'; titleEl.style.bottom = '80px';
            btn.style.right = '20px'; btn.style.bottom = '20px';
            break;
        case 'top-left':
            titleEl.style.left = '20px'; titleEl.style.top = '20px';
            btn.style.left = '20px'; btn.style.top = '80px';
            break;
        case 'top-right':
            titleEl.style.right = '20px'; titleEl.style.top = '20px';
            btn.style.right = '20px'; btn.style.top = '80px';
            break;
        case 'center':
            titleEl.style.left = '50%'; titleEl.style.transform = 'translateX(-50%)'; titleEl.style.top = '40%';
            btn.style.left = '50%'; btn.style.transform = 'translateX(-50%)'; btn.style.top = '54%';
            break;
    }
}

// export composed design by drawing image + overlays onto a canvas and downloading
document.getElementById('exportBtn').addEventListener('click', async () => {
    const platform = document.getElementById('platform').value;
    // determine export dims via simple mapping
    let outW = 1024, outH = 1024;
    if (platform === 'banner') { outW = 1920; outH = 640; }
    else if (platform === 'poster') { outW = 1000; outH = 1500; }
    else { outW = 1024; outH = 1024; }

    const img = document.getElementById('result');
    if (!img.src) { alert('No image to export'); return; }

    // create canvas
    const canvas = document.createElement('canvas');
    canvas.width = outW; canvas.height = outH;
    const ctx = canvas.getContext('2d');

    // background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, outW, outH);

    // draw generated image into bottom area (professional poster layout)
    const margin = Math.round(outW * 0.04);
    const imageTop = Math.round(outH * 0.38);
    const imageH = outH - imageTop - margin;
    const imageW = outW - margin * 2;

    const full = await loadImage(img.src);
    // compute crop to cover imageW x imageH
    const scale = Math.max(imageW / full.width, imageH / full.height);
    const sw = Math.round(imageW / scale), sh = Math.round(imageH / scale);
    const sx = Math.round((full.width - sw) / 2), sy = Math.round((full.height - sh) / 2);
    ctx.drawImage(full, sx, sy, sw, sh, margin, imageTop, imageW, imageH);

    // draw logo top-left if provided
    const logoInput = document.getElementById('logoInput');
    const logoScale = parseInt(document.getElementById('logoScale')?.value || '120', 10);
    if (logoInput && logoInput.files && logoInput.files[0]) {
        try {
            const file = logoInput.files[0];
            const logoImg = await loadFileImage(file);
            // compute logo width relative to outW — map logoScale (preview px) to output
            const logoW = Math.round(outW * (logoScale / 1024));
            const logoH = Math.round(logoW * (logoImg.height / logoImg.width));
            const lx = margin; const ly = margin;
            ctx.drawImage(logoImg, 0, 0, logoImg.width, logoImg.height, lx, ly, logoW, logoH);
        } catch (e) {
            console.warn('Logo load failed', e);
        }
    }

    // draw title centered at top
    const title = document.getElementById('titleText').value || '';
    const titleColor = document.getElementById('titleColor') ? document.getElementById('titleColor').value : '#ffffff';
    if (title) {
        const fontSize = Math.floor(outW / 14);
        ctx.font = `${fontSize}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        // drop shadow / stroke for legibility
        ctx.lineWidth = Math.max(4, Math.floor(fontSize / 8));
        ctx.strokeStyle = 'rgba(0,0,0,0.6)';
        ctx.fillStyle = titleColor;
        const tx = outW / 2; const ty = Math.round(outH * 0.06);
        ctx.strokeText(title, tx, ty);
        ctx.fillText(title, tx, ty);
    }

    // draw CTA near bottom area overlaying image
    const cta = document.getElementById('ctaText').value || '';
    const ctaColor = document.getElementById('ctaColor').value || '#111827';
    if (cta) {
        const btnW = Math.round(outW * 0.2);
        const btnH = Math.round(outH * 0.06);
        const bx = Math.round(outW * 0.06);
        const by = imageTop + imageH - btnH - Math.round(outH * 0.04);
        ctx.fillStyle = ctaColor;
        roundRect(ctx, bx, by, btnW, btnH, 10);
        ctx.fillStyle = 'white';
        ctx.font = `${Math.floor(outW/40)}px sans-serif`;
        ctx.textBaseline = 'middle';
        ctx.fillText(cta, bx + btnW / 2, by + btnH / 2);
    }

    // download
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download = (productSafeName() || 'design') + '.png';
    document.body.appendChild(a); a.click(); a.remove();
});

function productSafeName(){
    const p = document.getElementById('product');
    return p ? p.value.trim().replace(/\s+/g,'_') : '';
}

function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x+r, y);
    ctx.arcTo(x+w, y, x+w, y+h, r);
    ctx.arcTo(x+w, y+h, x, y+h, r);
    ctx.arcTo(x, y+h, x, y, r);
    ctx.arcTo(x, y, x+w, y, r);
    ctx.closePath();
    ctx.fill();
}

function loadImage(src){
    return new Promise((res, rej) => {
        const im = new Image();
        im.crossOrigin = 'anonymous';
        im.onload = () => res(im);
        im.onerror = rej;
        im.src = src;
    });
}

function loadFileImage(file){
    return new Promise((res, rej) => {
        const reader = new FileReader();
        reader.onload = () => {
            const img = new Image();
            img.onload = () => res(img);
            img.onerror = rej;
            img.src = reader.result;
        };
        reader.onerror = rej;
        reader.readAsDataURL(file);
    });
}

// wire up overlay input listeners
['titleText','ctaText','ctaColor','position'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateOverlayFromInputs);
});

// logo, logoScale and titleColor listeners
['logoInput','logoScale','titleColor'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateOverlayFromInputs);
});

const platformEl = document.getElementById('platform');
if (platformEl) platformEl.addEventListener('change', () => updatePreviewLayout(platformEl.value));

// initialize overlay values
updateOverlayFromInputs();

// Performance toggle listener: reflect in profile select
const perfToggleEl = document.getElementById('perfToggle');
if (perfToggleEl) {
    perfToggleEl.addEventListener('change', () => {
        const psel = document.getElementById('profile');
        if (perfToggleEl.checked) {
            if (psel) psel.value = 'fast';
        } else {
            if (psel && psel.value === 'fast') psel.value = 'balanced';
        }
    });
}

// exact aspect hint: when user toggles exactAspect, update width input to layout size
const exactEl = document.getElementById('exactAspect');
if (exactEl) {
    exactEl.addEventListener('change', () => {
        const platform = document.getElementById('platform').value;
        if (exactEl.checked) {
            const w = (platform === 'banner') ? 960 : (platform === 'poster' ? 512 : 640);
            const win = document.getElementById('width'); if (win) win.value = w;
        }
    });
}

// overlay control helpers: enable/disable until image exists
function disableOverlayControls() {
    ['titleText','ctaText','ctaColor','position','titleColor','subtitleText','logoInput','logoScale','exportBtn','downloadBtn'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = true;
    });
}

function enableOverlayControls() {
    ['titleText','ctaText','ctaColor','position','titleColor','subtitleText','logoInput','logoScale','exportBtn','downloadBtn'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = false;
    });
}

function applyPresetToInputs() {
    const preset = document.getElementById('preset') ? document.getElementById('preset').value : 'balanced';
    const platform = document.getElementById('platform') ? document.getElementById('platform').value : 'poster';
    const defaults = { banner: 960, poster: 512, instagram: 640 };
    const base = defaults[platform] || 640;
    let pp = { steps: 20, width: base };
    if (preset === 'fast') pp = { steps: 8, width: Math.max(256, Math.round(base * 0.6)) };
    if (preset === 'quality') pp = { steps: 40, width: Math.min(1024, Math.round(base * 1.2)) };
    const win = document.getElementById('width'); if (win) win.value = pp.width;
    const sin = document.getElementById('steps'); if (sin) sin.value = pp.steps;
}

// wire preset and template changes to update suggested sizes
const presetEl = document.getElementById('preset'); if (presetEl) presetEl.addEventListener('change', applyPresetToInputs);
const templateEl = document.getElementById('template'); if (templateEl) templateEl.addEventListener('change', () => {
    const platformEl = document.getElementById('platform');
    const t = templateEl.value || 'sale_poster';
    function mapTemplateToPlatform(t) {
        const tt = (t || '').toLowerCase();
        if (tt.includes('banner')) return 'banner';
        if (tt.includes('instagram')) return 'instagram';
        if (tt.includes('poster') || tt.includes('sale') || tt.includes('event')) return 'poster';
        return 'poster';
    }
    const p = mapTemplateToPlatform(t);
    if (platformEl) platformEl.value = p;
    applyPresetToInputs();
});

// start with overlays disabled until a generation occurs
disableOverlayControls();
