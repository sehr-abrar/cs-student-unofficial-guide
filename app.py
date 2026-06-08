"""
app.py — Gradio interface for the CS Unofficial Guide (Milestone 5)

Run with:
    python app.py

Then open http://localhost:7860 in your browser.
"""

import gradio as gr
from generate import ask


def handle_query(question: str):
    if not question.strip():
        return "", ""
    result = ask(question)
    sources_text = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources_text


example_questions = [
    "What do students say about Prof. Chen's office hours in Algorithms?",
    "What is the recruiting timeline for big tech summer internships?",
    "Can I use AI tools like GitHub Copilot on my CS assignments?",
    "How should I approach a homework problem I've been stuck on for an hour?",
    "What are signs my course workload has become unsustainable?",
]

with gr.Blocks(title="CS Unofficial Guide") as demo:
    gr.Markdown(
        """# CS Student Unofficial Guide
        Ask questions about professors, courses, study strategies, internships, and campus resources.
        Answers come only from student-authored documents — the system will say so if it doesn't know."""
    )

    with gr.Row():
        with gr.Column(scale=3):
            question_box = gr.Textbox(
                label="Your question",
                placeholder="e.g. What is Prof. Chen's teaching style like?",
                lines=2,
            )
            submit_btn = gr.Button("Ask", variant="primary")
        with gr.Column(scale=1):
            gr.Markdown("**Try these:**")
            for ex in example_questions:
                gr.Button(ex, size="sm").click(
                    fn=lambda q=ex: q,
                    outputs=question_box,
                )

    answer_box = gr.Textbox(label="Answer", lines=8, interactive=False)
    sources_box = gr.Textbox(label="Retrieved from", lines=4, interactive=False)

    submit_btn.click(handle_query, inputs=question_box, outputs=[answer_box, sources_box])
    question_box.submit(handle_query, inputs=question_box, outputs=[answer_box, sources_box])

if __name__ == "__main__":
    demo.launch()
