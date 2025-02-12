import argparse
from langchain.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from src.rag_app.get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"

# Generalized Prompt (No Regulatory-Specific Language)
PROMPT_TEMPLATE = """
Answer the question **only using the provided context**:

{context}

---
If the answer cannot be found in the retrieved context, respond with: "I don't know.". YET, if the context doesn't provide enough information but you can generalize the question from it and give significant, closest information, please do.

Frame your response clearly and concisely, ensuring it is structured and directly addresses the question.

Do not infer additional information beyond what is provided in the context. 


At the end of the answer, list the key references used to generate the response, IF available.

---
**Question:** {question}
**Answer:**
"""

def main():
    """Handles CLI input and triggers the retrieval-based answering process."""
    
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text
    query_rag(query_text)

def query_rag(query_text: str):
    """Retrieves the most relevant document chunks and generates an answer."""

    # Initialize ChromaDB with the appropriate embedding function
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Retrieve relevant chunks using Max Marginal Relevance (MMR) search
    results = db.max_marginal_relevance_search(query_text, k=5, fetch_k=15, lambda_mult=0.1)

    if not results:
        print("⚠️ No relevant documents found for this query.")
        return "No relevant documents found."

    # Extract relevant text and metadata from retrieved documents
    context_texts = []
    source_references = set()  # Stores unique references to retrieved sources
    sources_info = []  # Stores detailed chunk metadata

    for doc in results:
        context_texts.append(doc.page_content)

        # Extract metadata (handling non-regulatory documents)
        doc_title = doc.metadata.get("title", "Unknown Document")
        section_ref = doc.metadata.get("section", "Unknown Section")
        document_source = doc.metadata.get("source", "Unknown File")
        chunk_id = doc.metadata.get("id", "Unknown ID")

        # Build a simple reference system
        reference = f"{doc_title} - {section_ref}"
        source_references.add(reference)
        sources_info.append(f"{reference} (Chunk ID: {chunk_id})")

    # Format context into the LLM prompt
    context_text = "\n\n---\n\n".join(context_texts)
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # Debug: Print Retrieved Chunks
    print("\n=== Retrieved Chunks ===\n")
    for doc in results:
        print(f"🔹 Title: {doc.metadata.get('title', 'Unknown')}")
        print(f"🔹 Section: {doc.metadata.get('section', 'N/A')}")
        print(f"🔹 Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"🔹 Chunk ID: {doc.metadata.get('id', 'Unknown')}")
        print(doc.page_content[:500])  # Print only the first 500 characters for readability
        print("\n---\n")

    # Run LLM with retrieved context
    model = Ollama(model="deepseek-r1")
    response_text = model.invoke(prompt)

    # Format the final output with metadata-based citations
    formatted_response = (
        f"Response: {response_text}\n\n"
        f"**Sources Referenced:** {', '.join(sorted(source_references))}\n"
        f"**Detailed Sources:** {sources_info}"
    )

    print(formatted_response)
    return response_text

if __name__ == "__main__":
    main()