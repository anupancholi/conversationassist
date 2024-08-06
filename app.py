# Step 1: Import necessary libraries
import os
import tempfile
import streamlit as st
from streamlit_chat import message
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOllama
from langchain.embeddings import FastEmbedEmbeddings
from langchain.schema.output_parser import StrOutputParser
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import PromptTemplate
from langchain.vectorstores.utils import filter_complex_metadata

# Define the ChatPDF class
class ChatPDF:
    vector_store = None
    retriever = None
    chain = None

    def __init__(self):
        # Initialize the ChatOllama model
        self.model = ChatOllama(model="mistral")
        # Initialize the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
        # Define the prompt template for conversation
        self.prompt = PromptTemplate.from_template(
            """
            <s> [INST] You are an assistant for question-answering tasks. Use the following pieces of retrieved context 
            to answer the question. If you don't know the answer, just say that you don't know. Use three sentences
             maximum and keep the answer concise. [/INST] </s> 
            [INST] Question: {question} 
            Context: {context} 
            Answer: [/INST]
            """
        )
    
    # Step 3: Implement the ingest method
    # Implement the ingest method
    def ingest(self, uploaded_file):
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_file_path = temp_file.name
        
        try:
            # Load PDF documents
            docs = PyPDFLoader(file_path=temp_file_path).load()
            # Split the documents into smaller chunks
            chunks = self.text_splitter.split_documents(docs)
            # Filter out complex metadata
            chunks = filter_complex_metadata(chunks)

            # Create a vector store from the chunks with FastEmbed embeddings
            self.vector_store = Chroma.from_documents(documents=chunks, embedding=FastEmbedEmbeddings())
            # Convert the vector store into a retriever with specified search parameters
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": 3,
                    "score_threshold": 0.5,
                },
            )

            # Define the conversation chain using the retriever and prompt
            self.chain = self.retriever | self.prompt | self.model | StrOutputParser()
            print("Chain successfully created")
        except Exception as e:
            st.error(f"Error ingesting PDF: {e}")
        finally:
            os.remove(temp_file_path)
    
        
    # Implement the ask method
    def ask(self, query: str):
        # Check if the conversation chain has been initialized
        if not self.chain:
            return "Please, add a PDF document first."

        # Invoke the conversation chain with the user query
        try:
            result = self.chain.invoke({"question": query})
            return result
        except Exception as e:
            return f"Error during query: {e}"

    # Step 5: Implement the clear method
    def clear(self):
        # Clear the vector store, retriever, and conversation chain
        self.vector_store = None
        self.retriever = None
        self.chain = None
        st.success("PDF data cleared successfully!")


# step 6: integrate Streamlit with the ChatPDF class:
# Initialize ChatPDF instance
chat_pdf = ChatPDF()

# Streamlit app layout
st.title("PDF Question-Answering System")

# PDF file upload
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

# Function to handle PDF ingestion
def ingest_pdf(file):
    if file is not None:
        chat_pdf.ingest(file)
        st.success("PDF successfully ingested!")

# Function to handle user queries
def answer_query(query):
    if not chat_pdf.chain:
        st.warning("Please, add a PDF document first.")
        return
    answer = chat_pdf.ask(query)
    st.info(f"Answer: {answer}")

# Streamlit components for PDF ingestion and querying
if uploaded_file is not None:
    ingest_pdf(uploaded_file)

user_query = st.text_input("Enter your question:")
if st.button("Ask"):
    answer_query(user_query)

if st.button("Clear PDF Data"):
    clear_pdf_data()