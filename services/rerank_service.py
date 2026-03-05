from schemas.documents import ChunkRecord


class RerankService:
    async def rerank(self, query: str, candidates: list[ChunkRecord], top_n: int) -> list[ChunkRecord]:
        query_lower = query.lower()
        rescored: list[ChunkRecord] = []
        for candidate in candidates:
            item = candidate.model_copy(deep=True)
            score = item.score
            section = (item.metadata.section or "").lower()
            if "root cause" in query_lower and section == "root cause":
                score += 2.0
            if "fixed" in query_lower and section in {"mitigation", "mitigation steps"}:
                score += 2.0
            if "runbook" in query_lower and section in {"immediate checks", "mitigation steps", "escalation"}:
                score += 1.5
            item.score = score
            rescored.append(item)
        rescored.sort(key=lambda row: row.score, reverse=True)
        return rescored[:top_n]
