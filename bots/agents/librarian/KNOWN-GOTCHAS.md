# Librarian-specific gotchas

(Hand-edited.)

- **FAISS index must be rebuilt** after large archive changes. `librarian.reindex()` takes 3-5 min - warn the operator.
- **Embed model `nomic-embed-text` must be pulled** in Ollama before reindex. Failing fast on a missing model.
- **Grep fallback is slow** on first call (no keyword shards yet) - tell the operator if `mode: "grep"` is returned to consider running the indexer.
