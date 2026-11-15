# ==============================================================================
# BMW EntryNav2 (EntryEvo) Android Auto - Native Windows Manager
# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# ==============================================================================
# A native Windows WPF application with zero external dependencies.
# Runs on Windows 10 & 11 out of the box (PowerShell 5.1 / 7).
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$ShowConsole
)

# Hide the PowerShell console window so only the WPF window is visible
if (-not $ShowConsole) {
    try {
        $consoleDef = @'
[DllImport("kernel32.dll")]
public static extern IntPtr GetConsoleWindow();

[DllImport("user32.dll")]
public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
'@
        Add-Type -MemberDefinition $consoleDef -Name NativeConsole -Namespace Win32 -ErrorAction SilentlyContinue
        $consoleHandle = [Win32.NativeConsole]::GetConsoleWindow()
        if ($consoleHandle -ne [IntPtr]::Zero) {
            [Win32.NativeConsole]::ShowWindow($consoleHandle, 0) | Out-Null
        }
    } catch {}
}

# Add WPF and Windows Forms assemblies
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase

# Ensure TLS 1.2 / TLS 1.3 is enabled
try {
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
} catch {}
try {
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12 -bor [System.Net.SecurityProtocolType]'Tls13'
} catch {}

# Default Connection Parameters
$Script:DefaultIP   = "169.254.1.0"
$Script:DefaultUser = "root"
$Script:DefaultPass = "Entry0?Evo!1"
$Script:DefaultPort = 22
$Script:GitHubRepo  = "Jiraiya43/EntryNav2-Android-Auto"

# Built-in verified release catalogue (works offline or when GitHub API is rate-limited)
$Script:BuiltInCatalogue = @(
    [PSCustomObject]@{
        Tag        = "v0.12.1-rc.4"
        Name       = "EntryNav2 (EntryEvo) Android Auto 0.12.1-rc.4"
        PreRelease = $true
        Date       = "2026-11-14"
        TarName    = "entrynav2-android-auto-0.12.1-rc.4-armhf.tar"
        TarUrl     = "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.4/entrynav2-android-auto-0.12.1-rc.4-armhf.tar"
        ShaUrl     = "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.4/entrynav2-android-auto-0.12.1-rc.4-armhf.tar.sha256"
        ShaHash    = "a445a9697d1668c274dea598ba18cdfc2b13746534ac5675e96723b842357ff0"
    },
    [PSCustomObject]@{
        Tag        = "v0.12.1-rc.3"
        Name       = "EntryNav2 (EntryEvo) Android Auto 0.12.1-rc.3"
        PreRelease = $true
        Date       = "2026-11-14"
        TarName    = "entrynav2-android-auto-0.12.1-rc.3-armhf.tar"
        TarUrl     = "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.3/entrynav2-android-auto-0.12.1-rc.3-armhf.tar"
        ShaUrl     = "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.3/entrynav2-android-auto-0.12.1-rc.3-armhf.tar.sha256"
        ShaHash    = "8fa11fc02460e164432adb0c46e1f91f936ed467ccb78219b43456e7f03ba5fa"
    },
    [PSCustomObject]@{
        Tag        = "v0.12.1-rc.2"
        Name       = "EntryNav2 (EntryEvo) Android Auto 0.12.1-rc.2"
        PreRelease = $true
        Date       = "2026-11-14"
        TarName    = "entrynav2-android-auto-0.12.1-rc.2-armhf.tar"
        TarUrl     = "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.2/entrynav2-android-auto-0.12.1-rc.2-armhf.tar"
        ShaUrl     = "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.2/entrynav2-android-auto-0.12.1-rc.2-armhf.tar.sha256"
        ShaHash    = "98073b5bb51fe8f9b023532688abf1ee1664fa8befaa2f6f50c6bc22f441e876"
    },
    [PSCustomObject]@{
        Tag        = "v0.12.1-rc.1"
        Name       = "EntryNav2 (EntryEvo) Android Auto 0.12.1-rc.1"
        PreRelease = $true
        Date       = "2026-11-14"
        TarName    = "entrynav2-android-auto-0.12.1-rc.1-armhf.tar"
        TarUrl     = "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.1/entrynav2-android-auto-0.12.1-rc.1-armhf.tar"
        ShaUrl     = "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.1/entrynav2-android-auto-0.12.1-rc.1-armhf.tar.sha256"
        ShaHash    = "8e7762e12c4bcde93ceef565378b14c088c3238f495372b18262d22fd27c0d46"
    },
    [PSCustomObject]@{
        Tag        = "v0.12.0"
        Name       = "EntryNav2 (EntryEvo) Android Auto 0.12.0 (Stable)"
        PreRelease = $false
        Date       = "2026-11-13"
        TarName    = "entrynav2-android-auto-0.12.0-armhf.tar"
        TarUrl     = "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.0/entrynav2-android-auto-0.12.0-armhf.tar"
        ShaUrl     = "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.0/entrynav2-android-auto-0.12.0-armhf.tar.sha256"
        ShaHash    = "5dba7ec176b101b04750bf6e80712141ed91a85ea328ecc4a3d2056c483bf005"
    }
)

# Ensure askpass.exe helper exists in %TEMP% using clean on-the-fly compilation (No Base64 PE binary dropper)
$AskPassPath = Join-Path $env:TEMP "entrynav2_askpass.exe"
if (-not (Test-Path $AskPassPath)) {
    $csSource = @'
using System;
class P {
    static void Main() {
        string p = Environment.GetEnvironmentVariable("ENTRYNAV2_PASSWORD");
        if (!string.IsNullOrEmpty(p)) Console.Write(p);
    }
}
'@
    try {
        Add-Type -TypeDefinition $csSource -OutputAssembly $AskPassPath -OutputType WindowsApplication -ErrorAction SilentlyContinue
    } catch {}
}

# Find ssh.exe and scp.exe
$OpenSSHPath = Join-Path $env:SystemRoot "System32\OpenSSH"
$SSHExe = Join-Path $OpenSSHPath "ssh.exe"
$SCPExe = Join-Path $OpenSSHPath "scp.exe"
if (-not (Test-Path $SSHExe)) { $SSHExe = "ssh.exe" }
if (-not (Test-Path $SCPExe)) { $SCPExe = "scp.exe" }

# Forward declaration for UI Logging
function Write-GuiLog {
    param([string]$Message)
    $ts = (Get-Date).ToString("HH:mm:ss")
    $line = "[$ts] $Message"
    if ($txtConsoleLog -and $window -and $window.Dispatcher) {
        $window.Dispatcher.Invoke([Action]{
            $txtConsoleLog.AppendText("$line`r`n")
            $txtConsoleLog.ScrollToEnd()
        })
    } else {
        Write-Host $line
    }
}

# Helper to run SSH command remotely with transparent logging
function Invoke-CarSSH {
    param(
        [string]$IP,
        [string]$User,
        [string]$Pass,
        [string]$Command,
        [int]$Port = 22,
        [scriptblock]$OnOutputLine = $null
    )
    $env:ENTRYNAV2_PASSWORD = $Pass
    $env:SSH_ASKPASS = $AskPassPath
    $env:SSH_ASKPASS_REQUIRE = "force"
    $env:DISPLAY = "entrynav2:0"

    Write-GuiLog "[CMD >>] ssh $User@$IP`:$Port `"$Command`""

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $SSHExe
    $psi.Arguments = "-p $Port -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ConnectTimeout=8 -o LogLevel=ERROR $User@$IP `"$Command`""
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi

    $sbOut = New-Object System.Text.StringBuilder
    $sbErr = New-Object System.Text.StringBuilder

    $outHandler = [System.Diagnostics.DataReceivedEventHandler]{
        param($sender, $e)
        if ($e.Data -ne $null -and $e.Data.Trim() -ne "") {
            [void]$sbOut.AppendLine($e.Data)
            Write-GuiLog "[HU <<] $($e.Data)"
            if ($OnOutputLine) { & $OnOutputLine $e.Data }
        }
    }
    $errHandler = [System.Diagnostics.DataReceivedEventHandler]{
        param($sender, $e)
        if ($e.Data -ne $null -and $e.Data.Trim() -ne "") {
            [void]$sbErr.AppendLine($e.Data)
            Write-GuiLog "[HU <<] $($e.Data)"
            if ($OnOutputLine) { & $OnOutputLine $e.Data }
        }
    }

    $proc.add_OutputDataReceived($outHandler)
    $proc.add_ErrorDataReceived($errHandler)
    [void]$proc.Start()
    $proc.BeginOutputReadLine()
    $proc.BeginErrorReadLine()
    $proc.WaitForExit()

    $exitStatus = if ($proc.ExitCode -eq 0) { "0 (Success)" } else { "$($proc.ExitCode)" }
    Write-GuiLog "[EXIT] Return code: $exitStatus"

    return [PSCustomObject]@{
        ExitCode = $proc.ExitCode
        Output   = $sbOut.ToString()
        Error    = $sbErr.ToString()
    }
}

# Helper to upload via SCP with transparent progress
function Invoke-CarSCP {
    param(
        [string]$IP,
        [string]$User,
        [string]$Pass,
        [string]$LocalFile,
        [string]$RemoteDest,
        [int]$Port = 22
    )
    $env:ENTRYNAV2_PASSWORD = $Pass
    $env:SSH_ASKPASS = $AskPassPath
    $env:SSH_ASKPASS_REQUIRE = "force"
    $env:DISPLAY = "entrynav2:0"

    $leaf = Split-Path $LocalFile -Leaf
    $sizeBytes = if (Test-Path $LocalFile) { (Get-Item $LocalFile).Length } else { 0 }
    $sizeStr = if ($sizeBytes -ge 1MB) { "$([math]::Round($sizeBytes / 1MB, 2)) MB" } else { "$([math]::Round($sizeBytes / 1KB, 1)) KB" }
    Write-GuiLog "[SCP >>] Uploading $leaf ($sizeStr) -> $User@$IP`:$RemoteDest"

    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $SCPExe
    $psi.Arguments = "-P $Port -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ConnectTimeout=10 -o LogLevel=ERROR `"$LocalFile`" $User@$IP`:$RemoteDest"
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $proc = [System.Diagnostics.Process]::Start($psi)
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    $sw.Stop()

    $sec = [math]::Max(0.1, $sw.Elapsed.TotalSeconds)
    if ($proc.ExitCode -eq 0) {
        Write-GuiLog "[SCP <<] Upload finished in $([math]::Round($sec, 1))s -> Success (Code 0)"
    } else {
        Write-GuiLog "[SCP <<] Upload failed (Code $($proc.ExitCode)): $($stderr.Trim())"
    }

    return [PSCustomObject]@{
        ExitCode = $proc.ExitCode
        Output   = $stdout
        Error    = $stderr
    }
}

