@echo off
REM Script de configuración para el processor concurrente de DeepSeek
REM Optimizado para VPS 2 núcleos / 4GB RAM (versión Windows)

echo === Configuración del Processor Concurrente DeepSeek ===
echo.

REM Verificar si existe el archivo .env
if not exist .env (
    echo ⚠️  No se encontró archivo .env. Creando uno con valores por defecto...
    (
        echo # Database
        echo DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/db_ordenanzas
        echo.
        echo # DeepSeek API ^(requerido^)
        echo DEEPSEEK_API_KEY=tu_api_key_aqui
        echo.
        echo # Configuración del Processor Concurrente
        echo # Optimizado para VPS 2 núcleos / 4GB RAM
        echo DEEPSEEK_WORKERS=6          # Workers concurrentes ^(3 por núcleo^)
        echo DB_BATCH_SIZE=5             # Batch size para persistencia
        echo MAX_QUEUE_SIZE=50           # Límite de cola para backpressure
        echo.
        echo # Configuración del processor original ^(compatible^)
        echo BATCH_SIZE=50               # Número de ordenanzas a procesar
        echo MODEL=deepseek-chat         # Modelo de DeepSeek
        echo PROMPT_VERSION=v2.0
        echo.
        echo # Logging y debugging
        echo VERBOSE=false               # Activar logs detallados
        echo LOG_LEVEL=info             # Nivel de log: debug, info, warn, error
        echo NODE_ENV=production        # Entorno: development o production
    ) > .env
    echo ✅ Archivo .env creado. Por favor, ajusta los valores de DATABASE_URL y DEEPSEEK_API_KEY
    echo.
)

REM Verificar si las variables están configuradas correctamente
findstr /C:"DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/db_ordenanzas" .env >nul
if %errorlevel%==0 (
    echo ❌ DATABASE_URL no está configurado correctamente en .env
    echo    Por favor, edita el archivo .env con tu conexión a PostgreSQL
    pause
    exit /b 1
)

findstr /C:"DEEPSEEK_API_KEY=tu_api_key_aqui" .env >nul
if %errorlevel%==0 (
    echo ❌ DEEPSEEK_API_KEY no está configurado en .env
    echo    Por favor, obtén una API key en https://platform.deepseek.com/api_keys
    pause
    exit /b 1
)

echo ✅ Variables de entorno verificadas
echo.

REM Recomendaciones
echo 📊 Recomendaciones para tu sistema:
echo    Sistema: Windows ^(configuración estándar para 2 núcleos / 4GB RAM^):
echo       DEEPSEEK_WORKERS=6
echo       DB_BATCH_SIZE=5
echo       MAX_QUEUE_SIZE=50
echo.

echo 🎯 Comandos de ejecución:
echo.
echo    Para procesar un batch estándar:
echo    npm run process:deepseek-concurrent
echo.
echo    Para procesar TODAS las ordenanzas pendientes:
echo    npm run process:deepseek-concurrent -- --all
echo.
echo    Para activar logging detallado:
echo    set VERBOSE=true ^&^& npm run process:deepseek-concurrent
echo.
echo 📈 Comparación de rendimiento esperado:
echo    - Processor secuencial original: ~1-2 ordenanzas/minuto
echo    - Processor concurrente: ~10-15 ordenanzas/minuto
echo    - Mejora: 7-15x más rápido
echo.
echo ⚠️  Notas importantes:
echo    - El processor concurrente mantiene la lógica de resumibilidad
echo    - Los errores se marcan como ERROR_v1 igual que el original
echo    - Circuit breaker protege contra sobrecarga de la API
echo    - Batch processing reduce la carga en la base de datos
echo.

echo ✅ Configuración completada. ¡Listo para procesar!
pause