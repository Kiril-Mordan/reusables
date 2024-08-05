```python
import os
import sys
from dotenv import load_dotenv
load_dotenv("../../.local.env")
sys.path.append('../')
from proompter import Proompter
```

    /home/kyriosskia/miniconda3/envs/testenv/lib/python3.10/site-packages/tqdm/auto.py:21: TqdmWarning: IProgress not found. Please update jupyter and ipywidgets. See https://ipywidgets.readthedocs.io/en/stable/user_install.html
      from .autonotebook import tqdm as notebook_tqdm


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
     'created_at': '2024-08-05T04:57:00.847696577Z',
     'message': {'role': 'assistant',
      'content': "The sky appears blue because of a phenomenon called scattering, which involves the interaction between light, tiny molecules in the atmosphere, and our eyes. Here's a simplified explanation:\n\n1. **Sunlight**: When sunlight enters Earth's atmosphere, it consists of all the colors of the visible spectrum (red, orange, yellow, green, blue, indigo, and violet).\n2. **Molecules**: The atmosphere is made up of tiny molecules like nitrogen (N2) and oxygen (O2). These molecules are much smaller than the wavelength of light.\n3. **Scattering**: When sunlight hits these molecules, it scatters in all directions. This scattering effect is more pronounced for shorter wavelengths of light, such as blue and violet.\n4. **Blue dominance**: As a result of this scattering, the shorter wavelengths of light (blue and violet) are dispersed throughout the atmosphere, reaching our eyes from multiple angles. This is why the sky appears blue during the daytime, especially when the sun is overhead.\n5. **Other factors**: The color of the sky can be influenced by other atmospheric conditions, such as:\n\t* Dust and pollution particles: These can scatter light in various ways, changing the apparent color of the sky.\n\t* Water vapor: High humidity can cause the sky to appear more hazy or gray.\n\t* Clouds: Clouds can reflect and absorb light, affecting the overall color of the sky.\n\nSo, to summarize, the blue color we see in the sky is primarily due to the scattering of sunlight by tiny molecules in the atmosphere. The shorter wavelengths of light (blue and violet) are preferentially scattered, giving our skies their familiar blue hue."},
     'done_reason': 'stop',
     'done': True,
     'total_duration': 2893315343,
     'load_duration': 763924,
     'prompt_eval_count': 11,
     'prompt_eval_duration': 22698000,
     'eval_count': 339,
     'eval_duration': 2745388000,
     'response_time': 2.8988137245178223,
     'messages': [{'role': 'user', 'content': 'Why is the sky blue?'},
      {'role': 'assistant',
       'content': "The sky appears blue because of a phenomenon called scattering, which involves the interaction between light, tiny molecules in the atmosphere, and our eyes. Here's a simplified explanation:\n\n1. **Sunlight**: When sunlight enters Earth's atmosphere, it consists of all the colors of the visible spectrum (red, orange, yellow, green, blue, indigo, and violet).\n2. **Molecules**: The atmosphere is made up of tiny molecules like nitrogen (N2) and oxygen (O2). These molecules are much smaller than the wavelength of light.\n3. **Scattering**: When sunlight hits these molecules, it scatters in all directions. This scattering effect is more pronounced for shorter wavelengths of light, such as blue and violet.\n4. **Blue dominance**: As a result of this scattering, the shorter wavelengths of light (blue and violet) are dispersed throughout the atmosphere, reaching our eyes from multiple angles. This is why the sky appears blue during the daytime, especially when the sun is overhead.\n5. **Other factors**: The color of the sky can be influenced by other atmospheric conditions, such as:\n\t* Dust and pollution particles: These can scatter light in various ways, changing the apparent color of the sky.\n\t* Water vapor: High humidity can cause the sky to appear more hazy or gray.\n\t* Clouds: Clouds can reflect and absorb light, affecting the overall color of the sky.\n\nSo, to summarize, the blue color we see in the sky is primarily due to the scattering of sunlight by tiny molecules in the atmosphere. The shorter wavelengths of light (blue and violet) are preferentially scattered, giving our skies their familiar blue hue."}],
     'input_tokens': 378,
     'output_tokens': 338,
     'total_tokens': 716}



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
    
    Blue skies, so calm and bright
    A canvas of serenity in sight
    No clouds to mar the view
    Just endless blue, pure and true
    
    The sun shines down with gentle might
    Warming the earth, banishing night
    A blue expanse that's free from fear
    Invigorating all who draw near


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


    Nice to meet you, Kyrios! I'm LLaMA, an AI assistant developed by Meta AI that can understand and respond to human input in a conversational manner. I don't have a personal name, but feel free to call me LLaMA or just "Assistant" if you prefer! What brings you here today?



```python
answer = await llm_handler.chat(
    prompt = "Could you pls remind me my name?"
)

print(answer)
```

    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"


    Your name is Kyrios, isn't it?


Streaming variant is also available.


```python
generator = llm_handler.chat_stream(
    prompt = "Could you pls remind me my name?"
)
async for message in generator:
    print(message)

```

    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"


    I
     already
     did
    !
     Your
     name
     is
     Ky
    rios
    .
    


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
     'created_at': '2024-08-05T04:57:53.582111792Z',
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
     'total_duration': 146273731,
     'load_duration': 1145419,
     'prompt_eval_count': 9,
     'prompt_eval_duration': 12819000,
     'eval_count': 2,
     'eval_duration': 8360000,
     'response_time': 0.19240951538085938,
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


