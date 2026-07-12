import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from typing import Tuple, List, Dict

GROUNDED_PROMPT = """You are a helpful document assistant.
Use ONLY the following context to answer the question.

If you cannot find the answer in the context provided:
- Do NOT guess or use general knowledge
- Do NOT make up an answer
- Reply with EXACTLY this phrase: "No such information found in the document."

Context:
{context}

Question:
{question}

Answer:"""

def query_document(
    vector_store: FAISS,
    question: str,
    threshold: float = 0.5,
    k: int = 4
) -> Tuple[str, bool, List[Dict]]:
    """
    Query a document via RAG with strict grounding.

    Args:
        vector_store: FAISS index of the document
        question: the user's question
        threshold: relevance score threshold (0-1). If best match is below this,
                   return "not found" without calling LLM
        k: number of top chunks to retrieve

    Returns:
        (answer_text, found: bool, sources: list of dicts with page/content)
    """
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )

    # Retrieve with scores to check threshold
    docs_with_scores = vector_store.similarity_search_with_score(question, k=k)

    if not docs_with_scores:
        return "No such information found in the document.", False, []

    # Check if best match meets threshold
    best_score = docs_with_scores[0][1]
    if best_score < threshold:
        return "No such information found in the document.", False, []

    # Retrieve without scores for the prompt
    docs = [doc for doc, _ in docs_with_scores]
    context = "\n\n".join([doc.page_content for doc in docs])

    # Call LLM with strict prompt
    llm = ChatOpenAI(
        model=os.getenv("CHAT_MODEL", "gpt-4o-mini"),
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    prompt = PromptTemplate(
        template=GROUNDED_PROMPT,
        input_variables=["context", "question"]
    )

    chain = prompt | llm
    result = chain.invoke({"context": context, "question": question})

    answer_text = result.content.strip()

    # Check if LLM returned the sentinel phrase
    found = "No such information found in the document." not in answer_text

    # Build sources list
    sources = [
        {
            "page": doc.metadata.get("page", 0),
            "content": doc.page_content[:200] + "..."
        }
        for doc in docs
    ]

    return answer_text, found, sources
