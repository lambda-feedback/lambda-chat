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
    # TODO: update the test cases

    def test_missing_argument(self):
        arguments = ["answer", "response", "params"]

        for arg in arguments:
            event = {
                "answer": "Hello, World",
                "response": "Hello, World",
                "params": {}
            }
            event.pop(arg)

            result = handler(event, None)

            self.assertEqual(result.get("statusCode"), 400)
    
    def test_correct_arguments(self):
        event = {
            "answer": "Hello, World",
            "response": "Hello, World",
            "params": {}
        }

        result = handler(event, None)

        self.assertEqual(result.get("statusCode"), 200)

    def test_correct_response(self):
        event = {
            "answer": "Hello, World",
            "response": "Hello, World",
            "params": {}
        }

        result = handler(event, None)

        self.assertEqual(result.get("statusCode"), 200)
        