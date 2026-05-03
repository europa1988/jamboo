# dev.ps1 - Start Jamboo (Phoenix + Tailwind watch)
Set-Location "C:\Jamboo\jamboo"

Write-Host "Starting Jamboo..." -ForegroundColor Green
Write-Host "Installing dependencies and building assets..." -ForegroundColor Cyan
mix deps.get
mix assets.setup
mix assets.build

Write-Host "Starting Tailwind CSS in watch mode..." -ForegroundColor Magenta
Start-Process -NoNewWindow -FilePath "mix" -ArgumentList "tailwind", "default", "--watch"

Write-Host "Starting Phoenix server at http://localhost:4000" -ForegroundColor Yellow
mix phx.server
