$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$raizProjeto = Split-Path -Parent $PSScriptRoot

$pythonBuild = Join-Path $PSScriptRoot '.venv-build\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonBuild)) {
    python -m venv .venv-build
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o ambiente de compilação.' }
}
& $pythonBuild -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar o pip.' }
& $pythonBuild -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar as dependências.' }

$env:PYINSTALLER_CONFIG_DIR = Join-Path $PSScriptRoot '.build-cache'
foreach ($programa in @(
    @{ Nome = 'Gerar Envios'; Script = 'gerar_envios.py' },
    @{ Nome = 'Gerar Relatorios'; Script = 'gerar_relatorios.py' }
)) {
    & $pythonBuild -m PyInstaller --noconfirm --clean --onefile --console --noupx --hidden-import openpyxl --distpath $raizProjeto --workpath build --specpath build --name $programa.Nome $programa.Script
    if ($LASTEXITCODE -ne 0) { throw "Falha ao compilar $($programa.Nome)." }
}
Write-Host 'Os dois executáveis estão na pasta do projeto.'
