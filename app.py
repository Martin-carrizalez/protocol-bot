import streamlit as st
import os
import numpy as np
import re
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Asistente de Protocolos", page_icon="🚨")

# --- CONFIGURACIÓN DE API ---
def get_groq_client():
    """Obtiene cliente de Groq con manejo de secretos"""
    try:
        # Intenta usar secretos de HF Spaces
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        # Fallback a clave hardcodeada
        api_key = "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"
    
    return Groq(api_key=api_key)

# --- FUNCIONES DE PROCESAMIENTO ---

def clean_text(text):
    """Limpia el texto extraído de PDFs"""
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\']+', ' ', text)
    return text.strip()

def extract_text_with_metadata(pdf_path):
    """Extrae texto con metadatos de estructura"""
    reader = PdfReader(pdf_path)
    sections = []
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            cleaned_text = clean_text(text)
            
            lines = cleaned_text.split('.')
            for line in lines:
                line = line.strip()
                if len(line) > 10:
                    section = {
                        'text': line,
                        'source_file': os.path.basename(pdf_path),
                        'page': page_num + 1,
                        'is_title': line.isupper() and len(line) < 100
                    }
                    sections.append(section)
    
    return sections

def smart_chunking(sections, chunk_size=800, overlap=150):
    """Chunking inteligente que respeta estructura semántica"""
    chunks = []
    current_chunk = ""
    current_metadata = {}
    
    for section in sections:
        text = section['text']
        
        if section['is_title'] and current_chunk:
            if len(current_chunk) > 50:
                chunks.append({
                    'text': current_chunk.strip(),
                    'metadata': current_metadata.copy()
                })
            current_chunk = text + " "
            current_metadata = {
                'source_file': section['source_file'],
                'page': section['page'],
                'title': text if section['is_title'] else current_metadata.get('title', '')
            }
        else:
            if len(current_chunk + text) > chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'metadata': current_metadata.copy()
                })
                
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + text + " "
            else:
                current_chunk += text + " "
                
                if not current_metadata:
                    current_metadata = {
                        'source_file': section['source_file'],
                        'page': section['page'],
                        'title': ''
                    }
    
    if current_chunk.strip():
        chunks.append({
            'text': current_chunk.strip(),
            'metadata': current_metadata.copy()
        })
    
    return chunks

def expand_query(query):
    """Expande la consulta con términos relacionados"""
    emergency_keywords = {
        'accidente': ['accidente', 'lesión', 'herida', 'trauma', 'emergencia médica'],
        'violencia': ['violencia', 'agresión', 'conflicto', 'bullying', 'acoso'],
        'robo': ['robo', 'hurto', 'sustracción', 'pérdida', 'seguridad'],
        'emergencia': ['emergencia', 'crisis', 'urgencia', 'evacuación', 'alarma'],
        'protocolo': ['protocolo', 'procedimiento', 'pasos', 'actuación', 'respuesta']
    }
    
    expanded_terms = [query]
    query_lower = query.lower()
    
    for key, synonyms in emergency_keywords.items():
        if key in query_lower:
            expanded_terms.extend(synonyms)
    
    return ' '.join(expanded_terms)

