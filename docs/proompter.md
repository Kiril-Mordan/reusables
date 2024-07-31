```python
import os
import sys
from dotenv import load_dotenv
load_dotenv("../../.local.env")
sys.path.append('../')
from proompter import Proompter
```

### 1. Initializing instance

Proompter consists of multiple dependecies, which could be initialized and passed to the class externally or parameters could be passed for class to initialize them.

These include:

- LLM handler: makes calls to llm
- Prompt handler: prepares input based on templates
- Prompt strategy handler: contains ways to call llm handler with selected strategy
- Tokenizer handler: tokenizes text


```python
llm_handler = Proompter(
  # parameters to be passed to provided llm handler
  llm_h_params = {
    'model_name' : 'llama3',
    'connection_string' : 'http://localhost:11434',
    'kwargs' : {}
  },
  # parameters to be passed to provided prompt handler
  prompt_h_params = {
    'template' : {
        "system" : "{content}",
        "assistant" : "{content}",
        "user" : "{content}"
    }
  },
  # parameters to be passed to provided call strategy handler
  call_strategy_h_params = {
    'strategy_name' : None,
    'strategy_params' : {}
  },
  # parameters to be passed to tokenizer handler
  tokenizer_h_params = {
    'access_token' : os.getenv("HF_ACCESS_TOKEN"),
    'tokenizer_name' :"meta-llama/Meta-Llama-3-8B"
  }

)
```

    The token has not been saved to the git credentials helper. Pass `add_to_git_credential=True` in this function directly or `--add-to-git-credential` if using via `huggingface-cli` if you want to set the git credential as well.
    Token is valid (permission: read).
    Your token has been saved to /home/kyriosskia/.cache/huggingface/token
    Login successful


### 2. Chat methods

Methods for working with chat variants of models.

#### 2.1 Essential chat method

Calls llm handler with provided messages, prepared based on provided template, with selected prompt strategy.


