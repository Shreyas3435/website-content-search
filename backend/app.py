from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import nltk
from transformers import AutoTokenizer
import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout, Auth

nltk.download("punkt")
app = Flask(__name__)
CORS(app)

client = weaviate.WeaviateClient(
    ConnectionParams(
        http={"host": "localhost", "port": 8080, "secure": False},
        grpc={"host": "localhost", "port": 0, "secure": False}  # dummy grpc, will be skipped
    ),
    skip_init_checks=True
)

def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text(separator=" ")

def chunk_text(text, max_tokens=500):
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    tokens = tokenizer.tokenize(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = tokenizer.convert_tokens_to_string(tokens[i : i + max_tokens])
        chunks.append(chunk)
    return chunks

def ensure_class_exists():
    client.connect()
    try:
        client.collections.get("HtmlChunk")
    except weaviate.WeaviateApiError:  # Class does not exist
        client.collections.create(
            name="HtmlChunk",
            vectorizer_config="text2vec-transformers",
            properties=[{"name": "content", "dataType": "text"}]
        )

def store_chunks(chunks):
    client.connect()
    ensure_class_exists()
    collection = client.collections.get("HtmlChunk")
    for chunk in chunks:
        collection.data.insert({"content": chunk})

def search_chunks(query):
    client.connect()
    collection = client.collections.get("HtmlChunk")
    result = collection.query.near_text(
        query=query,
        limit=10,
        return_properties=["content"]
    )
    return [obj.properties["content"] for obj in result.objects]

@app.route("/search", methods=["POST"])
def search():
    data = request.json
    url = data.get("url")
    query = data.get("query")
    try:
        r = requests.get(url)
        r.raise_for_status()
        clean_text = clean_html(r.text)
        chunks = chunk_text(clean_text)
        store_chunks(chunks)
        matches = search_chunks(query)
        return jsonify(matches), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)