# --- CACHING DE RECURSOS ---
@st.cache_resource
def load_and_process_data(folder_path):
    """Procesa PDFs de la carpeta especificada"""
    st.info("📚 Procesando documentos PDF con técnicas avanzadas...")
    
    all_sections = []
    
    # Verificar que la carpeta existe
    if not os.path.exists(folder_path):
        st.error(f"❌ La carpeta '{folder_path}' no existe")
        return None, None, None
    
    # Obtener archivos PDF
    files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    
    if not files:
        st.error(f"❌ No se encontraron archivos PDF en '{folder_path}'")
        return None, None, None
    
    # Procesar archivos
    progress_bar = st.progress(0)
    
    for i, filename in enumerate(files):
        st.text(f"Procesando: {filename}")
        pdf_path = os.path.join(folder_path, filename)
        try:
            sections = extract_text_with_metadata(pdf_path)
            all_sections.extend(sections)
            st.text(f"✅ {filename}: {len(sections)} secciones extraídas")
        except Exception as e:
            st.error(f"❌ Error procesando {filename}: {str(e)}")
            continue
        
        progress_bar.progress((i + 1) / len(files))
    
    if not all_sections:
        st.error("❌ No se pudo extraer contenido de los PDFs")
        return None, None, None
    
    # Chunking inteligente
    st.text("📝 Organizando contenido en fragmentos semánticos...")
    chunks = smart_chunking(all_sections, chunk_size=800, overlap=150)
    
    # Crear embeddings
    st.text("🧠 Creando representaciones vectoriales...")
    try:
        embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = embedding_model.encode(chunk_texts, show_progress_bar=True, batch_size=16)
        
        st.success(f"✅ Procesados {len(chunks)} fragmentos de {len(files)} documentos!")
        return chunks, embeddings, embedding_model
        
    except Exception as e:
        st.error(f"❌ Error creando embeddings: {str(e)}")
        return None, None, None

# --- LÓGICA DEL CHATBOT ---
def find_relevant_chunks(user_query, chunks, embeddings, model, top_k=7):
    """Búsqueda mejorada con expansión de consulta"""
    expanded_query = expand_query(user_query)
    query_embedding = model.encode([expanded_query])
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    
    min_similarity = 0.15
    valid_indices = np.where(similarities > min_similarity)[0]
    
    if len(valid_indices) == 0:
        top_indices = np.argsort(similarities)[-top_k:][::-1]
    else:
        valid_similarities = similarities[valid_indices]
        sorted_valid = np.argsort(valid_similarities)[::-1]
        top_indices = valid_indices[sorted_valid[:min(top_k, len(valid_indices))]]
    
    relevant_chunks = []
    for idx in top_indices:
        chunk_info = chunks[idx].copy()
        chunk_info['similarity'] = similarities[idx]
        relevant_chunks.append(chunk_info)
    
    return relevant_chunks

def generate_response(user_query, context_chunks):
    """Genera respuesta con contexto enriquecido"""
    if not context_chunks:
        return "No encontré información específica sobre ese tema en los protocolos que tengo disponibles."
    
    try:
        groq_client = get_groq_client()
        
        # Construir contexto enriquecido
        context_text = ""
        for i, chunk in enumerate(context_chunks):
            metadata = chunk['metadata']
            context_text += f"\n--- Fragmento {i+1} (Archivo: {metadata['source_file']}, Página: {metadata['page']}) ---\n"
            if metadata.get('title'):
                context_text += f"Sección: {metadata['title']}\n"
            context_text += f"{chunk['text']}\n"
        
        prompt = f"""
        Eres un asistente experto en protocolos de actuación educativos. Tu tarea es ayudar a docentes en situaciones de emergencia, accidentes, violencia o robos.

        INSTRUCCIONES ESPECÍFICAS:
        1. Analiza la PREGUNTA del usuario cuidadosamente
        2. Usa EXCLUSIVAMENTE la información del CONTEXTO proporcionado
        3. Si la información está disponible, proporciona una respuesta clara y estructurada con:
           - Pasos específicos a seguir
           - Personas o autoridades a contactar
           - Acciones inmediatas recomendadas
        4. Si NO hay información suficiente en el contexto, responde: "No encontré información específica sobre ese tema en los protocolos disponibles."
        5. SIEMPRE indica de qué documento proviene la información cuando sea relevante

        --- CONTEXTO DE LOS PROTOCOLOS ---
        {context_text}
        --- FIN DEL CONTEXTO ---

        PREGUNTA DEL DOCENTE: {user_query}

        RESPUESTA PRECISA Y PRÁCTICA:
        """
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Ocurrió un error al contactar la API de Groq: {e}"