# Helper to download via SCP
function Invoke-CarSCPDownload {
    param(
        [string]$IP,
        [string]$User,
        [string]$Pass,
        [string]$RemoteFile,
        [string]$LocalDest,
        [int]$Port = 22
    )
    $env:ENTRYNAV2_PASSWORD = $Pass
    $env:SSH_ASKPASS = $AskPassPath
    $env:SSH_ASKPASS_REQUIRE = "force"
    $env:DISPLAY = "entrynav2:0"

    Write-GuiLog "[SCP >>] Downloading $RemoteFile -> $LocalDest"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $SCPExe
    $psi.Arguments = "-P $Port -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ConnectTimeout=10 -o LogLevel=ERROR $User@$IP`:$RemoteFile `"$LocalDest`""
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $proc = [System.Diagnostics.Process]::Start($psi)
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    $sw.Stop()

    $sec = [math]::Max(0.1, $sw.Elapsed.TotalSeconds)
    $dlBytes = if (Test-Path $LocalDest) { (Get-Item $LocalDest).Length } else { 0 }
    if ($proc.ExitCode -eq 0) {
        Write-GuiLog "[SCP <<] Download finished in $([math]::Round($sec, 1))s ($dlBytes bytes) -> Success (Code 0)"
    } else {
        Write-GuiLog "[SCP <<] Download failed (Code $($proc.ExitCode)): $($stderr.Trim())"
    }

    return [PSCustomObject]@{
        ExitCode = $proc.ExitCode
        Output   = $stdout
        Error    = $stderr
    }
}

# Launch interactive root shell in a new window with autologin
function Start-CarInteractiveShell {
    param(
        [string]$IP,
        [string]$User,
        [string]$Pass
    )
    $putty = Get-Command "putty.exe" -ErrorAction SilentlyContinue
    if ($putty) {
        Start-Process $putty.Source -ArgumentList "-ssh", "$User@$IP", "22", "-pw", "$Pass"
        Write-GuiLog "Launched PuTTY SSH session with autologin."
        return
    }

    $pwScript = @"
`$env:ENTRYNAV2_PASSWORD = '$Pass'
`$env:SSH_ASKPASS = '$AskPassPath'
`$env:SSH_ASKPASS_REQUIRE = 'force'
`$env:DISPLAY = 'entrynav2:0'
`$Host.UI.RawUI.WindowTitle = 'BMW EntryNav2 Root Terminal ($IP)'
Write-Host '================================================================' -ForegroundColor Cyan
Write-Host ' Connected to BMW EntryNav2 ($IP) as root' -ForegroundColor Green
Write-Host ' Password was automatically authenticated via ASKPASS.' -ForegroundColor Green
Write-Host ' Type exit to disconnect.' -ForegroundColor Gray
Write-Host '================================================================' -ForegroundColor Cyan
& '$SSHExe' -p 22 -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $User@$IP
"@
    $tempScript = Join-Path $env:TEMP "launch_car_ssh.ps1"
    [IO.File]::WriteAllText($tempScript, $pwScript)
    Start-Process powershell.exe -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$tempScript`""
    Write-GuiLog "Launched PowerShell root terminal window."
}

# ==============================================================================
# XAML GUI DEFINITION
# ==============================================================================
[xml]$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="BMW EntryNav2 Android Auto - Windows Management &amp; Flashing Suite"
        Height="780" Width="1060" MinHeight="620" MinWidth="850"
        WindowStartupLocation="CenterScreen" Background="#16181B" Foreground="#E6EDF3" FontFamily="Segoe UI">

    <Window.Resources>
        <Style TargetType="TabItem">
            <Setter Property="Background" Value="#21262D"/>
            <Setter Property="Foreground" Value="#C9D1D9"/>
            <Setter Property="FontSize" Value="13"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Setter Property="Padding" Value="16,8"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="TabItem">
                        <Border Name="Border" Background="{TemplateBinding Background}" BorderBrush="#30363D" BorderThickness="1,1,1,0" CornerRadius="6,6,0,0" Margin="2,0">
                            <ContentPresenter ContentSource="Header" RecognizesAccessKey="True" HorizontalAlignment="Center" VerticalAlignment="Center" Margin="12,6"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsSelected" Value="True">
                                <Setter TargetName="Border" Property="Background" Value="#0066B2"/>
                                <Setter Property="Foreground" Value="#FFFFFF"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
        <Style TargetType="Button">
            <Setter Property="Background" Value="#0066B2"/>
            <Setter Property="Foreground" Value="#FFFFFF"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Setter Property="Padding" Value="12,6"/>
            <Setter Property="BorderThickness" Value="0"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" CornerRadius="4" Padding="{TemplateBinding Padding}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
    </Window.Resources>

    <Grid Margin="12">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="180"/>
        </Grid.RowDefinitions>

        <!-- TOP CONNECTION BAR -->
        <Border Grid.Row="0" Background="#21262D" CornerRadius="6" Padding="12" Margin="0,0,0,10" BorderBrush="#30363D" BorderThickness="1">
            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="Auto"/>
                    <ColumnDefinition Width="130"/>
                    <ColumnDefinition Width="Auto"/>
                    <ColumnDefinition Width="50"/>
                    <ColumnDefinition Width="Auto"/>
                    <ColumnDefinition Width="70"/>
                    <ColumnDefinition Width="Auto"/>
                    <ColumnDefinition Width="140"/>
                    <ColumnDefinition Width="Auto"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>

                <TextBlock Text="Car IP:" VerticalAlignment="Center" FontWeight="SemiBold" Margin="4,0" Foreground="#58A6FF"/>
                <TextBox Name="txtCarIP" Grid.Column="1" Text="169.254.1.0" Background="#0D1117" Foreground="#E6EDF3" BorderBrush="#30363D" Padding="4,2" FontFamily="Consolas"/>

                <TextBlock Grid.Column="2" Text="Port:" VerticalAlignment="Center" FontWeight="SemiBold" Margin="8,0,4,0" Foreground="#58A6FF"/>
                <TextBox Name="txtPort" Grid.Column="3" Text="22" Background="#0D1117" Foreground="#E6EDF3" BorderBrush="#30363D" Padding="4,2" FontFamily="Consolas"/>

                <TextBlock Grid.Column="4" Text="User:" VerticalAlignment="Center" FontWeight="SemiBold" Margin="8,0,4,0" Foreground="#58A6FF"/>
                <TextBox Name="txtUser" Grid.Column="5" Text="root" Background="#0D1117" Foreground="#E6EDF3" BorderBrush="#30363D" Padding="4,2" FontFamily="Consolas"/>

                <TextBlock Grid.Column="6" Text="Password:" VerticalAlignment="Center" FontWeight="SemiBold" Margin="8,0,4,0" Foreground="#58A6FF"/>
                <PasswordBox Name="txtPass" Grid.Column="7" Password="Entry0?Evo!1" Background="#0D1117" Foreground="#E6EDF3" BorderBrush="#30363D" Padding="4,2" FontFamily="Consolas"/>

                <StackPanel Grid.Column="8" Orientation="Horizontal" Margin="8,0,0,0">
                    <Button Name="btnTestConn" Content="Test Connection" Margin="4,0" Background="#238636"/>
                    <Button Name="btnGetVersionId" Content="🔍 Check Android Auto Version" Margin="4,0" Background="#2EA043"/>
                    <Button Name="btnLaunchShell" Content="🚀 Open Root SSH Terminal" Margin="4,0" Background="#1F6FEB"/>
                    <Button Name="btnTopReboot" Content="🔄 Reboot Head Unit" Margin="4,0" Background="#8957E5"/>
                </StackPanel>

                <TextBlock Name="lblStatus" Grid.Column="9" Text="● Not Connected" VerticalAlignment="Center" HorizontalAlignment="Right" Foreground="#8B949E" FontWeight="Bold"/>
            </Grid>
        </Border>

        <!-- MAIN TABS -->
        <TabControl Grid.Row="1" Background="Transparent" BorderThickness="0">
            <!-- TAB 1: UPDATE / FLASH CAR -->
            <TabItem Header=" Update &amp; Flash Car ">
                <ScrollViewer VerticalScrollBarVisibility="Auto">
                    <StackPanel Margin="6,10">
                        <!-- Current Car State Banner -->
                        <Border Background="#21262D" CornerRadius="6" Padding="12" Margin="0,0,0,10" BorderBrush="#30363D" BorderThickness="1">
                            <Grid>
                                <Grid.ColumnDefinitions>
                                    <ColumnDefinition Width="Auto"/>
                                    <ColumnDefinition Width="*"/>
                                    <ColumnDefinition Width="Auto"/>
                                </Grid.ColumnDefinitions>
                                <TextBlock Text="Current Car State:" FontWeight="Bold" VerticalAlignment="Center" Foreground="#58A6FF" Margin="0,0,10,0"/>
                                <TextBlock Name="lblCurrentInstalled" Grid.Column="1" Text="Android Auto: Not Checked | iDrive FW: Not Checked" VerticalAlignment="Center" Foreground="#C9D1D9"/>
                                <Button Name="btnDetectInstalled" Grid.Column="2" Content="🔍 Detect Android Auto Version" Background="#30363D" Padding="10,4"/>
                            </Grid>
                        </Border>

                        <Border Background="#21262D" CornerRadius="6" Padding="14" Margin="0,0,0,10" BorderBrush="#30363D" BorderThickness="1">
                            <StackPanel>
                                <TextBlock Text="Step 1: Select Release Archive" FontSize="14" FontWeight="Bold" Foreground="#58A6FF" Margin="0,0,0,8"/>
                                <Grid Margin="0,4">
                                    <Grid.ColumnDefinitions>
                                        <ColumnDefinition Width="*"/>
                                        <ColumnDefinition Width="Auto"/>
                                        <ColumnDefinition Width="Auto"/>
                                    </Grid.ColumnDefinitions>
                                    <ComboBox Name="cmbReleases" Grid.Column="0" Height="28" Background="#21262D" Foreground="#0D1117" VerticalContentAlignment="Center" FontSize="11"/>
                                    <Button Name="btnFetchReleases" Grid.Column="1" Content="Fetch from GitHub" Margin="8,0" Background="#238636"/>
                                    <Button Name="btnBrowseLocal" Grid.Column="2" Content="Browse Local .tar..." Background="#30363D"/>
                                </Grid>

                                <Grid Margin="0,8,0,0">
                                    <Grid.ColumnDefinitions>
                                        <ColumnDefinition Width="Auto"/>
                                        <ColumnDefinition Width="*"/>
                                    </Grid.ColumnDefinitions>
                                    <TextBlock Text="Expected SHA-256:" FontWeight="SemiBold" VerticalAlignment="Center" Margin="0,0,8,0"/>
                                    <TextBox Name="txtExpectedSHA" Grid.Column="1" Background="#0D1117" Foreground="#3FB950" BorderBrush="#30363D" Padding="4" FontFamily="Consolas" FontSize="11"/>
                                </Grid>
                            </StackPanel>
                        </Border>

                        <Border Background="#21262D" CornerRadius="6" Padding="14" Margin="0,0,0,10" BorderBrush="#30363D" BorderThickness="1">
                            <StackPanel>
                                <TextBlock Text="Step 2: Vehicle Profile (Optional)" FontSize="14" FontWeight="Bold" Foreground="#58A6FF" Margin="0,0,0,8"/>
                                <Grid>
                                    <Grid.ColumnDefinitions>
                                        <ColumnDefinition Width="Auto"/>
                                        <ColumnDefinition Width="140"/>
                                        <ColumnDefinition Width="Auto"/>
                                        <ColumnDefinition Width="80"/>
                                        <ColumnDefinition Width="*"/>
                                    </Grid.ColumnDefinitions>
                                    <TextBlock Text="Model (e.g. 320d, X3, M340i):" VerticalAlignment="Center" Margin="0,0,6,0"/>
                                    <TextBox Name="txtModel" Grid.Column="1" Background="#0D1117" Foreground="#E6EDF3" BorderBrush="#30363D" Padding="4"/>
                                    <TextBlock Grid.Column="2" Text="Year (e.g. 2020):" VerticalAlignment="Center" Margin="12,0,6,0"/>
                                    <TextBox Name="txtYear" Grid.Column="3" Background="#0D1117" Foreground="#E6EDF3" BorderBrush="#30363D" Padding="4"/>
                                    <TextBlock Grid.Column="4" Text="Saves to /var/local/data/AA/vehicle" VerticalAlignment="Center" Foreground="#8B949E" Margin="10,0"/>
                                </Grid>
                            </StackPanel>
                        </Border>

                        <Border Background="#21262D" CornerRadius="6" Padding="14" BorderBrush="#30363D" BorderThickness="1">
                            <StackPanel>
                                <TextBlock Text="Step 3: Verification &amp; In-Car Safety Standards" FontSize="14" FontWeight="Bold" Foreground="#58A6FF" Margin="0,0,0,4"/>
                                <TextBlock Text="Enforces local SHA-256 validation, car storage check (&gt;= 16MB), RAM-disk /tmp upload, in-car MD5 verification, dynamic linker resolution check, and rehearsal dry-run (aa-supervisor --compat) before touching flash." TextWrapping="Wrap" Foreground="#8B949E" Margin="0,0,0,12"/>
                                <Grid>
                                    <Grid.ColumnDefinitions>
                                        <ColumnDefinition Width="Auto"/>
                                        <ColumnDefinition Width="*"/>
                                        <ColumnDefinition Width="Auto"/>
                                    </Grid.ColumnDefinitions>
                                    <Button Name="btnStartUpdate" Content="⚡ EXECUTE SAFE UPDATE &amp; FLASH" Height="36" FontSize="13" Background="#238636" HorizontalAlignment="Left" Padding="20,6"/>
                                    <ProgressBar Name="pbFlashProgress" Grid.Column="1" Height="22" Margin="14,0" Minimum="0" Maximum="8" Value="0" Background="#0D1117" Foreground="#238636" BorderBrush="#30363D"/>
                                    <TextBlock Name="lblFlashStep" Grid.Column="2" Text="Ready" VerticalAlignment="Center" FontWeight="Bold" Foreground="#8B949E"/>
                                </Grid>
                            </StackPanel>
                        </Border>
                    </StackPanel>
                </ScrollViewer>
            </TabItem>

            <!-- TAB 2: LOGS MANAGER -->
            <TabItem Header=" Logs Manager ">
                <Grid Margin="6,10">
                    <Grid.RowDefinitions>
                        <RowDefinition Height="Auto"/>
                        <RowDefinition Height="*"/>
                    </Grid.RowDefinitions>
                    <Border Grid.Row="0" Background="#21262D" CornerRadius="6" Padding="14" Margin="0,0,0,10" BorderBrush="#30363D" BorderThickness="1">
                        <StackPanel>
                            <Grid Margin="0,0,0,10">
                                <Grid.ColumnDefinitions>
                                    <ColumnDefinition Width="*"/>
                                    <ColumnDefinition Width="Auto"/>
                                </Grid.ColumnDefinitions>
                                <StackPanel Grid.Column="0">
                                    <TextBlock Text="Car Maintenance Logging Status" FontSize="14" FontWeight="Bold" Foreground="#58A6FF" Margin="0,0,0,4"/>
                                    <TextBlock Name="txtLogStatus" Text="● Logging Status: Unknown (Click 'Check Log Status')" FontSize="12" FontWeight="Bold" Foreground="#8B949E"/>
                                    <TextBlock Name="txtLogFilesOnCar" Text="Flag: /var/local/data/AA/maintenance | Diagnostic files: Not checked" FontSize="11" Foreground="#8B949E" Margin="0,2,0,0"/>
                                </StackPanel>
                                <Button Name="btnCheckLogStatus" Grid.Column="1" Content="🔄 Check Log Status" Background="#30363D" Padding="10,4" VerticalAlignment="Center"/>
                            </Grid>
                            <StackPanel Orientation="Horizontal" Margin="0,4,0,0">
                                <Button Name="btnEnableLogs" Content="✅ Enable Maintenance Logging" Background="#238636" Margin="0,0,8,0"/>
                                <Button Name="btnDisableLogs" Content="❌ Disable &amp; Clear Logs" Background="#DA3633" Margin="0,0,12,0"/>
                                <Button Name="btnPullLogs" Content="📥 Pull All Logs to PC" Background="#1F6FEB" Margin="0,0,8,0"/>
                                <Button Name="btnOpenLogsFolder" Content="📂 Open Logs Folder" Background="#30363D"/>
                            </StackPanel>
                            <TextBlock Text="When maintenance mode is active, logs are recorded to /var/local/data/AA/app.log and /tmp/entry-aa-service.log for diagnosing Wi-Fi link, crashes or audio issues." Foreground="#8B949E" Margin="0,8,0,0" TextWrapping="Wrap"/>
                        </StackPanel>
                    </Border>

                    <Border Grid.Row="1" Background="#21262D" CornerRadius="6" Padding="10" BorderBrush="#30363D" BorderThickness="1">
                        <Grid>
                            <Grid.RowDefinitions>
                                <RowDefinition Height="Auto"/>
                                <RowDefinition Height="*"/>
                            </Grid.RowDefinitions>
                            <TextBlock Text="Extracted Logs Preview:" FontWeight="SemiBold" Foreground="#8B949E" Margin="0,0,0,6"/>
                            <TextBox Name="txtLogsPreview" Grid.Row="1" Background="#0D1117" Foreground="#C9D1D9" FontFamily="Consolas" FontSize="11" IsReadOnly="True" VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Auto"/>
                        </Grid>
                    </Border>
                </Grid>
            </TabItem>

            <!-- TAB 3: SETTINGS & QUICK ACTIONS -->
            <TabItem Header=" Settings &amp; Actions ">
                <ScrollViewer VerticalScrollBarVisibility="Auto">
                    <StackPanel Margin="6,10">
                        <Border Background="#21262D" CornerRadius="6" Padding="14" Margin="0,0,0,10" BorderBrush="#30363D" BorderThickness="1">
                            <StackPanel>
                                <TextBlock Text="Quick Head Unit Actions" FontSize="14" FontWeight="Bold" Foreground="#58A6FF" Margin="0,0,0,8"/>
                                <WrapPanel>
                                    <Button Name="btnQuickGetVersionId" Content="🔍 Check Android Auto Version" Background="#2EA043" Margin="0,0,8,6"/>
                                    <Button Name="btnCheckCarStatus" Content="Check Processes &amp; Storage" Background="#1F6FEB" Margin="0,0,8,6"/>
                                    <Button Name="btnResetAppGuard" Content="Reset App Guard (app.disable)" Background="#D29922" Margin="0,0,8,6"/>
                                    <Button Name="btnRebootHU" Content="🔄 Reboot Head Unit" Background="#8957E5" Margin="0,0,12,6"/>
                                    <Button Name="btnUninstallAA" Content="⚠️ Uninstall Android Auto" Background="#DA3633" Margin="0,0,8,6"/>
                                </WrapPanel>
                            </StackPanel>
                        </Border>

                        <Border Background="#21262D" CornerRadius="6" Padding="14" BorderBrush="#30363D" BorderThickness="1">
                            <StackPanel>
                                <TextBlock Text="Android Auto Configuration Flags (/var/local/data/AA)" FontSize="14" FontWeight="Bold" Foreground="#58A6FF" Margin="0,0,0,8"/>
                                <CheckBox Name="chkAutostart" Content="Auto-start Android Auto automatically with iDrive" Foreground="#E6EDF3" Margin="0,4"/>
                                <CheckBox Name="chkUsb" Content="Force USB Cable connection instead of Wireless" Foreground="#E6EDF3" Margin="0,4"/>
                                <CheckBox Name="chkEntryDirect" Content="Direct launch into Android Auto (skip sub-menu)" Foreground="#E6EDF3" Margin="0,4"/>
                                <CheckBox Name="chkKombiOff" Content="Disable Turn-by-Turn guidance on instrument cluster / HUD" Foreground="#E6EDF3" Margin="0,4"/>
                                <CheckBox Name="chkKombiSingle" Content="Cluster single-maneuver mode (for clusters that reject full route graphs)" Foreground="#E6EDF3" Margin="0,4"/>
                                <CheckBox Name="chkGpsPhone" Content="Use phone's internal GPS instead of car's GPS" Foreground="#E6EDF3" Margin="0,4"/>
                                <CheckBox Name="chkMaintenance" Content="Enable diagnostic maintenance logging (/var/local/data/AA/maintenance)" Foreground="#E6EDF3" Margin="0,4"/>

                                <StackPanel Orientation="Horizontal" Margin="0,12,0,0">
                                    <Button Name="btnReadSettings" Content="Read Current Car Flags" Background="#30363D" Margin="0,0,8,0"/>
                                    <Button Name="btnSaveSettings" Content="💾 Save Flags to Car" Background="#238636"/>
                                </StackPanel>
                            </StackPanel>
                        </Border>
                    </StackPanel>
                </ScrollViewer>
            </TabItem>
        </TabControl>

        <!-- BOTTOM ACTIVITY & SAFETY LOG CONSOLE -->
        <Border Grid.Row="2" Background="#0D1117" CornerRadius="6" Padding="8" Margin="0,10,0,0" BorderBrush="#30363D" BorderThickness="1">
            <Grid>
                <Grid.RowDefinitions>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="*"/>
                </Grid.RowDefinitions>
                <TextBlock Text="Activity, Commands &amp; Safety Verification Log:" FontSize="11" FontWeight="Bold" Foreground="#58A6FF" Margin="4,0,0,4"/>
                <TextBox Name="txtConsoleLog" Grid.Row="1" Background="#0D1117" Foreground="#3FB950" BorderThickness="0" FontFamily="Consolas" FontSize="11" IsReadOnly="True" VerticalScrollBarVisibility="Auto"/>
            </Grid>
        </Border>
    </Grid>
</Window>
"@

# Load XAML
$reader = New-Object System.Xml.XmlNodeReader $xaml
$window = [System.Windows.Markup.XamlReader]::Load($reader)

# Element References
$txtCarIP            = $window.FindName("txtCarIP")
$txtPort             = $window.FindName("txtPort")
$txtUser             = $window.FindName("txtUser")
$txtPass             = $window.FindName("txtPass")
$lblStatus           = $window.FindName("lblStatus")
$btnTestConn         = $window.FindName("btnTestConn")
$btnGetVersionId     = $window.FindName("btnGetVersionId")
$btnLaunchShell      = $window.FindName("btnLaunchShell")
$btnTopReboot        = $window.FindName("btnTopReboot")

$lblCurrentInstalled = $window.FindName("lblCurrentInstalled")
$btnDetectInstalled  = $window.FindName("btnDetectInstalled")

$cmbReleases         = $window.FindName("cmbReleases")
$btnFetchReleases    = $window.FindName("btnFetchReleases")
$btnBrowseLocal      = $window.FindName("btnBrowseLocal")
$txtExpectedSHA      = $window.FindName("txtExpectedSHA")
$txtModel            = $window.FindName("txtModel")
$txtYear             = $window.FindName("txtYear")
$btnStartUpdate      = $window.FindName("btnStartUpdate")
$pbFlashProgress     = $window.FindName("pbFlashProgress")
$lblFlashStep        = $window.FindName("lblFlashStep")

$btnEnableLogs       = $window.FindName("btnEnableLogs")
$btnDisableLogs      = $window.FindName("btnDisableLogs")
$btnPullLogs         = $window.FindName("btnPullLogs")
$btnOpenLogsFolder   = $window.FindName("btnOpenLogsFolder")
$txtLogsPreview      = $window.FindName("txtLogsPreview")
$txtLogStatus        = $window.FindName("txtLogStatus")
$txtLogFilesOnCar    = $window.FindName("txtLogFilesOnCar")
$btnCheckLogStatus   = $window.FindName("btnCheckLogStatus")

$btnQuickGetVersionId= $window.FindName("btnQuickGetVersionId")
$btnCheckCarStatus   = $window.FindName("btnCheckCarStatus")
$btnResetAppGuard    = $window.FindName("btnResetAppGuard")
$btnRebootHU         = $window.FindName("btnRebootHU")
$btnUninstallAA      = $window.FindName("btnUninstallAA")
$chkAutostart        = $window.FindName("chkAutostart")
$chkUsb              = $window.FindName("chkUsb")
$chkEntryDirect      = $window.FindName("chkEntryDirect")
$chkKombiOff         = $window.FindName("chkKombiOff")
$chkKombiSingle      = $window.FindName("chkKombiSingle")
$chkGpsPhone         = $window.FindName("chkGpsPhone")
$chkMaintenance      = $window.FindName("chkMaintenance")
$btnReadSettings     = $window.FindName("btnReadSettings")
$btnSaveSettings     = $window.FindName("btnSaveSettings")

$txtConsoleLog       = $window.FindName("txtConsoleLog")

# Helper to update flash progress bar and status text
function Update-FlashProgress {
    param(
        [int]$Step,
        [string]$StatusText
    )
    if ($window -and $window.Dispatcher) {
        $window.Dispatcher.Invoke([Action]{
            if ($pbFlashProgress) { $pbFlashProgress.Value = $Step }
            if ($lblFlashStep) {
                $lblFlashStep.Text = $StatusText
                if ($Step -eq 8) {
                    $lblFlashStep.Foreground = [System.Windows.Media.Brushes]::LimeGreen
                } elseif ($Step -gt 0) {
                    $lblFlashStep.Foreground = [System.Windows.Media.Brushes]::LightBlue
                } else {
                    $lblFlashStep.Foreground = [System.Windows.Media.Brushes]::Gray
                }
            }
        })
    }
}

# State variables
$Script:FetchedReleases = @()
$Script:LastPulledFolder = ""

# ----------------- FUNCTION: RETRIEVE INSTALLED VERSION ID -----------------
function Retrieve-InstalledVersionInfo {
    param([bool]$ShowDialog = $true)

    $targetIP = $txtCarIP.Text.Trim()
    $targetPort = [int]$txtPort.Text.Trim()
    $targetUser = $txtUser.Text.Trim()
    $targetPass = $txtPass.Password

    Write-GuiLog "Querying head unit for installed Android Auto version..."
    $resV = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "head -n 1 /etc/version" -Port $targetPort
    if ($resV.ExitCode -ne 0) {
        $lblStatus.Text = "● Disconnected"
        $lblStatus.Foreground = [System.Windows.Media.Brushes]::Red
        if ($lblCurrentInstalled) {
            $lblCurrentInstalled.Text = "Head Unit: Offline / Unreachable"
            $lblCurrentInstalled.Foreground = [System.Windows.Media.Brushes]::Red
        }
        Write-GuiLog "❌ Could not reach head unit at $targetIP"
        if ($ShowDialog) {
            [System.Windows.MessageBox]::Show("Could not connect to car head unit at $targetIP.`n`nError: $($resV.Error)`n`nPlease check ENET cable and car ignition.", "Connection Error", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Error)
        }
        return
    }

    $huFw = $resV.Output.Trim()
    $lblStatus.Text = "● Connected ($huFw)"
    $lblStatus.Foreground = [System.Windows.Media.Brushes]::LimeGreen

    $resChk = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "test -f /opt/aa/entry-aad && echo EXISTS || echo NOT_INSTALLED" -Port $targetPort
    $isInstalled = ($resChk.Output -like "*EXISTS*")

    $detectedVer = "Unknown"
    $method = "None"
    $entryMd5 = ""
    $aaSupMd5 = ""
    $libMd5 = ""

    $knownReleases = @{
        "78661be323ab42622004b91083ebbbdc" = "v0.12.1-rc.4"
        "dfb0ebefe6e2a85041f6bb47646655eb" = "v0.12.1-rc.3"
        "b6c72ae9f4c144a4ad27b41944a05e8c" = "v0.12.1-rc.2"
        "f17b95fa8653992442daac05d03ff605" = "v0.12.1-rc.1"
        "b983052e63affecce7ff8c83594b2b6c" = "v0.12.0"
    }

    if (-not $isInstalled) {
        $detectedVer = "Not Installed"
        $method = "Flash inspection (/opt/aa empty)"
        Write-GuiLog "⚠️ Android Auto is NOT currently installed on this head unit."
        if ($lblCurrentInstalled) {
            $lblCurrentInstalled.Text = "Android Auto: NOT INSTALLED | iDrive FW: $huFw"
            $lblCurrentInstalled.Foreground = [System.Windows.Media.Brushes]::Red
        }
    } else {
        # Check stamp file
        $resStamp = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "cat /opt/aa/.version /var/local/data/AA/installed_version 2>/dev/null" -Port $targetPort
        if ($resStamp.ExitCode -eq 0 -and $resStamp.Output.Trim()) {
            foreach ($line in ($resStamp.Output -split '`r?`n')) {
                if ($line -like "*tag=*" -or $line -like "*version=*") {
                    $detectedVer = ($line -split '=')[-1].Trim()
                    $method = "Version stamp file (/opt/aa/.version)"
                    break
                }
            }
        }

        # Check MD5
        $resMd5 = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "md5sum /opt/aa/entry-aad /opt/aa/aa-supervisor /opt/hmi/data/ro/Plugins/EntryAad/libEntryAad.so 2>/dev/null" -Port $targetPort
        if ($resMd5.ExitCode -eq 0 -and $resMd5.Output.Trim()) {
            foreach ($line in ($resMd5.Output -split '`r?`n')) {
                $parts = ($line.Trim() -split '\s+')
                if ($parts.Count -ge 2) {
                    $hash = $parts[0].ToLower()
                    $file = $parts[1]
                    if ($file -like "*entry-aad" -and $file -notlike "*libEntryAad*") {
                        $entryMd5 = $hash
                        if ($knownReleases.ContainsKey($hash)) {
                            $detectedVer = $knownReleases[$hash]
                            $method = "Cryptographic MD5 Match ($($knownReleases[$hash]))"
                        }
                    } elseif ($file -like "*aa-supervisor*") {
                        $aaSupMd5 = $hash
                    } elseif ($file -like "*libEntryAad.so*") {
                        $libMd5 = $hash
                    }
                }
            }
        }

        # Binary strings fallback
        if ($detectedVer -eq "Unknown") {
            $resStr = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "strings /opt/aa/entry-aad 2>/dev/null | grep -E '^[0-9]+\.[0-9]+' | head -n 1" -Port $targetPort
            if ($resStr.Output.Trim()) {
                $detectedVer = "v$($resStr.Output.Trim())"
                $method = "Binary internal version string"
            }
        }

        if ($lblCurrentInstalled) {
            $lblCurrentInstalled.Text = "Android Auto: $detectedVer ($method) | iDrive FW: $huFw"
            $lblCurrentInstalled.Foreground = [System.Windows.Media.Brushes]::LimeGreen
        }
    }

    $resPid = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "pidof aa-supervisor entry-aad" -Port $targetPort
    $runningPids = $resPid.Output.Trim()

    $resVeh = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "cat /var/local/data/AA/vehicle 2>/dev/null" -Port $targetPort
    $vehModel = "iDrive"
    $vehYear = "2019"
    if ($resVeh.Output.Trim()) {
        foreach ($line in ($resVeh.Output -split '`r?`n')) {
            if ($line -like "*model=*") { $vehModel = ($line -split '=')[-1].Trim() }
            if ($line -like "*year=*") { $vehYear = ($line -split '=')[-1].Trim() }
        }
    }

    Write-GuiLog "=========================================================="
    if ($isInstalled) {
        Write-GuiLog "📦 ANDROID AUTO INSTALLED VERSION: $detectedVer"
        Write-GuiLog "   • Detection Source:   $method"
        if ($entryMd5) { Write-GuiLog "   • entry-aad MD5:      $entryMd5" }
        if ($aaSupMd5) { Write-GuiLog "   • aa-supervisor MD5:  $aaSupMd5" }
        if ($libMd5)   { Write-GuiLog "   • libEntryAad.so MD5: $libMd5" }
    } else {
        Write-GuiLog "📦 ANDROID AUTO STATUS: NOT INSTALLED (/opt/aa empty)"
    }
    Write-GuiLog "   • Car iDrive Firmware: $huFw"
    Write-GuiLog "   • Process State:      $(if ($runningPids) { "Active (PID $runningPids)" } else { "Stopped" })"
    Write-GuiLog "   • Vehicle Profile:    Model=$vehModel, Year=$vehYear"
    Write-GuiLog "=========================================================="

    # Also silently refresh log status
    Check-LoggingStatus -Silent

    if ($ShowDialog) {
        $statusTxt = if ($isInstalled) { "INSTALLED & READY" } else { "NOT INSTALLED" }
        $dlgMsg = @"
=== Android Auto Installation Details ===

• Android Auto Status:   $statusTxt
• Android Auto Version:  $detectedVer
• Detection Method:     $method

• Running Processes:    $(if ($runningPids) { $runningPids } else { "None (Stopped)" })
• Car iDrive Firmware:  $huFw
• Vehicle Profile:      Model: $vehModel, Year: $vehYear

• Installed Binary Checksums (MD5):
  - entry-aad:      $(if ($entryMd5) { $entryMd5 } else { "N/A" })
  - aa-supervisor:  $(if ($aaSupMd5) { $aaSupMd5 } else { "N/A" })
  - libEntryAad.so: $(if ($libMd5) { $libMd5 } else { "N/A" })
"@
        [System.Windows.MessageBox]::Show($dlgMsg, "Android Auto Installed Version", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Information)
    }
}

# ----------------- EVENT: TEST CONNECTION -----------------
$btnTestConn.Add_Click({
    Retrieve-InstalledVersionInfo -ShowDialog $false
})

$btnGetVersionId.Add_Click({
    Retrieve-InstalledVersionInfo -ShowDialog $true
})

$btnDetectInstalled.Add_Click({
    Retrieve-InstalledVersionInfo -ShowDialog $false
})

$btnQuickGetVersionId.Add_Click({
    Retrieve-InstalledVersionInfo -ShowDialog $true
})

# ----------------- EVENT: LAUNCH ROOT SSH SHELL -----------------
$btnLaunchShell.Add_Click({
    $ip = $txtCarIP.Text.Trim()
    $user = $txtUser.Text.Trim()
    $pass = $txtPass.Password

    Write-GuiLog "Launching interactive root SSH terminal with autologin..."
    Start-CarInteractiveShell -IP $ip -User $user -Pass $pass
})

# ----------------- EVENT: REBOOT HEAD UNIT (TOP BAR) -----------------
$btnTopReboot.Add_Click({
    $confirm = [System.Windows.MessageBox]::Show("Are you sure you want to reboot the BMW head unit?`n`nThe display and audio will restart briefly.", "Confirm Reboot Head Unit", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Warning)
    if ($confirm -eq [System.Windows.MessageBoxResult]::Yes) {
        $targetIP = $txtCarIP.Text.Trim()
        $targetPort = [int]$txtPort.Text.Trim()
        $targetUser = $txtUser.Text.Trim()
        $targetPass = $txtPass.Password
        Write-GuiLog "Sending reboot command to head unit ($targetIP)..."
        $lblStatus.Text = "● Rebooting..."
        $lblStatus.Foreground = [System.Windows.Media.Brushes]::Orange
        Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "reboot" -Port $targetPort | Out-Null
        Write-GuiLog "🔄 Reboot signal sent to BMW head unit."
    }
})

# ----------------- RELEASES UI POPULATION HELPER -----------------
function Load-ReleasesToUI {
    param(
        [array]$Releases,
        [string]$Source = "GitHub"
    )
    $items = @()
    $parsed = @()

    foreach ($r in $Releases) {
        $entry = $r
        if (-not $entry.TarUrl) {
            $tarAsset = $r.assets | Where-Object { $_.name -like "*.tar" } | Select-Object -First 1
            $shaAsset = $r.assets | Where-Object { $_.name -like "*.tar.sha256" -or $_.name -like "*.sha256" } | Select-Object -First 1
            if ($tarAsset) {
                $pubDate = ""
                if ($r.published_at -and $r.published_at.Length -ge 10) {
                    $pubDate = $r.published_at.Substring(0, 10)
                } elseif ($r.created_at -and $r.created_at.Length -ge 10) {
                    $pubDate = $r.created_at.Substring(0, 10)
                }
                $entry = [PSCustomObject]@{
                    Tag        = $r.tag_name
                    Name       = $r.name
                    PreRelease = [bool]$r.prerelease
                    Date       = $pubDate
                    TarName    = $tarAsset.name
                    TarUrl     = $tarAsset.browser_download_url
                    ShaUrl     = if ($shaAsset) { $shaAsset.browser_download_url } else { $null }
                    ShaHash    = $null
                }
            } else {
                continue
            }
        }
        $parsed += $entry
        $typeStr = if ($entry.PreRelease) { "[RC/Pre-Release]" } else { "[STABLE]" }
        $dateStr = if ($entry.Date) { "($($entry.Date))" } else { "" }
        $items += "$($entry.Tag) $dateStr $typeStr - $($entry.TarName)"
    }

    $Script:FetchedReleases = $parsed

    $cmbReleases.ItemsSource = $items
    if ($items.Count -gt 0) {
        $cmbReleases.SelectedIndex = 0
        $first = $Script:FetchedReleases[0]
        if ($first.ShaHash) {
            $txtExpectedSHA.Text = $first.ShaHash
        }
    }
    Write-GuiLog "✅ Loaded $($items.Count) release(s) ($Source)."
}

# ----------------- EVENT: FETCH GITHUB RELEASES -----------------
$btnFetchReleases.Add_Click({
    $repo = $Script:GitHubRepo
    Write-GuiLog "Querying GitHub ($repo) for releases..."
    $loadedOk = $false
    try {
        $apiUrl = "https://api.github.com/repos/$repo/releases"
        $jsonStr = $null
        try {
            $wc = New-Object System.Net.WebClient
            $wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EntryNav2-Windows-Manager")
            $wc.Encoding = [System.Text.Encoding]::UTF8
            $jsonStr = $wc.DownloadString($apiUrl)
        } catch {
            $headers = @{ "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EntryNav2-Windows-Manager" }
            $jsonStr = (Invoke-RestMethod -Uri $apiUrl -Headers $headers -UseBasicParsing -TimeoutSec 12 | ConvertTo-Json -Depth 6)
        }

        if ($jsonStr) {
            $ghReleases = $jsonStr | ConvertFrom-Json
            if ($ghReleases -and $ghReleases.Count -gt 0) {
                Load-ReleasesToUI -Releases $ghReleases -Source "GitHub Live"
                $loadedOk = $true
            }
        }
    } catch {
        Write-GuiLog "⚠️ GitHub API request failed: $($_.Exception.Message)"
    }

    if (-not $loadedOk) {
        Write-GuiLog "ℹ️ Retaining built-in verified catalogue."
        Load-ReleasesToUI -Releases $Script:BuiltInCatalogue -Source "Built-in Offline"
    }
})

# ----------------- EVENT: COMBOBOX SELECTION CHANGED -----------------
$cmbReleases.Add_SelectionChanged({
    $idx = $cmbReleases.SelectedIndex
    if ($idx -ge 0 -and $idx -lt $Script:FetchedReleases.Count) {
        $rel = $Script:FetchedReleases[$idx]
        if ($rel.ShaHash) {
            $txtExpectedSHA.Text = $rel.ShaHash
        }
        if ($rel.ShaUrl) {
            $shaUrl = $rel.ShaUrl
            try {
                $wc = New-Object System.Net.WebClient
                $wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EntryNav2-Windows-Manager")
                $shaRaw = $wc.DownloadString($shaUrl).Trim()
                $cand = ($shaRaw -split '\s+')[0].Trim().ToLower()
                if ($cand.Length -eq 64) { $txtExpectedSHA.Text = $cand }
            } catch {}
        }
    }
})

# ----------------- EVENT: BROWSE LOCAL TAR -----------------
$btnBrowseLocal.Add_Click({
    $dlg = New-Object Microsoft.Win32.OpenFileDialog
    $dlg.Filter = "Tar archives (*.tar)|*.tar|All files (*.*)|*.*"
    if ($dlg.ShowDialog()) {
        $cmbReleases.ItemsSource = @("Local: $($dlg.FileName)")
        $cmbReleases.SelectedIndex = 0
        $shaCand = "$($dlg.FileName).sha256"
        if (Test-Path $shaCand) {
            $txtExpectedSHA.Text = ((Get-Content $shaCand -Raw).Trim() -split '\s+')[0]
        }
    }
})

# ----------------- EVENT: START SAFE UPDATE / FLASH -----------------
$btnStartUpdate.Add_Click({
    $targetIP = $txtCarIP.Text.Trim()
    $targetPort = [int]$txtPort.Text.Trim()
    $targetUser = $txtUser.Text.Trim()
    $targetPass = $txtPass.Password
    $expectedSha = $txtExpectedSHA.Text.Trim().ToLower()

    if (-not $expectedSha) {
        [System.Windows.MessageBox]::Show("Please fetch or enter the expected SHA-256 hash first.", "SHA-256 Required", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Warning)
        return
    }

    $confirm = [System.Windows.MessageBox]::Show("Are you sure you want to update/flash EntryNav2 Android Auto?`n`nEnsure car ignition is ON and parked.", "Confirm Flash", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Question)
    if ($confirm -ne [System.Windows.MessageBoxResult]::Yes) { return }

    $btnStartUpdate.IsEnabled = $false
    Update-FlashProgress -Step 0 -StatusText "Starting..."

    try {
        Write-GuiLog "=========================================================="
        Write-GuiLog "🚀 INITIATING SAFE ENTRYNAV2 FLASH PROCEDURE"
        Write-GuiLog "=========================================================="

        $selectedItem = [string]$cmbReleases.SelectedItem
        $localTar = ""

        if ($selectedItem -like "Local: *") {
            $localTar = $selectedItem.Substring(7).Trim()
            Update-FlashProgress -Step 1 -StatusText "Step 1/8: Selected local archive"
        } else {
            $idx = $cmbReleases.SelectedIndex
            if ($idx -lt 0 -or $idx -ge $Script:FetchedReleases.Count) {
                Write-GuiLog "❌ No release selected."
                Update-FlashProgress -Step 0 -StatusText "Failed: No release"
                return
            }
            $rel = $Script:FetchedReleases[$idx]
            $localTar = Join-Path $env:TEMP $rel.TarName
            
            $needDownload = $true
            if (Test-Path $localTar) {
                $existingSha = (Get-FileHash -Path $localTar -Algorithm SHA256).Hash.ToLower()
                if ($existingSha -eq $expectedSha) {
                    Write-GuiLog "[Step 1/8] Using verified cached archive: $localTar"
                    Update-FlashProgress -Step 1 -StatusText "Step 1/8: Archive cached"
                    $needDownload = $false
                } else {
                    Remove-Item $localTar -Force -ErrorAction SilentlyContinue
                }
            }

            if ($needDownload) {
                Write-GuiLog "[Step 1/8] Downloading $($rel.TarName)..."
                Update-FlashProgress -Step 1 -StatusText "Step 1/8: Downloading..."
                try {
                    $wc = New-Object System.Net.WebClient
                    $wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EntryNav2-Windows-Manager")
                    $wc.DownloadFile($rel.TarUrl, $localTar)
                } catch {
                    Invoke-WebRequest -Uri $rel.TarUrl -OutFile $localTar -UseBasicParsing -TimeoutSec 90
                }
                Write-GuiLog "   [download] 100% Download completed."
            }
        }

        $tarName = [System.IO.Path]::GetFileName($localTar)

        # 1. Local SHA-256 check
        Write-GuiLog "[Step 2/8] Computing local SHA-256 hash..."
        Update-FlashProgress -Step 2 -StatusText "Step 2/8: Verifying SHA-256..."
        $calcSha = (Get-FileHash -Path $localTar -Algorithm SHA256).Hash.ToLower()
        Write-GuiLog "   Expected SHA-256:   $expectedSha"
        Write-GuiLog "   Calculated SHA-256: $calcSha"
        if ($calcSha -ne $expectedSha) {
            Write-GuiLog "❌ SHA-256 verification failed! Corrupted download. Halting."
            Update-FlashProgress -Step 0 -StatusText "Failed: SHA-256 mismatch"
            return
        }
        Write-GuiLog "✅ SHA-256 verified successfully."

        # 2. Pre-flight checks on car
        Write-GuiLog "[Step 3/8] Connecting to car and running pre-flight checks..."
        Update-FlashProgress -Step 3 -StatusText "Step 3/8: Pre-flight checks..."
        $resVer = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "head -n 1 /etc/version" -Port $targetPort
        if ($resVer.ExitCode -ne 0) {
            Write-GuiLog "❌ Cannot reach car via SSH: $($resVer.Error)"
            Update-FlashProgress -Step 0 -StatusText "Failed: SSH unreachable"
            return
        }
        Write-GuiLog "✅ Car firmware: $($resVer.Output.Trim())"

        # Check free space on /
        $resDf = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "df -k /" -Port $targetPort
        $freeKb = 0
        $match = [regex]::Match($resDf.Output, '(\d+)\s+\d+%\s+/')
        if ($match.Success) {
            [int]::TryParse($match.Groups[1].Value, [ref]$freeKb) | Out-Null
        } else {
            # Fallback token parsing
            $tokens = ($resDf.Output.Trim() -split '\s+')
            for ($i = 0; $i -lt $tokens.Count; $i++) {
                if ($tokens[$i] -eq "/" -and $i -ge 2) {
                    [int]::TryParse($tokens[$i - 2], [ref]$freeKb) | Out-Null
                }
            }
        }
        Write-GuiLog "   Available space on /: $freeKb KB ($([math]::Round($freeKb / 1024, 1)) MB)"
        if ($freeKb -lt 16384) {
            Write-GuiLog "❌ Insufficient flash storage on / (< 16 MB). Cannot proceed."
            Update-FlashProgress -Step 0 -StatusText "Failed: Low flash space"
            return
        }
        Write-GuiLog "✅ Sufficient flash storage verified."

        # Check running processes
        $resPid = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "pidof aa-supervisor entry-aad" -Port $targetPort
        if ($resPid.Output.Trim()) {
            Write-GuiLog "⚠️ Android Auto is running (PID $($resPid.Output.Trim())). Stopping cleanly..."
            Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "killall aa-supervisor entry-aad 2>/dev/null; sleep 1; killall -9 aa-supervisor entry-aad 2>/dev/null" -Port $targetPort | Out-Null
        }

        # 3. SCP upload to car RAM-disk /tmp
        Write-GuiLog "[Step 4/8] Uploading $tarName to car RAM-disk /tmp/..."
        Update-FlashProgress -Step 4 -StatusText "Step 4/8: Uploading to car..."
        $resScp = Invoke-CarSCP -IP $targetIP -User $targetUser -Pass $targetPass -LocalFile $localTar -RemoteDest "/tmp/" -Port $targetPort
        if ($resScp.ExitCode -ne 0) {
            Write-GuiLog "❌ SCP Upload failed: $($resScp.Error)"
            Update-FlashProgress -Step 0 -StatusText "Failed: SCP upload"
            return
        }
        Write-GuiLog "✅ Archive successfully uploaded to /tmp/."

        # Inspect folder inside archive
        $vStr = "current"
        if ($tarName -match '(?:entrynav2-android-auto|entry-aad)-([0-9a-zA-Z\.\-]+)-armhf\.tar') {
            $vStr = $Matches[1]
        }
        $folderPrefix = if ($tarName -like "*entrynav2*") { "entrynav2-android-auto" } else { "entry-aad" }
        $extractedFolder = "/tmp/$folderPrefix-$vStr"

        # 4. Unpack in /tmp and verify MD5SUMS
        Write-GuiLog "[Step 5/8] Extracting archive and verifying MD5 on car..."
        Update-FlashProgress -Step 5 -StatusText "Step 5/8: In-car MD5 check..."
        $cmdUnpack = "cd /tmp && rm -rf $folderPrefix-$vStr && tar -xvf $tarName && cd $folderPrefix-$vStr && md5sum -c MD5SUMS"
        $resMd5 = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command $cmdUnpack -Port $targetPort
        if ($resMd5.ExitCode -ne 0 -or $resMd5.Output -like "*FAILED*") {
            Write-GuiLog "❌ MD5SUMS check failed on car! Archive corrupted in transit."
            Update-FlashProgress -Step 0 -StatusText "Failed: MD5 mismatch"
            return
        }
        Write-GuiLog "✅ In-car MD5 validation passed."

        # 5. Dynamic Linker & Symbol check
        Write-GuiLog "[Step 6/8] Verifying car shared libraries & symbol resolution..."
        Update-FlashProgress -Step 6 -StatusText "Step 6/8: Linker check..."
        $cmdLinker = @"
export L=/usr/local/lib:/opt/hmi/lib:/usr/lib:/lib
cd $extractedFolder
for f in opt/aa/entry-aad opt/aa/aa-supervisor opt/hmi/data/ro/Plugins/EntryAad/libEntryAad.so; do
    if [ -f "`$f" ]; then
        echo "Checking `$f..."
        LD_TRACE_LOADED_OBJECTS=1 LD_WARN=yes LD_BIND_NOW=yes LD_LIBRARY_PATH=`$L /lib/ld-linux-armhf.so.3 ./`$f 2>&1 |
            grep -E 'not found|undefined symbol|not defined in file'
    fi
done
"@
        $resLinker = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command $cmdLinker -Port $targetPort
        if ($resLinker.Output.Trim() -and ($resLinker.Output -match 'not found|undefined symbol|not defined in file')) {
            Write-GuiLog "❌ Missing shared library or unresolved symbols:`n$($resLinker.Output)"
            Write-GuiLog "❌ Refusing to install to protect head unit."
            Update-FlashProgress -Step 0 -StatusText "Failed: Linker check"
            return
        }
        Write-GuiLog "✅ Dynamic linker resolution passed."

        # 6. Rehearsal compatibility dry-run (aa-supervisor --compat)
        Write-GuiLog "[Step 7/8] Running compatibility dry-run (aa-supervisor --compat)..."
        Update-FlashProgress -Step 7 -StatusText "Step 7/8: Compatibility test..."
        $cmdCompat = @"
export L=/usr/local/lib:/opt/hmi/lib:/usr/lib:/lib
cd $extractedFolder
LD_LIBRARY_PATH=`$L XDG_RUNTIME_DIR=/run/system/0 WAYLAND_DISPLAY=wayland-0 HOME=/tmp \
    busybox timeout -t 60 ./opt/aa/aa-supervisor --compat
"@
        $resCompat = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command $cmdCompat -Port $targetPort
        if ($resCompat.Output -like "*@block*") {
            Write-GuiLog "❌ Unit incompatible. Installation blocked."
            Update-FlashProgress -Step 0 -StatusText "Failed: Incompatible unit"
            return
        }
        Write-GuiLog "✅ Compatibility checks passed."

        # 7. Flash Installation (atomic write, version stamp & remount)
        Write-GuiLog "[Step 8/8] Performing atomic flash install..."
        Update-FlashProgress -Step 8 -StatusText "Step 8/8: Installing to flash..."
        $cmdInstall = @"
cd $extractedFolder && \
echo "Remounting / rw..." && \
mount -o remount,rw / && \
mkdir -p /opt/hmi/data/ro/Plugins/EntryAad /opt/aa /var/local/data/AA && \
rm -f /opt/hmi/data/ro/Plugins/EntryAad/* /opt/aa/* && \
echo "Copying plugins and binaries..." && \
cp -v opt/hmi/data/ro/Plugins/EntryAad/* /opt/hmi/data/ro/Plugins/EntryAad/ && \
cp -v opt/aa/* /opt/aa/ && \
chmod 755 /opt/aa/entry-aad /opt/aa/aa-supervisor /opt/hmi/data/ro/Plugins/EntryAad/libEntryAad.so && \
touch /opt/aa/.installed-by-entryaad /opt/hmi/data/ro/Plugins/EntryAad/.installed-by-entryaad && \
printf "version=$folderPrefix-$vStr\ntag=$folderPrefix-$vStr\nsha256=$expectedSha\ninstalled_at=`$(date -Iseconds 2>/dev/null || date)\n" > /opt/aa/.version && \
cp /opt/aa/.version /var/local/data/AA/installed_version && \
echo "Syncing flash..." && \
sync && \
(mount -o remount,ro / 2>/dev/null || true) && \
echo "Flash write completed."
"@
        $resInstall = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command $cmdInstall -Port $targetPort
        Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "sync; mount -o remount,ro / 2>/dev/null || true" -Port $targetPort | Out-Null

        if ($resInstall.ExitCode -ne 0) {
            Write-GuiLog "❌ Flash install copy failed: $($resInstall.Error)"
            Update-FlashProgress -Step 0 -StatusText "Failed: Flash write"
            return
        }

        # Post-install flash verification
        $cmdPostVerify = "cd / && md5sum -c $extractedFolder/MD5SUMS"
        $resPost = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command $cmdPostVerify -Port $targetPort
        if ($resPost.ExitCode -ne 0 -or $resPost.Output -like "*FAILED*") {
            Write-GuiLog "❌ Post-install MD5 verification failed on flash!"
            Update-FlashProgress -Step 0 -StatusText "Failed: Flash MD5"
            return
        }
        Write-GuiLog "✅ Flash files verified identical to MD5SUMS!"

        # Optional vehicle profile
        $model = $txtModel.Text.Trim()
        $year = $txtYear.Text.Trim()
        if ($model -or $year) {
            if (-not $model) { $model = "iDrive" }
            if (-not $year) { $year = "2019" }
            Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "mkdir -p /var/local/data/AA && printf 'model=$model\nyear=$year\n' > /var/local/data/AA/vehicle" -Port $targetPort | Out-Null
        }

        # Cleanup /tmp
        Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "rm -rf $extractedFolder /tmp/$tarName" -Port $targetPort | Out-Null

        Update-FlashProgress -Step 8 -StatusText "✅ Done / Completed"
        Write-GuiLog "=========================================================="
        Write-GuiLog "🎉 INSTALLATION / UPDATE COMPLETED SUCCESSFULLY!"
        Write-GuiLog "   Installed Version ID: $folderPrefix-$vStr"
        Write-GuiLog "   Please reboot head unit and start Android Auto in iDrive."
        Write-GuiLog "=========================================================="

        Retrieve-InstalledVersionInfo -ShowDialog $false

        $askReboot = [System.Windows.MessageBox]::Show("Installation completed and verified on flash!`n`nWould you like to reboot the head unit now?", "Update Complete", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Information)
        if ($askReboot -eq [System.Windows.MessageBoxResult]::Yes) {
            Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "reboot" -Port $targetPort | Out-Null
            Write-GuiLog "Reboot signal sent to head unit."
        }
    } finally {
        $btnStartUpdate.IsEnabled = $true
    }
})

