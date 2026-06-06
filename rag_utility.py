import os
import logging
import threading
import itertools
import sys
from dotenv import load_dotenv

from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------

load_dotenv()

working_dir = os.path.dirname(os.path.abspath(__file__))

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

embedding = HuggingFaceEmbeddings()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# -----------------------------------------------------------------------------
# Spinner
# -----------------------------------------------------------------------------

class Spinner:
    """A simple terminal spinner for long-running tasks."""

    def __init__(self, message="Processing..."):
        self.message = message
        self.spinner = itertools.cycle(["|", "/", "-", "\\"])
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin)

    def _spin(self):
        while not self._stop_event.is_set():
            sys.stdout.write(f"\r{self.message} {next(self.spinner)}")
            sys.stdout.flush()
            self._stop_event.wait(0.1)

        sys.stdout.write(f"\r{self.message} Done!     \n")
        sys.stdout.flush()

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *args):
        self._stop_event.set()
        self._thread.join()

# -----------------------------------------------------------------------------
# Document Processing
# -----------------------------------------------------------------------------

def process_document_to_chroma_db(file_name: str) -> int:
    """
    Load a PDF document, split it into chunks,
    and store the chunks in a FAISS vector database.

    Args:
        file_name (str): Name of the PDF file.

    Returns:
        int: 0 on success, -1 on failure.
    """

    try:
        with Spinner("Uploading and processing document..."):

            pdf_path = os.path.join(working_dir, file_name)

            # Load PDF
            loader = UnstructuredPDFLoader(pdf_path)
            documents = loader.load()

            # Split document
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,
                chunk_overlap=200
            )

            texts = text_splitter.split_documents(documents)

            # Create FAISS vector store
            vector_db = FAISS.from_documents(
                documents=texts,
                embedding=embedding
            )

            # Save locally
            vector_db.save_local(
                os.path.join(working_dir, "faiss_index")
            )

        logging.info(
            f"Successfully processed '{file_name}' into FAISS vector store."
        )

        return 0

    except Exception as e:
        logging.exception("Error processing document")
        logging.error(str(e))
        return -1

# -----------------------------------------------------------------------------
# Question Answering
# -----------------------------------------------------------------------------

def answer_question(user_question: str) -> str:
    """
    Answer a question using retrieved document context.

    Args:
        user_question (str): User question.

    Returns:
        str: Generated answer.
    """

    try:
        faiss_path = os.path.join(
            working_dir,
            "faiss_index"
        )

        if not os.path.exists(faiss_path):
            return (
                "No document has been processed yet. "
                "Please upload and process a PDF first."
            )

        # Load FAISS vector store
        vector_db = FAISS.load_local(
            faiss_path,
            embedding,
            allow_dangerous_deserialization=True
        )

        # Retriever
        retriever = vector_db.as_retriever(
            search_kwargs={"k": 3}
        )

        # Prompt
        prompt = PromptTemplate.from_template(
            """
You are a helpful assistant.

Use the provided context to answer the question as accurately as possible.

If the answer cannot be found in the context, respond with:

"I don't have enough information to answer that."

Context:
{context}

Question:
{question}

Answer:
"""
        )

        # Format retrieved documents
        def format_docs(docs):
            return "\n\n".join(
                doc.page_content for doc in docs
            )

        # LCEL Chain
        chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        return chain.invoke(user_question)

    except Exception as e:
        logging.exception("Error answering question")
        logging.error(str(e))
        return "Error answering question."



















































# import os
# import logging
# import threading
# import itertools
# import sys
# from dotenv import load_dotenv
# from langchain_community.document_loaders import UnstructuredPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from langchain_groq import ChatGroq
# from langchain_core.prompts import PromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.runnables import RunnablePassthrough

# # Set up logging
# logging.basicConfig(level=logging.INFO)

# # Load environment variables from .env file
# load_dotenv()

# # Set the working directory
# working_dir = os.path.dirname(os.path.abspath(__file__))

# # Load the embedding model
# embedding = HuggingFaceEmbeddings()

# # Load the llama-3.3-70B-versatile model from Groq
# llm = ChatGroq(
#     model="llama-3.3-70B-versatile",
#     temperature=0
# )


# class Spinner:
#     """A simple terminal spinner for long-running tasks."""

#     def __init__(self, message="Processing..."):
#         self.message = message
#         self.spinner = itertools.cycle(["|", "/", "-", "\\"])
#         self._stop_event = threading.Event()
#         self._thread = threading.Thread(target=self._spin)

#     def _spin(self):
#         while not self._stop_event.is_set():
#             sys.stdout.write(f"\r{self.message} {next(self.spinner)}")
#             sys.stdout.flush()
#             self._stop_event.wait(0.1)
#         sys.stdout.write(f"\r{self.message} Done!     \n")
#         sys.stdout.flush()

#     def __enter__(self):
#         self._thread.start()
#         return self

#     def __exit__(self, *args):
#         self._stop_event.set()
#         self._thread.join()


# def process_document_to_chroma_db(file_name: str) -> int:
#     """
#     Load a PDF document, split it into chunks, and store the chunks in a Chroma vector database.
#     Args:
#         file_name (str): The name of the PDF file to load.
#     Returns:
#         int: 0 on success, -1 on failure.
#     """
#     try:
#         with Spinner("Uploading and processing document..."):
#             # Load the document using UnstructuredPDFLoader
#             loader = UnstructuredPDFLoader(f"{working_dir}/{file_name}")
#             documents = loader.load()

