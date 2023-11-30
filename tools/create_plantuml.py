import os
from dotenv import load_dotenv
from openai import OpenAI
import argparse


# Set up argument parser
parser = argparse.ArgumentParser(description='Generate PlantUML code from module.')
parser.add_argument('module_name', type=str, help='Name of the module')
args = parser.parse_args()

# Use the argument
module_name = args.module_name
#module_name = "mock_vector_database"

# parameters

chat_paramters = {
    'model' : "gpt-3.5-turbo",
    'temperature' : 0.0,  # Set to 0 for maximum determinism
    'max_tokens' : 500,   # Adjust based on how long you want the responses to be
    'stop' : None,       # Define any stopping sequence if necessary
    'top_p' : 1,         # Set to 1 for deterministic behavior
    'frequency_penalty' : 0,  # Set to 0 to avoid penalizing repetition
    'presence_penalty' : 0    # Set to 0 to avoid penalizing new topics
}

system_meessage = "You are knowledgeble sofware engineer and you always give a precises solution silently."

prompt_shell = """{code}

Given the code above, please create a code for planUML tool to create a state diagram. The code should work and not have too many nested elements.
Respond  only with the plantuml code and nothing else but the code.
"""


LOCAL_ID = os.getenv('TERM_PROGRAM')
if LOCAL_ID:
    load_dotenv('../.env')

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# connect to OpenAI API
client = OpenAI(api_key=OPENAI_API_KEY)

# read code
module_file_path = f'python_modules/{module_name}.py'
with open(module_file_path, 'r') as file:
        code_content = file.read()


# compose input for completion
prompt_for_chat = prompt_shell.format(code = code_content)
messages = [
    {"role": "system", "content": system_meessage},
    {"role": "user", "content": prompt_for_chat}
  ]

# request completion
completion = client.chat.completions.create(
  messages=messages,
  **chat_paramters
)

# get plantum code
plantuml_code = completion.choices[0].message.content

# save plantum code
plantuml_file_path = f'plantuml/{module_name}.txt'

with open(plantuml_file_path, 'w') as file:
    file.write(plantuml_code)

print(f"Plantum code for {module_name} has been saved to {plantuml_file_path}.")





