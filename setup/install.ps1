# BazBeans Smart Installer for Windows
# This script detects the installation method and adapts accordingly

param(
    [switch]$System,
    [switch]$Force
)

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Green"
}

function Write-Warn {
    param([string]$Message)
    Write-ColorOutput "[WARN] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

# Check if running with admin privileges for system install
if ($System -and (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))) {
    Write-Error "System installation requires administrator privileges"
    Write-Info "Please run PowerShell as Administrator or use user installation"
    exit 1
}

# Determine installation paths
if ($System) {
    $BinDir = "$env:ProgramFiles\BazBeans"
    $ConfigDir = "$env:ProgramData\BazBeans"
    $BazBeansHome = "$env:ProgramFiles\BazBeans"
} else {
    $BinDir = "$env:LOCALAPPDATA\BazBeans\bin"
    $ConfigDir = "$env:APPDATA\BazBeans"
    $BazBeansHome = "$env:LOCALAPPDATA\BazBeans"
}

# Detect installation method
Write-Info "Detecting installation method..."
$InstallMode = "unknown"

# Check if bazbeans is already installed via package manager (pip/pipx/conda)
if (Get-Command pipx -ErrorAction SilentlyContinue) {
    try {
        $pipxList = pipx list 2>$null | Out-String
        if ($pipxList -match "bazbeans") {
            Write-Info "BazBeans detected in pipx"
            $InstallMode = "package_manager"
        }
    } catch {}
}

if ($InstallMode -eq "unknown") {
    try {
        $null = python -c "import bazbeans" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Info "BazBeans Python package detected (installed via pip/conda)"
            $InstallMode = "package_manager"
        }
    } catch {
        # Try alternative import
        try {
            $null = python -c "import src.control_cli" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Info "BazBeans Python package detected (installed via pip/conda)"
                $InstallMode = "package_manager"
            }
        } catch {}
    }
}

# Check for existing standalone installation
if ($InstallMode -eq "unknown") {
    if ((Test-Path $BazBeansHome) -or (Test-Path "$env:ProgramFiles\BazBeans")) {
        Write-Info "Existing standalone installation detected"
        $InstallMode = "standalone"
    } else {
        Write-Info "No existing installation found - will perform standalone installation"
        $InstallMode = "fresh"
    }
}

# Set BAZBEANS_HOME environment variable
Write-Info "Setting BAZBEANS_HOME environment variable..."
try {
    if ($System) {
        [Environment]::SetEnvironmentVariable("BAZBEANS_HOME", $BazBeansHome, "Machine")
        $verify = [Environment]::GetEnvironmentVariable("BAZBEANS_HOME", "Machine")
    } else {
        [Environment]::SetEnvironmentVariable("BAZBEANS_HOME", $BazBeansHome, "User")
        $verify = [Environment]::GetEnvironmentVariable("BAZBEANS_HOME", "User")
    }
    if ($verify -eq $BazBeansHome) {
        Write-Info "BAZBEANS_HOME set persistently to $BazBeansHome"
    } else {
        Write-Warn "Failed to verify BAZBEANS_HOME was set persistently"
    }
} catch {
    Write-Warn "Failed to set BAZBEANS_HOME persistently: $_"
}

# Also set for current session
$env:BAZBEANS_HOME = $BazBeansHome
Write-Info "BAZBEANS_HOME set for current session to $BazBeansHome"

# Create directories
Write-Info "Creating directories..."
New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BazBeansSource = Split-Path -Parent $ScriptDir

# Check if bazbeans source exists
if (-not (Test-Path $BazBeansSource)) {
    Write-Error "BazBeans source not found at $BazBeansSource"
    exit 1
}

