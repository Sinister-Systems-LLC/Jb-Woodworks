# Author: RKOJ-ELENO :: 2026-05-24
# Sinister OS :: vm-boot :: boot-virtualbox.ps1
#
# Create-or-reuse a VirtualBox VM named "Sinister-OS-Test" and boot it from the
# Sinister OS ISO. First run creates the VM; subsequent runs just start it.
#
# Usage:
#   powershell -File source/vm-boot/boot-virtualbox.ps1
#   powershell -File source/vm-boot/boot-virtualbox.ps1 -IsoPath D:\path\to\sinister.iso
#   powershell -File source/vm-boot/boot-virtualbox.ps1 -DryRun
#   powershell -File source/vm-boot/boot-virtualbox.ps1 -Recreate    # destroy + rebuild
#
# Defaults:
#   - VM name        : Sinister-OS-Test
#   - RAM            : 4096 MB
#   - vCPUs          : 4
#   - Disk           : 60 GB sparse VDI
#   - Firmware       : EFI
#   - Graphics       : VMSVGA, 128 MB VRAM, 3D off (safest for Hyprland live boot)
#   - Network        : NAT (host can reach guest via port-forward later)
#   - Audio          : disabled (cuts noise during boot tests)
#
# Won't touch the operator's existing VMs (only acts on "Sinister-OS-Test").

[CmdletBinding()]
param(
    [string]$VmName     = 'Sinister-OS-Test',
    [string]$IsoPath    = '',
    [int]   $MemoryMB   = 4096,
    [int]   $Cpus       = 4,
    [int]   $DiskGB     = 60,
    [switch]$DryRun,
    [switch]$Recreate,
    [switch]$Headless
)

$ErrorActionPreference = 'Stop'

function Resolve-VBoxManage {
    $cmd = Get-Command VBoxManage -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidates = @(
        'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe',
        'C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe'
    )
    foreach ($p in $candidates) { if (Test-Path $p) { return $p } }
    throw "VBoxManage not found. Install VirtualBox first (see install-helpers/install-virtualbox.ps1)."
}

function Resolve-Iso {
    param([string]$Override)
    if ($Override) {
        if (-not (Test-Path $Override)) { throw "ISO not found at -IsoPath: $Override" }
        return (Resolve-Path $Override).Path
    }
    # Default: look in the parallel iso-build lane's out dir.
    $scriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $PSCommandPath }
    if (-not $scriptRoot) { $scriptRoot = (Get-Location).Path }
    $isoDir     = Join-Path $scriptRoot '..\iso-build\out'
    if (-not (Test-Path $isoDir)) {
        Write-Host "  note: iso-build/out not created yet by parallel agent." -ForegroundColor Yellow
        return $null
    }
    $iso = Get-ChildItem -Path $isoDir -Filter 'sinister-*.iso' -ErrorAction SilentlyContinue |
           Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $iso) { return $null }
    return $iso.FullName
}

function Invoke-VBox {
    param([string]$Vbm, [string[]]$Arguments, [switch]$Dry)
    $display = "VBoxManage " + ($Arguments -join ' ')
    if ($Dry) {
        Write-Host "  DRYRUN: $display" -ForegroundColor Cyan
        return
    }
    Write-Host "  exec: $display" -ForegroundColor DarkGray
    & $Vbm @Arguments
    if ($LASTEXITCODE -ne 0) { throw "VBoxManage failed (exit $LASTEXITCODE): $display" }
}

# --- main ---
Write-Host "Sinister OS :: VirtualBox boot harness" -ForegroundColor Magenta
Write-Host "  VM name : $VmName"
Write-Host "  RAM     : $MemoryMB MB"
Write-Host "  vCPUs   : $Cpus"
Write-Host "  Disk    : $DiskGB GB (sparse VDI)"
Write-Host "  DryRun  : $DryRun"
Write-Host "  Headless: $Headless"
Write-Host ""

$vbm = Resolve-VBoxManage
Write-Host "  using VBoxManage at: $vbm"

$iso = Resolve-Iso -Override $IsoPath
if ($iso) {
    Write-Host "  ISO: $iso" -ForegroundColor Green
} else {
    Write-Host "  ISO: (none found yet -- parallel agent still building)" -ForegroundColor Yellow
    Write-Host "       Will create the VM shell but skip ISO attach + boot." -ForegroundColor Yellow
}