# ----------------- EVENT: LOGS MANAGEMENT -----------------
function Check-LoggingStatus {
    param([switch]$Silent)
    $targetIP = $txtCarIP.Text.Trim()
    $targetPort = [int]$txtPort.Text.Trim()
    $targetUser = $txtUser.Text.Trim()
    $targetPass = $txtPass.Password

    if (-not $Silent) { Write-GuiLog "Checking maintenance logging status on car..." }
    $resM = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "test -f /var/local/data/AA/maintenance && echo ENABLED || echo DISABLED" -Port $targetPort
    $isMaint = ($resM.Output -like "*ENABLED*")
    $resLs = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "ls -lh /var/local/data/AA/app.log /var/local/data/AA/app.old.log /tmp/entry-aa-service.log 2>/dev/null" -Port $targetPort

    $files = @()
    if ($resLs.ExitCode -eq 0 -and $resLs.Output.Trim()) {
        foreach ($l in ($resLs.Output -split "`r?`n")) {
            $parts = ($l.Trim() -split '\s+')
            if ($parts.Count -ge 9) {
                $fName = Split-Path $parts[8] -Leaf
                $fSize = $parts[4]
                $files += "$fName ($fSize)"
            }
        }
    }

    if ($window -and $window.Dispatcher) {
        $window.Dispatcher.Invoke([Action]{
            if ($txtLogStatus) {
                if ($resM.ExitCode -ne 0) {
                    $txtLogStatus.Text = "● Logging Status: Offline / Unreachable"
                    $txtLogStatus.Foreground = [System.Windows.Media.Brushes]::Red
                } elseif ($isMaint) {
                    $txtLogStatus.Text = "● Logging Status: ENABLED (/var/local/data/AA/maintenance active)"
                    $txtLogStatus.Foreground = [System.Windows.Media.Brushes]::LimeGreen
                } else {
                    $txtLogStatus.Text = "○ Logging Status: DISABLED (Normal mode - no logs written)"
                    $txtLogStatus.Foreground = [System.Windows.Media.Brushes]::LightCoral
                }
            }
            if ($txtLogFilesOnCar) {
                $fStr = if ($files.Count -gt 0) { ($files -join ", ") } else { "None found on car" }
                $txtLogFilesOnCar.Text = "Flag: /var/local/data/AA/maintenance | Diagnostic files: $fStr"
            }
        })
    }

    if (-not $Silent) {
        if ($resM.ExitCode -ne 0) {
            Write-GuiLog "⚠️ Head unit unreachable at $targetIP to verify maintenance logging."
        } else {
            Write-GuiLog "🔍 Maintenance logging is $(if ($isMaint) { 'ENABLED' } else { 'DISABLED' }) on car."
        }
    }
}

