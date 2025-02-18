import streamlit as st
import os
from dotenv import load_dotenv
import vertexai
# Use Chroma as the vector store instead of Pinecone
from langchain.vectorstores import Chroma
# Use Vertex AI’s embeddings
from langchain.embeddings import VertexAIEmbeddings
# Use Vertex AI’s chat model
from langchain.chat_models import ChatVertexAI
# Import message types (depending on your LangChain version, these may be in langchain.schema)
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import getpass
import os

load_dotenv()

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

# Set your VertexAI credentials and initialize VertexAI.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./nih_key.json"
PROJECT_ID = "nih-cl-cm500-jrobert3-1e1c"  # Replace with your project id
REGION = "us-central1"
vertexai.init(project=PROJECT_ID, location=REGION)


st.title("Chatbot")

# Initialize the embeddings model using Vertex AI
embeddings = VertexAIEmbeddings()  # You can pass additional parameters if needed

# Initialize the Chroma vector store (assumes a pre-populated collection in the "db" directory)
vector_store = Chroma(
    persist_directory="db",       # Change this to your persistent directory
    embedding_function=embeddings,
    collection_name="research_collection"  # Update to match your collection name
)

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        SystemMessage("You are an assistant for question-answering tasks.")
    )

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)

# Chat input widget
prompt = st.chat_input("What is your Machine Learning research question?")

if prompt:
    # Display the user message and add it to the session state
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append(HumanMessage(prompt))

    # Initialize the Vertex AI chat model
    llm = ChatVertexAI(
        model_name="claude-3-haiku@20240307",  # Change model_name if desired
        temperature=0.3
    )

    # Create a retriever from the vector store (using similarity search)
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}  # Retrieve top 3 relevant documents
    )
    # Retrieve documents relevant to the prompt
    docs = retriever.get_relevant_documents(prompt)
    docs_text = "".join(d.page_content for d in docs)

    # Define the system prompt that includes the retrieved context
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, just say that you don't know. "
        "Use three sentences maximum and keep the answer concise.\n"
        "Context: {context}:"
    )
    system_prompt_fmt = system_prompt.format(context=docs_text)
    st.session_state.messages.append(SystemMessage(system_prompt_fmt))

    # Invoke the Vertex AI LLM with the full message history
    result = llm.invoke(st.session_state.messages).content

    # Display the assistant's response and add it to the session state
    with st.chat_message("assistant"):
        st.markdown(result)
    st.session_state.messages.append(AIMessage(result))
