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

    def test_missing_parameters(self):
        # Checking state for missing parameters on default agent
        response = "Hello, World"
        expected_params = Params(include_test_data=True, conversation_history=[{ "type": "user", "content": response }], \
                                    summary="", conversational_style="", \
                                    question_response_details={}, conversation_id="1234Test")

        for p in expected_params:
            params = expected_params.copy()
            # except for the special parameters
            if p not in ["include_test_data", "conversation_id", "conversation_history"]:
                params.pop(p)

                try:
                    result = chat_module(response, params)
                except Exception as e:
                    self.assertTrue("agent could not be invoked" in str(e))
                else:
                    self.assertIsNotNone(result)
                    self.assertEqual("error" in result, False)
            elif p == "include_test_data":
                params.pop(p)

                try:
                    result = chat_module(response, params)
                except Exception as e:
                    self.assertTrue("agent could not be invoked" in str(e))
                else:
                    # check if result has nothing except for the chatbot_response
                    self.assertIsNotNone(result.get("chatbot_response"))
                    self.assertEqual(len(result), 1)
            elif p == "conversation_id":
                params.pop(p)
                
                with self.assertRaises(Exception) as cm:
                    chat_module(response, params)

                self.assertTrue("Internal Error" in str(cm.exception))
                self.assertTrue("conversation id" in str(cm.exception))
            elif p == "conversation_history":
                params.pop(p)

                with self.assertRaises(Exception) as cm:
                    chat_module(response, params)

                if "agent could not be invoked" in str(cm.exception):
                    self.assertTrue("agent could not be invoked" in str(cm.exception))
                else:
                    self.assertTrue("Internal Error" in str(cm.exception))
                    self.assertTrue("conversation history" in str(cm.exception))

    def test_all_agents_output(self):
        # Checking the output of the agents
        agents = ["informational", "socratic"]
        for agent in agents:
            response = "Hello, World"
            params = Params(conversation_id="1234Test", agent_type=agent, conversation_history=[{ "type": "user", "content": response }])

            try:
                result = chat_module(response, params)
            except Exception as e:
                self.assertTrue("agent could not be invoked" in str(e))
            else:
                self.assertIsNotNone(result.get("chatbot_response"))

    def test_unknown_agent_type(self):
        agents = ["unknown"]
        for agent in agents:
            response = "Hello, World"
            params = Params(conversation_id="1234Test", agent_type=agent, conversation_history=[{ "type": "user", "content": response }])

            with self.assertRaises(Exception) as cm:
                chat_module(response, params)

            self.assertTrue("Input Parameter Error:" in str(cm.exception))
            self.assertTrue("Agent Type" in str(cm.exception))

    def test_processing_time_calc(self):
        # Checking the processing time calculation
        response = "Hello, World"
        params = Params(include_test_data=True, conversation_id="1234Test", conversation_history=[{ "type": "user", "content": response }])

        try:
            result = chat_module(response, params)
        except Exception as e:
            self.assertTrue("agent could not be invoked" in str(e))
        else:
            self.assertIsNotNone(result.get("processing_time"))
            self.assertGreaterEqual(result.get("processing_time"), 0)