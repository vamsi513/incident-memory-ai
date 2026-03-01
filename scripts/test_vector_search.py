from retrieval.embedder import Embedder
from retrieval.vector_store import FaissStore


def main() -> None:
    query = "What fixed the checkout timeout incident?"

    embedder = Embedder()
    store = FaissStore.load("data/processed")

    query_embedding = embedder.encode([query])[0]
    results = store.search(query_embedding=query_embedding, top_k=3)

    print(f"Query: {query}\n")
    for i, result in enumerate(results, start=1):
        print(f"Result {i}")
        print(f"Title: {result['title']}")
        print(f"Section: {result['section']}")
        print(f"Score: {result['vector_score']:.4f}")
        print(f"Text: {result['text']}")
        print("-" * 50)


if __name__ == "__main__":
    main()

