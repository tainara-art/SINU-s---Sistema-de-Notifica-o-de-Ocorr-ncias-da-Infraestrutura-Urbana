(function () {
  const instances = [];

  function getNumber(value, fallback) {
    const parsed = parseFloat(String(value || '').replace(',', '.'));
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function setStatus(element, text, type) {
    if (!element) return;
    element.textContent = text;
    element.dataset.status = type || 'info';
  }

  function createIcon() {
    return L.divIcon({
      className: 'sinus-map-pin',
      html: '<span>📍</span>',
      iconSize: [34, 34],
      iconAnchor: [17, 34],
      popupAnchor: [0, -30]
    });
  }

  /**
   * Busca o CEP via reverse geocoding no Nominatim e preenche o campo.
   * O campo CEP já vem com readonly do Django — apenas alteramos o value via JS.
   */
  async function fetchAndFillCep(lat, lng, cepInput, statusElement) {
    if (!cepInput) return;

    try {
      const url =
        'https://nominatim.openstreetmap.org/reverse?format=json&addressdetails=1' +
        '&lat=' + encodeURIComponent(lat) +
        '&lon=' + encodeURIComponent(lng);

      const response = await fetch(url, {
        headers: {
          'Accept-Language': 'pt-BR,pt;q=0.9',
          'User-Agent': 'SINUS-PI/1.0 (projeto academico)'
        }
      });

      if (!response.ok) throw new Error('Resposta inválida do servidor de geocodificação.');

      const data = await response.json();
      console.log('[SINUS] Nominatim resposta:', data);
      console.log('[SINUS] postcode encontrado:', data.address && data.address.postcode);
      const postcode = (data.address && data.address.postcode)
        ? data.address.postcode.replace(/\D/g, '')   // remove traços e espaços
        : '';

      if (postcode && postcode.length >= 8) {
        const digits = postcode.substring(0, 8);
        cepInput.value = digits.substring(0, 5) + '-' + digits.substring(5); // formato 00000-000
      } else {
        cepInput.value = '';
        setStatus(
          statusElement,
          'Localização selecionada, mas CEP não encontrado para este ponto. Tente outro local.',
          'warn'
        );
      }
    } catch (err) {
      console.error('[SINUS] Erro ao buscar CEP:', err);
      // Falha silenciosa no CEP — não bloqueia o fluxo do mapa
      cepInput.value = '';
    }
  }

  function initializeMap(wrapper) {
    const form            = wrapper.closest('form');
    const mapElement      = wrapper.querySelector('.js-sinus-map');
    const latInput        = form ? form.querySelector('input[name="latitude"]')  : null;
    const lngInput        = form ? form.querySelector('input[name="longitude"]') : null;
    const fotosInput      = form ? form.querySelector('input[name="fotos"]') : null;
    const cepInput        = form ? form.querySelector('.js-map-cep')             : null;
    const statusElement   = wrapper.querySelector('.js-location-status');
    const modal           = wrapper.querySelector('.js-location-modal');
    const useLocationBtns = wrapper.querySelectorAll('.js-use-location, .js-modal-location');
    const manualButton    = wrapper.querySelector('.js-modal-manual');
    const searchInput     = wrapper.querySelector('.js-map-search');
    const searchButton    = wrapper.querySelector('.js-search-address');

    // Ao selecionar fotos, tenta utilizar os metadados GPS da primeira imagem
   // para preencher automaticamente a localização da ocorrência.
    if (fotosInput) {
      fotosInput.addEventListener('change', function () {
        const arquivo = fotosInput.files[0];

        if (!arquivo) return;

        obterLocalizacaoDaFoto(arquivo);
      });
    }

    if (!mapElement || !latInput || !lngInput || !window.L) return;

    const defaultLat = getNumber(wrapper.dataset.defaultLat, -22.3572);
    const defaultLng = getNumber(wrapper.dataset.defaultLng, -47.3842);
    const map = L.map(mapElement, { scrollWheelZoom: true }).setView([defaultLat, defaultLng], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      maxZoom: 19
    }).addTo(map);

    let marker = null;

    function closeModal() {
      if (modal) modal.classList.add('is-hidden');
    }

    function setMarker(lat, lng, zoom) {
      const cleanLat = Number(lat);
      const cleanLng = Number(lng);
      if (!Number.isFinite(cleanLat) || !Number.isFinite(cleanLng)) return;

      if (!marker) {
        marker = L.marker([cleanLat, cleanLng], {
          icon: createIcon(),
          draggable: true
        }).addTo(map);

        marker.on('dragend', function () {
          const position = marker.getLatLng();
          setMarker(position.lat, position.lng);
        });
      } else {
        marker.setLatLng([cleanLat, cleanLng]);
      }

      latInput.value = cleanLat.toFixed(6);
      lngInput.value = cleanLng.toFixed(6);
      setStatus(statusElement, 'Localização selecionada no mapa. Buscando CEP...', 'info');
      closeModal();

      // Preenche o CEP automaticamente (async — não bloqueia o marcador)
      fetchAndFillCep(cleanLat, cleanLng, cepInput, statusElement).then(function () {
        // Atualiza o status só se o CEP foi encontrado (campo não ficou vazio)
        if (cepInput && cepInput.value) {
          setStatus(statusElement, 'Localização e CEP preenchidos automaticamente.', 'success');
        }
      });

      if (zoom) {
        map.setView([cleanLat, cleanLng], zoom);
      }
    }

 // Tenta obter automaticamente a localização registrada nos metadados EXIF
// da foto selecionada.
//
// A imagem é enviada para a API de localização, que utiliza o ExifService
// no backend e retorna latitude e longitude quando houver GPS disponível.
    async function obterLocalizacaoDaFoto(arquivo){
      const formData = new FormData();
        // O nome "foto" deve ser o mesmo esperado pela LocalizacaoFotoView.

      form.Data.append('foto', arquivo);

      setStatus(
        statusElement,
        'Buscando localização nos dados da foto...',
        'info'
      );

      try {
        const responser = await fetch ('/api/fotos/localizacao/',{
          method: 'POST',
          body: formData
        });

        const data = await response.json();
          // A ausência de GPS não impede o cadastro.
          // O usuário ainda poderá informar a localização manualmente pelo mapa.
        if (!response.ok){
          setStatus(
            statusElement,
            'A foto não possui localização GPS. Você pode selecionar o local no mapa.',
            'warn'
          );
          return;
        }
        // Proteção contra uma resposta válida, mas sem coordenadas utilizáveis.
        if (data.latitude == null || data.longitude == null){
          return;
        }
        // Reutiliza o fluxo existente do mapa para:
        // - posicionar o marcador;
        // - preencher latitude e longitude;
        // - buscar o CEP;
        // - centralizar o mapa.
        setMarker(data.latitude, data.longitude, 17);

        setStatus(
          statusElement,
          'Localização encontrada automaticamente pela foto.',
          'success'
        );

        map.invalidateSize();
      } catch (error){
        console.error('[SINUS] Erro ao obter localização da foto:', error);
        // Falha na análise da foto também não bloqueia o preenchimento manual.
        setStatus(
          statusElement,
          'Não foi possível analisar a localização da foto.',
          'warn'
        );
      }
    }

    function useCurrentLocation() {
      closeModal();

      if (!navigator.geolocation) {
        setStatus(statusElement, 'Geolocalização não suportada pelo navegador. Selecione no mapa.', 'error');
        alert('Geolocalização não suportada pelo navegador. Selecione o local no mapa.');
        return;
      }

      setStatus(statusElement, 'Obtendo localização atual...', 'info');

      navigator.geolocation.getCurrentPosition(
        function (position) {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          setMarker(lat, lng, 17);
          map.invalidateSize();
        },
        function () {
          setStatus(statusElement, 'Permissão negada ou localização indisponível. Clique no mapa para selecionar.', 'error');
          alert('Não foi possível usar a localização atual. Clique no mapa para selecionar o local da ocorrência.');
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    }

    async function searchAddress() {
      const query = searchInput ? searchInput.value.trim() : '';
      if (!query) {
        alert('Digite um endereço para buscar.');
        return;
      }

      setStatus(statusElement, 'Buscando endereço no mapa...', 'info');

      try {
        const url =
          'https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=br&q=' +
          encodeURIComponent(query);
        const response = await fetch(url);
        const data     = await response.json();

        if (!Array.isArray(data) || !data.length) {
          setStatus(statusElement, 'Endereço não encontrado. Clique no mapa para selecionar.', 'error');
          alert('Endereço não encontrado. Tente outro endereço ou clique no mapa.');
          return;
        }

        const lat = parseFloat(data[0].lat);
        const lng = parseFloat(data[0].lon);
        setMarker(lat, lng, 17);
      } catch (error) {
        setStatus(statusElement, 'Não foi possível buscar o endereço. Clique no mapa para selecionar.', 'error');
        alert('Não foi possível buscar o endereço. Clique no mapa para selecionar.');
      }
    }

    map.on('click', function (event) {
      setMarker(event.latlng.lat, event.latlng.lng);
    });

    useLocationBtns.forEach(function (button) {
      button.addEventListener('click', useCurrentLocation);
    });

    if (manualButton) {
      manualButton.addEventListener('click', function () {
        closeModal();
        setStatus(statusElement, 'Clique no mapa para selecionar o local da ocorrência.', 'info');
        setTimeout(function () { map.invalidateSize(); }, 100);
      });
    }

    if (searchButton) {
      searchButton.addEventListener('click', searchAddress);
    }

    if (searchInput) {
      searchInput.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          searchAddress();
        }
      });
    }

    // Se já há coordenadas salvas (edição de ocorrência), posiciona o marcador
    if (latInput.value && lngInput.value) {
      setMarker(
        getNumber(latInput.value, defaultLat),
        getNumber(lngInput.value, defaultLng),
        16
      );
    }

    if (form) {
      form.addEventListener('submit', function (event) {
        if (!latInput.value || !lngInput.value) {
          event.preventDefault();
          event.stopImmediatePropagation();
          setStatus(statusElement, 'Selecione a localização da ocorrência no mapa antes de enviar.', 'error');
          alert('Selecione a localização da ocorrência no mapa antes de enviar.');
          wrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });
          setTimeout(function () { map.invalidateSize(); }, 250);
          return false;
        }
        return true;
      }, true);
    }

    setTimeout(function () { map.invalidateSize(); }, 300);

    instances.push({ map: map, wrapper: wrapper });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-sinus-map]').forEach(initializeMap);
  });

  window.SINUS_MAPS = {
    invalidateAll: function () {
      instances.forEach(function (instance) {
        instance.map.invalidateSize();
      });
    }
  };
})();
