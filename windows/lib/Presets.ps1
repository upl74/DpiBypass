# Синхронизировано с app/.../DpiDefaults.kt
$script:Bind = '-i 127.0.0.1 -p 1080'
$script:LadderFull = '-d1 -d3+s -s6+s -d9+s -s12+s -d15+s -s20+s -d25+s -s30+s -d35+s'
$script:MtProtoRaw = '-d1 -f-1 -t 8 -r1 -Ku -As -d3 -f-1 -t 8 -Ku'

$script:PresetMap = @{
    youtube = "$script:Bind $script:LadderFull -r1+s -S -a1 -As $script:LadderFull -S -a1"
    hybrid  = "$script:Bind -Kt,h $script:LadderFull -r1+s -S -a1 -As -Kt,h $script:LadderFull -S -a1 $script:MtProtoRaw"
    lite    = "$script:Bind -Kt,h -d1 -d3+s -s6+s -d9+s -r1+s -S -a1 -d1 -f-1 -t 8 -Ku"
    minimal = "$script:Bind -d1 -f-1 -t 8 -Ku"
    light   = "$script:Bind -s0 -o1 -d1 -r1+s"
}

$script:PresetLabels = @{
    youtube = 'YouTube / Instagram (recommended)'
    hybrid  = 'Hybrid TG+YT'
    lite    = 'GoodbyeDPI Lite'
    minimal = 'Minimal'
    light   = 'Light'
}

function Get-PresetNames {
    $script:PresetLabels.Keys | Sort-Object
}

function Get-PresetLabel {
    param([string]$Name)
    if ($script:PresetLabels.ContainsKey($Name)) { return $script:PresetLabels[$Name] }
    return $Name
}

function Get-PresetCommand {
    param([string]$Name)
    if (-not $script:PresetMap.ContainsKey($Name)) {
        throw "Unknown preset: $Name"
    }
    return $script:PresetMap[$Name]
}

function Split-PresetArgs {
    param([string]$CommandLine)
    $trimmed = $CommandLine.Trim()
    $idx = $trimmed.IndexOf('-')
    if ($idx -gt 0) { $trimmed = $trimmed.Substring($idx) }
  return [regex]::Matches($trimmed, '[^\s"]+|"[^"]*"') |
        ForEach-Object { $_.Value.Trim('"') }
}