if ($btnCheckLogStatus) {
    $btnCheckLogStatus.Add_Click({ Check-LoggingStatus })
}

$btnEnableLogs.Add_Click({
    $targetIP = $txtCarIP.Text.Trim()
    $targetPort = [int]$txtPort.Text.Trim()
    $targetUser = $txtUser.Text.Trim()
    $targetPass = $txtPass.Password

    Write-GuiLog "Enabling maintenance logging on car..."
    $res = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "mkdir -p /var/local/data/AA && touch /var/local/data/AA/maintenance" -Port $targetPort
    if ($res.ExitCode -eq 0) {
        Write-GuiLog "✅ Maintenance logging ENABLED (/var/local/data/AA/maintenance created)."
        Check-LoggingStatus
    } else {
        Write-GuiLog "❌ Failed: $($res.Error)"
    }
})

$btnDisableLogs.Add_Click({
    $targetIP = $txtCarIP.Text.Trim()
    $targetPort = [int]$txtPort.Text.Trim()
    $targetUser = $txtUser.Text.Trim()
    $targetPass = $txtPass.Password

    Write-GuiLog "Disabling maintenance logging and purging log files..."
    $cmd = "rm -f /var/local/data/AA/maintenance /var/local/data/AA/app.log /var/local/data/AA/app.old.log /tmp/entry-aa-service.log"
    $res = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command $cmd -Port $targetPort
    if ($res.ExitCode -eq 0) {
        Write-GuiLog "✅ Logs purged and maintenance logging disabled."
        Check-LoggingStatus
    } else {
        Write-GuiLog "❌ Failed: $($res.Error)"
    }
})

