param(
    [Parameter(Mandatory = $true)][string]$GitHubPat
)

$ErrorActionPreference = "Stop"
$owner = "asyazavrik"
$repo = "linkedin-brand-agent"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Invoke-GitHubApi {
    param([string]$Method, [string]$Path, [string]$JsonBody = $null)
    $req = [System.Net.HttpWebRequest]::Create("https://api.github.com$Path")
    $req.Method = $Method
    $req.UserAgent = "linkedin-brand-agent"
    $req.Accept = "application/vnd.github+json"
    $req.Headers["Authorization"] = "Bearer $GitHubPat"
    if ($JsonBody) {
        $req.ContentType = "application/json; charset=utf-8"
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($JsonBody)
        $req.ContentLength = $bytes.Length
        $stream = $req.GetRequestStream()
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Close()
    }
    $resp = $req.GetResponse()
    $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
    $text = $reader.ReadToEnd()
    $reader.Close()
  if ($text) { return $text | ConvertFrom-Json }
  return $null
}

function New-BlobSha([string]$FilePath) {
    $content = [Convert]::ToBase64String([IO.File]::ReadAllBytes($FilePath))
    $json = '{"content":"' + $content + '","encoding":"base64"}'
    $blob = Invoke-GitHubApi -Method POST -Path "/repos/$owner/$repo/git/blobs" -JsonBody $json
    return $blob.sha
}

function Build-Tree([string]$Dir) {
    $entries = @()
    foreach ($name in Get-ChildItem $Dir -Name | Sort-Object) {
        $full = Join-Path $Dir $name
        if (Test-Path $full -PathType Leaf) {
            if ($name -in @("deploy_github.ps1", "deploy_github.py")) { continue }
            $entries += @{ path = $name; mode = "100644"; type = "blob"; sha = (New-BlobSha $full) }
            Write-Host "blob $name"
        } elseif (Test-Path $full -PathType Container) {
            $sub = Build-Tree $full
            if ($sub.Count -gt 0) {
                $subJson = @{ tree = $sub } | ConvertTo-Json -Compress -Depth 6
                $subTree = Invoke-GitHubApi -Method POST -Path "/repos/$owner/$repo/git/trees" -JsonBody $subJson
                $entries += @{ path = $name; mode = "040000"; type = "tree"; sha = $subTree.sha }
            }
        }
    }
    return $entries
}

Write-Host "Building tree..."
$treeEntries = Build-Tree $root
$treeJson = @{ tree = $treeEntries } | ConvertTo-Json -Compress -Depth 8
$tree = Invoke-GitHubApi -Method POST -Path "/repos/$owner/$repo/git/trees" -JsonBody $treeJson
$commitJson = (@{ message = "Initial deploy: LinkedIn brand agent"; tree = $tree.sha } | ConvertTo-Json -Compress)
$commit = Invoke-GitHubApi -Method POST -Path "/repos/$owner/$repo/git/commits" -JsonBody $commitJson
try {
    $refJson = (@{ ref = "refs/heads/main"; sha = $commit.sha } | ConvertTo-Json -Compress)
    Invoke-GitHubApi -Method POST -Path "/repos/$owner/$repo/git/refs" -JsonBody $refJson | Out-Null
} catch {
    $patchJson = (@{ sha = $commit.sha; force = $true } | ConvertTo-Json -Compress)
    Invoke-GitHubApi -Method PATCH -Path "/repos/$owner/$repo/git/refs/heads/main" -JsonBody $patchJson | Out-Null
}
Write-Host "Pushed $($commit.sha.Substring(0,7))"

$pub = Invoke-GitHubApi -Method GET -Path "/repos/$owner/$repo/actions/secrets/public-key"
$parent = Split-Path $root -Parent
$deepseek = (Get-Content (Get-ChildItem $parent -Filter "sk-*.txt" | Select-Object -First 1).FullName -Raw).Trim()
$secrets = @{
    TELEGRAM_BOT_TOKEN = "8777535229:AAHs4ZgjJQ-3Oixrbpwf-eFu8PovoGKsgcQ"
    TELEGRAM_CHAT_ID = "874111772"
    DEEPSEEK_API_KEY = $deepseek
}

$py = @'
import sys, json, base64, subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "pynacl", "-q"])
import requests
from nacl import encoding, public
token, owner, repo, key_id, key_b64, secrets = sys.argv[1:6]
data = json.loads(secrets)
pk = public.PublicKey(key_b64.encode(), encoding.Base64Encoder())
box = public.SealedBox(pk)
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
for name, value in data.items():
    enc = base64.b64encode(box.encrypt(value.encode())).decode()
    r = requests.put(f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{name}", headers=headers, json={"encrypted_value": enc, "key_id": key_id})
    r.raise_for_status()
    print("SECRET", name)
'@
$pyPath = Join-Path $env:TEMP "gh_secrets.py"
Set-Content $pyPath $py -Encoding UTF8
$pyExe = @(
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "C:\Program Files\Python312\python.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $pyExe) { throw "Python not found for secrets" }
& $pyExe $pyPath $GitHubPat $owner $repo $pub.key_id $pub.key (ConvertTo-Json $secrets -Compress)

$wfJson = '{"ref":"main"}'
Invoke-GitHubApi -Method POST -Path "/repos/$owner/$repo/actions/workflows/morning_digest.yml/dispatches" -JsonBody $wfJson | Out-Null
Write-Host "Workflow triggered"
Write-Host "DONE https://github.com/$owner/$repo"
