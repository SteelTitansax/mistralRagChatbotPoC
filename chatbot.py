import warnings
import sys
import os
from langchain_community.llms import LlamaCpp
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
import requests
from ddgs import DDGS
from utils import wikipedia_search, suppress_output, load_docs_from_sqlite
from constants import MODEL_PATH,DB_PATH,FAISS_INDEX_PATH,sentence_transformer 
from constants import qa_prompt_template 

# --- Silenciar warnings ---

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore")

# --- Inicializar LLM ---

with suppress_output():
    llm = LlamaCpp(model_path=MODEL_PATH, n_ctx=4096, temperature=0.1)

# --- Inicializar Embeddings ---

embedding_model = HuggingFaceEmbeddings(model_name=sentence_transformer)

# --- Splitter ---

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

# --- Cargar y preparar documentos ---

raw_docs = load_docs_from_sqlite(DB_PATH)

split_docs = []
for doc in raw_docs:
    chunks = text_splitter.split_text(doc["page_content"])
    for i, chunk in enumerate(chunks):
        split_docs.append(Document(page_content=chunk, metadata={"id": doc["metadata"]["id"], "title": doc["metadata"]["title"], "chunk": i}))

# --- Crear o cargar vectorstore FAISS ---

if os.path.exists(FAISS_INDEX_PATH):
    vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)
else:
    vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)
    vectorstore.save_local(FAISS_INDEX_PATH)


prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=qa_prompt_template,
)


# --- Crear RetrievalQA con prompt personalizado ---

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt},
    return_source_documents=True,
)


# --- Función para consultar con contexto y documentos ---

def ask_with_context(question):
    if "busca en internet" in question.lower():
        query = question.lower().replace("busca en internet", "").strip()
        if not query:
            return "¿Qué quieres que busque en internet?"
        return wikipedia_search(query)

    # Si no hay mención a buscar en internet, usa la base de datos local
    with suppress_output():
        result = qa_chain({"query": question})
    answer = result["result"].strip()
    return answer


# --- Main ---
if __name__ == "__main__":
    print("Hola soy Marea, tu asistente virtual. ¿ En que puedo ayudarte ?.")
    while True:
        q = input("Tu : ").strip()
        if q.lower() == "exit":
            break
        if len(q) == 0:
            print("Por favor, escribe una pregunta válida.")
            continue
        if len(q) > 1000:
            print("La pregunta es demasiado larga.")
            continue
        answer = ask_with_context(q)
        print("Marea:", answer)
