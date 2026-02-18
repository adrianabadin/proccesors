#!/bin/bash

# Script de configuración para el processor concurrente de DeepSeek
# Optimizado para VPS 2 núcleos / 4GB RAM

echo "=== Configuración del Processor Concurrente DeepSeek ==="
echo ""

# Verificar si existe el archivo .env
if [ ! -f .env ]; then
    echo "⚠️  No se encontró archivo .env. Creando uno con valores por defecto..."
    cat > .env << EOL
# Database
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/db_ordenanzas

# DeepSeek API (requerido)
DEEPSEEK_API_KEY=tu_api_key_aqui

# Configuración del Processor Concurrente
# Optimizado para VPS 2 núcleos / 4GB RAM
DEEPSEEK_WORKERS=6          # Workers concurrentes (3 por núcleo)
DB_BATCH_SIZE=5             # Batch size para persistencia
MAX_QUEUE_SIZE=50           # Límite de cola para backpressure

# Configuración del processor original (compatible)
BATCH_SIZE=50               # Número de ordenanzas a procesar
MODEL=deepseek-chat         # Modelo de DeepSeek
PROMPT_VERSION=v2.0

# Logging y debugging
VERBOSE=false               # Activar logs detallados
LOG_LEVEL=info             # Nivel de log: debug, info, warn, error
NODE_ENV=production        # Entorno: development o production
EOL
    echo "✅ Archivo .env creado. Por favor, ajusta los valores de DATABASE_URL y DEEPSEEK_API_KEY"
    echo ""
fi

# Verificar variables de entorno críticas
source .env 2>/dev/null

if [ -z "$DATABASE_URL" ] || [ "$DATABASE_URL" = "postgresql://usuario:contraseña@localhost:5432/db_ordenanzas" ]; then
    echo "❌ DATABASE_URL no está configurado correctamente en .env"
    echo "   Por favor, edita el archivo .env con tu conexión a PostgreSQL"
    exit 1
fi

if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "tu_api_key_aqui" ]; then
    echo "❌ DEEPSEEK_API_KEY no está configurado en .env"
    echo "   Por favor, obtén una API key en https://platform.deepseek.com/api_keys"
    exit 1
fi

echo "✅ Variables de entorno verificadas"
echo ""

# Recomendaciones basadas en recursos disponibles
echo "📊 Recomendaciones para tu sistema:"
echo ""

# Detectar sistema operativo y memoria
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
    CPU_CORES=$(nproc)
    
    echo "   Sistema detectado: Linux"
    echo "   RAM: ${TOTAL_RAM_GB}GB"
    echo "   Núcleos CPU: ${CPU_CORES}"
    echo ""
    
    if [ $TOTAL_RAM_GB -ge 8 ]; then
        echo "   🚀 Sistema con recursos amplios:"
        echo "      DEEPSEEK_WORKERS=12-16"
        echo "      DB_BATCH_SIZE=10"
        echo "      MAX_QUEUE_SIZE=100"
    elif [ $TOTAL_RAM_GB -ge 4 ]; then
        echo "   ⚡ Sistema mediano (recomendado):"
        echo "      DEEPSEEK_WORKERS=6-8"
        echo "      DB_BATCH_SIZE=5"
        echo "      MAX_QUEUE_SIZE=50"
    else
        echo "   🔋 Sistema con recursos limitados:"
        echo "      DEEPSEEK_WORKERS=3-4"
        echo "      DB_BATCH_SIZE=3"
        echo "      MAX_QUEUE_SIZE=25"
    fi
    
else
    echo "   Sistema: No se pudo detectar automáticamente"
    echo "   Asumiendo configuración estándar para 2 núcleos / 4GB RAM:"
    echo "      DEEPSEEK_WORKERS=6"
    echo "      DB_BATCH_SIZE=5"
    echo "      MAX_QUEUE_SIZE=50"
fi

echo ""
echo "🎯 Comandos de ejecución:"
echo ""
echo "   Para procesar un batch estándar:"
echo "   npm run process:deepseek-concurrent"
echo ""
echo "   Para procesar TODAS las ordenanzas pendientes:"
echo "   npm run process:deepseek-concurrent -- --all"
echo ""
echo "   Para activar logging detallado:"
echo "   VERBOSE=true npm run process:deepseek-concurrent"
echo ""
echo "📈 Comparación de rendimiento esperado:"
echo "   - Processor secuencial original: ~1-2 ordenanzas/minuto"
echo "   - Processor concurrente: ~10-15 ordenanzas/minuto"
echo "   - Mejora: 7-15x más rápido"
echo ""
echo "⚠️  Notas importantes:"
echo "   - El processor concurrente mantiene la lógica de resumibilidad"
echo "   - Los errores se marcan como ERROR_v1 igual que el original"
echo "   - Circuit breaker protege contra sobrecarga de la API"
echo "   - Batch processing reduce la carga en la base de datos"
echo ""

echo "✅ Configuración completada. ¡Listo para procesar!"