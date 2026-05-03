alias Jamboo.Repo
alias Jamboo.Content.Post

[
  %{title: "Добро пожаловать в Jamboo", body: "Это сообщество для обсуждения технологий.", author_nickname: "admin", vote_score: 5},
  %{title: "Elixir и Phoenix в 2026", body: "Стек всё ещё прекрасен.", author_nickname: "dev", vote_score: 12},
  %{title: "HTMX — простой интерактив", body: "Голосуйте без перезагрузки страницы.", author_nickname: "htmx_fan", vote_score: 3}
]
|> Enum.each(fn attrs ->
  %Post{}
  |> Post.changeset(attrs)
  |> Repo.insert!(on_conflict: :nothing)
end)