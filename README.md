# Fake News Detector — AI Project

An AI-powered web application that detects fake news using NLP models. Built during internship at GLP Software — reduced fake news detection time by 35%.

## Features

- Real-time news article classification (real vs fake)
- BERT-based NLP model for high accuracy
- REST API backend with FastAPI
- Clean web interface for easy use

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Model | BERT (HuggingFace Transformers) |
| Embeddings | SentenceTransformers |
| Vector Search | Qdrant |
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |

## How It Works

```
Input: News article text
    → Tokenized with BERT tokenizer
    → Embeddings generated
    → Similarity search in Qdrant
    → Classification: Real / Fake
    → Confidence score returned
```

## Getting Started

```bash
git clone https://github.com/AkezhanY/Fake-News-Detector-Ai-Project
cd Fake-News-Detector-Ai-Project
pip install -r requirements.txt
uvicorn main:app --reload
```

## Results

- 35% reduction in manual fake news detection time (production use at GLP Software)
- Integrated into live content moderation pipeline

## Author

**Akezhan Yergali** — [LinkedIn](https://linkedin.com/in/akezhan-yergali) | [GitHub](https://github.com/AkezhanY)
