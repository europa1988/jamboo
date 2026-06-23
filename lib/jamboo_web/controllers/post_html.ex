defmodule JambooWeb.PostHTML do
  @moduledoc "Шаблоны и хелперы для постов"
  use JambooWeb, :html

  embed_templates "post_html/*"

  def render("post_vote.html", assigns) do
    post_vote(assigns)
  end

  @doc """
  Возвращает HTML‑фрагмент блока голосования для поста.
  """
  attr :post, :any, required: true

  def post_vote(assigns) do
    ~H"""
    <div class="flex flex-col items-center space-y-1 vote-container">
      <button
        hx-put={~p"/posts/#{@post.id}/upvote"}
        hx-target="closest .vote-container"
        hx-swap="outerHTML"
        class="p-2 hover:bg-gray-100 rounded-full transition-colors"
        title="Повысить рейтинг"
      >
        <span class="material-icons text-gray-600 hover:text-orange-500">arrow_upward</span>
      </button>

      <span class={["font-bold text-lg", if(@post.vote_score > 0, do: "text-orange-500", else: "text-gray-700")]}>
        {@post.vote_score}
      </span>

      <button
        hx-put={~p"/posts/#{@post.id}/downvote"}
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

  @doc """
  Возвращает HTML‑фрагмент блока голосования для поста.
  Оставлено для обратной совместимости, если где-то вызывается как строка.
  """
  def render_post_vote(post) do
    assigns = %{post: post}
    Phoenix.HTML.Safe.to_iodata(post_vote(assigns)) |> IO.iodata_to_binary()
  end
end
