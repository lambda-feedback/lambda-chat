import json
import time
import os
try:
    from .parse_json_context_to_prompt import parse_json_to_prompt
    from ..base_agent.base_agent import invoke_base_agent
    from ..informational_agent.informational_agent import InformationalAgent, invoke_informational_agent
    from ..socratic_agent.socratic_agent import invoke_socratic_agent
    from ..informational_agent.informational_prompts import \
        informational_role_prompt, conv_pref_prompt, update_conv_pref_prompt, summary_prompt, update_summary_prompt
except ImportError:
    from src.agents.utils.parse_json_context_to_prompt import parse_json_to_prompt
    from src.agents.base_agent.base_agent import invoke_base_agent
    from src.agents.informational_agent.informational_agent import InformationalAgent, invoke_informational_agent
    from src.agents.socratic_agent.socratic_agent import invoke_socratic_agent
    from src.agents.informational_agent.informational_prompts import \
        informational_role_prompt, conv_pref_prompt, update_conv_pref_prompt, summary_prompt, update_summary_prompt

# File path for the input text
path = "src/agents/utils/"
input_file = path + "example_inputs/" + "example_input_6.json"

"""
 STEP 1: Read the USER INFO from the WEB client from a file
"""
with open(input_file, "r") as file:
    raw_text = file.read()

def testbench_agents(message, remove_index, agent_type = "informational", informational_role_prompt = informational_role_prompt):  
    try:
        """
          STEP 2: Parse the question information from the JSON file
        """
        parsed_json = json.loads(raw_text)
        parsed_json["message"] = message
        parsed_json["params"]["conversation_history"][-1]["content"] = message

        params = parsed_json["params"]

        if "include_test_data" in params:
            include_test_data = params["include_test_data"]
        if "conversation_history" in params:
            conversation_history = params["conversation_history"]
        if "summary" in params:
            summary = params["summary"]
        if "conversational_style" in params:
            conversationalStyle = params["conversational_style"]
        if "question_response_details" in params:
            question_response_details = params["question_response_details"]
            question_submission_summary = question_response_details["questionSubmissionSummary"] if "questionSubmissionSummary" in question_response_details else []
            question_information = question_response_details["questionInformation"] if "questionInformation" in question_response_details else {}
            question_access_information = question_response_details["questionAccessInformation"] if "questionAccessInformation" in question_response_details else {}
            question_response_details_prompt = parse_json_to_prompt(
                question_submission_summary,
                question_information,
                question_access_information
            )
            # print("Question Response Details Prompt:", question_response_details_prompt, "\n\n")
            print("------- Question Submission Summary:", len(question_response_details_prompt), "\n\n")

        # if "agent_type" in params:
        #     agent_type = params["agent_type"]
        if "conversation_id" in params:
            conversation_id = params["conversation_id"]
        else:
            raise Exception("Internal Error: The conversation id is required in the parameters of the chat module.")

        """
        STEP 3: Call the LLM agent to get a response to the user's message
        """
        if agent_type == "socratic":
            invoke = invoke_socratic_agent
        elif agent_type == "informational":
            """
            STEP 4: Update the prompt to verify their performance
            """
            role_prompt_components = informational_role_prompt.split("\n\n")
            main_prompt = role_prompt_components[0]
            teaching_methods = role_prompt_components[1].split("## Teaching Methods:\n")[1].split("\n")
            key_qualities = role_prompt_components[2].split("## Key Qualities:\n")[1].split("\n")
            flexibility_prompt = [item + '.' for item in role_prompt_components[3].split("## Flexibility:\n")[1].split(".") if item]
            governance_prompt = [item + '.' for item in role_prompt_components[-1].split("## Governance:\n")[1].split(".") if item]
            prompts = [main_prompt] + teaching_methods + key_qualities + flexibility_prompt + governance_prompt
            
            
            # Remove one of the prompts to test the agent's performance
            prompt_missing = "None"
            if remove_index >= len(prompts):
                raise Exception("Remove index exceeds the number of prompts available.")
            if remove_index != -1:
                prompt_missing = prompts[remove_index]
                print("Number of prompts:", len(prompts), ", current index:", remove_index, ", prompt removed:", prompt_missing)
                prompts.remove(prompt_missing)

            updated_prompt = "\n\n".join(prompts)

            agent = InformationalAgent(informational_role_prompt=updated_prompt, \
                                        conv_pref_prompt=conv_pref_prompt, \
                                        update_conv_pref_prompt=update_conv_pref_prompt, \
                                        summary_prompt=summary_prompt, \
                                        update_summary_prompt=update_summary_prompt)
            invoke = invoke_informational_agent
        else:
            raise Exception("Unknown Tutor Agent Type")

        response = invoke(query=message, \
                                conversation_history=conversation_history, \
                                summary=summary, \
                                conversationalStyle=conversationalStyle, \
                                question_response_details=question_response_details_prompt, \
                                session_id=conversation_id,
                                agent=agent)
        
        print(response)
        print("AI Response:", response['output'])
        return message, response, updated_prompt, prompt_missing

    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)


if __name__ == "__main__":
    file = path + "synthetic_conversations/" + "prompts_importance.tsv"
    # create the file if it doesnt exist
    if not os.path.exists(file):
        with open(file, "w") as f:
            f.write("message\t response\t prompt_missing\t prompt\n")

    # NOTE: #### This is the testing message!! #####
    message = "What is the question?" 
    # NOTE: ########################################

    index_count = -1 # Number of prompts to be removed for testing (-1 if no removal)
    indices = range(0, index_count) if index_count > -1 else [-1]
    for i in indices:
        # if i == 16:
        #     time.sleep(60)
        message, response, prompt, prompt_missing = testbench_agents(message, remove_index=i)

        with open(file, "a") as f:
            # append another line to the file
            if prompt_missing != " ":
                f.write(message + "\t" + ' '.join(response['output'].split('\n')) + "\t" + prompt_missing + "\t" + ' '.join(prompt.split('\n')) + "\n")
                print("File written successfully!")


