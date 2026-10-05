# JARVIS Native 8.0.0

Windows-native migration scaffold for JARVIS.

Goals:
- self-contained Windows executable
- no Python installation required on the target PC
- Arduino USB/Serial bridge
- preserve the existing V8 Python system during migration
- keep external actions explicit and confirmation-gated

Build on a Windows machine with the .NET 8 SDK:

    dotnet publish Jarvis.Native/Jarvis.Native.csproj -c Release

The resulting self-contained application is the target portable runtime. This repository release contains the source and build definition; it does not silently replace an existing JARVIS installation.
