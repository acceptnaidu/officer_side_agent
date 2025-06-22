import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from google.adk.tools import FunctionTool

# Define the embedding model
# Using a common sentence-transformer model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME) # Updated class usage

class CitizenInfoRAG:
    """
    A simple RAG system for storing and retrieving citizen information.
    Uses Chroma as the vector store and HuggingFace embeddings.
    """
    def __init__(self, persist_directory="./chroma_db"):
        """
        Initializes the RAG system.

        Args:
            persist_directory (str): Directory to persist the Chroma database.
                                     If None, uses an in-memory database.
        """
        self.persist_directory = persist_directory
        self.vectorstore = None
        self._initialize_vectorstore()

    def _initialize_vectorstore(self):
        """Initializes or loads the Chroma vector store."""
        # Check if the persist directory exists and contains data
        if self.persist_directory and os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
             print(f"Loading vectorstore from {self.persist_directory}")
             self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=embeddings)
        else:
            print("Creating new vectorstore (in-memory initially)")
            # Create an empty in-memory vectorstore initially
            # Persistence will happen when documents are added
            self.vectorstore = Chroma(embedding_function=embeddings) # Initialize in-memory without persist_directory


    def add_document(self, text: str, metadata: dict = None):
        """
        Adds a single text document to the RAG system.

        Args:
            text (str): The content of the document.
            metadata (dict, optional): Optional metadata for the document. Defaults to None.
        """
        if not text:
            print("Warning: Cannot add empty document.")
            return

        # Split the text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = text_splitter.create_documents([text], metadatas=[metadata] if metadata else [{}])

        # Add chunks to the vector store
        if docs:
            self.vectorstore.add_documents(docs)
            print(f"Added {len(docs)} chunks to the vectorstore.")
            # Persist the database after adding documents
            if self.persist_directory:
                 self.vectorstore.persist()
                 print(f"Vectorstore persisted to {self.persist_directory}")
        else:
            print("No chunks generated from the document.")


    def add_documents(self, texts: list[str], metadatas: list[dict] = None):
        """
        Adds multiple text documents to the RAG system.

        Args:
            texts (list[str]): A list of document contents.
            metadatas (list[dict], optional): A list of metadata dictionaries. Defaults to None.
                                             Must have the same length as texts.
        """
        if not texts:
            print("Warning: No documents provided to add.")
            return

        if metadatas and len(texts) != len(metadatas):
            print("Error: Number of texts and metadatas must match.")
            return

        # Create Document objects
        documents = []
        for i, text in enumerate(texts):
            if text:
                documents.append(Document(page_content=text, metadata=metadatas[i] if metadatas else {}))
            else:
                 print(f"Warning: Skipping empty document at index {i}.")


        if not documents:
             print("No valid documents to process.")
             return

        # Split the documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = text_splitter.split_documents(documents)

        # Add chunks to the vector store
        if docs:
            self.vectorstore.add_documents(docs)
            print(f"Added {len(docs)} chunks to the vectorstore.")
            # Persist the database after adding documents
            if self.persist_directory:
                 self.vectorstore.persist()
                 print(f"Vectorstore persisted to {self.persist_directory}")
        else:
            print("No chunks generated from the documents.")


    def retrieve(self, query: str, k: int = 3):
        """
        Retrieves relevant documents for a given query.

        Args:
            query (str): The query string.
            k (int, optional): The number of relevant documents to retrieve. Defaults to 4.

        Returns:
            list[Document]: A list of retrieved documents.
        """
        if not query:
            print("Warning: Query is empty.")
            return []

        if self.vectorstore is None:
            print("Error: Vector store not initialized.")
            return []

        # Perform similarity search
        retrieved_docs = self.vectorstore.similarity_search(query, k=k)
        print(f"Retrieved {len(retrieved_docs)} documents for query: '{query}'")
        return retrieved_docs

# Example Usage (Optional - uncomment to test)
if __name__ == "__main__":
    # Initialize the RAG system
    rag = CitizenInfoRAG(persist_directory="./citizen_rag_db")

    # Add some documents
    rag.add_document("John Doe lives at 123 Main St, Apt 4B. His phone number is 555-1234.")
    rag.add_document("Jane Smith is a registered voter in the downtown district. Her email is jane.smith@example.com.")
    rag.add_document("The city park is located at Oak Ave and Elm St. It is open from 6 AM to 9 PM daily.")
    rag.add_document("Permits for building renovations can be obtained from the Public Works Department.")

    # Retrieve information
    query = "What is John Doe's address?"
    results = rag.retrieve(query)

    print("\n--- Retrieval Results ---")
    for i, doc in enumerate(results):
        print(f"Document {i+1}:")
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}")
        print("-" * 20)

    query = "Where is the city park?"
    results = rag.retrieve(query)

    print("\n--- Retrieval Results ---")
    for i, doc in enumerate(results):
        print(f"Document {i+1}:")
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}")
        print("-" * 20)

    data_retrieval = FunctionTool(
        func=rag.retrieve(),
    )
