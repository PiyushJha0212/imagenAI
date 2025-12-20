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
    const platform = document.getElementById("platform").value;
    const style = document.getElementById("style").value;
    let width = parseInt(document.getElementById('width').value || '384', 10);
    let steps = parseInt(document.getElementById('steps').value || '20', 10);
    const preset = document.getElementById('preset').value;

    // apply preset shortcuts
    if (preset === 'fast') {
        steps = Math.max(6, Math.min(steps, 12));
        width = Math.min(320, width);
    } else if (preset === 'quality') {
        steps = Math.max(30, steps);
        width = Math.max(512, width);
    }
    const btn = document.getElementById('generateBtn');
    const downloadBtn = document.getElementById('downloadBtn');
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
            body: JSON.stringify({ product, use_case, platform, style, width, steps, guidance_scale: guidance, negative_prompt, seed })
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
        };

    } catch (err) {
        console.error(err);
        setMessage('Error: ' + (err.message || err), 'error');
        showSpinner(false);
    } finally {
        btn.disabled = false;
    }
}
