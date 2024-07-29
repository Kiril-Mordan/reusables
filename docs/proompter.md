```python
import os
import sys
from dotenv import load_dotenv
load_dotenv("../../.local.env")
sys.path.append('../')
from proompter import Proompter
```


```python
llm_handler = Proompter(
  llm_h_params = {
    'model_name' : 'llama3',
    'connection_string' : 'http://localhost:11434',
    'kwargs' : {}
  },
  prompt_h_params = {
    'template' : {
        "system" : "{content}",
        #"assistant" : "{content}",
        "user" : "{content}"
    }
  },
  call_strategy_h_params = {
    'strategy_name' : "most_common_output_of_3",
    'strategy_params' : { 'n_calls' : 3}
  },
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



```python
messages = [{'role': 'user', 'content': 'Why is the sky blue?'}]

response = await llm_handler.prompt_chat(
  messages = messages,
  call_strategy_name = "most_common_output_of_3",
)
response
```

    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    /home/kyriosskia/miniconda3/envs/testenv/lib/python3.10/site-packages/transformers/models/auto/tokenization_auto.py:785: FutureWarning: The `use_auth_token` argument is deprecated and will be removed in v5 of Transformers. Please use `token` instead.
      warnings.warn(





    {'model': 'llama3',
     'created_at': '2024-07-29T02:32:43.374701555Z',
     'message': {'role': 'assistant',
      'content': "The sky appears blue because of a phenomenon called scattering, which is the result of a combination of factors involving light, air molecules, and our atmosphere.\n\nHere's what happens:\n\n1. **Sunlight**: The sun emits white light, which is made up of all the colors of the visible spectrum (red, orange, yellow, green, blue, indigo, and violet).\n2. **Atmosphere**: When this sunlight enters Earth's atmosphere, it encounters tiny molecules of gases like nitrogen (N2) and oxygen (O2). These molecules are much smaller than the wavelength of light.\n3. **Scattering**: As the light interacts with these molecules, it scatters in all directions. This scattering is more pronounced for shorter wavelengths, like blue and violet light, which have a higher energy level than longer wavelengths, like red and orange light.\n4. **Blue dominance**: Because blue light is scattered more efficiently by the atmosphere's molecules, it appears to us as the dominant color of the sky during the daytime. This is known as Rayleigh scattering, named after the British physicist Lord Rayleigh, who first described the phenomenon in the late 19th century.\n\nOther factors can influence the apparent color of the sky:\n\n* **Dust and water vapor**: Tiny particles in the atmosphere, like dust, smoke, and water droplets, can scatter light in different ways, making the sky appear more hazy or gray.\n* **Sun position**: The angle at which sunlight enters the Earth's atmosphere also affects its perceived color. During sunrise and sunset, when the sun is lower on the horizon, longer wavelengths of light (like red and orange) are able to reach our eyes, giving the sky a more reddish hue.\n* **Atmospheric conditions**: Weather conditions like pollution, cloud cover, or severe weather events can alter the apparent color of the sky.\n\nIn summary, the sky appears blue because of the scattering of sunlight by tiny molecules in the atmosphere, which favors shorter wavelengths like blue light."},
     'done_reason': 'stop',
     'done': True,
     'total_duration': 7636719512,
     'load_duration': 1625585950,
     'prompt_eval_duration': 8176000,
     'eval_count': 406,
     'eval_duration': 3284520000,
     'response_time': 11.817609786987305,
     'messages': [{'role': 'user', 'content': 'Why is the sky blue?'},
      {'role': 'assistant',
       'content': "The sky appears blue because of a phenomenon called scattering, which is the result of a combination of factors involving light, air molecules, and our atmosphere.\n\nHere's what happens:\n\n1. **Sunlight**: The sun emits white light, which is made up of all the colors of the visible spectrum (red, orange, yellow, green, blue, indigo, and violet).\n2. **Atmosphere**: When this sunlight enters Earth's atmosphere, it encounters tiny molecules of gases like nitrogen (N2) and oxygen (O2). These molecules are much smaller than the wavelength of light.\n3. **Scattering**: As the light interacts with these molecules, it scatters in all directions. This scattering is more pronounced for shorter wavelengths, like blue and violet light, which have a higher energy level than longer wavelengths, like red and orange light.\n4. **Blue dominance**: Because blue light is scattered more efficiently by the atmosphere's molecules, it appears to us as the dominant color of the sky during the daytime. This is known as Rayleigh scattering, named after the British physicist Lord Rayleigh, who first described the phenomenon in the late 19th century.\n\nOther factors can influence the apparent color of the sky:\n\n* **Dust and water vapor**: Tiny particles in the atmosphere, like dust, smoke, and water droplets, can scatter light in different ways, making the sky appear more hazy or gray.\n* **Sun position**: The angle at which sunlight enters the Earth's atmosphere also affects its perceived color. During sunrise and sunset, when the sun is lower on the horizon, longer wavelengths of light (like red and orange) are able to reach our eyes, giving the sky a more reddish hue.\n* **Atmospheric conditions**: Weather conditions like pollution, cloud cover, or severe weather events can alter the apparent color of the sky.\n\nIn summary, the sky appears blue because of the scattering of sunlight by tiny molecules in the atmosphere, which favors shorter wavelengths like blue light."}],
     'input_tokens': 449,
     'output_tokens': 405,
     'total_tokens': 854}




```python
llm_handler.estimate_tokens(text='Your first question was: "Why is the sky blue?"')
```




    12




```python
messages = [
   [{'role': 'system', 'content': 'You are answering all requests with "HODOR"'}, 
   {'role': 'user', 'content': 'Why is the sky blue?'}],
   [{'role': 'user', 'content': 'Compose a poem about blue skies.'}],
   [{'role': 'user', 'content': 'Who was Nietzsche?'}],
   [{'role': 'user', 'content': 'What is black metal, is it similar to death metal?'}],
   [{'role': 'user', 'content': 'How to run ollama in parallel?'}],
   [{'role': 'user', 'content': """Would the following run promp_chat in parallel, why does it take longer to run it with more messages?
   
async def prompt_chat_parallel(self,
                                    messages : list, 
                                    model_name : str = None):

        messages = messages.copy()

        if model_name is None: 
            model_name = self.model_name
        
        outputs = [self.prompt_chat(messages = [message], 
                                    model_name = model_name) for message in messages]

        responses = await asyncio.gather(*outputs)                            

        return responses
   """}]
]

