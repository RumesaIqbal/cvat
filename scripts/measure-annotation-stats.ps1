#Requires -Version 5.1
<#
.SYNOPSIS
    Measures the wall-clock response time of GET /api/tasks/<id>/annotation-stats.
.DESCRIPTION
    Sends one discarded warm-up request, then Count timed requests. Every timed
    request opens a fresh connection, so TCP connection setup is part of every
    reported number. Prints the raw runs and a median / max / spread summary so
    the result can be pasted into docs/perf/annotation-stats.md (MO-1 evidence).
.PARAMETER BaseUrl
    Scheme and host of the deployment, e.g. http://localhost:8080
.PARAMETER TaskId
    Task whose statistics are measured. Default 1.
.PARAMETER Username
.PARAMETER Password
    Used as HTTP basic auth. Avoid on shared machines.
.PARAMETER Count
    Number of timed runs. Default 5.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\measure-annotation-stats.ps1
#>
param(
    [string]$BaseUrl = 'http://localhost:8080',
    [int]$TaskId = 1,
    [string]$Username = 'admin',
    [string]$Password = 'Cvat2026!',
    [int]$Count = 5
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Net.Http
$url = "$($BaseUrl.TrimEnd('/'))/api/tasks/$TaskId/annotation-stats?group_by=label"

function Invoke-TimedRequest {
    param(
        [string]$Url,
        [string]$User,
        [string]$Pass,
        [string]$Label
    )

    $handler = New-Object System.Net.Http.HttpClientHandler
    $client = New-Object System.Net.Http.HttpClient($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(60)
    $pair = "${User}:${Pass}"
    $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue(
        'Basic',
        [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
    )

    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $response = $client.GetAsync($Url).GetAwaiter().GetResult()
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        $sw.Stop()
        $status = [int]$response.StatusCode
    }
    finally {
        $client.Dispose()
        $handler.Dispose()
    }

    if ($status -ne 200) {
        throw "HTTP $status on $Label ($Url)"
    }

    $parsed = $body | ConvertFrom-Json
    if ($null -eq $parsed.total) {
        throw "Unexpected body on $Label : $body"
    }

    [pscustomobject]@{
        Label  = $Label
        Ms     = [long]$sw.ElapsedMilliseconds
        Status = $status
        Total  = $parsed.total
    }
}

Write-Output "URL: $url"
Write-Output 'Warm-up request (discarded):'
$warm = Invoke-TimedRequest $url $Username $Password 'warm-up'
Write-Output ("  {0} ms  (status {1}, total {2})" -f $warm.Ms, $warm.Status, $warm.Total)

$runs = @()
for ($i = 1; $i -le $Count; $i++) {
    $r = Invoke-TimedRequest $url $Username $Password "run $i"
    $runs += $r
    Write-Output ("run {0}: {1} ms  (status {2}, total {3})" -f $i, $r.Ms, $r.Status, $r.Total)
}

$sorted = @($runs.Ms | Sort-Object)
if ($sorted.Count % 2 -eq 0) {
    $median = [Math]::Round(($sorted[$sorted.Count / 2 - 1] + $sorted[$sorted.Count / 2]) / 2, 0)
}
else {
    $median = $sorted[[Math]::Floor($sorted.Count / 2)]
}
$min = ($runs.Ms | Measure-Object -Minimum).Minimum
$max = ($runs.Ms | Measure-Object -Maximum).Maximum

Write-Output ''
Write-Output ("Timed runs: {0}   median: {1} ms   min: {2} ms   max: {3} ms   spread: {4} ms" -f $runs.Count, $median, $min, $max, ($max - $min))
Write-Output ("MO-1 verdict  median <= 500 ms: {0}   max <= 1000 ms: {1}" -f ($median -le 500), ($max -le 1000))