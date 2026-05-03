defmodule JambooWeb.PostHTML do
  @moduledoc "Шаблоны и хелперы для постов"
  use JambooWeb, :html

  embed_templates "post_html/*"

  @doc """
  Возвращает HTML‑фрагмент блока голосования для поста.

  Используется в HTMX‑ответах, поэтому возвращает строку, а не HEEx‑шаблон.
  """
  def render_post_vote(post) do
    """
    <div class="flex flex-col items-center space-y-1 vote-container">
      <button 
        hx-put="/posts/#{post.id}/upvote"
        hx-target="closest .vote-container"
        hx-swap="outerHTML"
        class="p-2 hover:bg-gray-100 rounded-full transition-colors"
        title="Повысить рейтинг"
      >
        <span class="material-icons text-gray-600 hover:text-orange-500">arrow_upward</span>
      </button>

      <span class="font-bold text-lg #{if post.vote_score > 0, do: "text-orange-500", else: "text-gray-700"}">
        #{post.vote_score}
      </span>

      <button 
        hx-put="/posts/#{post.id}/downvote"
        hx-target="closest .vote-container"
        hx-swap="outerHTML"
        class="p-2 hover:bg-gray-100 rounded-full transition-colors"
        title="Понизить рейтинг"
      >
        <span class="material-icons text-gray-600 hover:text-blue-500">arrow_downward</span>
      </button>
    </div>
    """
  end
end