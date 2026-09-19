#!/bin/bash
# Script de configuración para OpenCode con Servidor MCP de Ordenanzas
# Optimizado para sistemas Linux y macOS

echo "=== Configuración de OpenCode para Servidor MCP de Ordenanzas ==="
echo ""
echo "Creando opencode.jsonc..."
echo ""

cat > opencode.jsonc << 'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "ordenanzas-saladillo": {
      "type": "local",
      "command": ["npx", "tsx", "src/mcp-server/index.ts"],
      "environment": {
        "DATABASE_URL": "{env:DATABASE_URL}",
        "GROQ_API_KEY": "{env:GROQ_API_KEY}",
        "OPENAI_API_KEY": "{env:GROQ_API_KEY}",
        "VERBOSE": "false",
        "LOG_LEVEL": "info"
      },
      "enabled": false
    }
  }
}
EOF

echo "✅ opencode.jsonc creado exitosamente"
echo ""
echo "Para habilitar el servidor MCP:"
echo "  1. Abre opencode.jsonc"
echo "  2. Cambia 'enabled': false a 'enabled': true"
echo "  3. Guarda el archivo"
echo "  4. Reinicia OpenCode"
echo ""
echo "⚠️  Recuerda verificar que .env tiene las variables de entorno requeridas:"
echo "  - DATABASE_URL (obligatorio)"
echo "  - GROQ_API_KEY (obligatorio)"