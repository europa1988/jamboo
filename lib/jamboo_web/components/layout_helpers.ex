defmodule JambooWeb.LayoutHelpers do
  @moduledoc """
  Вспомогательные функции для макетов и внешних скриптов.
  Обеспечивает автономную работу без интернета.
  """
  use JambooWeb, :html

  @doc """
  Возвращает HTML-тег <script> для подключения HTMX:

  * сначала пытается загрузить локальный файл `/vendor/htmx/htmx.min.js`;
  * если загрузка не удалась — подключает HTMX с CDN.
  """
  def htmx_script_tag(_conn) do
    src = ~p"/vendor/htmx/htmx.min.js"

    """
    <script>
      if (typeof htmx === 'undefined') {
        const script = document.createElement('script');
        script.src = '#{src}';
        script.onload = () => {
          console.log('HTMX загружен из локального файла');
          initializeHtmx();
        };
        script.onerror = () => {
          const cdn = document.createElement('script');
          cdn.src = 'https://unpkg.com/htmx.org@2.0.8';
          cdn.onload = initializeHtmx;
          document.head.appendChild(cdn);
          console.log('HTMX загружен из CDN (fallback)');
        };
        document.head.appendChild(script);
      } else {
        initializeHtmx();
      }

      function initializeHtmx() {
        document.body.addEventListener('htmx:configRequest', (event) => {
          const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
          if (csrfToken) {
            event.detail.headers['X-CSRF-Token'] = csrfToken;
          }
        });
      }
    </script>
    """
  end
end
