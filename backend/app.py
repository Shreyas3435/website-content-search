from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import weaviate
from weaviate.classes.config import Configure, Property, DataType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


embedder = SentenceTransformer('all-MiniLM-L6-v2')


client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    grpc_port=50051
)

def clean_html(html_content):
    """Extract clean text from HTML"""
    soup = BeautifulSoup(html_content, "html.parser")
    
    
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()
    

    text = soup.get_text(separator=" ")
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text

def chunk_text(text, max_tokens=400):
    """Split text into chunks based on token count"""
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    tokens = tokenizer.tokenize(text)
    chunks = []
    
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk = tokenizer.convert_tokens_to_string(chunk_tokens)
        if chunk.strip(): 
            chunks.append(chunk.strip())
    
    return chunks

def ensure_collection_exists():
    """Create the HtmlChunk collection if it doesn't exist"""
    try:
        
        client.collections.get("HtmlChunk")
        logger.info("Collection 'HtmlChunk' already exists")
    except Exception as e:
        
        logger.info("Creating collection 'HtmlChunk'")
        client.collections.create(
            name="HtmlChunk",
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="url", data_type=DataType.TEXT)
            ]
        )

def clear_collection():
    """Clear all data from the collection"""
    try:
        collection = client.collections.get("HtmlChunk")
        collection.data.delete_many(where={})
        logger.info("Cleared collection data")
    except Exception as e:
        logger.error(f"Error clearing collection: {e}")

def store_chunks(chunks, url):
    """Store chunks in Weaviate with embeddings"""
    ensure_collection_exists()
    collection = client.collections.get("HtmlChunk")
    
  
    clear_collection()
    
    data_objects = []
    for chunk in chunks:
       
        embedding = embedder.encode(chunk).tolist()
        
        data_objects.append({
            "content": chunk,
            "url": url,
            "vector": embedding
        })
    
  
    if data_objects:
        with collection.batch.dynamic() as batch:
            for obj in data_objects:
                vector = obj.pop("vector")
                batch.add_object(
                    properties=obj,
                    vector=vector
                )
        logger.info(f"Stored {len(data_objects)} chunks")

def search_chunks(query, limit=10):
    """Search for relevant chunks using vector similarity"""
    collection = client.collections.get("HtmlChunk")
    
   
    query_embedding = embedder.encode(query).tolist()
    
   
    response = collection.query.near_vector(
        near_vector=query_embedding,
        limit=limit,
        return_properties=["content", "url"]
    )
    
    results = []
    for obj in response.objects:
        results.append({
            "content": obj.properties["content"],
            "url": obj.properties.get("url", "")
        })
    
    return results

@app.route("/search", methods=["POST"])
def search():
    """Main search endpoint"""
    data = request.json
    url = data.get("url")
    query = data.get("query")
    
    if not url or not query:
        return jsonify({"error": "URL and query are required"}), 400
    
    try:
        logger.info(f"Fetching URL: {url}")
        
       
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        
        logger.info("Cleaning HTML...")
        clean_text = clean_html(r.text)
        
        if not clean_text or len(clean_text) < 50:
            return jsonify({"error": "Not enough content found on the webpage"}), 400
        
        logger.info(f"Chunking text (length: {len(clean_text)})...")
        chunks = chunk_text(clean_text)
        
        if not chunks:
            return jsonify({"error": "No text chunks created"}), 400
        
        logger.info(f"Storing {len(chunks)} chunks...")
        store_chunks(chunks, url)
        
        logger.info(f"Searching for: {query}")
        matches = search_chunks(query, limit=10)
        
        
        results = [match["content"] for match in matches]
        
        return jsonify({
            "results": results,
            "chunks_processed": len(chunks)
        }), 200
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return jsonify({"error": f"Failed to fetch URL: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    try:
        
        client.collections.list_all()
        return jsonify({"status": "healthy", "weaviate": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

if __name__ == "__main__":
    try:
        ensure_collection_exists()
        logger.info("Backend ready!")
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        client.close()
