def reciprocal_rank_fusion(result_sets: list[list[dict]], k: int = 60) -> list[dict]:
    fused: dict[str, dict] = {}

    for result_set in result_sets:
        for rank, record in enumerate(result_set, start=1):
            key = record["chunk_id"]

            if key not in fused:
                fused[key] = dict(record)
                fused[key]["hybrid_score"] = 0.0

            fused[key]["hybrid_score"] += 1.0 / (k + rank)

    return sorted(
        fused.values(),
        key=lambda x: x["hybrid_score"],
        reverse=True,
    )

