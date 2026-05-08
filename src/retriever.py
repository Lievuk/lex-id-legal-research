"""
Hybrid BM25 + dense retrieval over partitioned indexes.
Each source type lives in its own Elasticsearch index so we can target specific corpora.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RetrievedDoc:
    doc_id: str
    source_type: str
    title: str
    text: str
    score: float
    url: Optional[str] = None


class HybridRetriever:
    def __init__(self, es_client, embed_fn, bm25_weight: float = 0.4):
        self.es = es_client
        self.embed = embed_fn
        self.bm25_weight = bm25_weight

    def search(self, query: str, source_types: List[str], top_k: int = 8) -> List[RetrievedDoc]:
        query_vec = self.embed(query)
        results: List[RetrievedDoc] = []
        for st in source_types:
            index = f"lex-id-{st}"
            body = {
                "size": top_k,
                "query": {
                    "script_score": {
                        "query": {
                            "bool": {
                                "should": [
                                    {"match": {"text": query}},
                                ]
                            }
                        },
                        "script": {
                            "source": (
                                f"({self.bm25_weight} * _score) + "
                                f"({1 - self.bm25_weight} * cosineSimilarity(params.query_vector, \"vec\") + 1.0)"
                            ),
                            "params": {"query_vector": query_vec},
                        },
                    }
                },
            }
            resp = self.es.search(index=index, body=body)
            for hit in resp["hits"]["hits"]:
                src = hit["_source"]
                results.append(RetrievedDoc(
                    doc_id=hit["_id"],
                    source_type=st,
                    title=src.get("title", ""),
                    text=src.get("text", ""),
                    score=hit["_score"],
                    url=src.get("url"),
                ))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
