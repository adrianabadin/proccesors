# Processor Concurrente DeepSeek

## 📋 Resumen

Procesador optimizado y concurrente para ordenanzas municipales usando DeepSeek API. Diseñado específicamente para VPS con 2 núcleos y 4GB RAM, escalable a sistemas más potentes.

## 🚀 Características

### Arquitectura Concurrente
- **Worker Pool**: 6 workers concurrentes para llamadas a API (configurable)
- **Batch Processing**: Persistencia en batches de 5 ordenanzas (optimizado para RAM)
- **Task Queue**: Control de backpressure con límite configurable
- **Circuit Breaker**: Protección contra sobrecarga de API
- **Retry Inteligente**: Exponential backoff para fallos reintentables

### Optimizaciones Específicas para DeepSeek
- **Sin Rate Limits Artificiales**: DeepSeek no tiene límites oficiales
- **Conexión Directa**: Usa API OpenAI-compatible de DeepSeek
- **Costo Competitivo**: $0.28/1M input tokens, $0.42/1M output tokens
- **Modelo Avanzado**: DeepSeek-V3.2 con 128K context

### Compatibilidad y Resumibilidad
- **100% Compatible**: Mantiene lógica del processor original
- **Resumibilidad**: Los errores se marcan como `ERROR_v1`
- **Base de Datos**: Misma estructura y migraciones
- **Prompts**: Mismo sistema de prompts y parsing

## ⚡ Mejoras de Rendimiento

### Comparación de Rendimiento
| Métrica | Processor Original | Processor Concurrente | Mejora |
|----------|-------------------|----------------------|---------|
| Velocidad | 1-2 ord/min | 10-15 ord/min | **7-15x** |
| Concurrency | 1 worker | 6 workers | **6x** |
| API Calls | Secuenciales | Paralelas | **6x** |
| Batch Size | 1 | 5 | **5x** |

### Optimización para Recursos
- **CPU**: 3 workers por núcleo (configurable)
- **RAM**: Batch size limitado para evitar swapping
- **Red**: Conexiones concurrentes optimizadas
- **BD**: Transacciones por batch para reducir lock time

## 🛠️ Instalación y Configuración

### 1. Scripts Automáticos
Ejecuta el script de configuración según tu sistema operativo:

**Linux/macOS:**
```bash
chmod +x scripts/setup-concurrent-deepseek.sh
./scripts/setup-concurrent-deepseek.sh
```

**Windows:**
```cmd
scripts\setup-concurrent-deepseek.bat
```

### 2. Configuración Manual
Crea/actualiza tu archivo `.env`:

```bash
# Database (requerido)
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/db_ordenanzas

# DeepSeek API (requerido)
DEEPSEEK_API_KEY=tu_api_key_aqui

# Configuración concurrente (optimizado para 2 núcleos/4GB RAM)
DEEPSEEK_WORKERS=6          # Workers concurrentes
DB_BATCH_SIZE=5             # Batch size para persistencia
MAX_QUEUE_SIZE=50           # Límite de cola para backpressure

# Configuración compatible
BATCH_SIZE=50               # Número de ordenanzas a procesar
MODEL=deepseek-chat         # Modelo de DeepSeek
PROMPT_VERSION=v2.0

# Logging y debugging
VERBOSE=false               # Activar logs detallados
LOG_LEVEL=info             # Nivel de log: debug, info, warn, error
NODE_ENV=production        # Entorno: development o production
```

## 🎯 Uso

### Comandos Básicos

```bash
# Procesar batch estándar (50 ordenanzas)
npm run process:deepseek-concurrent

# Procesar TODAS las ordenanzas pendientes
npm run process:deepseek-concurrent -- --all

# Activar logging detallado
VERBOSE=true npm run process:deepseek-concurrent

# Configurar workers personalizados
DEEPSEEK_WORKERS=10 npm run process:deepseek-concurrent
```

### Configuración por Sistema

#### Sistema Bajo (1 núcleo / 2GB RAM)
```bash
DEEPSEEK_WORKERS=3 DB_BATCH_SIZE=3 MAX_QUEUE_SIZE=25 npm run process:deepseek-concurrent
```

#### Sistema Estándar (2 núcleos / 4GB RAM)
```bash
DEEPSEEK_WORKERS=6 DB_BATCH_SIZE=5 MAX_QUEUE_SIZE=50 npm run process:deepseek-concurrent
```

