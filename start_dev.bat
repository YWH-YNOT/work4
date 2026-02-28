@echo off
echo Starting AI_YWH Agentic Architecture MVP



echo Starting FastAPI Backend...
cd backend
start cmd /c "call venv\Scripts\activate && uvicorn main:app --port 8002 --reload"

echo Starting Vue3 Frontend (Premium Design)...
cd ..\frontend
start cmd /c "npm run dev"

echo System started successfully!
echo Backend API available at http://localhost:8001/docs
echo Frontend UI available at http://localhost:5173
echo Please ensure you set OPENAI_API_KEY in backend environment to test OCR and Chat!