#             # Split the text into chunks for embedding
#             text_splitter = RecursiveCharacterTextSplitter(
#                 chunk_size=2000,
#                 chunk_overlap=200
#             )
#             texts = text_splitter.split_documents(documents)

#             # Store the document chunks in the Chroma vector database
#             Chroma.from_documents(
#                 documents=texts,
#                 embedding=embedding,
#                 persist_directory=f"{working_dir}/doc_vectorstore"
#             )

#         logging.info(f"Successfully processed '{file_name}' into the vector store.")
#         return 0

#     except Exception as e:
#         logging.error(f"Error processing document: {e}")
#         return -1


# def answer_question(user_question: str) -> str:
#     """
#     Answer a user question using an LCEL chain and the llama-3.3-70B model.
#     Args:
#         user_question (str): The user's question.
#     Returns:
#         str: The answer to the user's question.
#     """
#     try:
#         # Load the persistent Chroma database
#         vector_db = Chroma(
#             persist_directory=f"{working_dir}/doc_vectorstore",
#             embedding_function=embedding
#         )

#         # Create a retriever for document search
#         retriever = vector_db.as_retriever(search_kwargs={"k": 3})

#         # Define the prompt template
#         prompt = PromptTemplate.from_template(
#             """You are a helpful assistant. Use the following context to answer the question as accurately as possible.
# If the answer is not in the context, say "I don't have enough information to answer that."

# Context:
# {context}

# Question: {question}

# Answer:"""
#         )

#         # Helper to format retrieved documents
#         def format_docs(docs):
#             return "\n\n".join(doc.page_content for doc in docs)

#         # Build the LCEL chain
#         chain = (
#             {"context": retriever | format_docs, "question": RunnablePassthrough()}
#             | prompt
#             | llm
#             | StrOutputParser()
#         )

#         return chain.invoke(user_question)

#     except Exception as e:
#         logging.error(f"Error answering question: {e}")
#         return "Error answering question"
































# import os
# import logging
# from dotenv import load_dotenv
# from langchain_community.document_loaders import UnstructuredPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from langchain_groq import ChatGroq
# from langchain_core.prompts import PromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.runnables import RunnablePassthrough
#
# # Set up logging
# logging.basicConfig(level=logging.INFO)
#
# # Load environment variables from .env file
# load_dotenv()
#
# # Set the working directory
# working_dir = os.path.dirname(os.path.abspath(__file__))
#
# # Load the embedding model
# embedding = HuggingFaceEmbeddings()
#
# # Load the llama-3.3-70B-versatile model from Groq
# llm = ChatGroq(
#     model="llama-3.3-70B-versatile",
#     temperature=0
# )
#
# def process_document_to_chroma_db(file_name: str) -> int:
#     """
#     Load a PDF document, split it into chunks, and store the chunks in a Chroma vector database.
#     Args:
#         file_name (str): The name of the PDF file to load.
#     Returns:
#         int: 0 on success, -1 on failure.
#     """
#     try:
#         # Load the document using UnstructuredPDFLoader
#         loader = UnstructuredPDFLoader(f"{working_dir}/{file_name}")
#         documents = loader.load()
#
#         # Split the text into chunks for embedding
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=2000,
#             chunk_overlap=200
#         )
#         texts = text_splitter.split_documents(documents)
#
#         # Store the document chunks in the Chroma vector database
#         Chroma.from_documents(
#             documents=texts,
#             embedding=embedding,
#             persist_directory=f"{working_dir}/doc_vectorstore"
#         )
#
#         logging.info(f"Successfully processed '{file_name}' into the vector store.")
#         return 0
#
#     except Exception as e:
#         logging.error(f"Error processing document: {e}")
#         return -1
#
#
# def answer_question(user_question: str) -> str:
#     """
#     Answer a user question using an LCEL chain and the llama-3.3-70B model.
#     Args:
#         user_question (str): The user's question.
#     Returns:
#         str: The answer to the user's question.
#     """
#     try:
#         # Load the persistent Chroma database
#         vector_db = Chroma(
#             persist_directory=f"{working_dir}/doc_vectorstore",
#             embedding_function=embedding
#         )
#
#         # Create a retriever for document search
#         retriever = vector_db.as_retriever(search_kwargs={"k": 3})
#
#         # Define the prompt template
#         prompt = PromptTemplate.from_template(
#             """You are a helpful assistant. Use the following context to answer the question as accurately as possible.
# If the answer is not in the context, say "I don't have enough information to answer that."
#
# Context:
# {context}
#
# Question: {question}
#
# Answer:"""
#         )
#
#         # Helper to format retrieved documents
#         def format_docs(docs):
#             return "\n\n".join(doc.page_content for doc in docs)
#
#         # Build the LCEL chain
#         chain = (
#             {"context": retriever | format_docs, "question": RunnablePassthrough()}
#             | prompt
#             | llm
#             | StrOutputParser()
#         )
#
#         return chain.invoke(user_question)
#
#     except Exception as e:
#         logging.error(f"Error answering question: {e}")
#         return "Error answering question"

# Example usage:
# if __name__ == "__main__":
#     file_name = "example.pdf"
#     process_document_to_chroma_db(file_name)
#     user_question = "What is the main topic of the document?"
#     answer = answer_question(user_question)
#     print(f"Answer: {answer}")
