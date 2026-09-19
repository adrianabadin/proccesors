@echo off
REM Script de configuración para OpenCode con Servidor MCP de Ordenanzas
REM Optimizado para sistemas Windows

echo === Configuración de OpenCode para Servidor MCP de Ordenanzas ===
echo.
echo Creando opencode.jsonc...
echo.

(
echo {
echo   "$schema": "https://opencode.ai/config.json",
echo   "mcp": {
echo     "ordenanzas-saladillo": {
echo       "type": "local",
echo       "command": ["npx", "tsx", "src/mcp-server/index.ts"],
echo       "environment": {
echo         "DATABASE_URL": "{env:DATABASE_URL}",
echo         "GROQ_API_KEY": "{env:GROQ_API_KEY}",
echo         "OPENAI_API_KEY": "{env:GROQ_API_KEY}",
echo         "VERBOSE": "false",
echo         "LOG_LEVEL": "info"
echo       },
echo       "enabled": false
echo     }
echo   }
echo }
) > opencode.jsonc

echo ✅ opencode.jsonc creado exitosamente
echo.
echo Para habilitar el servidor MCP:
echo   1. Abre opencode.jsonc
echo   2. Cambia "enabled": false a "enabled": true
echo   3. Guarda el archivo
echo   4. Reinicia OpenCode
echo.
echo ⚠️  Recuerda verificar que .env tiene las variables de entorno requeridas:
echo   - DATABASE_URL (obligatorio)
echo   - GROQ_API_KEY (obligatorio)
echo.
pause