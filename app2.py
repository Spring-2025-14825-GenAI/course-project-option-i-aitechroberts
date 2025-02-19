import os
import glob
import streamlit as st
from dotenv import load_dotenv
import vertexai
from langchain.vectorstores import Chroma
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

# For PDF loading and text splitting
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

# Set tracing and API key environment variables
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

# Set your Vertex AI credentials and initialize Vertex AI.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./nih_key.json"
PROJECT_ID = "nih-cl-cm500-jrobert3-1e1c"  # Replace with your project id
REGION = "us-central1"
vertexai.init(project=PROJECT_ID, location=REGION)

st.title("RAG Chatbot with PDF Ingestion")

# Use a consistent embeddings model for both vector store creation and PDF processing.
EMBEDDING_MODEL_NAME = "text-embedding-004"
embedding_model = VertexAIEmbeddings(model_name=EMBEDDING_MODEL_NAME)

# Initialize the Chroma vector store (using a persistent directory "db")
vector_store = Chroma(
    persist_directory="db",
    embedding_function=embedding_model,
    collection_name="research_collection"  # Update as needed
)

# -------------------------------------------------
# Step 1: Ingest PDFs from the "documents/" directory and add to vector store.
# -------------------------------------------------

# Get list of all PDF files in the directory "documents"
pdf_files = glob.glob(os.path.join("documents", "*.pdf"))
all_chunks = []  # To store all document chunks

if len(all_chunks) == 0:
    if pdf_files:
        st.write("Indexing PDF documents from the 'documents/' folder...")
        for pdf_path in pdf_files:
            try:
                loader = PyPDFLoader(pdf_path)
                pages = loader.load()
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                )
                chunks = splitter.split_documents(pages)
                all_chunks.extend(chunks)
                st.write(f"Loaded {len(chunks)} chunks from {os.path.basename(pdf_path)}")
            except Exception as e:
                st.error(f"Error processing {pdf_path}: {e}")
        
        if all_chunks:
            # Add the chunks to the vector store. This will index them using the embedding model.
            vector_store.add_documents(all_chunks)
            st.write(f"Added {len(all_chunks)} document chunks to the vector store.")
    else:
        st.write("No PDF files found in the 'documents/' directory.")

# -------------------------------------------------
# Step 2: Initialize chat history.
# -------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        SystemMessage("You are an assistant for question-answering tasks.")
    )

# Display past chat messages
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)

# Chat input widget
user_prompt = st.chat_input("What is your Machine Learning research question?")

if user_prompt:
    # Display and store user message
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.messages.append(HumanMessage(user_prompt))
    
    # -------------------------------------------------
    # Step 3: Retrieve relevant context from the vector store.
    # -------------------------------------------------
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 2}  # Adjust the number of retrieved documents as needed
    )
    retrieved_docs = retriever.get_relevant_documents(user_prompt)
    docs_text = "\n\n".join(d.page_content for d in retrieved_docs)
    
    # -------------------------------------------------
    # Step 4: Set up an LLMChain with a prompt template that includes both the user's query and retrieved context.
    # -------------------------------------------------
    prompt_template = PromptTemplate(
        input_variables=["question", "context"],
        template=(
            "You are an assistant for question-answering tasks. "
            "Whatever language the question was asked in, respond in that language."
            "Based on the context provided, answer the following question concisely (up to three sentences). "
            "If you don't know the answer, simply say you don't know.\n\n"
            "Context:\n{context}\n\n"
            "Question:\n{question}"
        )
    )
    
    # Initialize the Vertex AI chat model
    llm = VertexAI(
        model_name="gemini-1.5-pro-002",  # Change model_name if desired
        temperature=0.3,
        allow_image_uploads=False,
        verbose=True
    )
    
    llm_chain = LLMChain(llm=llm, prompt=prompt_template)
    
    # Prepare input for the chain
    chain_input = {"question": user_prompt, "context": docs_text}
    answer = llm_chain.run(chain_input)
    
    # Display and store the assistant's response
    with st.chat_message("assistant"):
        st.markdown(answer)
    st.session_state.messages.append(AIMessage(answer))
