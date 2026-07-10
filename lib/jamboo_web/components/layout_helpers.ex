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

    # We use raw because curly braces interpolation doesn't work inside <script> tags in HEEx
    # unless it's a component attribute, but here we are in the script body.
    # Wait, the guideline says:
    # "The 'JambooWeb.LayoutHelpers.htmx_script_tag/1' implementation uses 'raw/1' with string interpolation
    # for the script body, as standard HEEx curly brace interpolation '{}' is not supported inside '<script>' or '<style>' tags."

    script_body = """
      if (typeof htmx === 'undefined') {
        const script = document.createElement('script');
        script.src = '#{src}';
        script.onload = () => console.log('HTMX загружен из локального файла');
        script.onerror = () => {
          const cdn = document.createElement('script');
          cdn.src = 'https://unpkg.com/htmx.org@2.0.8';
          document.head.appendChild(cdn);
          console.log('HTMX загружен из CDN (fallback)');
        };
        document.head.appendChild(script);
      }
    """

    ~H"""
    <script>
      {raw(script_body)}
    </script>
    """
  end
end
