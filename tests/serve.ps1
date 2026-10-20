# Minimal static server for the regression page (no Python/Node needed).
# Usage: pwsh -NoProfile -File tests/serve.ps1   → http://localhost:8765/tests/regress.html?cand=../index.html&base=../_baseline.html
param([string]$Root = (Split-Path -Parent $PSScriptRoot), [int]$Port = $(if ($env:PORT) { [int]$env:PORT } else { 8765 }))
$l = [System.Net.HttpListener]::new()
$l.Prefixes.Add("http://localhost:$Port/")
$l.Start()
Write-Host "Serving $Root on http://localhost:$Port/"
$types = @{ '.html'='text/html; charset=utf-8'; '.md'='text/plain; charset=utf-8'; '.txt'='text/plain; charset=utf-8'; '.pdf'='application/pdf'; '.js'='text/javascript'; '.css'='text/css'; '.svg'='image/svg+xml'; '.png'='image/png'; '.jpg'='image/jpeg'; '.json'='application/json' }
while ($l.IsListening) {
  $c = $l.GetContext()
  $p = [Uri]::UnescapeDataString($c.Request.Url.AbsolutePath).TrimStart('/')
  if ($p -eq '') { $p = 'index.html' }
  $f = Join-Path $Root $p
  if (Test-Path $f -PathType Leaf) {
    $b = [IO.File]::ReadAllBytes($f)
    $ext = [IO.Path]::GetExtension($f).ToLower()
    $c.Response.ContentType = $(if ($types[$ext]) { $types[$ext] } else { 'application/octet-stream' })
    $c.Response.Headers.Add('Cache-Control', 'no-store')
    $c.Response.OutputStream.Write($b, 0, $b.Length)
  } else { $c.Response.StatusCode = 404 }
  $c.Response.Close()
}