$btnPullLogs.Add_Click({
    $targetIP = $txtCarIP.Text.Trim()
    $targetPort = [int]$txtPort.Text.Trim()
    $targetUser = $txtUser.Text.Trim()
    $targetPass = $txtPass.Password

    $ts = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $targetDir = Join-Path $PSScriptRoot "BMW_Logs\Logs_$ts"
    [System.IO.Directory]::CreateDirectory($targetDir) | Out-Null
    $Script:LastPulledFolder = $targetDir

    Write-GuiLog "Pulling logs from EntryNav2 to: $targetDir"

    $files = @(
        @{ Remote = "/var/local/data/AA/app.log"; Name = "app.log" },
        @{ Remote = "/var/local/data/AA/app.old.log"; Name = "app.old.log" },
        @{ Remote = "/tmp/entry-aa-service.log"; Name = "entry-aa-service.log" },
        @{ Remote = "/var/local/data/AA/app-guard"; Name = "app-guard" },
        @{ Remote = "/var/local/data/AA/vehicle"; Name = "vehicle" }
    )

    $pulledCount = 0
    $previewText = ""

    foreach ($f in $files) {
        $dest = Join-Path $targetDir $f.Name
        $res = Invoke-CarSCPDownload -IP $targetIP -User $targetUser -Pass $targetPass -RemoteFile $f.Remote -LocalDest $dest -Port $targetPort
        if (Test-Path $dest -and (Get-Item $dest).Length -gt 0) {
            $pulledCount++
            $len = (Get-Item $dest).Length
            Write-GuiLog "   [Pulled] $($f.Name) ($len bytes)"
            $previewText += "========================================`r`n"
            $previewText += "FILE: $($f.Name) ($len bytes)`r`n"
            $previewText += "========================================`r`n"
            $lines = Get-Content $dest -Tail 100 -ErrorAction SilentlyContinue
            $previewText += ($lines -join "`r`n") + "`r`n`r`n"
        }
    }

    if ($pulledCount -gt 0) {
        $txtLogsPreview.Text = $previewText
        Write-GuiLog "✅ Pulled $pulledCount log file(s)."
    } else {
        Write-GuiLog "⚠️ No log files found on car. (Ensure maintenance logging was enabled and Android Auto was started)."
    }
})

