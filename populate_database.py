import argparse
import os
import shutil
import re
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.schema.document import Document
from get_embedding_function import get_embedding_function
from langchain.vectorstores import Chroma

CHROMA_PATH = "chroma"
DATA_PATH = "data"
CHUNK_SIZE = 1200  # Character-based chunking size
OVERLAP = 300  # Overlap between chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    
    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    documents = load_documents()
    structured_chunks = chunk_documents_by_length(documents)

    print("\n=== Sample Parsed Chunk ===\n")
    print(structured_chunks[0].page_content)  # Log first chunk
    print(f"\nMetadata: {structured_chunks[0].metadata}")

    print("\nAdding structured chunks to Chroma...")
    add_to_chroma(structured_chunks)


def load_documents():
    """Loads all PDFs from the data directory."""
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()


def chunk_documents_by_length(documents: list[Document]):
    """Splits text into chunks of fixed size with overlap to preserve context."""
    
    structured_chunks = []
    
    for doc in documents:
        raw_text = doc.page_content
        metadata = doc.metadata.copy()
        doc_id = os.path.basename(metadata.get("source", "Unknown")).replace(" ", "_").split(".")[0]  # Filename as ID

        start = 0
        chunk_counter = 0

        while start < len(raw_text):
            end = min(start + CHUNK_SIZE, len(raw_text))
            chunk_text = raw_text[start:end].strip()
            
            # Assign unique ID for each chunk
            chunk_metadata = metadata.copy()
            chunk_metadata["id"] = f"{doc_id}_chunk_{chunk_counter}"

            structured_chunks.append(Document(page_content=chunk_text, metadata=chunk_metadata))

            chunk_counter += 1
            start += CHUNK_SIZE - OVERLAP  # Move forward with overlap

    return structured_chunks


def add_to_chroma(chunks: list[Document]):
    """Clears ChromaDB and adds structured chunks with metadata."""
    if os.path.exists(CHROMA_PATH):
        print("🧹 Clearing ChromaDB to repopulate...")
        shutil.rmtree(CHROMA_PATH)

    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embedding_function())

    new_chunks = []
    new_metadata = []

    for chunk in chunks:
        new_chunks.append(chunk.page_content)
        new_metadata.append(chunk.metadata)

    if new_chunks:
        print(f"📥 Adding {len(new_chunks)} structured documents to ChromaDB")
        db.add_texts(new_chunks, metadatas=new_metadata)
        db.persist()
    else:
        print("✅ No new documents to add")


def clear_database():
    """Deletes the Chroma database directory."""
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    main()