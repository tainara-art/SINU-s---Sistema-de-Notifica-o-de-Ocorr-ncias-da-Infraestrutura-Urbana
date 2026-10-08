(function () {
  const instances = [];


  function getNumber(value, fallback) {
    const parsed = parseFloat(
      String(value || '').replace(',', '.')
    );

    return Number.isFinite(parsed)
      ? parsed
      : fallback;
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
   * Busca o CEP através de reverse geocoding no Nominatim.
   *
   * O campo CEP é readonly no formulário Django,
   * portanto o valor é preenchido somente via JavaScript.
   */
  async function fetchAndFillCep(
    lat,
    lng,
    cepInput,
    statusElement
  ) {
    if (!cepInput) return;

    try {
      const url =
        'https://nominatim.openstreetmap.org/reverse' +
        '?format=json' +
        '&addressdetails=1' +
        '&lat=' + encodeURIComponent(lat) +
        '&lon=' + encodeURIComponent(lng);

      const response = await fetch(url, {
        headers: {
          'Accept-Language': 'pt-BR,pt;q=0.9'
        }
      });

      if (!response.ok) {
        throw new Error(
          'Resposta inválida do servidor de geocodificação.'
        );
      }

      const data = await response.json();

      console.log(
        '[SINUS] Nominatim resposta:',
        data
      );

      console.log(
        '[SINUS] postcode encontrado:',
        data.address && data.address.postcode
      );

      const postcode =
        data.address && data.address.postcode
          ? data.address.postcode.replace(/\D/g, '')
          : '';

      if (
        postcode &&
        postcode.length >= 8
      ) {
        const digits = postcode.substring(0, 8);

        cepInput.value =
          digits.substring(0, 5) +
          '-' +
          digits.substring(5);
      } else {
        cepInput.value = '';

        setStatus(
          statusElement,
          'Localização selecionada, mas CEP não encontrado para este ponto. Tente outro local.',
          'warn'
        );
      }

    } catch (error) {
      console.error(
        '[SINUS] Erro ao buscar CEP:',
        error
      );

      // A falha na busca do CEP não impede
      // o preenchimento manual da ocorrência.
      cepInput.value = '';
    }
  }


  function initializeMap(wrapper) {
    const form =
      wrapper.closest('form');

    const mapElement =
      wrapper.querySelector('.js-sinus-map');

    const latInput =
      form
        ? form.querySelector(
            'input[name="latitude"]'
          )
        : null;

    const lngInput =
      form
        ? form.querySelector(
            'input[name="longitude"]'
          )
        : null;

    const fotosInput =
      form
        ? form.querySelector(
            'input[name="fotos"]'
          )
        : null;

    const cepInput =
      form
        ? form.querySelector(
            '.js-map-cep'
          )
        : null;

    // Campos preenchidos automaticamente
    // com os dados sugeridos pela IA.
    const categoriaInput =
      form
        ? form.querySelector(
            'select[name="categoria"]'
          )
        : null;

    const descricaoInput =
      form
        ? form.querySelector(
            'textarea[name="descricao"]'
          )
        : null;

    const statusElement =
      wrapper.querySelector(
        '.js-location-status'
      );

    const modal =
      wrapper.querySelector(
        '.js-location-modal'
      );

    const useLocationBtns =
      wrapper.querySelectorAll(
        '.js-use-location, .js-modal-location'
      );

    const manualButton =
      wrapper.querySelector(
        '.js-modal-manual'
      );

    const searchInput =
      wrapper.querySelector(
        '.js-map-search'
      );

    const searchButton =
      wrapper.querySelector(
        '.js-search-address'
      );


    /**
     * Sem os elementos essenciais do mapa,
     * não há como inicializar o componente.
     */
    if (
      !mapElement ||
      !latInput ||
      !lngInput ||
      !window.L
    ) {
      return;
    }


    const defaultLat =
      getNumber(
        wrapper.dataset.defaultLat,
        -22.3572
      );

    const defaultLng =
      getNumber(
        wrapper.dataset.defaultLng,
        -47.3842
      );


    const map = L.map(
      mapElement,
      {
        scrollWheelZoom: true
      }
    ).setView(
      [
        defaultLat,
        defaultLng
      ],
      14
    );


    L.tileLayer(
      'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      {
        attribution: '© OpenStreetMap',
        maxZoom: 19
      }
    ).addTo(map);


    let marker = null;


    function closeModal() {
      if (modal) {
        modal.classList.add(
          'is-hidden'
        );
      }
    }


    /**
     * Posiciona ou atualiza o marcador do mapa.
     *
     * Também:
     * - atualiza latitude;
     * - atualiza longitude;
     * - procura o CEP;
     * - centraliza o mapa.
     */
    function setMarker(
      lat,
      lng,
      zoom
    ) {
      const cleanLat =
        Number(lat);

      const cleanLng =
        Number(lng);


      if (
        !Number.isFinite(cleanLat) ||
        !Number.isFinite(cleanLng)
      ) {
        return;
      }


      if (!marker) {
        marker = L.marker(
          [
            cleanLat,
            cleanLng
          ],
          {
            icon: createIcon(),
            draggable: true
          }
        ).addTo(map);


        /**
         * Permite que o usuário corrija manualmente
         * a localização arrastando o marcador.
         */
        marker.on(
          'dragend',
          function () {
            const position =
              marker.getLatLng();

            setMarker(
              position.lat,
              position.lng
            );
          }
        );

      } else {
        marker.setLatLng([
          cleanLat,
          cleanLng
        ]);
      }


      latInput.value =
        cleanLat.toFixed(6);

      lngInput.value =
        cleanLng.toFixed(6);


      setStatus(
        statusElement,
        'Localização selecionada no mapa. Buscando CEP...',
        'info'
      );


      closeModal();


      /**
       * O CEP é buscado de forma assíncrona.
       * A operação não bloqueia a atualização do mapa.
       */
      fetchAndFillCep(
        cleanLat,
        cleanLng,
        cepInput,
        statusElement
      ).then(function () {

        if (
          cepInput &&
          cepInput.value
        ) {
          setStatus(
            statusElement,
            'Localização e CEP preenchidos automaticamente.',
            'success'
          );
        }
      });


      if (zoom) {
        map.setView(
          [
            cleanLat,
            cleanLng
          ],
          zoom
        );
      }
    }


    /**
     * Envia a primeira foto selecionada
     * para o endpoint de preenchimento automático.
     *
     * No backend, a PreenchimentoAutomaticoFacade
     * coordena:
     *
     * - EXIF para latitude e longitude;
     * - Gemini para categoria e descrição.
     *
     * O resultado é utilizado para preencher
     * automaticamente o formulário.
     */
    async function preencherAutomaticamenteDaFoto(
      arquivo
    ) {
      const formData =
        new FormData();


      /**
       * "foto" precisa possuir o mesmo nome
       * esperado pela PreenchimentoAutomaticoView.
       */
      formData.append(
        'foto',
        arquivo
      );


      setStatus(
        statusElement,
        'Analisando foto e buscando localização...',
        'info'
      );


      try {
        // Envia a imagem para a API de IA + EXIF.
        // O token CSRF permite utilizar a sessão autenticada.
        // Obtém o token CSRF do formulário Django.
        // Caso não exista no formulário, utiliza o cookie csrftoken.
        const csrfTokenInput = form?.querySelector(
          'input[name="csrfmiddlewaretoken"]'
        );

        const csrfTokenCookie = document.cookie
          .split('; ')
          .find(cookie => cookie.startsWith('csrftoken='))
          ?.split('=')[1];

        const csrfToken = csrfTokenInput?.value ||
          (csrfTokenCookie ? decodeURIComponent(csrfTokenCookie) : null);

        // Envia a foto para a API com o token de segurança do Django.
        const response = await fetch(
          '/api/ocorrencias/preenchimento-automatico/',
          {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'X-CSRFToken': csrfToken || ''
            },
            body: formData
          }
        );

        const data =
          await response.json();
        // Exibe o status HTTP e a resposta do backend
        // para facilitar a identificação de erros.
        console.log('[SINUS] Status da IA:', response.status);
        console.log('[SINUS] Resposta da IA:', data);

        /**
         * Uma falha na análise automática
         * não impede o usuário de preencher
         * a ocorrência manualmente.
         */
        if (!response.ok) {
          setStatus(
            statusElement,
            data.erro ||
            data.detail ||
            'Não foi possível analisar a foto.',
            'warn'
          );

          return;
        }


        /**
         * Categoria sugerida pela IA.
         */
        if (
          categoriaInput &&
          data.categoria
        ) {
          categoriaInput.value =
            data.categoria;
        }


        /**
         * Descrição sugerida pela IA.
         */
        if (
          descricaoInput &&
          data.descricao
        ) {
          descricaoInput.value =
            data.descricao;
        }


        /**
         * Quando a imagem possui GPS no EXIF,
         * reaproveitamos a função já existente
         * para preencher mapa, coordenadas e CEP.
         */
        if (
          data.latitude != null &&
          data.longitude != null
        ) {
          setMarker(
            data.latitude,
            data.longitude,
            17
          );

          map.invalidateSize();

        } else {

          /**
           * A IA pode funcionar mesmo quando
           * a fotografia não contém GPS.
           */
          setStatus(
            statusElement,
            'Categoria e descrição preenchidas. Selecione a localização no mapa.',
            'success'
          );
        }

      } catch (error) {
        console.error(
          '[SINUS] Erro no preenchimento automático:',
          error
        );


        setStatus(
          statusElement,
          'Não foi possível analisar a foto.',
          'warn'
        );
      }
    }


    /**
     * Ao selecionar fotos, utiliza a primeira
     * imagem como referência para IA + EXIF.
     */
    if (fotosInput) {
      fotosInput.addEventListener(
        'change',
        function () {
          const arquivo =
            fotosInput.files[0];


          if (!arquivo) {
            return;
          }


          preencherAutomaticamenteDaFoto(
            arquivo
          );
        }
      );
    }


    /**
     * Usa a geolocalização atual do navegador
     * quando o usuário escolher essa opção.
     */
    function useCurrentLocation() {
      closeModal();


      if (!navigator.geolocation) {
        setStatus(
          statusElement,
          'Geolocalização não suportada pelo navegador. Selecione no mapa.',
          'error'
        );


        alert(
          'Geolocalização não suportada pelo navegador. Selecione o local no mapa.'
        );

        return;
      }


      setStatus(
        statusElement,
        'Obtendo localização atual...',
        'info'
      );


      navigator.geolocation.getCurrentPosition(

        function (position) {
          const lat =
            position.coords.latitude;

          const lng =
            position.coords.longitude;


          setMarker(
            lat,
            lng,
            17
          );


          map.invalidateSize();
        },


        function () {
          setStatus(
            statusElement,
            'Permissão negada ou localização indisponível. Clique no mapa para selecionar.',
            'error'
          );


          alert(
            'Não foi possível usar a localização atual. Clique no mapa para selecionar o local da ocorrência.'
          );
        },


        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    }


    /**
     * Pesquisa um endereço utilizando
     * o serviço Nominatim/OpenStreetMap.
     */
    async function searchAddress() {
      const query =
        searchInput
          ? searchInput.value.trim()
          : '';


      if (!query) {
        alert(
          'Digite um endereço para buscar.'
        );

        return;
      }


      setStatus(
        statusElement,
        'Buscando endereço no mapa...',
        'info'
      );


      try {
        const url =
          'https://nominatim.openstreetmap.org/search' +
          '?format=json' +
          '&limit=1' +
          '&countrycodes=br' +
          '&q=' +
          encodeURIComponent(query);


        const response =
          await fetch(url);


        const data =
          await response.json();


        if (
          !Array.isArray(data) ||
          !data.length
        ) {
          setStatus(
            statusElement,
            'Endereço não encontrado. Clique no mapa para selecionar.',
            'error'
          );


          alert(
            'Endereço não encontrado. Tente outro endereço ou clique no mapa.'
          );

          return;
        }


        const lat =
          parseFloat(
            data[0].lat
          );

        const lng =
          parseFloat(
            data[0].lon
          );


        setMarker(
          lat,
          lng,
          17
        );

      } catch (error) {
        console.error(
          '[SINUS] Erro ao buscar endereço:',
          error
        );


        setStatus(
          statusElement,
          'Não foi possível buscar o endereço. Clique no mapa para selecionar.',
          'error'
        );


        alert(
          'Não foi possível buscar o endereço. Clique no mapa para selecionar.'
        );
      }
    }


    /**
     * Permite selecionar manualmente
     * a localização clicando no mapa.
     */
    map.on(
      'click',
      function (event) {
        setMarker(
          event.latlng.lat,
          event.latlng.lng
        );
      }
    );


    useLocationBtns.forEach(
      function (button) {
        button.addEventListener(
          'click',
          useCurrentLocation
        );
      }
    );


    if (manualButton) {
      manualButton.addEventListener(
        'click',
        function () {
          closeModal();


          setStatus(
            statusElement,
            'Clique no mapa para selecionar o local da ocorrência.',
            'info'
          );


          setTimeout(
            function () {
              map.invalidateSize();
            },
            100
          );
        }
      );
    }


    if (searchButton) {
      searchButton.addEventListener(
        'click',
        searchAddress
      );
    }


    if (searchInput) {
      searchInput.addEventListener(
        'keydown',
        function (event) {

          if (
            event.key === 'Enter'
          ) {
            event.preventDefault();

            searchAddress();
          }
        }
      );
    }


    /**
     * Caso existam coordenadas previamente
     * preenchidas, como na edição de uma ocorrência,
     * posiciona o marcador automaticamente.
     */
    if (
      latInput.value &&
      lngInput.value
    ) {
      setMarker(
        getNumber(
          latInput.value,
          defaultLat
        ),
        getNumber(
          lngInput.value,
          defaultLng
        ),
        16
      );
    }


    /**
     * Impede o envio do formulário
     * enquanto não houver localização válida.
     */
    if (form) {
      form.addEventListener(
        'submit',
        function (event) {

          if (
            !latInput.value ||
            !lngInput.value
          ) {
            event.preventDefault();

            event.stopImmediatePropagation();


            setStatus(
              statusElement,
              'Selecione a localização da ocorrência no mapa antes de enviar.',
              'error'
            );


            alert(
              'Selecione a localização da ocorrência no mapa antes de enviar.'
            );


            wrapper.scrollIntoView({
              behavior: 'smooth',
              block: 'center'
            });


            setTimeout(
              function () {
                map.invalidateSize();
              },
              250
            );


            return false;
          }


          return true;
        },
        true
      );
    }


    /**
     * Corrige possíveis problemas de tamanho
     * quando o mapa estiver dentro de elementos
     * inicialmente ocultos.
     */
    setTimeout(
      function () {
        map.invalidateSize();
      },
      300
    );


    instances.push({
      map: map,
      wrapper: wrapper
    });
  }


  /**
   * Inicializa todos os mapas SINUS
   * existentes na página.
   */
  document.addEventListener(
    'DOMContentLoaded',
    function () {
      document
        .querySelectorAll(
          '[data-sinus-map]'
        )
        .forEach(
          initializeMap
        );
    }
  );


  /**
   * Permite que outras partes do frontend
   * solicitem a atualização visual dos mapas.
   */
  window.SINUS_MAPS = {
    invalidateAll: function () {
      instances.forEach(
        function (instance) {
          instance.map.invalidateSize();
        }
      );
    }
  };

})();