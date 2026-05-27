# Document Extractor

A FastAPI-based AI-powered document extraction system that can upload, process, classify, and extract information from documents.

---

## Features

* Upload documents using API
* Extract text and important information
* AI-based document classification
* FastAPI backend support
* Database integration
* REST API endpoints
* Structured project architecture
* Environment variable support using `.env`

---

## Tech Stack

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* Uvicorn
* SQLite/MySQL

---

## Project Structure

```bash
Document-Extractor/
│
├── app/
│   ├── api/
│   ├── database/
│   ├── schemas/
│   ├── services/
│   └── main.py
│
├── templates/
├── uploads/
├── tests/
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-username/document-extractor.git
cd document-extractor
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / Mac

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file and add:

```env
DATABASE_URL=your_database_url
API_KEY=your_api_key
```

---

## Run the Project

```bash
uvicorn app.main:app --reload
```

Server will run at:

```bash
http://127.0.0.1:8000
```

---

## API Documentation

Swagger UI:

```bash
http://127.0.0.1:8000/docs
```

ReDoc:

```bash
http://127.0.0.1:8000/redoc
```

---

## Git Ignore

Recommended `.gitignore`:

```bash
venv/
.env
__pycache__/
*.pyc
```

---

## Future Improvements

* OCR support
* PDF parsing
* AI summarization
* Multi-language extraction
* Authentication system
* Cloud deployment

---

## Author

Chinmay Dalvi

GitHub: [https://github.com/ChinmayDalvi09](https://github.com/ChinmayDalvi09)
