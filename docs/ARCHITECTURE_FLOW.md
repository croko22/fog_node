# 🏗️ Arquitectura Fog Computing - Flujo de Datos

## 📊 Situación ACTUAL (Incorrecta)

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND                                                   │
│  └─> Intenta servir desde: /audio/file.wav (LOCAL)         │
└─────────────────────────────────────────────────────────────┘
                        ❌ DEPENDE DEL FOG NODE
┌─────────────────────────────────────────────────────────────┐
│  FOG NODE (Docker Container)                                │
│  1. Genera audio localmente → generated_audio/file.wav     │
│  2. Sube a GCS (solo como backup, NO se usa)                │
│  3. Guarda en Firestore: "generated_audio/file.wav"          │
│  4. Sirve desde: /audio/file.wav (STATIC FILES)             │
└─────────────────────────────────────────────────────────────┘
                        ⚠️ PROBLEMA: Si el contenedor se reinicia
                        los archivos locales se pierden
┌─────────────────────────────────────────────────────────────┐
│  GCS (Cloud Storage)                                         │
│  └─> Archivos subidos pero NO se usan para servir          │
└─────────────────────────────────────────────────────────────┘
```

**Problemas:**
- ❌ Archivos locales se pierden al reiniciar contenedor
- ❌ Frontend depende de que el fog node tenga el archivo localmente
- ❌ No aprovecha el storage centralizado (GCS)
- ❌ No es verdadero Fog Computing (debería usar cloud storage)

---

## ✅ Cómo DEBERÍA ser (Fog Computing Correcto)

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND                                                   │
│  └─> Sirve desde: GCS Public URL o Signed URL               │
│      https://storage.googleapis.com/bucket/audiobooks/...   │
└─────────────────────────────────────────────────────────────┘
                        ✅ INDEPENDIENTE DEL FOG NODE
┌─────────────────────────────────────────────────────────────┐
│  FOG NODE (Edge Processing)                                  │
│  1. Genera audio localmente (PROCESAMIENTO EN EDGE)          │
│  2. Sube a GCS (STORAGE CENTRALIZADO)                         │
│  3. Guarda en Firestore: "gs://bucket/audiobooks/..."         │
│  4. Opcional: Cache local para servir rápido                 │
└─────────────────────────────────────────────────────────────┘
                        ✅ PROCESAMIENTO EN EDGE, STORAGE EN CLOUD
┌─────────────────────────────────────────────────────────────┐
│  GCS (Cloud Storage) - FUENTE DE VERDAD                     │
│  └─> Archivos persistentes, accesibles desde cualquier lugar│
│      - URLs públicas (si bucket es público)                 │
│      - Signed URLs (si bucket es privado)                   │
└─────────────────────────────────────────────────────────────┘
```

**Ventajas:**
- ✅ Archivos persisten aunque el fog node se reinicie
- ✅ Frontend puede servir desde GCS directamente
- ✅ Múltiples fog nodes pueden acceder a los mismos archivos
- ✅ Escalabilidad: procesamiento en edge, storage en cloud
- ✅ Verdadero Fog Computing: procesamiento distribuido + storage centralizado

---

## 🔄 Flujo Correcto de Fog Computing

### 1. **Procesamiento (Edge - Fog Node)**
```
PDF/EPUB → Fog Node → Extrae texto → Genera audio localmente
```
**Razón:** Procesamiento pesado (TTS) cerca del usuario (baja latencia)

### 2. **Almacenamiento (Cloud - GCS)**
```
Audio generado → Sube a GCS → Persiste en cloud
```
**Razón:** Storage centralizado, accesible desde cualquier lugar

### 3. **Serving (Cloud o Edge)**
```
Frontend → Solicita audio → GCS (URL pública/signed) → Reproduce
```
**Razón:** No depende del fog node, siempre disponible

---

## 🎯 Implementación Correcta

### Cambios Necesarios:

1. **Guardar URI de GCS en Firestore** (no ruta local)
   ```python
   # ❌ ACTUAL
   JobManager.add_output_file(job_id, "generated_audio/file.wav")
   
   # ✅ CORRECTO
   cloud_uri = StorageService.upload_file(...)
   JobManager.add_output_file(job_id, cloud_uri)  # "gs://bucket/..."
   ```

2. **Frontend sirve desde GCS**
   ```typescript
   // ❌ ACTUAL
   const audioUrl = `${job.nodeUrl}/audio/${filename}`
   
   // ✅ CORRECTO
   const audioUrl = getGcsPublicUrl(job.output_files[0])
   // o signed URL si es privado
   ```

3. **Bucket público o generar Signed URLs**
   - Opción A: Bucket público (más simple)
   - Opción B: Endpoint en fog node que genera signed URLs (más seguro)

---

## 📝 Resumen

| Aspecto | Actual (Incorrecto) | Correcto (Fog Computing) |
|---------|---------------------|---------------------------|
| **Procesamiento** | Edge (Fog Node) ✅ | Edge (Fog Node) ✅ |
| **Storage** | Local (se pierde) ❌ | GCS (persistente) ✅ |
| **Serving** | Local `/audio/` ❌ | GCS (URL pública) ✅ |
| **Persistencia** | No ❌ | Sí ✅ |
| **Escalabilidad** | Limitada ❌ | Alta ✅ |

