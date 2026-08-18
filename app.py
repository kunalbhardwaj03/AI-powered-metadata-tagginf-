import os
from flask import Flask, render_template, request, jsonify
import spacy
from collections import Counter
import re

app = Flask(__name__)

# Load a small English model for NLP processing
# Load a small English model for NLP processing
try:
    import en_core_web_sm
    nlp = en_core_web_sm.load()
except Exception:
    class BlankNLP:
        def __init__(self): pass
        def __call__(self, text): return BlankDoc(text)
    class BlankDoc:
        def __init__(self, text):
            self.text = text
            self.ents = []
            self.sents = [BlankSent(text)]
            self.tokens = text.split()
        def __iter__(self):
            return iter([BlankToken(t) for t in self.tokens])
    class BlankSent:
        def __init__(self, text): self.text = text
    class BlankToken:
        def __init__(self, text):
            self.text = text
            self.is_stop = False
            self.is_punct = False
    nlp = BlankNLP()

def extract_metadata(text):
    if not text.strip():
        return {
            "entities": [],
            "keywords": [],
            "summary": "No transcript provided.",
            "metrics": {"word_count": 0, "char_count": 0, "reading_time_min": 0}
        }
    
    doc = nlp(text)
    
    # 1. Named Entity Recognition (NER)
    entities = []
    seen_entities = set()
    for ent in doc.ents:
        entity_key = (ent.text.strip(), ent.label_)
        if entity_key not in seen_entities and len(ent.text.strip()) > 1:
            entities.append({"text": ent.text.strip(), "label": ent.label_})
            seen_entities.add(entity_key)
            
    # 2. Keyword Extraction (filtering stop words, punctuation, and checking frequency)
    words = [token.text.lower() for token in doc if not token.is_stop and not token.is_punct and len(token.text.strip()) > 2]
    word_freq = Counter(words)
    keywords = [word for word, count in word_freq.most_common(7)]
    
    # 3. Simple Extractive Rule-based Summary (Fallback if advanced summarizer is not configured)
    sentences = [sent.text.strip() for sent in doc.sents]
    if len(sentences) <= 2:
        summary = " ".join(sentences)
    else:
        summary = " ".join(sentences[:2]) + " ... " + sentences[-1]

    # 4. Document Metrics
    word_count = len(text.split())
    char_count = len(text)
    reading_time = round(word_count / 200, 1) # Avg 200 WPM
    if reading_time == 0 and word_count > 0:
        reading_time = 0.1
        
    return {
        "entities": entities[:10], # Limit to top 10 for layout cleanliness
        "keywords": keywords,
        "summary": summary,
        "metrics": {
            "word_count": word_count,
            "char_count": char_count,
            "reading_time_min": reading_time
        }
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    transcript = data.get('transcript', '')
    metadata = extract_metadata(transcript)
    return jsonify(metadata)

if __name__ == '__main__':
    # Bind to PORT if provided by environment, default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
