(function () {
  const categoriaCores = {
    SB: '#2f6150',
    PV: '#c47a1a',
    IP: '#b88400',
    LU: '#2a6a9a',
    AS: '#a6414b',
    AP: '#4c8a57',
    ST: '#5f62a8',
    OS: '#7a587f'
  };

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function getPoints(scriptId) {
    const script = document.getElementById(scriptId);
    if (!script) return [];
    try {
      const parsed = JSON.parse(script.textContent || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.error('Não foi possível carregar os pontos do mapa.', error);
      return [];
    }
  }

  function createIcon(point) {
    const color = categoriaCores[point.categoria] || '#2f6150';
    return L.divIcon({
      className: 'dashboard-map-pin',
      html: `<span style="background:${color}"></span>`,
      iconSize: [26, 26],
      iconAnchor: [13, 26],
      popupAnchor: [0, -24]
    });
  }

  function popupHtml(point) {
    return `
      <div class="dashboard-map-popup">
        <strong>${escapeHtml(point.categoria_label || 'Ocorrência')}</strong>
        <p>${escapeHtml(point.descricao || '')}</p>
        <small>Status: ${escapeHtml(point.status_label || '-')}</small><br>
        ${point.secretaria ? `<small>Secretaria: ${escapeHtml(point.secretaria)}</small><br>` : ''}
        ${point.prefeitura ? `<small>Prefeitura: ${escapeHtml(point.prefeitura)}</small><br>` : ''}
        ${point.cep ? `<small>CEP: ${escapeHtml(point.cep)}</small><br>` : ''}
        ${point.data ? `<small>Data: ${escapeHtml(point.data)}</small>` : ''}
      </div>
    `;
  }

  function initializeDashboardMap(element) {
    if (!window.L || element.dataset.initialized === 'true') return;

    const defaultLat = parseFloat(element.dataset.defaultLat || '-22.3572');
    const defaultLng = parseFloat(element.dataset.defaultLng || '-47.3842');
    const points = getPoints(element.dataset.pointsScript);

    const map = L.map(element, { scrollWheelZoom: true }).setView([defaultLat, defaultLng], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    if (!points.length) {
      L.popup()
        .setLatLng([defaultLat, defaultLng])
        .setContent('Nenhuma ocorrência com localização para exibir.')
        .openOn(map);
      element.dataset.initialized = 'true';
      setTimeout(function () { map.invalidateSize(); }, 250);
      return;
    }

    const bounds = [];
    points.forEach(function (point) {
      const lat = parseFloat(point.latitude);
      const lng = parseFloat(point.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

      bounds.push([lat, lng]);
      L.marker([lat, lng], { icon: createIcon(point) })
        .addTo(map)
        .bindPopup(popupHtml(point));
    });

    if (bounds.length === 1) {
      map.setView(bounds[0], 16);
    } else if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [28, 28] });
    }

    element.dataset.initialized = 'true';
    setTimeout(function () { map.invalidateSize(); }, 250);
  }

  function initializeAll() {
    document.querySelectorAll('[data-dashboard-map]').forEach(initializeDashboardMap);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAll);
  } else {
    initializeAll();
  }
})();
