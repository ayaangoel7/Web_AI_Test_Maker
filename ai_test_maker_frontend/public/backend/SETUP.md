# AI Test Maker - Backend Setup

## Quick Start

### 1. Create backend folder
```
mkdir ai-test-maker-backend
cd ai-test-maker-backend
```

### 2. Copy files
Place these files in the folder:
- `server.py` (from public/backend/server.py)
- `ai_engine.py` (your original)
- `pdf_processor.py` (your original)
- `test_generator.py` (your original)
- `test_grader.py` (your original)
- `question_customizer.py` (your original)

### 3. Install dependencies
```bash
pip install fastapi uvicorn python-multipart
pip install -r requirements.txt  # your existing requirements
```

### 4. Run
```bash
python server.py
```

Server starts at `http://0.0.0.0:8000`. Other PCs on LAN access via `http://<server-ip>:8000`.

### 5. Connect frontend
Create `.env` in the React project root:
```
VITE_API_URL=http://localhost:8000
```

For LAN access, set `VITE_API_URL=http://<server-ip>:8000`.

---

## Folder Tree
```
ai-test-maker-backend/
├── server.py
├── ai_engine.py
├── pdf_processor.py
├── test_generator.py
├── test_grader.py
├── question_customizer.py
├── requirements.txt
├── .env
├── models/          (auto-created)
├── uploads/         (auto-created)
├── Dockerfile       (optional)
└── docker-compose.yml (optional)
```

## Docker Setup (Optional)

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fastapi uvicorn python-multipart
COPY . .
EXPOSE 8000
CMD ["python", "server.py"]
```

### docker-compose.yml
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./uploads:/app/uploads
    environment:
      - CORS_ORIGIN=http://localhost:5173
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
```

## Windows Auto-Start
1. Create `run_server.bat`:
```batch
@echo off
cd /d "%~dp0"
python server.py
```
2. Press Win+R, type `shell:startup`, paste a shortcut to the batch file.

## Linux Auto-Start
```bash
# /etc/systemd/system/ai-test-maker.service
[Unit]
Description=AI Test Maker Backend
After=network.target

[Service]
WorkingDirectory=/path/to/backend
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Then: `sudo systemctl enable ai-test-maker`

## Troubleshooting
- **CORS errors**: Ensure `CORS_ORIGIN` in server.py matches your frontend URL
- **Models not loading**: Check VRAM (needs ~4GB for Phi-3 4-bit)
- **Upload fails**: Check `uploads/` folder permissions
- **LAN access**: Ensure firewall allows port 8000
