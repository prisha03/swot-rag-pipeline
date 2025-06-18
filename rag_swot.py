rag_swot.py (final)

import numpy as np
import nltk
import re
from sentence_transformers import SentenceTransformer, util
from embed_store import model
import subprocess

nltk.download('punkt')

SWOT_QUESTIONS = {
    "Strengths": "What are the company's internal advantages that support its success?",
    "Weaknesses": "What are the internal challenges or limitations the company is facing?",
    "Opportunities": "What external trends or market conditions could the company capitalize on?",
    "Threats": "What external risks or uncertainties could negatively affect the company?"
}

sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
TOP_K = 5
MODEL_NAME = "llama3"

def retrieve_top_k(question, vectorstore, k=TOP_K):
    question_embedding = model.encode([question])
    _, indices = vectorstore["index"].search(np.array(question_embedding), k)
    return [vectorstore["chunks"][i] for i in indices[0]]

def query_ollama(prompt, model_name=MODEL_NAME):
    command = ["ollama", "run", model_name]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, _ = process.communicate(input=prompt)
    return output.strip()

def find_support_excerpt(bullet, sentences, window=1):
    bullet_emb = sentence_model.encode(bullet, convert_to_tensor=True)
    sent_embs = sentence_model.encode(sentences, convert_to_tensor=True)
    cosine_scores = util.pytorch_cos_sim(bullet_emb, sent_embs)
    best_idx = int(cosine_scores.cpu().argmax())
    start = max(0, best_idx - window)
    end = min(len(sentences), best_idx + window + 1)
    return " ".join(sentences[start:end])

def clean_bullet_line(line):
    return line.strip("- •\n")

def generate_swot(vectorstore):
    swot_output = {}
    transcript_sentences = nltk.sent_tokenize(" ".join(vectorstore["chunks"]))

    for category, question in SWOT_QUESTIONS.items():
        top_chunks = retrieve_top_k(question, vectorstore)
        context = "\n\n".join(top_chunks)

        prompt = f"""
You are a strategic business analyst. Generate a boardroom-ready SWOT analysis for the category: **{category}**.

Use this format for each bullet:
[Business fact] → [Strategic implication]

Guidelines:
- Be concise (1 sentence per bullet)
- Focus on substance, not fluff
- Use insights from the context below
- List 3 to 4 points only

### Context:
{context}

Now list the {category}:
"""

        response = query_ollama(prompt)
        raw_lines = re.split(r'\n+|\d+\.\s+|[-•]\s+', response)
        raw_bullets = [clean_bullet_line(line) for line in raw_lines if line.strip()]

        swot_output[category] = []
        for bullet in raw_bullets[:4]:
            quote = find_support_excerpt(bullet, transcript_sentences)
            swot_output[category].append({"point": bullet, "support": quote})

    return swot_output
