def rewrite_query(query: str) -> list[str]:
    rewrites = [query]

    lower = query.lower()

    if "fixed" in lower:
        rewrites.append(query.replace("fixed", "mitigated"))
        rewrites.append(query.replace("fixed", "resolved"))
        rewrites.append(query.replace("fixed", "mitigation resolved"))
        rewrites.append(query.replace("fixed", "mitigation was"))
        rewrites.append(query.replace("fixed", "resolved the incident"))

    if "what fixed" in lower:
        rewrites.append(query.replace("What fixed", "What mitigation fixed"))
        rewrites.append(query.replace("What fixed", "How was"))
        rewrites.append(query.replace("What fixed", "What was the mitigation for"))

    if "root cause" in lower:
        rewrites.append(query.replace("root cause", "cause"))
        rewrites.append(query.replace("root cause", "why it happened"))

    if "runbook" in lower and "steps" in lower:
        rewrites.append(query.replace("runbook steps", "immediate checks"))
        rewrites.append(query.replace("runbook steps", "mitigation steps"))

    return list(dict.fromkeys(rewrites))