# --- INTERFAZ PRINCIPAL ---
st.title("🚨 Asistente de Protocolos de Actuación Educativa")
st.write("""
**Sistema especializado en emergencias, accidentes, violencia y robos escolares**

Este asistente ha sido entrenado con los protocolos oficiales de tu institución educativa.
Puedes consultar sobre situaciones como:
- 🩹 Accidentes y emergencias médicas
- ⚠️ Actos de violencia y conflictos  
- 🔒 Robos y problemas de seguridad
- 📋 Procedimientos de evacuación
""")

# Verificar y cargar protocolos
protocols_folder = "protocolos"

if os.path.exists(protocols_folder):
    # Mostrar información de archivos disponibles
    pdf_files = [f for f in os.listdir(protocols_folder) if f.endswith('.pdf')]
    
    with st.expander("📋 Protocolos cargados", expanded=False):
        for pdf_file in pdf_files:
            file_path = os.path.join(protocols_folder, pdf_file)
            file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
            st.write(f"• **{pdf_file}** ({file_size:.1f} MB)")
    
    # Procesar documentos
    chunks, embeddings, model = load_and_process_data(protocols_folder)
    
    if chunks is not None and embeddings is not None and model is not None:
        # Sidebar con estadísticas
        with st.sidebar:
            st.header("📊 Estado del Sistema")
            st.metric("Documentos procesados", len(pdf_files))
            st.metric("Fragmentos de texto", len(chunks))
            
            st.header("🔥 Consultas frecuentes")
            example_queries = [
                "¿Qué hacer si un estudiante se accidenta?",
                "Protocolo para casos de violencia escolar",
                "¿Cómo actuar ante un robo en el colegio?",
                "Pasos para evacuar el edificio",
                "¿A quién contactar en una emergencia?"
            ]
            
            for query in example_queries:
                if st.button(query, key=f"example_{hash(query)}"):
                    # Forzar nueva consulta
                    if "example_query" not in st.session_state:
                        st.session_state.example_query = query
                        st.rerun()
        
        # Sistema de chat
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Manejar consulta de ejemplo
        if "example_query" in st.session_state:
            user_input = st.session_state.example_query
            del st.session_state.example_query
        else:
            user_input = None

        # Mostrar historial de chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input del usuario
        if not user_input:
            user_input = st.chat_input("¿En qué situación necesitas ayuda? Describe el problema...")

        if user_input:
            # Agregar mensaje del usuario
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Generar respuesta
            with st.chat_message("assistant"):
                with st.spinner("🔍 Consultando protocolos..."):
                    relevant_chunks = find_relevant_chunks(user_input, chunks, embeddings, model)
                    
                    # Debug info
                    with st.expander("🔧 Información de búsqueda", expanded=False):
                        st.write(f"**Consulta expandida:** {expand_query(user_input)}")
                        st.write(f"**Fragmentos encontrados:** {len(relevant_chunks)}")
                        for i, chunk in enumerate(relevant_chunks):
                            st.write(f"**Fragmento {i+1}** (Similitud: {chunk['similarity']:.3f})")
                            st.write(f"- Archivo: {chunk['metadata']['source_file']}")
                            st.write(f"- Página: {chunk['metadata']['page']}")
                    
                    response = generate_response(user_input, relevant_chunks)
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    else:
        st.error("❌ No se pudieron procesar los documentos. Verifica que los PDFs sean válidos.")

else:
    st.error(f"""
    ❌ **Carpeta de protocolos no encontrada**
    
    Se esperaba encontrar la carpeta `{protocols_folder}` con los archivos PDF.
    
    **Estructura esperada:**
    ```
    protocolos/
    ├── protocolo1.pdf
    ├── protocolo2.pdf  
    └── protocolo3.pdf
    ```
    
    **Para desarrolladores:** Asegúrate de incluir la carpeta `protocolos` con los PDFs en tu repositorio.
    """)

# Footer
st.markdown("---")
st.markdown("*🤖 Asistente de Protocolos v2.0 - Powered by Groq & Hugging Face*")
