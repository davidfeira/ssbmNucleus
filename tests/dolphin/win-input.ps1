param(
    [Parameter(Mandatory = $true)]
    [int]$ProcessId,

    [Parameter(Mandatory = $true)]
    [ValidateSet('focus', 'tap', 'keyDown', 'keyUp')]
    [string]$Action,

    [string]$Key,

    [int]$DurationMs = 80,

    [int]$FocusTimeoutMs = 10000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class DolphinInputNative
{
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}
"@

function Resolve-VirtualKey {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $normalized = $Name.Trim().ToUpperInvariant()
    $map = @{
        'ENTER'  = 0x0D
        'RETURN' = 0x0D
        'ESC'    = 0x1B
        'ESCAPE' = 0x1B
        'SPACE'  = 0x20
        'LEFT'   = 0x25
        'UP'     = 0x26
        'RIGHT'  = 0x27
        'DOWN'   = 0x28
        'LSHIFT' = 0xA0
        'LCTRL'  = 0xA2
        'LCONTROL' = 0xA2
        'LMENU'  = 0xA4
    }

    if ($map.ContainsKey($normalized)) {
        return [byte]$map[$normalized]
    }

    if ($normalized.Length -eq 1) {
        $charCode = [int][char]$normalized
        return [byte]$charCode
    }

    throw "Unsupported key name: $Name"
}

function Get-MainWindowHandle {
    param(
        [Parameter(Mandatory = $true)]
        [int]$TargetPid,

        [Parameter(Mandatory = $true)]
        [int]$TimeoutMs
    )

    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMs)

    while ([DateTime]::UtcNow -lt $deadline) {
        $process = Get-Process -Id $TargetPid -ErrorAction SilentlyContinue
        if (-not $process) {
            throw "Process $TargetPid is no longer running."
        }

        if ($process.MainWindowHandle -ne 0) {
            return $process.MainWindowHandle
        }

        Start-Sleep -Milliseconds 200
    }

    throw "Timed out waiting for process $TargetPid to create a window."
}

function Focus-Window {
    param(
        [Parameter(Mandatory = $true)]
        [int]$TargetPid,

        [Parameter(Mandatory = $true)]
        [int]$TimeoutMs
    )

    $handle = Get-MainWindowHandle -TargetPid $TargetPid -TimeoutMs $TimeoutMs
    [void][DolphinInputNative]::ShowWindowAsync($handle, 5)
    Start-Sleep -Milliseconds 100

    $focused = [DolphinInputNative]::SetForegroundWindow($handle)
    if (-not $focused) {
        try {
            $shell = New-Object -ComObject WScript.Shell
            $focused = $shell.AppActivate($TargetPid)
        }
        catch {
            $focused = $false
        }
    }

    if (-not $focused) {
        throw "Failed to focus Dolphin window for process $TargetPid."
    }

    Start-Sleep -Milliseconds 100
}

function Send-KeyEvent {
    param(
        [Parameter(Mandatory = $true)]
        [byte]$VirtualKey,

        [Parameter(Mandatory = $true)]
        [bool]$KeyUp
    )

    $flags = if ($KeyUp) { 0x0002 } else { 0x0000 }
    [DolphinInputNative]::keybd_event($VirtualKey, 0, $flags, [UIntPtr]::Zero)
}

if ($Action -eq 'focus') {
    Focus-Window -TargetPid $ProcessId -TimeoutMs $FocusTimeoutMs
    exit 0
}

if (-not $Key) {
    throw "A key is required for action '$Action'."
}

$virtualKey = Resolve-VirtualKey -Name $Key
Focus-Window -TargetPid $ProcessId -TimeoutMs $FocusTimeoutMs

switch ($Action) {
    'tap' {
        Send-KeyEvent -VirtualKey $virtualKey -KeyUp $false
        Start-Sleep -Milliseconds $DurationMs
        Send-KeyEvent -VirtualKey $virtualKey -KeyUp $true
    }
    'keyDown' {
        Send-KeyEvent -VirtualKey $virtualKey -KeyUp $false
    }
    'keyUp' {
        Send-KeyEvent -VirtualKey $virtualKey -KeyUp $true
    }
}
