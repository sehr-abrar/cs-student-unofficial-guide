# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**CS Student Survival Guide** — student-authored advice covering professor reviews, study strategies, course selection, internship recruiting, debugging habits, campus resources, academic integrity, and grad school pathways for undergraduate CS students.

This knowledge is hard to find through official channels because course catalogs, syllabi, and department websites describe policies and content but not teaching style, exam difficulty, real grading practices, or what it actually feels like to be a student in the course. Informal wisdom lives in hallways, Discord servers, and conversations between students, but none of it is searchable or persistent. A student at the start of their degree asking "Which algorithms professor should I take?" or "How do I approach OS without burning out?" has no reliable official source — this system makes that dispersed, peer-to-peer knowledge searchable.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | CS Survival Guide — Introduction | General tips on office hours, emailing professors, and first-week planning | documents/01_intro_cs_survival_tips.txt |
| 2 | Professor Reviews — Algorithms | Student reviews of CS301 (Chen), CS401 (Marcus), CS201 (Williams) | documents/02_professor_reviews_algorithms.txt |
| 3 | Study Strategies | How to study for CS exams: practice problems, rubber duck debugging, interleaving | documents/03_study_strategies_cs.txt |
| 4 | Course Selection Guide | Prerequisite planning, reading RMP correctly, balancing semester load, waitlists | documents/04_course_selection_guide.txt |
| 5 | Internship Recruiting | Timeline, resume advice, Leetcode prep, negotiation, rejection handling | documents/05_internship_recruiting_tips.txt |
| 6 | Debugging and Coding Habits | Debugging process, common mistakes, version control, code style | documents/06_debugging_and_coding_habits.txt |
| 7 | Professor Reviews — Systems | Student reviews of OS (Okonkwo), Networks (Tanaka), Architecture (Vasquez) | documents/07_professor_reviews_systems.txt |
| 8 | Mental Health and Workload | Comparison trap, impostor syndrome, unsustainable workload signs, resources | documents/08_mental_health_and_workload.txt |
| 9 | Campus Resources | CS Help Room, writing center, career services, library resources, peer mentoring | documents/09_campus_resources_for_cs_students.txt |
| 10 | Professor Reviews — ML/AI | Student reviews of ML (Rodriguez), NLP (Kim), Computer Vision (Patel) | documents/10_professor_reviews_ml_and_ai.txt |
| 11 | Academic Integrity Guide | Collaboration policies, common violations, AI tool policies, what to do if accused | documents/11_academic_integrity_guide.txt |
| 12 | Research and Grad School | Finding advisors, PhD applications, timeline for senior year | documents/12_research_and_grad_school.txt |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 50 characters

**Reasoning:** The corpus is a mix of document types. Professor reviews are short and dense (one review ≈ 200–400 characters of opinion about a specific person or course). Guide sections are longer, multi-paragraph advice (study strategies, internship timelines) where a single point spans 3–6 sentences. 400 characters is large enough to capture a complete thought in either case while staying small enough that retrieval returns a focused result rather than half a document.

**Why 50-character overlap:** If a key fact ("she will sit with you for 20 minutes on a single problem") falls near a chunk boundary, it may appear partially in two adjacent chunks, but neither chunk alone is retrievable as a complete idea. A 50-character overlap carries the tail of the previous chunk into the start of the next, so a sentence that straddles a boundary is present in full within at least one chunk.

**Signs of wrong chunk size:**
- *Too small (e.g., 100 characters):* Retrieval returns sentence fragments that lack enough context for the LLM to form a useful answer. A query about "Prof. Chen's exam format" might retrieve "Her exams are fair" with no surrounding detail.
- *Too large (e.g., 1500 characters):* Retrieval returns chunks so broad that they contain both relevant and irrelevant information. The LLM sees noise alongside the answer, increasing the chance of hallucination or a diluted response. Large chunks also reduce the number of distinct chunks retrieved (top-k=4 × 1500 chars ≈ 6000 chars of context, which is wasteful and less precise).

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 4

**Why top-k=4:** 4 chunks × ~400 characters = ~1600 characters of context, which is enough for the LLM to synthesize a complete answer without being overwhelmed. Too few (k=1 or 2) risks missing relevant context when an answer spans multiple sections — e.g., "how hard is OS?" touches both the professor review and the workload guide. Too many (k=10+) floods the prompt with loosely related chunks, increasing cost and the chance the model latches onto irrelevant material.

**Why semantic search works without exact word matches:** Embedding models map text into a high-dimensional vector space where semantically similar phrases land near each other, regardless of surface words. A query like "is the OS course brutal?" produces a vector close to "the projects have almost no scaffolding" even though no word overlaps — both express difficulty and workload. The model learned these associations during pretraining on large corpora. This is why semantic search outperforms keyword search for conversational, opinion-based queries.

