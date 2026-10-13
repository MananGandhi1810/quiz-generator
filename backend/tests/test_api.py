from fastapi.testclient import TestClient
from app.main import app
from app.models import Quiz, Question
from app.gemini import GeminiError

client = TestClient(app)

def mock_quiz(count):
    return Quiz(title='Cell biology', questions=[Question(question=f'Question {i}?', options=['A','B','C','D'], correct_answer=1, explanation='From the notes.') for i in range(count)])


def test_health():
    assert client.get('/api/health').json()['status'] == 'ok'


def test_upload_and_cleanup(documents, monkeypatch):
    seen = []
    from app.documents import extract_document
    def capture(path):
        seen.append(path)
        return extract_document(path)
    async def generate(text, count, difficulty):
        assert 'Photosynthesis' in text
        assert difficulty == 'hard'
        return mock_quiz(count)
    monkeypatch.setattr('app.main.extract_document', capture)
    monkeypatch.setattr('app.main.generate_quiz', generate)
    with (documents/'notes.docx').open('rb') as f:
        response = client.post('/api/quiz',files={'file':('notes.docx', f)}, data={'question_count':5,'difficulty':'hard'})
    assert response.status_code == 200
    assert len(response.json()['questions']) == 5
    assert response.json()['source']['filename'] == 'notes.docx'
    assert not seen[0].parent.exists()


def test_invalid_requests():
    assert client.post('/api/quiz',files={'file':('bad.exe',b'x')}).status_code == 415
    assert client.post('/api/quiz',files={'file':('notes.pdf',b'x')},data={'question_count':6}).status_code == 422
    assert client.post('/api/quiz',files={'file':('notes.pdf',b'x')},data={'difficulty':'invalid'}).status_code == 422
    assert client.post('/api/quiz',files={'file':('notes.pdf',b'x')}).status_code == 422


def test_size_limit(monkeypatch):
    monkeypatch.setattr('app.main.MAX_UPLOAD', 10)
    assert client.post('/api/quiz',files={'file':('notes.pdf',b'x'*11)}).status_code == 413


def test_provider_failure(documents, monkeypatch):
    async def fail(*args): raise GeminiError('Quota reached',429)
    monkeypatch.setattr('app.main.generate_quiz', fail)
    response = client.post('/api/quiz',files={'file':('notes.docx',(documents/'notes.docx').read_bytes())})
    assert response.status_code == 429
    assert response.json()['detail'] == 'Quota reached'
