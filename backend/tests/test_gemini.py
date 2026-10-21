import asyncio
import httpx
import pytest
from app.gemini import generate_quiz, GeminiError
from test_api import mock_quiz

@pytest.fixture(autouse=True)
def mock_research(monkeypatch):
    async def research(*args):
        return {'summary': 'Verified research fact.', 'sources': [{'title': 'Reference', 'url': 'https://example.com'}]}
    monkeypatch.setattr('app.gemini.research_topic', research)


@pytest.mark.parametrize('status,expected', [(429,429),(403,503),(500,502)])
def test_error_mapping(monkeypatch,status,expected):
    monkeypatch.setenv('GEMINI_API_KEY','test-key')
    async def post(*args,**kwargs): return httpx.Response(status,json={})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    with pytest.raises(GeminiError) as error: asyncio.run(generate_quiz('notes',5,'easy'))
    assert error.value.status == expected

@pytest.mark.parametrize('case',['valid','wrong_count','invalid_json','blocked'])
def test_response_validation(monkeypatch,case):
    monkeypatch.setenv('GEMINI_API_KEY','test-key')
    data={'candidates':[{'content':{'parts':[{'text':mock_quiz(5 if case=='valid' else 2).model_dump_json()}]}}]}
    if case=='invalid_json': data['candidates'][0]['content']['parts'][0]['text']='invalid'
    if case=='blocked': data={'promptFeedback':{'blockReason':'SAFETY'}}
    async def post(*args,**kwargs): return httpx.Response(200,json=data)
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    if case=='valid': assert len(asyncio.run(generate_quiz('notes',5,'easy')).questions)==5
    else:
        with pytest.raises(GeminiError): asyncio.run(generate_quiz('notes',5,'easy'))


def test_invalid_answer_choices():
    from pydantic import ValidationError
    from app.models import Question
    with pytest.raises(ValidationError):
        Question(question='Which?', options=['A','A','C','D'], correct_answer=0, explanation='Reason')
    with pytest.raises(ValidationError):
        Question(question='Which?', options=['A','B','C','D'], correct_answer=4, explanation='Reason')
    with pytest.raises(ValidationError):
        Question(question=' ', options=['A','B','C','D'], correct_answer=0, explanation='Reason')


def test_research_used_before_writing(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    async def post(*args, **kwargs):
        payload = kwargs['json']
        assert 'Verified research fact.' in payload['contents'][0]['parts'][0]['text']
        assert 'research' not in payload['generationConfig']['responseJsonSchema']['properties']
        return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': mock_quiz(5).model_dump_json()}]}}]})
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    quiz = asyncio.run(generate_quiz('notes', 5, 'easy'))
    assert quiz.research['sources'][0]['url'] == 'https://example.com'
