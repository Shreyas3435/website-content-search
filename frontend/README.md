# Website Content Search

## Stack
- Frontend: React (Create React App)
- Backend: Python (Flask)
- Vector Database: Weaviate (Docker, v4 API)
- HTML Parsing: BeautifulSoup
- Chunking: transformers (bert-base-uncased tokenizer)

## Getting Started

### 1. Start Vector DB

$ docker run -d --name weaviate -p 8080:8080 -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true -e ENABLE_MODULES=none -e CLUSTER_JOIN=none -e QUERY_DEFAULTS_LIMIT=25 -e GRPC_ENABLED=false semitechnologies/weaviate:1.27.0

### 2. Backend

cd backend
python -m venv venv
Source venv\Scripts\activate       
pip install -r requirements.txt
python app.py


### 3. Frontend

cd frontend
npm install
npm start


### 4. Usage
- Open [http://localhost:3000](http://localhost:3000)
- Enter a website URL and query. See top 10 results.

