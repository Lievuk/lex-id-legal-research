# Lex-ID — Legal Research Agent for Indonesian Law

A multi-step retrieval agent that answers complex legal questions over the Indonesian legal corpus: UU (Undang-Undang), Perpres, Permen, plus 200,000+ Mahkamah Agung judgments. Built for law firms that cannot ship case files to a cloud LLM.

## Why this exists

Generic LLMs hallucinate citations. Indonesian lawyers spend 6–14 hours per case cross-referencing statutes, regulations, and judgments by hand. We tested ChatGPT and Claude on 240 sample queries from a Jakarta firm — the output cited non-existent UU articles 31% of the time and misquoted MA judgments 42% of the time. Unusable.

Lex-ID solves this by grounding every answer in retrieved primary sources, with a planner-decomposer that splits a query into sub-questions before any retrieval happens.

## Architecture

```
Question
   │
   ▼
[Planner]  ── decomposes into 3–7 sub-queries (statute lookup, judgment search, regulation cross-ref)
   │
   ▼
[Retriever] ── BM25 + dense (BGE-M3) hybrid over corpus partitioned by source
   │              ├── UU/Perpres/Permen index (37k docs)
   │              ├── MA Putusan index (216k docs)
   │              └── Fatwa MUI / SE OJK index (8k docs)
   ▼
[Reasoner] ── synthesizes answer with required-citation enforcement
   │
   ▼
[Verifier] ── re-reads each cited source and rejects synthetic citations
   │
   ▼
Final answer (markdown with footnoted citations)
```

## Why on-prem

Law firms cannot legally send client matter to a third-party API in most cases — privileged communication and client confidentiality rules under Kode Etik Advokat. We run the inference layer on a single workstation with 2× RTX 4090 (vLLM, AWQ-quantized 70B class). The retrieval index lives on the same machine.

## Status

Pilot since Sep 2025 with 18 lawyers across 4 firms in Jakarta. Median time to a citable answer dropped from 4h 12m to 9m 30s. False-citation rate measured at 0.7% on the 240-query benchmark (vs 31% baseline).

## Why MiMo

I want to evaluate MiMo as the reasoner step. Current setup uses a 70B model that maxes a single workstation; MiMo's reported reasoning quality at smaller parameter counts would mean we can run the full pipeline on a single 4090, which lowers the upfront hardware cost for smaller firms by roughly 6×.

## Stack

- Retrieval: Elasticsearch + sentence-transformers (BGE-M3)
- Inference: vLLM with AWQ quantization
- Orchestration: LangGraph (planner-reasoner-verifier loop)
- Storage: PostgreSQL for case sessions, S3-compatible (MinIO) for source PDFs
- Frontend: SvelteKit (single-tenant, on-prem)

## License

MIT for the framework code in this repo. The legal corpus is sourced from public records (peraturan.bpk.go.id, putusan3.mahkamahagung.go.id) and is not redistributed here.
