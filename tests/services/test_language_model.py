import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from src.modules.service.language_model import LanguageModel
import asyncio

class TestLanguageModel(unittest.TestCase):
    @patch('src.modules.service.language_model.requests.post')
    def test_generate_response(self, mock_post):
        # mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': '你好，世界！'}}
            ]
        }
        mock_post.return_value = mock_response

        lm = LanguageModel()
        result = lm.generate_response('你好')
        self.assertEqual(result, '你好，世界！')

    @patch('src.modules.service.language_model.aiohttp.ClientSession')
    def test_generate_response_async(self, mock_session_cls):
        # mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json = AsyncMock(return_value={
            'choices': [
                {'message': {'content': '异步回复'}}
            ]
        })
        # mock session.post().__aenter__() 返回 mock_response
        mock_post_ctx = AsyncMock()
        mock_post_ctx.__aenter__.return_value = mock_response
        mock_session = AsyncMock()
        mock_session.post.return_value = mock_post_ctx
        # mock ClientSession().__aenter__() 返回 mock_session
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        lm = LanguageModel()
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(lm.generate_response_async('async test'))
        self.assertEqual(result, '异步回复')

    @patch('src.modules.service.language_model.aiohttp.ClientSession')
    def test_async_concurrent(self, mock_session_cls):
        # mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json = AsyncMock(return_value={
            'choices': [
                {'message': {'content': '异步回复'}}
            ]
        })
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_session = AsyncMock()
        mock_session.post.return_value = mock_context
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        lm = LanguageModel()

        async def other_task():
            await asyncio.sleep(0.1)
            return 'other done'

        async def run_tasks():
            res1 = asyncio.create_task(lm.generate_response_async('async test'))
            res2 = asyncio.create_task(other_task())
            done, _ = await asyncio.wait([res1, res2])
            results = [task.result() for task in done]
            return results

        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(run_tasks())
        self.assertIn('异步回复', results)
        self.assertIn('other done', results)

if __name__ == '__main__':
    unittest.main()
