import os
import uuid
import logging
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
# We will use HuggingFace embeddings running locally or an API inference endpoint.
# For MVP, we will use an accessible open embeddings model.
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb

from core.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Initialize chroma client
        self.chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_SERVER_HOST,
            port=settings.CHROMA_SERVER_PORT
        )
        
        # Using a highly effective, small local embedding model. 
        # In a real environment, you'd likely pin the model cache dir.
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        self.vector_store = Chroma(
            client=self.chroma_client,
            collection_name="course_materials",
            embedding_function=self.embeddings
        )
        
        # Configured as per plan: 500 characters, 100 overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len
        )
        
    def process_file(self, file_path: str, metadata: dict) -> int:
        """
        Loads a document, splits it into chunks, and stores them in ChromaDB 
        with the associated metadata (e.g. course_id).
        Returns the number of chunks stored.
        """
        try:
            if file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith(".txt") or file_path.endswith(".md"):
                loader = TextLoader(file_path, encoding="utf-8")
            else:
                raise ValueError(f"Unsupported file format for {file_path}")
                
            documents = loader.load()
            
            # Inject metadata into every loaded document before splitting
            for doc in documents:
                doc.metadata.update(metadata)
                
            chunks = self.text_splitter.split_documents(documents)
            
            if chunks:
                self.vector_store.add_documents(documents=chunks)
                
            return len(chunks)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise e
            
    def similarity_search(self, query: str, course_id: int, top_k: int = 4) -> List[dict]:
        """
        Retrieves the top_k most relevant chunks for a given query, filtered by course_id.
        """
        filter_dict = {"course_id": course_id}
        
        # Note: Chroma allows metadata filtering during search
        results = self.vector_store.similarity_search_with_score(
            query, 
            k=top_k, 
            filter=filter_dict
        )
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })
            
        return formatted_results
