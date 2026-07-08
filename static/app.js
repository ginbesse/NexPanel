async function proxyRequest(target, queryString, resultNode, loadingText = 'Sorgulanıyor…') {
  resultNode.textContent = loadingText;
  const params = new URLSearchParams({ target, query: queryString });
  const response = await fetch(`/api/proxy?${params.toString()}`);
  const data = await response.json();

  if (!data.ok) {
    resultNode.textContent = `Hata: ${data.error || data.body || 'Bilinmeyen hata'}`;
    return;
  }

  const pretty = JSON.stringify(data, null, 2);
  resultNode.textContent = pretty;
}

function setStatus(text) {
  document.getElementById('status-pill').textContent = text;
}

async function handleGrade(event) {
  event.preventDefault();
  const tc = document.getElementById('tc').value.trim();
  if (!tc) return;
  setStatus('MEB notları');
  await proxyRequest(
    'https://servisler.meb.gov.tr/api/v1/ogrenci/notlar',
    `tc=${encodeURIComponent(tc)}`,
    document.getElementById('grade-result')
  );
}

async function handleEokul(event) {
  event.preventDefault();
  const eokulUrl = document.getElementById('eokulUrl').value.trim() || 'https://e-okul.meb.gov.tr/logineokul.aspx';
  setStatus('E-Okul');
  const resultNode = document.getElementById('eokul-result');
  resultNode.textContent = 'ASP.NET akışı inceleniyor…';
  const params = new URLSearchParams({ target: eokulUrl });
  const response = await fetch(`/api/proxy?${params.toString()}`);
  const data = await response.json();

  if (!data.ok) {
    resultNode.textContent = `Hata: ${data.error || 'Bilinmeyen hata'}`;
    return;
  }

  const summary = {
    url: data.url,
    status: data.status,
    contentType: data.contentType,
    cookies: data.cookies || [],
    hiddenFields: data.hiddenFields || {},
    detectedLoginFields: data.detectedLoginFields || {},
    forms: data.forms || [],
    scriptUrls: data.scriptUrls || [],
    payload: data.payload || null,
    bodyPreview: typeof data.body === 'string' ? data.body.slice(0, 2200) : data.body,
  };
  resultNode.textContent = JSON.stringify(summary, null, 2);
}

async function handleHarita(event) {
  event.preventDefault();
  const query = document.getElementById('haritaQuery').value.trim();
  setStatus('Harita');
  await proxyRequest(
    'https://atlas.harita.gov.tr/webservis/harita/hgm_ortofoto/',
    query ? `q=${encodeURIComponent(query)}` : '',
    document.getElementById('harita-result')
  );
}

async function handleBelsis(event) {
  event.preventDefault();
  const type = document.getElementById('belsisType').value;
  const value = document.getElementById('belsisValue').value.trim();
  if (!value) return;
  setStatus('Belsis');
  const endpoint = {
    adsoyad: 'https://belsis.store/api/req/adsoyad.php',
    vesika: 'https://belsis.store/api/req/vesika.php',
    tapu: 'https://belsis.store/api/req/tapu.php',
    sokak: 'https://belsis.store/api/req/sokak.php'
  }[type];
  await proxyRequest(endpoint, `q=${encodeURIComponent(value)}`, document.getElementById('belsis-result'));
}

async function handleAdliSicil(event) {
  event.preventDefault();
  const target = document.getElementById('adliSicilUrl').value.trim() || 'https://www.turkiye.gov.tr/adli-sicil-kaydi';
  setStatus('Adli Sicil');
  const resultNode = document.getElementById('adli-sicil-result');
  resultNode.textContent = 'Sayfa inceleniyor…';
  const params = new URLSearchParams({ target });
  const response = await fetch(`/api/proxy?${params.toString()}`);
  const data = await response.json();

  if (!data.ok) {
    resultNode.textContent = `Hata: ${data.error || 'Bilinmeyen hata'}`;
    return;
  }

  const summary = {
    url: data.url,
    status: data.status,
    contentType: data.contentType,
    cookies: data.cookies || [],
    hiddenFields: data.hiddenFields || {},
    detectedLoginFields: data.detectedLoginFields || {},
    forms: data.forms || [],
    scriptUrls: data.scriptUrls || [],
    bodyPreview: typeof data.body === 'string' ? data.body.slice(0, 2200) : data.body,
  };
  resultNode.textContent = JSON.stringify(summary, null, 2);
}

document.getElementById('grade-form').addEventListener('submit', handleGrade);
document.getElementById('eokul-form').addEventListener('submit', handleEokul);
document.getElementById('harita-form').addEventListener('submit', handleHarita);
document.getElementById('belsis-form').addEventListener('submit', handleBelsis);
document.getElementById('adli-sicil-form').addEventListener('submit', handleAdliSicil);
