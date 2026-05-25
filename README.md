# HCAI-ITS

## Structure

```
HCAI-ITS/
├── frontend/          # React
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI routes
│   │   ├── domain/              # core business logic
│   │   ├── application/         # workflows/use-cases
│   │   ├── infrastructure/      # concrete tech implementations
│   │   ├── schemas/             # request/response models
│   │   ├── config/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
└── docs/
```

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Frontend

See [frontend/README.md](frontend/README.md).