# Function to create CLI wrapper for package manager installations
function Create-PackageManagerWrapper {
    Write-Info "Creating CLI wrapper for package manager installation..."
    
    # Create batch file wrapper
    $BazBeansBat = @"
@echo off
REM BazBeans CLI Wrapper for Package Manager Installation

REM Find configuration file
set CONFIG_LOCATIONS=%BAZBEANS_CONFIG% "%USERPROFILE%\.bazbeans\config.yaml" "%ProgramData%\BazBeans\config.yaml" ".\bazbeans.yaml"

set CONFIG_FILE=
for %%f in (%CONFIG_LOCATIONS%) do (
    if exist "%%f" (
        set CONFIG_FILE=%%f
        goto :found
    )
)
:found

REM Extract redis_url from config if available
set REDIS_URL=
if defined CONFIG_FILE (
    for /f "tokens=2 delims=:" %%a in ('findstr /R "^redis_url:" "%CONFIG_FILE%"') do (
        set REDIS_URL=%%a
    )
)

REM Clean up the redis_url
set REDIS_URL=%REDIS_URL:"=%
set REDIS_URL=%REDIS_URL: =%

REM Use environment variable if set, then config, then default
if not defined REDIS_URL (
    if defined BAZBEANS_REDIS_URL (
        set REDIS_URL=%BAZBEANS_REDIS_URL%
    ) else (
        set REDIS_URL=redis://localhost:6379/0
    )
)

REM Try to run via Python module (works with pip/pipx/conda installations)
python -c "import src.control_cli" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python -c "from src.control_cli import cli; cli()" --redis-url "%REDIS_URL%" %*
) else (
    python -c "import bazbeans.control_cli" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        python -c "from bazbeans.control_cli import cli; cli()" --redis-url "%REDIS_URL%" %*
    ) else (
        echo Error: BazBeans Python package not found
        echo Please ensure BazBeans is installed via pip, pipx, or conda
        exit /b 1
    )
)
"@
    
    $BazBeansBat | Out-File -FilePath "$BinDir\bazbeans.bat" -Encoding ASCII
    
    # Create PowerShell wrapper
    $BazBeansPS = @"
# BazBeans PowerShell Wrapper for Package Manager Installation

# Find configuration file
`$ConfigLocations = @(
    `$env:BAZBEANS_CONFIG,
    "`$env:USERPROFILE\.bazbeans\config.yaml",
    "`$env:ProgramData\BazBeans\config.yaml",
    ".\bazbeans.yaml"
)

`$ConfigFile = `$null
foreach (`$loc in `$ConfigLocations) {
    if (`$loc -and (Test-Path `$loc)) {
        `$ConfigFile = `$loc
        break
    }
}

# Extract redis_url from config if available
`$RedisUrl = ""
if (`$ConfigFile) {
    `$RedisUrl = (Select-String -Path `$ConfigFile -Pattern "^redis_url:" | ForEach-Object {
        `$_.Line -replace '.*redis_url:\s*[''"]?\s*([^''"]*)[''"]?.*', '$1'
    })
}

# Use environment variable if set, then config, then default
if (-not `$RedisUrl) {
    `$RedisUrl = `$env:BAZBEANS_REDIS_URL
    if (-not `$RedisUrl) {
        `$RedisUrl = "redis://localhost:6379/0"
    }
}

# Try to run via Python module (works with pip/pipx/conda installations)
# First try pipx (which handles its own virtual environment)
if (Get-Command pipx -ErrorAction SilentlyContinue) {
    try {
        `$pipxList = pipx list 2>`$null | Out-String
        if (`$pipxList -match "bazbeans") {
            & pipx run --spec bazbeans python -c "from src.control_cli import cli; cli()" --redis-url `$RedisUrl `$args
            exit `$LASTEXITCODE
        }
    } catch {}
}

# Try direct Python import (for pip/conda installations)
try {
    `$null = python -c "import src.control_cli" 2>`$null
    if (`$LASTEXITCODE -eq 0) {
        & python -c "from src.control_cli import cli; cli()" --redis-url `$RedisUrl `$args
        exit `$LASTEXITCODE
    }
} catch {}

try {
    `$null = python -c "import bazbeans.control_cli" 2>`$null
    if (`$LASTEXITCODE -eq 0) {
        & python -c "from bazbeans.control_cli import cli; cli()" --redis-url `$RedisUrl `$args
        exit `$LASTEXITCODE
    }
} catch {}

Write-Error "BazBeans Python package not found"
Write-Error "Please ensure BazBeans is installed via pip, pipx, or conda"
exit 1
"@
    
    $BazBeansPS | Out-File -FilePath "$BinDir\bazbeans.ps1" -Encoding UTF8
    Write-Info "CLI wrapper created successfully"
}