**Production tradeoff reflection:** `all-MiniLM-L6-v2` is a 22M-parameter model designed for semantic similarity, runs locally with no API cost, and handles sentence-length inputs well — a good fit for short review excerpts and advice paragraphs. Its main limitations are a 256-token context window (fine for our 400-char chunks) and reduced accuracy on highly domain-specific vocabulary (e.g., course codes, professors' names as proper nouns). In production, I'd weigh switching to `text-embedding-3-small` (OpenAI) for stronger multilingual support and higher accuracy on diverse student language, or `instructor-xl` for the ability to tune the embedding prompt to the retrieval task. Latency is a tradeoff: API-hosted models add network overhead; a local model like MiniLM stays under 50ms per query. For a student-facing tool that should respond quickly with no per-query cost, local embedding is the right default.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Prof. Chen's office hours in the Algorithms course? | Almost no one shows up to her Thursday 3–5pm slot; she will sit with you for 20 minutes on a single problem if you've tried something first |
| 2 | How should I approach a homework problem I've been stuck on for over an hour? | After more than an hour without progress, ask for help — via the CS help room, a TA, or office hours; explain where exactly you're stuck |
| 3 | What is the recruiting timeline for big tech summer internships? | Applications open August–September; online assessments follow; phone rounds November–December — waiting until January means most large companies have already closed |
| 4 | Can I use AI tools like GitHub Copilot on my CS assignments? | Policies vary by course; some ban AI entirely, some allow it with citation, some have no policy — ask your professor in writing before using any AI tool |
| 5 | What are the signs that my course workload has become unsustainable? | Consistently sleeping under 6 hours, unable to eat regularly, missing classes due to exhaustion or anxiety — these are signs to talk to an advisor or counseling center, not push harder |

---

## Anticipated Challenges

1. **Proper noun retrieval (professor names, course codes):** Embedding models treat names like "Okonkwo" or "CS350" as out-of-vocabulary or rare tokens, which may reduce retrieval accuracy for queries that use those exact names. A student asking "what is OS with Prof. Okonkwo like?" relies on the model associating the name with the review document. Mitigation: ensure professor names and course codes appear consistently in the document text and aren't buried only in headings.

2. **Chunk boundary splits for multi-part advice:** Some advice spans multiple paragraphs — for example, the step-by-step debugging process in document 06. If a 400-character chunk cuts mid-step, the retrieved chunk will be incomplete. The 50-character overlap helps but doesn't fully solve this. During evaluation, I'll watch for questions that require 2–3 consecutive chunks to answer fully and consider increasing overlap or hand-splitting those sections.

---

## Architecture

```
Document Ingestion          Chunking               Embedding + Vector Store
─────────────────           ─────────────          ────────────────────────
.txt files in               custom sliding-        sentence-transformers
documents/           ──►    window chunker     ──► all-MiniLM-L6-v2
(12 documents)              (400 chars,            + ChromaDB (local)
                            50 overlap)
                            ingest.py

        │
        ▼
    Retrieval                         Generation
    ─────────                         ──────────
    Query → embed                     Top-4 chunks → context
    → ChromaDB similarity   ──────►   + system prompt (grounding)
      search (top-k=4)               → llama-3.3-70b-versatile
      retrieve.py                      via Groq API
                                     → Answer with source citations
                                       generate.py / app.py
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
I gave Claude the Chunking Strategy section and asked it to implement `load_documents()`, `clean_text()`, and `chunk_text()` in `ingest.py`. Since LangChain is not in `requirements.txt`, it wrote a custom character-level chunker with the same sliding-window logic (chunk_size=400, chunk_overlap=50). I verified by running the script and inspecting 5 random chunks — all substantive, no HTML artifacts. Total: 92 chunks across 12 documents, avg length 371 chars.

**Milestone 4 — Embedding and retrieval:**
I'll give Claude the Retrieval Approach section and the ChromaDB documentation for the local persistent client, asking it to implement `embed_and_store()` and `retrieve()`. I'll verify by running a test query ("what do students say about office hours?") and printing the top-4 returned chunks to confirm they're topically relevant.

**Milestone 5 — Generation and interface:**
I gave Claude the grounding requirement and pipeline diagram and asked it to implement `generate.py` (`ask()`) and `app.py` (Gradio UI). It produced a system prompt with explicit "CRITICAL RULES" instructing the model to answer only from the provided context and decline (not hallucinate) when the documents don't cover a question. Source attribution is programmatic — retrieved filenames are always appended regardless of what the LLM cites. Tested all 3 covered queries (grounded, cited correctly) and 1 out-of-scope query ("best sushi near campus?") — system responded "I don't have enough information in my documents to answer that." Groq model: llama-3.3-70b-versatile, temperature=0.2.
