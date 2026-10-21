import asyncio

import httpx
import pytest

from app.gemini import GeminiError
from app.research import research_topic


@pytest.mark.parametrize('case', ['valid', 'no_sources', 'no_search', 'unsafe_url', 'blocked', 'quota', 'timeout'])
def test_grounded_research(monkeypatch, case):
    metadata = {
        'webSearchQueries': ['photosynthesis educational overview'],
        'groundingChunks': [{'web': {'uri': 'https://example.com/biology', 'title': 'Biology'}}],
        'searchEntryPoint': {'renderedContent': '<div>Search suggestions</div>'},
    }
    if case == 'no_sources':
        metadata['groundingChunks'] = []
    if case == 'no_search':
        metadata['webSearchQueries'] = []
    if case == 'unsafe_url':
        metadata['groundingChunks'][0]['web']['uri'] = 'javascript:alert(1)'

    async def post(*args, **kwargs):
        assert kwargs['json']['tools'] == [{'google_search': {}}]
        assert 'responseMimeType' not in kwargs['json']['generationConfig']
        if case == 'timeout':
            raise httpx.ReadTimeout('timeout')
        if case == 'quota':
            return httpx.Response(429)
        data = {'candidates': [{'content': {'parts': [{'text': 'Plants convert light into chemical energy.'}]}, 'groundingMetadata': metadata}]}
        if case == 'blocked':
            data = {'promptFeedback': {'blockReason': 'SAFETY'}}
        return httpx.Response(200, json=data)

    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    if case == 'valid':
        result = asyncio.run(research_topic('Photosynthesis notes', 'test-key', 'gemini-2.5-flash'))
        assert result['sources'] == [{'title': 'Biology', 'url': 'https://example.com/biology'}]
        assert result['search_entry_point'] == '<div>Search suggestions</div>'
    else:
        with pytest.raises(GeminiError) as error:
            asyncio.run(research_topic('notes', 'test-key', 'gemini-2.5-flash'))
        assert error.value.status == {'quota': 429, 'timeout': 504}.get(case, 502)