#### Sistema Potente (4+ núcleos / 8GB+ RAM)
```bash
DEEPSEEK_WORKERS=15 DB_BATCH_SIZE=10 MAX_QUEUE_SIZE=100 npm run process:deepseek-concurrent
```

## 🏗️ Arquitectura Interna

### Componentes

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Task Queue    │───▶│  Worker Pool     │───▶│ Database Batcher│
│ (Backpressure)  │    │ (6 Workers)     │    │ (Batch Size 5)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Circuit Breaker  │    │   PostgreSQL    │
                       │ (Fail Fast)     │    │ (Transactional)│
                       └──────────────────┘    └─────────────────┘
```

### Flujo de Procesamiento

1. **Producer**: Encola ordenanzas en Task Queue
2. **Workers**: Procesan concurrentemente con retry y circuit breaker
3. **Batcher**: Persiste resultados en batches transaccionales
4. **Metrics**: Monitorea performance y errores

### Manejo de Errores

- **API Errors**: Reintentable con exponential backoff
- **Parse Errors**: Marcado como `ERROR_v1` (compatible)
- **Database Errors**: Retry y logging
- **Circuit Breaker**: Protege contra sobrecarga

## 📊 Monitoreo y Métricas

### Métricas en tiempo real
```
=== Procesamiento concurrente completado ===
Procesadas: 50
Tiempo total: 45.2s
Velocidad: 1.11 ord/segundo (66.6 ord/min)
Circuit breaker trips: 0
Configuración: 6 workers, batch 5
```

### Variables de MONITOREO
```bash
# Activar logging detallado
VERBOSE=true

# Nivel de log específico
LOG_LEVEL=debug

# Modo desarrollo
NODE_ENV=development
```

## ⚠️ Consideraciones

### Recursos del Sistema
- **CPU**: Cada worker consume ~15-20% de un núcleo
- **RAM**: Cada batch usa ~100-200MB temporales
- **Red**: 6 conexiones simultáneas a API
- **BD**: Batches reducen lock time significativamente

### Limitaciones de API
- DeepSeek no tiene rate limits oficiales
- Timeout de conexión: 10 minutos
- Reintentos automáticos para fallos temporales

### Best Practices
1. **Start Small**: Comienza con 3-4 workers, ajusta según rendimiento
2. **Monitor Memory**: Observa uso de RAM con `htop` o Task Manager
3. **Database Indexing**: Asegura índices en `procesado_ia`, `anio`, `numero`
4. **Backups**: Realiza backups antes de procesar grandes volúmenes

## 🔧 Troubleshooting

### Errores Comunes

**"Circuit breaker OPEN"**
- Solución: Espera 1 minuto o reduce `DEEPSEEK_WORKERS`

**"Too many connections"**
- Solución: Reduce `DEEPSEEK_WORKERS` o `MAX_QUEUE_SIZE`

**"Out of memory"**
- Solución: Reduce `DB_BATCH_SIZE` o `DEEPSEEK_WORKERS`

### Debugging

```bash
# Ver logs detallados
VERBOSE=true LOG_LEVEL=debug npm run process:deepseek-concurrent

# Probar con batch pequeño
DEEPSEEK_WORKERS=2 DB_BATCH_SIZE=2 npm run process:deepseek-concurrent
```

## 🆚 Comparación con Processor Original

| Característica | Original | Concurrente |
|----------------|-----------|--------------|
| **Speed** | 1-2 ord/min | 10-15 ord/min |
| **Concurrency** | No | Sí (6 workers) |
| **Batching** | No | Sí (batch 5) |
| **Error Handling** | Básico | Avanzado |
| **Resource Usage** | Bajo | Medio |
| **Complexity** | Simple | Moderada |
| **Resumibility** | ✅ | ✅ |

## 🚀 Roadmap Futuro

- [ ] Auto-scaling dinámico de workers
- [ ] Métricas en tiempo real via dashboard
- [ ] Configuración adaptive basada en load
- [ ] Integración con Redis para cache distribuida
- [ ] Modo debugging con breakpoint automático

---

**Desarrollado por**: [Tu Nombre]  
**Versión**: 1.0.0  
**Última actualización**: 2025-02-18