# Function to create CLI wrapper for standalone installations
function Create-StandaloneWrapper {
    Write-Info "Creating CLI wrapper for standalone installation..."
    
    # Create batch file wrapper
    $BazBeansBat = @"
@echo off
REM BazBeans CLI Wrapper for Standalone Installation

REM Find configuration file
set CONFIG_LOCATIONS=%BAZBEANS_CONFIG% "%USERPROFILE%\.bazbeans\config.yaml" "%ProgramData%\BazBeans\config.yaml" ".\bazbeans.yaml"

set CONFIG_FILE=
for %%f in (%CONFIG_LOCATIONS%) do (
    if exist "%%f" (
        set CONFIG_FILE=%%f
        goto :found
    )
)
:found

REM Extract redis_url from config if available
set REDIS_URL=
if defined CONFIG_FILE (
    for /f "tokens=2 delims=:" %%a in ('findstr /R "^redis_url:" "%CONFIG_FILE%"') do (
        set REDIS_URL=%%a
    )
)

REM Clean up the redis_url
set REDIS_URL=%REDIS_URL:"=%
set REDIS_URL=%REDIS_URL: =%

REM Use environment variable if set, then config, then default
if not defined REDIS_URL (
    if defined BAZBEANS_REDIS_URL (
        set REDIS_URL=%BAZBEANS_REDIS_URL%
    ) else (
        set REDIS_URL=redis://localhost:6379/0
    )
)

REM Find bazbeans installation
if not defined BAZBEANS_HOME (
    set BAZBEANS_HOME=%LOCALAPPDATA%\BazBeans
)

REM Check system location if not found in user location
if not exist "%BAZBEANS_HOME%\src\control_cli.py" (
    set BAZBEANS_HOME=%ProgramFiles%\BazBeans
)

REM Run the CLI from standalone installation
if exist "%BAZBEANS_HOME%\src\control_cli.py" (
    python -c "import sys; sys.path.insert(0, '%BAZBEANS_HOME%'); from src.control_cli import cli; cli()" --redis-url "%REDIS_URL%" %*
) else (
    echo Error: BazBeans not found at %BAZBEANS_HOME%
    echo Please reinstall BazBeans
    exit /b 1
)
"@
    
    $BazBeansBat | Out-File -FilePath "$BinDir\bazbeans.bat" -Encoding ASCII
    
    # Create PowerShell wrapper
    $BazBeansPS = @"
# BazBeans PowerShell Wrapper for Standalone Installation

# Find configuration file
`$ConfigLocations = @(
    `$env:BAZBEANS_CONFIG,
    "`$env:USERPROFILE\.bazbeans\config.yaml",
    "`$env:ProgramData\BazBeans\config.yaml",
    ".\bazbeans.yaml"
)

`$ConfigFile = `$null
foreach (`$loc in `$ConfigLocations) {
    if (`$loc -and (Test-Path `$loc)) {
        `$ConfigFile = `$loc
        break
    }
}

# Extract redis_url from config if available
`$RedisUrl = ""
if (`$ConfigFile) {
    `$RedisUrl = (Select-String -Path `$ConfigFile -Pattern "^redis_url:" | ForEach-Object {
        `$_.Line -replace '.*redis_url:\s*[''"]?\s*([^''"]*)[''"]?.*', '$1'
    })
}

# Use environment variable if set, then config, then default
if (-not `$RedisUrl) {
    `$RedisUrl = `$env:BAZBEANS_REDIS_URL
    if (-not `$RedisUrl) {
        `$RedisUrl = "redis://localhost:6379/0"
    }
}

# Find bazbeans installation
`$BazBeansHome = `$env:BAZBEANS_HOME
if (-not `$BazBeansHome) {
    `$BazBeansHome = "`$env:LOCALAPPDATA\BazBeans"
}

# Check system location if not found
if (-not (Test-Path "`$BazBeansHome\src\control_cli.py")) {
    `$BazBeansHome = "`$env:ProgramFiles\BazBeans"
}

# Run the CLI from standalone installation
if (Test-Path "`$BazBeansHome\src\control_cli.py") {
    & python -c "import sys; sys.path.insert(0, '$($BazBeansHome -replace '\\', '/')'); from src.control_cli import cli; cli()" --redis-url `$RedisUrl `$args
} else {
    Write-Error "BazBeans not found at `$BazBeansHome"
    Write-Error "Please reinstall BazBeans"
    exit 1
}
"@
    
    $BazBeansPS | Out-File -FilePath "$BinDir\bazbeans.ps1" -Encoding UTF8
    Write-Info "CLI wrapper created successfully"
}

