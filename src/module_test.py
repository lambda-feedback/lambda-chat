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
    # TODO: update the test cases

    def test_module_default_true(self):
        response, answer, params = "Hello, World", "Hello, World", Params(conversation_id="1234Test")

        result = chat_module(response, answer, params)

        self.assertEqual(result.get("is_correct"), True)

    def test_missing_parameters(self):
        # Checking state for missing parameters
        response, answer, params = "Hello, World", "Hello, World", \
            Params()
        expected_params = Params(include_test_data=True, conversation_history=[], \
                                    summary="", conversational_style="", \
                                    question_response_details="", conversation_id="1234Test")

        for p in expected_params:
            params = expected_params.copy()
            # except for the special parameters
            if p not in ["include_test_data", "conversation_id"]:
                params.pop(p)

                result = chat_module(response, answer, params)

                self.assertIsNotNone(result.get("metadata"))
                self.assertEqual("error" in result.get("metadata"), False)
            elif p == "include_test_data":
                params.pop(p)

                result = chat_module(response, answer, params)

                self.assertIsNone(result.get("metadata"))
            elif p == "conversation_id":
                params.pop(p)

                result = chat_module(response, answer, params)

                self.assertEqual("error" in result.get("metadata"), True)

    def test_agent_output(self):
        # Checking the output of the agents
        response, answer, params = "Hello, World", "Hello, World", \
            Params(conversation_id="1234Test")

        result = chat_module(response, answer, params)

        self.assertIsNotNone(result.get("feedback"))
    
    def test_processing_time_calc(self):
        # Checking the processing time calculation
        response, answer, params = "Hello, World", "Hello, World", \
            Params(include_test_data=True, conversation_id="1234Test")

        result = chat_module(response, answer, params)

        self.assertIsNotNone(result.get("processing_time"))
        self.assertGreaterEqual(result.get("processing_time"), 0)