import unittest

try:
    from .module import Params, chat_module
except ImportError:
    from module import Params, chat_module

class TestChatModuleFunction(unittest.TestCase):
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

    def test_module_default_true(self):
        response, answer, params = "Hello, World", "Hello, World", Params()

        result = chat_module(response, answer, params)

        self.assertEqual(result.get("is_correct"), True)