$btnOpenLogsFolder.Add_Click({
    if ($Script:LastPulledFolder -and (Test-Path $Script:LastPulledFolder)) {
        Start-Process explorer.exe -ArgumentList "`"$Script:LastPulledFolder`""
    } else {
        [System.Windows.MessageBox]::Show("No logs pulled yet. Click 'Pull All Logs to PC' first.", "Logs", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Information)
    }
})

# ----------------- EVENT: QUICK ACTIONS -----------------
$btnCheckCarStatus.Add_Click({
    $targetIP = $txtCarIP.Text.Trim()
    $targetPort = [int]$txtPort.Text.Trim()
    $targetUser = $txtUser.Text.Trim()
    $targetPass = $txtPass.Password

    Write-GuiLog "Checking car status..."
    $resV = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "head -n 1 /etc/version" -Port $targetPort
    $resP = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "pidof HmiMain3D aa-supervisor entry-aad" -Port $targetPort
    $resM = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "grep -c libEntryAad /proc/`$(pidof HmiMain3D)/maps 2>/dev/null" -Port $targetPort
    $resDf = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "df -h /" -Port $targetPort
    Write-GuiLog "[Status] Firmware: $($resV.Output.Trim())"
    Write-GuiLog "[Status] Running Processes (HmiMain3D / aa-supervisor / entry-aad): $($resP.Output.Trim())"
    Write-GuiLog "[Status] iDrive HMI libEntryAad Loaded Mappings: $($resM.Output.Trim())"
    Write-GuiLog "[Status] Flash Storage:`n$($resDf.Output.Trim())"
})

$btnResetAppGuard.Add_Click({
    $targetIP = $txtCarIP.Text.Trim()
    $targetPort = [int]$txtPort.Text.Trim()
    $targetUser = $txtUser.Text.Trim()
    $targetPass = $txtPass.Password

    Write-GuiLog "Clearing app-guard and disable flags..."
    Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "rm -f /var/local/data/AA/app.disable /var/local/data/AA/app-guard" -Port $targetPort | Out-Null
    Write-GuiLog "✅ App guard cleared."
})

$btnRebootHU.Add_Click({
    $confirm = [System.Windows.MessageBox]::Show("Are you sure you want to reboot the BMW head unit?", "Reboot Head Unit", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Warning)
    if ($confirm -eq [System.Windows.MessageBoxResult]::Yes) {
        $targetIP = $txtCarIP.Text.Trim()
        $targetPort = [int]$txtPort.Text.Trim()
        $targetUser = $txtUser.Text.Trim()
        $targetPass = $txtPass.Password
        Write-GuiLog "Sending reboot command to head unit..."
        Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "reboot" -Port $targetPort | Out-Null
        Write-GuiLog "Reboot initiated."
    }
})

$btnUninstallAA.Add_Click({
    $confirm = [System.Windows.MessageBox]::Show("Are you sure you want to completely uninstall EntryNav2 Android Auto from the car?`n`nThis removes /opt/aa and plugins.", "CONFIRM UNINSTALL", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Exclamation)
    if ($confirm -eq [System.Windows.MessageBoxResult]::Yes) {
        $targetIP = $txtCarIP.Text.Trim()
        $targetPort = [int]$txtPort.Text.Trim()
        $targetUser = $txtUser.Text.Trim()
        $targetPass = $txtPass.Password
        Write-GuiLog "Uninstalling EntryNav2 Android Auto from head unit..."
        $cmd = @"
mount -o remount,rw / && \
rm -rf /opt/hmi/data/ro/Plugins/EntryAad /opt/aa && \
sync && \
(mount -o remount,ro / 2>/dev/null || true) && \
rm -rf /var/local/data/AA
"@
        $res = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command $cmd -Port $targetPort
        Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "sync; mount -o remount,ro / 2>/dev/null || true" -Port $targetPort | Out-Null
        if ($res.ExitCode -eq 0) {
            Write-GuiLog "✅ Android Auto successfully uninstalled from car. Reboot head unit."
            if ($lblCurrentInstalled) {
                $lblCurrentInstalled.Text = "Android Auto: NOT INSTALLED"
                $lblCurrentInstalled.Foreground = [System.Windows.Media.Brushes]::Red
            }
        } else {
            Write-GuiLog "❌ Uninstall failed: $($res.Error)"
        }
    }
})

# ----------------- EVENT: FLAGS READ & SAVE -----------------
$btnReadSettings.Add_Click({
    $targetIP = $txtCarIP.Text.Trim()
    $targetPort = [int]$txtPort.Text.Trim()
    $targetUser = $txtUser.Text.Trim()
    $targetPass = $txtPass.Password

    Write-GuiLog "Reading settings flags from /var/local/data/AA..."
    $res = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command "ls /var/local/data/AA 2>/dev/null" -Port $targetPort
    if ($res.ExitCode -ne 0) {
        Write-GuiLog "⚠️ Could not read flags: Head unit unreachable at $targetIP. Local settings preserved."
        return
    }
    $files = ($res.Output -split '\s+')
    $chkAutostart.IsChecked   = ($files -contains "autostart")
    $chkUsb.IsChecked         = ($files -contains "usb")
    $chkEntryDirect.IsChecked = ($files -contains "entry-direct")
    $chkKombiOff.IsChecked    = ($files -contains "kombi-off")
    $chkKombiSingle.IsChecked = ($files -contains "kombi-single-maneuver")
    $chkGpsPhone.IsChecked    = ($files -contains "gps-telephone")
    if ($chkMaintenance) {
        $chkMaintenance.IsChecked = ($files -contains "maintenance")
    }
    Write-GuiLog "✅ Settings flags refreshed from car."
})

$btnSaveSettings.Add_Click({
    $targetIP = $txtCarIP.Text.Trim()
    $targetPort = [int]$txtPort.Text.Trim()
    $targetUser = $txtUser.Text.Trim()
    $targetPass = $txtPass.Password

    $cmds = @("mkdir -p /var/local/data/AA")
    if ($chkAutostart.IsChecked)   { $cmds += "touch /var/local/data/AA/autostart" } else { $cmds += "rm -f /var/local/data/AA/autostart" }
    if ($chkUsb.IsChecked)         { $cmds += "touch /var/local/data/AA/usb" } else { $cmds += "rm -f /var/local/data/AA/usb" }
    if ($chkEntryDirect.IsChecked) { $cmds += "touch /var/local/data/AA/entry-direct" } else { $cmds += "rm -f /var/local/data/AA/entry-direct" }
    if ($chkKombiOff.IsChecked)    { $cmds += "touch /var/local/data/AA/kombi-off" } else { $cmds += "rm -f /var/local/data/AA/kombi-off" }
    if ($chkKombiSingle.IsChecked) { $cmds += "touch /var/local/data/AA/kombi-single-maneuver" } else { $cmds += "rm -f /var/local/data/AA/kombi-single-maneuver" }
    if ($chkGpsPhone.IsChecked)    { $cmds += "touch /var/local/data/AA/gps-telephone" } else { $cmds += "rm -f /var/local/data/AA/gps-telephone" }
    if ($chkMaintenance -and $chkMaintenance.IsChecked) { $cmds += "touch /var/local/data/AA/maintenance" } else { $cmds += "rm -f /var/local/data/AA/maintenance" }

    $fullCmd = $cmds -join " && "
    Write-GuiLog "Saving settings flags to car..."
    $res = Invoke-CarSSH -IP $targetIP -User $targetUser -Pass $targetPass -Command $fullCmd -Port $targetPort
    if ($res.ExitCode -eq 0) {
        Write-GuiLog "✅ Settings flags successfully saved to /var/local/data/AA."
        Check-LoggingStatus -Silent
    } else {
        Write-GuiLog "❌ Failed to save settings: $($res.Error)"
    }
})

# Auto fetch releases on window loaded
$window.Add_Loaded({
    Load-ReleasesToUI -Releases $Script:BuiltInCatalogue -Source "Built-in"
    $btnFetchReleases.RaiseEvent((New-Object System.Windows.RoutedEventArgs([System.Windows.Controls.Button]::ClickEvent)))
})

# Show the window
$window.ShowDialog() | Out-Null
[System.Environment]::Exit(0)
