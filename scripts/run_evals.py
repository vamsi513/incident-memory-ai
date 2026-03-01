import json
from pathlib import Path

from evals.metrics import recall_at_k, reciprocal_rank
from retrieval.pipeline import run_retrieval


def main() -> None:
    dataset_path = Path("evals/dataset.json")
    examples = json.loads(dataset_path.read_text(encoding="utf-8"))

    recall_1_scores = []
    recall_3_scores = []
    recall_5_scores = []
    mrr_scores = []

    print("\n=== Retrieval Evaluation ===\n")

    for example in examples:
        query = example["query"]
        expected_doc_ids = example["expected_doc_ids"]

        results = run_retrieval(query, top_k=5)
        retrieved_doc_ids = [result["doc_id"] for result in results]

        r1 = recall_at_k(retrieved_doc_ids, expected_doc_ids, k=1)
        r3 = recall_at_k(retrieved_doc_ids, expected_doc_ids, k=3)
        r5 = recall_at_k(retrieved_doc_ids, expected_doc_ids, k=5)
        rr = reciprocal_rank(retrieved_doc_ids, expected_doc_ids)

        recall_1_scores.append(r1)
        recall_3_scores.append(r3)
        recall_5_scores.append(r5)
        mrr_scores.append(rr)

        print(f"Query: {query}")
        print(f"Expected: {expected_doc_ids}")
        print(f"Retrieved: {retrieved_doc_ids}")
        print(f"Recall@1: {r1:.2f}")
        print(f"Recall@3: {r3:.2f}")
        print(f"Recall@5: {r5:.2f}")
        print(f"Reciprocal Rank: {rr:.2f}")
        print("-" * 60)

    avg_r1 = sum(recall_1_scores) / len(recall_1_scores)
    avg_r3 = sum(recall_3_scores) / len(recall_3_scores)
    avg_r5 = sum(recall_5_scores) / len(recall_5_scores)
    avg_mrr = sum(mrr_scores) / len(mrr_scores)

    print("\n=== Aggregate Metrics ===")
    print(f"Average Recall@1: {avg_r1:.2f}")
    print(f"Average Recall@3: {avg_r3:.2f}")
    print(f"Average Recall@5: {avg_r5:.2f}")
    print(f"Average MRR: {avg_mrr:.2f}")


if __name__ == "__main__":
    main()