# Handle installation based on detected mode
switch ($InstallMode) {
    "package_manager" {
        Write-Info "Installing CLI wrapper for package manager installation..."
        Create-PackageManagerWrapper
        
        # Check if entry points were created
        if (Get-Command bazbeans-cli -ErrorAction SilentlyContinue) {
            Write-Info "Entry point 'bazbeans-cli' detected - you can also use that command"
        }
    }
    
    { $_ -in "standalone", "fresh" } {
        Write-Info "Performing standalone installation..."
        
        # Create installation directory
        New-Item -ItemType Directory -Path $BazBeansHome -Force | Out-Null
        
        # Copy bazbeans source
        Write-Info "Installing BazBeans files to $BazBeansHome..."
        Copy-Item -Path "$BazBeansSource\*" -Destination "$BazBeansHome" -Recurse -Force -Exclude ".git"
        
        # Install Python dependencies only for fresh installations
        if ($InstallMode -eq "fresh") {
            Write-Info "Installing Python dependencies..."
            try {
                & pip install --user -r "$BazBeansHome\requirements.txt"
                if ($LASTEXITCODE -ne 0) {
                    Write-Warn "Some dependencies may have failed to install"
                }
            } catch {
                Write-Warn "pip not found or failed, please install Python dependencies manually:"
                Write-Warn "  pip install --user -r $BazBeansHome\requirements.txt"
            }
        } else {
            Write-Info "Skipping dependency installation (updating existing installation)"
        }
        
        # Create standalone wrapper
        Create-StandaloneWrapper
    }
    
    default {
        Write-Error "Could not determine installation method"
        exit 1
    }
}

# Install configuration file
$ConfigFile = "$ConfigDir\config.yaml"
if (-not (Test-Path $ConfigFile) -or $Force) {
    Write-Info "Installing default configuration..."
    Copy-Item -Path "$ScriptDir\bazbeans.yaml" -Destination $ConfigFile -Force
} else {
    Write-Warn "Configuration already exists at $ConfigFile"
}

# Add to PATH for user installation
if (-not $System) {
    $CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($CurrentPath -notlike "*$BinDir*") {
        Write-Info "Adding $BinDir to PATH..."
        [Environment]::SetEnvironmentVariable("PATH", "$CurrentPath;$BinDir", "User")
        Write-Info "Please restart your terminal for PATH changes to take effect"
    }
}

# Create uninstall script
$UninstallScript = @"
# BazBeans Uninstaller for Windows

param([switch]`$Force)

Write-Host "This will remove BazBeans from your system." -ForegroundColor Yellow
if (-not `$Force) {
    `$response = Read-Host "Are you sure? [y/N]"
    if (`$response -notmatch '^[Yy]$') {
        Write-Host "Uninstall cancelled." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "Removing bazbeans command..." -ForegroundColor Green
Remove-Item -Path "$BinDir\bazbeans.bat" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$BinDir\bazbeans.ps1" -Force -ErrorAction SilentlyContinue

Write-Host "Removing BazBeans files..." -ForegroundColor Green
Remove-Item -Path "$BazBeansHome" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Removing configuration..." -ForegroundColor Green
Remove-Item -Path "$ConfigDir" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "BazBeans uninstalled successfully." -ForegroundColor Green
Write-Host "Note: If installed via pip/pipx, also run: pip uninstall bazbeans" -ForegroundColor Yellow
"@

$UninstallScript | Out-File -FilePath "$BinDir\uninstall-bazbeans.ps1" -Encoding UTF8

# Test installation
Write-Info "Testing installation..."
$BazBeansBat = "$BinDir\bazbeans.bat"
if (Test-Path $BazBeansBat) {
    Write-Info "BazBeans installed successfully!"
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  bazbeans list-nodes" -ForegroundColor White
    Write-Host "  bazbeans freeze <node-id>" -ForegroundColor White
    Write-Host "  bazbeans --help" -ForegroundColor White
    Write-Host ""
    Write-Host "Configuration: $ConfigFile" -ForegroundColor Cyan
    
    if ($InstallMode -eq "package_manager") {
        Write-Host "Installation: Python package (via pip/pipx/conda)" -ForegroundColor Cyan
    } else {
        Write-Host "Installation: $BazBeansHome" -ForegroundColor Cyan
    }
    
    if (-not $System) {
        Write-Host ""
        Write-Warn "Remember to restart your terminal for PATH changes to take effect"
    }
} else {
    Write-Error "Installation failed - bazbeans command not found"
    exit 1
}