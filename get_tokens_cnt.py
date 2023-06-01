import os
import json

from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained('models/llama-7b', use_fast=False)

def find_string_and_tokenize(d):
    if isinstance(d, str):
        return len(tokenizer.tokenize(d))
    token_cnt = 0
    if isinstance(d, list):
        for item in d:
            token_cnt += find_string_and_tokenize(item)
    elif isinstance(d, dict):
        for item in d.values():
            token_cnt += find_string_and_tokenize(item)
    return token_cnt
    

# traverse
for file in os.listdir('training_data'):
    if file.endswith('.json'):
        with open(os.path.join('training_data', file)) as f:
            data = json.load(f)
        token_cnt = find_string_and_tokenize(data)
        print(f'{file}: {token_cnt}')
        