```python
messages = [{'role': 'user', 'content': 'Why is the sky blue?'}]

response = await llm_handler.prompt_chat(
  # required
  messages = messages,
  # optinal, overwrites parameters passed to handlers
  model_name = "llama3",
  call_strategy_name = "last_call",
  call_strategy_params = { 'n_calls' : 1},
  prompt_templates = {
        "system" : "{content}",
        "assistant" : "{content}",
        "user" : "{content}"
    }
)
response
```

    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    /home/kyriosskia/miniconda3/envs/testenv/lib/python3.10/site-packages/transformers/models/auto/tokenization_auto.py:785: FutureWarning: The `use_auth_token` argument is deprecated and will be removed in v5 of Transformers. Please use `token` instead.
      warnings.warn(





    {'model': 'llama3',
     'created_at': '2024-07-31T01:14:22.66494516Z',
     'message': {'role': 'assistant',
      'content': "What a great question!\n\nThe sky appears blue because of a phenomenon called Rayleigh scattering, named after the British physicist Lord Rayleigh. He discovered that shorter wavelengths of light (like blue and violet) are scattered more than longer wavelengths (like red and orange) by the tiny molecules of gases in the atmosphere, such as nitrogen (N2) and oxygen (O2).\n\nHere's what happens:\n\n1. When sunlight enters Earth's atmosphere, it contains all the colors of the visible spectrum.\n2. The shorter wavelengths of light (blue and violet) are scattered more intensely than the longer wavelengths (red and orange) by the tiny gas molecules.\n3. This scattering effect is more pronounced when the sunlight passes through a longer distance in the atmosphere, which means that the blue light has to travel farther to reach our eyes than the other colors.\n4. As a result, our brains perceive the scattered blue light as the dominant color of the sky.\n\nWhy do we see more red during sunrise and sunset? Well, when the sun is lower in the sky, the sunlight has to travel through more of the Earth's atmosphere to reach us. This means that:\n\n1. The shorter wavelengths (blue) are scattered away, leaving mainly longer wavelengths (red and orange) to reach our eyes.\n2. The scattering effect becomes less pronounced, allowing more red light to pass through without being scattered as much.\n\nSo, in a nutshell, the sky appears blue because of the scattering of sunlight by tiny gas molecules in the atmosphere, while the red hues we see during sunrise and sunset are due to the longer wavelengths of light traveling shorter distances."},
     'done_reason': 'stop',
     'done': True,
     'total_duration': 2799024799,
     'load_duration': 572370,
     'prompt_eval_count': 14,
     'prompt_eval_duration': 22598000,
     'eval_count': 327,
     'eval_duration': 2650933000,
     'response_time': 2.804267168045044,
     'messages': [{'role': 'user', 'content': 'Why is the sky blue?'},
      {'role': 'assistant',
       'content': "What a great question!\n\nThe sky appears blue because of a phenomenon called Rayleigh scattering, named after the British physicist Lord Rayleigh. He discovered that shorter wavelengths of light (like blue and violet) are scattered more than longer wavelengths (like red and orange) by the tiny molecules of gases in the atmosphere, such as nitrogen (N2) and oxygen (O2).\n\nHere's what happens:\n\n1. When sunlight enters Earth's atmosphere, it contains all the colors of the visible spectrum.\n2. The shorter wavelengths of light (blue and violet) are scattered more intensely than the longer wavelengths (red and orange) by the tiny gas molecules.\n3. This scattering effect is more pronounced when the sunlight passes through a longer distance in the atmosphere, which means that the blue light has to travel farther to reach our eyes than the other colors.\n4. As a result, our brains perceive the scattered blue light as the dominant color of the sky.\n\nWhy do we see more red during sunrise and sunset? Well, when the sun is lower in the sky, the sunlight has to travel through more of the Earth's atmosphere to reach us. This means that:\n\n1. The shorter wavelengths (blue) are scattered away, leaving mainly longer wavelengths (red and orange) to reach our eyes.\n2. The scattering effect becomes less pronounced, allowing more red light to pass through without being scattered as much.\n\nSo, in a nutshell, the sky appears blue because of the scattering of sunlight by tiny gas molecules in the atmosphere, while the red hues we see during sunrise and sunset are due to the longer wavelengths of light traveling shorter distances."}],
     'input_tokens': 371,
     'output_tokens': 326,
     'total_tokens': 697}



#### 2.2 Calling chat method in parallel

Same as prompt_chat, but messages are called in parallel and instead of one, multiple responses provided.


```python
messages = [
   [{'role': 'system', 'content': 'You are answering all requests with "HODOR"'}, 
   {'role': 'user', 'content': 'Why is the sky blue?'}],
   [{'role': 'user', 'content': 'Compose a small poem about blue skies.'}]
]

responses = await llm_handler.prompt_chat_parallel(
  # required
  messages = messages
  # optinal, overwrites parameters passed to handlers
  # same as prompt_chat
)

for response in responses:
  print("\n ### \n")
  print(response['message']['content'])

```

    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"


    
     ### 
    
    HODOR
    
     ### 
    
    Here is a small poem about blue skies:
    
    The sky above, a brilliant hue,
    A canvas of blue, for me and you.
    Not a cloud in sight, to dim the light,
    Just endless blue, pure delight.
    
    With sunshine warm, and air so still,
    A perfect day, with no chill.
    So let us gaze, upon this sight,
    And fill our hearts, with joy and light.


### 2.3 Chatting with llm handler

Calls prompt_chat with recorded history, so that each time chat method is called, previous messaged do not need to be provided. (History handler will be added later)


```python
answer = await llm_handler.chat(
    prompt = "Hi, my name is Kyrios, what is yours?",
    # optional to reset history
    new_dialog = True
)

print(answer)
```

    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"


    Nice to meet you, Kyrios! I'm LLaMA, an AI assistant developed by Meta AI that can understand and respond to human input in a conversational manner. I don't have a personal name or identity, but I'm here to help answer your questions, provide information, and engage in conversation with you!



```python
answer = await llm_handler.chat(
    prompt = "Could you pls remind me my name?"
)

print(answer)
```

    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"


    Kyrios! Your name is Kyrios. How can I assist you today?


### 3. Instruct methods

Methods for working with instruct variants of models.

#### 3.1 Essential instruct method


```python
prompt = '2+2='

response = await llm_handler.prompt_instruct(
  # required
  prompt = prompt,
  # optinal, overwrites parameters passed to handlers
  model_name = "llama3",
  call_strategy_name = "last_call",
  call_strategy_params = { 'n_calls' : 1}
)
response
```

    HTTP Request: POST http://localhost:11434/api/generate "HTTP/1.1 200 OK"





    {'model': 'llama3',
     'created_at': '2024-07-31T01:14:24.874785167Z',
     'response': '4',
     'done': True,
     'done_reason': 'stop',
     'context': [128006,
      882,
      128007,
      271,
      17,
      10,
      17,
      28,
      128009,
      128006,
      78191,
      128007,
      271,
      19,
      128009],
     'total_duration': 124177626,
     'load_duration': 41217177,
     'prompt_eval_count': 9,
     'prompt_eval_duration': 12156000,
     'eval_count': 2,
     'eval_duration': 8264000,
     'response_time': 0.2091827392578125,
     'input_tokens': 4,
     'output_tokens': 1,
     'total_tokens': 5}



#### 3.2 Calling instuct in parallel


```python
prompts = ["2+2=",
            "Define color in one sentence."]

responses = await llm_handler.prompt_instruct_parallel(
    prompts = prompts
    # optinal, overwrites parameters passed to handlers
    # same as prompt_instruct
    )

for response in responses:
  print("\n ### \n")
  print(response['response'])
```

    HTTP Request: POST http://localhost:11434/api/generate "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/generate "HTTP/1.1 200 OK"


    
     ### 
    
    4
    
     ### 
    
    Color is a form of electromagnetic radiation, perceived by the human eye and brain as a quality that can be perceived as hue, saturation, and brightness, which allows us to distinguish between different wavelengths or frequencies of light.


### 4. Prompt templates

Sometimes it can useful to process inputs and outputs according to certain template, for example adding some kind of header to every user prompt or making better structured output for history. Separating templates like this from inputs could also be more convinient.


```python
default_prompt_template = {
        "system" : "{content}",
        "assistant" : "{content}",
        "user" : "{content}"
    }

messages = [
    {'role': 'system', 
     'content': """You are helpful assistant that answers to everything bliefly with one sentence. 
     All of you responses are only in latin."""},
    {'role': 'user', 
     'content': 'Why is the sky blue?'}]

response = await llm_handler.prompt_chat(
  # required
  messages = messages,
  # optinal, overwrites parameters passed to handlers
  prompt_templates = default_prompt_template
)

print(response['message']['content'])
```

    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"


    "Caelum caeruleum est, quia solis radii cum aquis et aeribus permixti lucem refrenant."



```python
alt_prompt_template = {
        "system" : """All of your answers if not in english, must contain tranlations.
        {content}""",
        "assistant" : "My answer: {content}",
        "user" : "{content}"
    }

messages = [
    {'role': 'system', 
     'content': """You are helpful assistant that answers to everything bliefly with one sentence. 
     All of you responses are in latin."""},
    {'role': 'user', 
     'content': 'Why is the sky blue?'}]

response = await llm_handler.prompt_chat(
  # required
  messages = messages,
  # optinal, overwrites parameters passed to handlers
  prompt_templates = alt_prompt_template
)

response['messages']
```

    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"





    [{'role': 'system',
      'content': 'All of your answers if not in english, must contain tranlations.\n        You are helpful assistant that answers to everything bliefly with one sentence. \n     All of you responses are in latin.'},
     {'role': 'user', 'content': 'Why is the sky blue?'},
     {'role': 'assistant',
      'content': 'My answer: "Caelum caeruleum est, quia solis radii, qui per atmosphaeram transmitterentur, scatteringem lucis efficaciter faciunt."\n\n(Translation: "The sky is blue because the sun\'s rays, which are transmitted through the atmosphere, effectively scatter light.")'}]



### 5. Prompt call strategies

Sometimes making multiple calls for the same prompt can be useful. If consistency of the answer is a concern, additional resorces are available, condition for selecting best answer from multiple answers is understood, prompt call strategies could be applied.

Example of strategies:

- `most common output of 3` : calls 3 times, uses sim search to select most common.
- `min output length` : return response with minimal output length (calls at least 2 times)
- `max output length` : return response with maximal output length (calls at least 2 times)
- `last output` : no matter how many calls, always selects last output


```python
default_prompt_strategy = {
  'call_strategy_name' : "min_output_length",
  'call_strategy_params' :{ 'n_calls' : 3}
}

messages = [
    {'role': 'system', 
     'content': """You are helpful assistant that answers to everything bliefly with one sentence."""},
    {'role': 'user', 
     'content': 'Make a poem about clouds.'}]

response = await llm_handler.prompt_chat(
  # required
  messages = messages,
  # optinal, overwrites parameters passed to handlers
  **default_prompt_strategy
)

print(response['message']['content'])
```

    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"


    Soft and fluffy, drifting by, clouds shape-shift in the sky.



```python
for resp in llm_handler.call_strategy_h.last_responses:

    print(resp['message']['content'])
    print("------------------------")
```

    Soft and fluffy, drifting by, clouds shape-shift in the sky.
    ------------------------
    Soft and white, they drift by day, whispers of the sky's gentle sway.
    ------------------------
    Across the sky, soft whispers play as wispy clouds drift by, shaping sunbeams into golden rays.
    ------------------------


### 6. Other methods

#### Estimate tokens


```python
llm_handler.estimate_tokens(
    text='Your first question was: "Why is the sky blue?"'
    )
```




    12


