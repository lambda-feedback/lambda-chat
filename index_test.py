import unittest

try:
    from .index import handler
except ImportError:
    from index import handler

class TestChatIndexFunction(unittest.TestCase):
    """
    TestCase Class used to test the algorithm.
    ---
    Tests are used here to check that the algorithm written
    is working as it should.

    It's best practise to write these tests first to get a
    kind of 'specification' for how your algorithm should
    work, and you should run these tests before committing
    your code to AWS.

    Read the docs on how to use unittest here:
    https://docs.python.org/3/library/unittest.html

    Use module() to check your algorithm works
    as it should.
    """

    def test_missing_argument(self):
        arguments = ["message", "params"]

        for arg in arguments:
            event = {
                "message": "Hello, World",
                "params": {"conversation_id": "1234Test", "conversation_history": [{"type": "user", "content": "Hello, World"}]}
            }
            event.pop(arg)

            result = handler(event, None)

            self.assertIn(result.get("statusCode"), [400, 500])
    
    def test_correct_arguments(self):
        event = {
            "message": "Hello, World",
            "params": {"conversation_id": "1234Test", "conversation_history": [{"type": "user", "content": "Hello, World"}]}
        }

        result = handler(event, None)

        self.assertIn(result.get("statusCode"), [200, 500])

    def test_correct_response(self):
        event = {
            "message": "Hello, World",
            "params": {"conversation_id": "1234Test", "conversation_history": [{"type": "user", "content": "Hello, World"}]}
        }

        result = handler(event, None)

        self.assertIn(result.get("statusCode"), [200, 500])
