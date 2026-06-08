# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This system is a **CS Student Survival Guide** — a searchable collection of student-authored advice covering professor reviews, study strategies, course selection, internship recruiting, debugging habits, campus resources, academic integrity policies, and grad school pathways for undergraduate CS students.

This knowledge is valuable because official channels — course catalogs, syllabi, and department websites — describe policies and content but not teaching style, real exam difficulty, grading culture, or what it actually feels like to be a student in the course. Informal peer wisdom lives in hallways and Discord servers but is not persistent or searchable. A student asking "Which algorithms professor should I take?" or "What are the signs I'm burning out?" has no reliable official source. This system makes that dispersed, peer-to-peer knowledge searchable through natural-language queries.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | CS Survival Guide — Introduction | Plain text guide | documents/01_intro_cs_survival_tips.txt |
| 2 | Professor Reviews — Algorithms | Student reviews | documents/02_professor_reviews_algorithms.txt |
| 3 | Study Strategies for CS | Student advice guide | documents/03_study_strategies_cs.txt |
| 4 | Course Selection Guide | Student advice guide | documents/04_course_selection_guide.txt |
| 5 | Internship Recruiting Tips | Student advice guide | documents/05_internship_recruiting_tips.txt |
| 6 | Debugging and Coding Habits | Student advice guide | documents/06_debugging_and_coding_habits.txt |
| 7 | Professor Reviews — Systems | Student reviews | documents/07_professor_reviews_systems.txt |
| 8 | Mental Health and Workload | Student advice guide | documents/08_mental_health_and_workload.txt |
| 9 | Campus Resources | Student resource guide | documents/09_campus_resources_for_cs_students.txt |
| 10 | Professor Reviews — ML/AI | Student reviews | documents/10_professor_reviews_ml_and_ai.txt |
| 11 | Academic Integrity Guide | Student advice guide | documents/11_academic_integrity_guide.txt |
| 12 | Research and Grad School | Student advice guide | documents/12_research_and_grad_school.txt |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 50 characters

**Why these choices fit your documents:** The corpus mixes two document types: short, dense professor reviews (one review ≈ 200–400 chars) and longer multi-paragraph advice sections (study strategies, internship timelines). 400 characters is large enough to capture a complete thought in either case — a full professor review or a single piece of advice — while staying small enough that retrieval returns focused results rather than half a document. The 50-character overlap carries the tail of one chunk into the start of the next, so a sentence that straddles a boundary is fully present in at least one chunk.

**Final chunk count:** 92 chunks across 12 documents (avg length 371 chars, all non-empty).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (local, no API key required)

**Production tradeoff reflection:** `all-MiniLM-L6-v2` is a 22M-parameter model trained for semantic similarity that runs locally with no per-query cost and sub-50ms latency per encoding. Its 256-token context window fits our 400-character chunks cleanly. The main limitation is reduced accuracy on domain-specific proper nouns — professor names like "Okonkwo" and course codes like "CS350" are rare or out-of-vocabulary tokens, so queries using those exact names may not retrieve the right chunks as reliably as queries phrased in general language.

In production, I would evaluate `text-embedding-3-small` (OpenAI) for stronger accuracy on diverse student language and better handling of informal writing style, and `instructor-xl` for its ability to condition the embedding on a task-specific prompt (e.g., "represent this student review for retrieval"). The tradeoff is API latency and per-query cost versus local speed. For a student-facing tool that needs to respond quickly with no operational cost, local embedding is the right default; for a deployed product at scale, API-hosted embeddings with caching are worth the added complexity.

---

## Grounded Generation

**System prompt grounding instruction:**

```
You are a helpful assistant for an Unofficial CS Student Survival Guide.
Answer questions about CS courses, professors, study strategies, internships, and campus resources.

CRITICAL RULES:
1. Answer ONLY using information explicitly stated in the DOCUMENTS section below.
2. Do NOT use your general training knowledge, even if you think you know the answer.
3. Do NOT make up details, infer information, or fill gaps with plausible-sounding content.
4. If the provided documents do not contain enough information to answer the question,
   respond with exactly: "I don't have enough information in my documents to answer that."
5. When the documents do contain the answer, be specific and quote or closely paraphrase
   what they say. Keep your answer concise and direct.
```

The user message then passes the retrieved chunks as a numbered list — `[1] (source: filename)\n{chunk text}` — followed by the question and an instruction to cite source numbers inline.

**How source attribution is surfaced in the response:** Attribution is **programmatic and guaranteed** — `generate.py` always appends the list of retrieved source filenames to the response dict regardless of what the LLM includes inline. The LLM is also instructed to cite `[1]`, `[2]`, etc. within its answer text, but even if it fails to do so, the source list is still returned and displayed in the UI's "Retrieved from" panel.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Prof. Chen's office hours in the Algorithms course? | Thursday 3–5pm slot, almost no one goes, she'll work with you for 20 min if you've tried first | Quoted exact Thursday 3–5pm detail and the 20-minute offer; cited [2] from the algorithms review doc | Relevant | Accurate |
| 2 | How should I approach a homework problem I've been stuck on for over an hour? | After >1 hour without progress, ask for help via CS help room, TA, or office hours; explain where you're stuck | Mentioned rubber duck method (30-min threshold) and "write down where you're stuck" from the study strategies doc — missed the specific "after an hour, ask for help" passage | Partially relevant | Partially accurate |
| 3 | What is the recruiting timeline for big tech summer internships? | Apps open August–September; OAs follow; offers November–December; January is too late | Correctly cited August–October applications, OA process, HackerRank; cited [1] from the recruiting doc | Relevant | Accurate |
| 4 | Can I use AI tools like GitHub Copilot on my CS assignments? | Policies vary; some courses ban AI, some allow with citation, some have no policy — ask your professor in writing | Listed all three policy variations accurately and cited [1]; added "ask the professor" advice | Relevant | Accurate |
| 5 | What are the signs that my course workload has become unsustainable? | Sleeping under 6 hours consistently, unable to eat regularly, missing classes from exhaustion/anxiety | Enumerated all three signs correctly from the mental health doc; cited [1] | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "How should I approach a homework problem I've been stuck on for over an hour?"