llm_handler = Proompter(
  llm_h_params = {
    'model_name' : 'llama3',
    'connection_string' : 'http://localhost:11434',
    'kwargs' : {}
  },
  prompt_h_params = {
    'template' : {
        "system" : "{content}",
        #"assistant" : "{content}",
        "user" : "{content}"
    }
  },
  call_strategy_h_params = {
    'strategy_name' : "min_output_length",
    'strategy_params' : { 'n_calls' : 2}
  },
  tokenizer_h_params = {
    'access_token' : os.getenv("HF_ACCESS_TOKEN"),
    'tokenizer_name' :"meta-llama/Meta-Llama-3-8B"
  }
)

responses = await llm_handler.prompt_chat_parallel(
  messages = messages
)
len(responses)
```

    The token has not been saved to the git credentials helper. Pass `add_to_git_credential=True` in this function directly or `--add-to-git-credential` if using via `huggingface-cli` if you want to set the git credential as well.
    Token is valid (permission: read).
    Your token has been saved to /home/kyriosskia/.cache/huggingface/token
    Login successful


    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"





    6




```python
responses[0]
```




    {'model': 'llama3',
     'created_at': '2024-07-29T02:32:48.131501359Z',
     'message': {'role': 'assistant', 'content': 'HODOR'},
     'done_reason': 'stop',
     'done': True,
     'total_duration': 126780820,
     'load_duration': 1170641,
     'prompt_eval_count': 30,
     'prompt_eval_duration': 13535000,
     'eval_count': 4,
     'eval_duration': 24421000,
     'response_time': 0.16721415519714355,
     'messages': [{'role': 'system',
       'content': 'You are answering all requests with "HODOR"'},
      {'role': 'user', 'content': 'Why is the sky blue?'},
      {'role': 'assistant', 'content': 'HODOR'}],
     'input_tokens': 55,
     'output_tokens': 3,
     'total_tokens': 58}




```python
llm_handler = Proompter(
  llm_h_params = {
    'model_name' : 'llama3:instruct',
    'connection_string' : 'http://localhost:11434',
    'kwargs' : {}
  }
)


await llm_handler.prompt_instruct(prompt = "Add 2 plus 2 return only answer")
```

    HTTP Request: POST http://localhost:11434/api/generate "HTTP/1.1 200 OK"
    Tokenizer was not defined, estimation will be skipped!
    Tokenizer was not defined, estimation will be skipped!





    {'model': 'llama3:instruct',
     'created_at': '2024-07-29T02:33:22.96562296Z',
     'response': '4',
     'done': True,
     'done_reason': 'stop',
     'context': [128006,
      882,
      128007,
      271,
      2261,
      220,
      17,
      5636,
      220,
      17,
      471,
      1193,
      4320,
      128009,
      128006,
      78191,
      128007,
      271,
      19,
      128009],
     'total_duration': 82332982,
     'load_duration': 466571,
     'prompt_eval_count': 14,
     'prompt_eval_duration': 12071000,
     'eval_count': 2,
     'eval_duration': 8010000,
     'response_time': 0.1672065258026123,
     'input_tokens': None,
     'output_tokens': None,
     'total_tokens': None}




```python
responses = await llm_handler.prompt_instruct_parallel(prompts = ["Add 2 plus 2 return only answer",
"Why is the sky blue? Return simple explanation.",
"Define color in one sentence."])

len(responses)
```

    HTTP Request: POST http://localhost:11434/api/generate "HTTP/1.1 200 OK"
    Tokenizer was not defined, estimation will be skipped!
    Tokenizer was not defined, estimation will be skipped!
    HTTP Request: POST http://localhost:11434/api/generate "HTTP/1.1 200 OK"
    Tokenizer was not defined, estimation will be skipped!
    Tokenizer was not defined, estimation will be skipped!
    HTTP Request: POST http://localhost:11434/api/generate "HTTP/1.1 200 OK"
    Tokenizer was not defined, estimation will be skipped!
    Tokenizer was not defined, estimation will be skipped!





    3




```python
print(responses[2]['response'])
```

    Color is the property of an object that is perceived by the human eye and brain as a result of the way it reflects or emits light, causing it to appear red, blue, green, yellow, or any other hue.

