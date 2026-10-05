$ErrorActionPreference = "Stop"
dotnet publish "$PSScriptRoot/Jarvis.Native/Jarvis.Native.csproj" -c Release
Write-Host "JARVIS native build complete."