**What the system returned:** The model described the rubber duck debugging method (explain the problem out loud when stuck for more than 30 minutes) and advised writing down where you got stuck. Both pieces of advice are real and in the documents — but neither is the direct answer to the question. The expected answer ("after more than an hour without progress, that's when you ask for help") appears in `06_debugging_and_coding_habits.txt` under the heading "HOW LONG SHOULD THIS TAKE?"

**Root cause (tied to a specific pipeline stage):** **Retrieval stage.** The top source returned was `03_study_strategies_cs.txt`, not `06_debugging_and_coding_habits.txt`. The query phrase "stuck on a homework problem for over an hour" semantically aligned more closely with the study strategies document — which discusses getting stuck on practice problems during exam prep — than with the debugging document. Within `06_debugging_and_coding_habits.txt`, the "HOW LONG SHOULD THIS TAKE?" section contains the exact answer, but that chunk was ranked lower than the study strategies chunks because the embedding model found the study strategies context a slightly stronger semantic match for "stuck on homework."

This is a case where two documents cover related territory (being stuck, asking for help) and the model's embedding similarity score could not distinguish "stuck on a practice problem during exam prep" from "stuck on a homework assignment." The 400-char chunk size meant the "how long should this take" section was isolated in one chunk, and that chunk lost the retrieval competition to the study strategies chunks.

**What you would change to fix it:** Increase `top_k` from 4 to 6 so that more chunks are passed to the LLM — the correct chunk from `06_debugging_and_coding_habits.txt` likely appears at rank 5 or 6. Alternatively, restructure the debugging document so the "after one hour, ask for help" advice appears in the same chunk as other "stuck debugging" context, improving its retrieval signal.

---

## Spec Reflection

**One way the spec helped you during implementation:**

The Chunking Strategy section of `planning.md` forced me to commit to specific numbers (400 chars, 50 overlap) and write out the reasoning before writing any code. When I ran the first chunk inspection and saw the average length was 371 characters — close to but not equal to 400 — I understood immediately that this was expected behavior from the sliding window, not a bug, because I had already thought through how the chunker worked. Without the spec, I might have spent time debugging correct behavior. The written reasoning also made it easy to spot the one real issue that did need fixing: `---` separator lines appearing in chunks as artifacts. Because I had documented what "clean" meant (substantive content only, no formatting noise), I had a clear standard to check against.

**One way your implementation diverged from the spec, and why:**

The spec's AI Tool Plan specified using LangChain's `CharacterTextSplitter` for chunking. During implementation, I found that LangChain is not listed in the project's `requirements.txt`, and adding it would pull in a large dependency tree for a component I could implement in 15 lines of Python. The sliding-window logic in `chunk_text()` is equivalent to `CharacterTextSplitter` with the same parameters — I confirmed this by checking LangChain's source. The spec was updated to reflect the custom implementation. This divergence improved the project: the final `ingest.py` has zero external dependencies beyond the standard library, making it easier to understand and debug.

---

## AI Usage

**Instance 1 — Ingestion and chunking pipeline**

- *What I gave the AI:* The Chunking Strategy and Documents sections from `planning.md`, the pipeline architecture diagram, and the constraint that LangChain was not available as a dependency.
- *What it produced:* `ingest.py` with `load_documents()`, `clean_text()`, `chunk_text()`, and `build_chunks()`. The chunker implemented the correct sliding-window logic. The cleaning function stripped `Source:`/`URL:` header lines and normalized whitespace.
- *What I changed or overrode:* The first version did not strip the `---` markdown separator lines that appeared throughout the documents. After running the chunk inspection and seeing `---` appear in the middle of chunks, I added a `re.fullmatch(r"-{3,}", stripped)` check to the cleaning function. I also added the chunk length statistics output (`min`, `max`, `avg`) to the inspection block, which the AI had not included but which turned out to be useful for confirming the chunker was behaving correctly.

**Instance 2 — Grounded generation and Gradio interface**

- *What I gave the AI:* The Retrieval Approach and Evaluation Plan sections from `planning.md`, the grounding requirement (answer only from retrieved context, decline if not covered), the output format (answer + source list), and the Groq API as the LLM backend.
- *What it produced:* `generate.py` with `ask()` — a system prompt with numbered CRITICAL RULES, a `format_context()` helper that formats retrieved chunks as a numbered list, and a Groq API call with `temperature=0.2`. Also produced `app.py` with a Gradio Blocks interface.
- *What I changed or overrode:* The initial system prompt used softer language ("try to answer only from the documents"). I rewrote it to use explicit imperative rules ("Answer ONLY using information explicitly stated in the DOCUMENTS section below") and tested the grounding by asking a question the documents don't cover ("best sushi near campus"). The first version returned a plausible non-answer; after the rule tightening, it correctly responded "I don't have enough information in my documents to answer that." I also added `temperature=0.2` (the AI's default was 0.7), which reduced hedging language and made responses more concise and direct.
