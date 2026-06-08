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

**Reasoning:** The documents are medium-length guide sections separated by headings (e.g., "OFFICE HOURS ARE NOT OPTIONAL", "HOW TO EMAIL A PROFESSOR"). Each section is a self-contained piece of advice — typically 3–8 sentences — making 400 characters a good fit: large enough to capture a complete point, small enough that retrieval returns a focused result rather than an entire document. A 50-character overlap ensures no sentence is split at a chunk boundary without any context carrying over. Long-form documents like the grad school guide have natural section breaks that align well with this size. Professor reviews run slightly longer per entry (~200–400 chars each), so this size typically captures one full review or one clear subsection of advice.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 4

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
.txt files in               CharacterTextSplitter  sentence-transformers
documents/           ──►    (400 chars,        ──► all-MiniLM-L6-v2
(12 documents)              50 overlap)            + ChromaDB (local)
                            via LangChain

        │
        ▼
    Retrieval                         Generation
    ─────────                         ──────────
    Query → embed                     Top-4 chunks → context
    → ChromaDB similarity   ──────►   + system prompt (grounding)
      search (top-k=4)               → Claude claude-haiku-4-5
                                     → Answer with source citations
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
I'll give Claude the Chunking Strategy section of this document and the requirements for `ingest.py`, asking it to implement `load_documents()` (reads all `.txt` files from `documents/`) and `chunk_text()` (uses LangChain's `CharacterTextSplitter` with chunk_size=400, chunk_overlap=50). I'll verify by printing chunk count and the first 3 chunks to check boundaries look reasonable.

**Milestone 4 — Embedding and retrieval:**
I'll give Claude the Retrieval Approach section and the ChromaDB documentation for the local persistent client, asking it to implement `embed_and_store()` and `retrieve()`. I'll verify by running a test query ("what do students say about office hours?") and printing the top-4 returned chunks to confirm they're topically relevant.

**Milestone 5 — Generation and interface:**
I'll give Claude the Evaluation Plan questions and ask it to implement the generation step with a system prompt that restricts the model to only answer from retrieved context. I'll run all 5 evaluation questions and compare outputs to expected answers, then adjust the system prompt grounding instruction if responses go off-document.