# Discover existing VM
$existing = & $vbm list vms
$vmExists = $existing -match [regex]::Escape("`"$VmName`"")

if ($vmExists -and $Recreate) {
    Write-Host "  -Recreate set: removing existing VM (disk too)." -ForegroundColor Yellow
    Invoke-VBox $vbm @('unregistervm', $VmName, '--delete') -Dry:$DryRun
    $vmExists = $false
}

if (-not $vmExists) {
    Write-Host "  Creating new VM..." -ForegroundColor Green

    # Default machine folder discovery (so we can compute disk path).
    $sysProps = & $vbm list systemproperties
    $machineFolder = ($sysProps | Select-String 'Default machine folder' | ForEach-Object {
        ($_ -split ':',2)[1].Trim()
    })
    if (-not $machineFolder) { $machineFolder = "$env:USERPROFILE\VirtualBox VMs" }
    $vmDir   = Join-Path $machineFolder $VmName
    $diskVdi = Join-Path $vmDir "$VmName.vdi"

    Invoke-VBox $vbm @('createvm','--name',$VmName,'--ostype','ArchLinux_64','--register') -Dry:$DryRun
    Invoke-VBox $vbm @('modifyvm',$VmName,
        '--memory',"$MemoryMB",
        '--cpus',"$Cpus",
        '--firmware','efi64',
        '--graphicscontroller','vmsvga',
        '--vram','128',
        '--accelerate3d','off',
        '--nic1','nat',
        '--audio-driver','none',
        '--boot1','dvd','--boot2','disk','--boot3','none','--boot4','none',
        '--rtcuseutc','on',
        '--ioapic','on',
        '--usbohci','on',
        '--clipboard-mode','bidirectional'
    ) -Dry:$DryRun

    $diskBytes = [int64]$DiskGB * 1GB
    Invoke-VBox $vbm @('createmedium','disk','--filename',$diskVdi,'--size',"$($DiskGB * 1024)",'--format','VDI','--variant','Standard') -Dry:$DryRun
    Invoke-VBox $vbm @('storagectl',$VmName,'--name','SATA','--add','sata','--controller','IntelAhci','--portcount','2','--bootable','on') -Dry:$DryRun
    Invoke-VBox $vbm @('storageattach',$VmName,'--storagectl','SATA','--port','0','--device','0','--type','hdd','--medium',$diskVdi) -Dry:$DryRun
    Invoke-VBox $vbm @('storagectl',$VmName,'--name','IDE','--add','ide','--controller','PIIX4') -Dry:$DryRun

    if ($iso) {
        Invoke-VBox $vbm @('storageattach',$VmName,'--storagectl','IDE','--port','0','--device','0','--type','dvddrive','--medium',$iso) -Dry:$DryRun
    } else {
        Invoke-VBox $vbm @('storageattach',$VmName,'--storagectl','IDE','--port','0','--device','0','--type','dvddrive','--medium','emptydrive') -Dry:$DryRun
    }
}
else {
    Write-Host "  VM already exists -- reusing." -ForegroundColor Green
    # If user passed a fresh ISO, hot-swap the IDE slot.
    if ($iso) {
        Write-Host "  Re-attaching ISO (in case it changed)..."
        Invoke-VBox $vbm @('storageattach',$VmName,'--storagectl','IDE','--port','0','--device','0','--type','dvddrive','--medium',$iso) -Dry:$DryRun
    }
}

if (-not $iso) {
    Write-Host ""
    Write-Host "Stopping before boot: no ISO present." -ForegroundColor Yellow
    Write-Host "When the iso-build lane produces source/iso-build/out/sinister-*.iso, re-run this script."
    return
}

# Boot.
$startType = if ($Headless) { 'headless' } else { 'gui' }
Write-Host ""
Write-Host "  Starting VM (type=$startType)..." -ForegroundColor Green
Invoke-VBox $vbm @('startvm',$VmName,'--type',$startType) -Dry:$DryRun

if (-not $DryRun) {
    Write-Host ""
    Write-Host "VM started. The VirtualBox window should open with the Sinister OS boot menu." -ForegroundColor Magenta
    Write-Host "Power off cleanly via the guest, or:"
    Write-Host "  & '$vbm' controlvm $VmName acpipowerbutton"
}
