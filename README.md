# 🚨 Asistente de Protocolos de Actuación Educativa

## 📋 Instalación y Configuración

### 1. **Instalar dependencias**
```bash
pip install streamlit
pip install pypdf
pip install sentence-transformers
pip install scikit-learn
pip install groq
pip install langchain
```

### 2. **Configurar la API de Groq**

#### Opción A: Con archivo de secretos de Streamlit (RECOMENDADO)
1. Crea una carpeta `.streamlit` en la raíz de tu proyecto
2. Crea un archivo `.streamlit/secrets.toml`
3. Añade tu clave:

```toml
GROQ_API_KEY = ""
```

#### Opción B: Directamente en el código (MENOS SEGURO)
Modifica esta línea en el código:
```python
groq_client = Groq(api_key="")
```

### 3. **Estructura de carpetas**
```
tu-proyecto/
├── app_final_mejorado.py
├── .streamlit/
│   └── secrets.toml
└── protocolos_test/  (se crea automáticamente)
```

### 4. **Ejecutar la aplicación**
```bash
streamlit run app_final_mejorado.py
```

## 🔧 **Cómo funciona**

### **¿Dónde pongo mis PDFs?**
**NO necesitas crear carpetas manualmente.** El sistema funciona así:

1. **Ejecutas** la aplicación con `streamlit run app_final_mejorado.py`
2. **Se abre** una interfaz web en tu navegador
3. **Subes los PDFs** usando el botón "Carga tus PDFs de protocolos aquí"
4. **El sistema** procesa automáticamente los documentos
5. **Ya puedes** hacer preguntas sobre los protocolos

### **Flujo completo:**
```
PDFs → Subes en interfaz → Sistema procesa → Chat disponible
```

## 🚀 **Uso paso a paso**

1. **Inicia** la aplicación:
   ```bash
   streamlit run app_final_mejorado.py
   ```

2. **Abre** tu navegador en `http://localhost:8501`

3. **Sube** tus 3 PDFs de protocolos usando el área de carga

4. **Espera** a que se procesen (verás una barra de progreso)

5. **Haz preguntas** como:
   - "¿Qué hacer si un estudiante se accidenta?"
   - "Protocolo para casos de violencia escolar"
   - "¿Cómo actuar ante un robo en el colegio?"

## ⚠️ **Problemas comunes y soluciones**

### Error: "No module named 'sentence_transformers'"
```bash
pip install sentence-transformers==2.2.2
```

### Error: "GROQ_API_KEY not found"
- Verifica que el archivo `.streamlit/secrets.toml` existe
- Verifica que la clave API es correcta
- O usa la opción B (directamente en código)

### Error: "No se pueden procesar PDFs"
- Verifica que los PDFs no están protegidos con contraseña
- Asegúrate de que son PDFs con texto (no solo imágenes)

### La aplicación no encuentra información
- Verifica que subiste los PDFs correctamente
- Prueba con preguntas más específicas
- Los PDFs deben contener texto legible

## 🎯 **Tipos de preguntas que puedes hacer**

### ✅ **Ejemplos buenos:**
- "¿Qué pasos seguir ante un accidente de un estudiante?"
- "Protocolo de evacuación en caso de emergencia"
- "¿A quién contactar si hay violencia en el aula?"
- "Procedimiento para reportar un robo"

### ❌ **Evita preguntas muy generales:**
- "¿Qué dice el documento?"
- "Explícame todo"
- "¿Qué protocolos hay?"

## 🔍 **Características avanzadas**

- **Debug info**: Expande "🔧 Información de búsqueda" para ver qué encontró
- **Ejemplos**: Usa los botones de ejemplo en la barra lateral
- **Múltiples PDFs**: Sube todos tus documentos de una vez
- **Historial**: El chat mantiene conversaciones previas

## 📞 **¿Necesitas ayuda?**

Si algo no funciona:
1. Verifica que instalaste todas las dependencias
2. Confirma que la API key está configurada
3. Asegúrate de que los PDFs se subieron correctamente
4. Revisa la consola donde ejecutaste streamlit para errores
