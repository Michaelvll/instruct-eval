from typing import Optional

from fire import Fire
from pydantic import BaseModel
from transformers import (
    PreTrainedModel,
    PreTrainedTokenizer,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    AutoModelForCausalLM,
    LlamaForCausalLM,
    LlamaTokenizer,
)


class EvalModel(BaseModel, arbitrary_types_allowed=True):
    max_input_length: int = 512
    max_output_length: int = 512

    def run(self, prompt: str) -> str:
        raise NotImplementedError

    def check_valid_length(self, text: str) -> bool:
        raise NotImplementedError


class SeqToSeqModel(EvalModel):
    model_path: str
    model: Optional[PreTrainedModel]
    tokenizer: Optional[PreTrainedTokenizer]
    device: str = "cuda"

    def load(self):
        if self.model is None:
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
            self.model.eval()
            self.model.to(self.device)
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

    def run(self, prompt: str) -> str:
        self.load()
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_length=self.max_output_length)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def check_valid_length(self, text: str) -> bool:
        self.load()
        inputs = self.tokenizer(text)
        return len(inputs.input_ids) <= self.max_input_length


class CausalModel(SeqToSeqModel):
    def load(self):
        if self.model is None:
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
            self.model.eval()
            self.model.to(self.device)
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

    def run(self, prompt: str) -> str:
        self.load()
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_output_length,
            pad_token_id=self.tokenizer.eos_token_id,  # Avoid pad token warning
        )
        batch_size, length = inputs.input_ids.shape
        return self.tokenizer.decode(outputs[0, length:], skip_special_tokens=True)


class LlamaModel(SeqToSeqModel):
    """
    Not officially supported by AutoModelForCausalLM, so we need the specific class
    Also includes the prompt template from: https://github.com/tatsu-lab/stanford_alpaca/blob/main/train.py
    """

    def load(self):
        if self.tokenizer is None:
            self.tokenizer = LlamaTokenizer.from_pretrained(self.model_path)
        if self.model is None:
            self.model = LlamaForCausalLM.from_pretrained(self.model_path)
            self.model.eval()
            self.model.to(self.device)

    def run(self, prompt: str) -> str:
        self.load()
        template = (
            "Below is an instruction that describes a task. "
            "Write a response that appropriately completes the request.\n\n"
            "### Instruction:\n{instruction}\n\n### Response:"
        )

        text = template.format_map(dict(instruction=prompt))
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_output_length,
        )
        batch_size, length = inputs.input_ids.shape
        return self.tokenizer.decode(outputs[0, length:], skip_special_tokens=True)


def select_model(model_name: str, **kwargs) -> EvalModel:
    if model_name == "seq_to_seq":
        return SeqToSeqModel(**kwargs)
    if model_name == "causal":
        return CausalModel(**kwargs)
    if model_name == "llama":
        return LlamaModel(**kwargs)
    raise ValueError(f"Invalid name: {model_name}")


def test_model(
    prompt: str = "Write an email about an alpaca that likes flan.",
    model_name: str = "seq_to_seq",
    model_path: str = "google/flan-t5-base",
):
    model = select_model(model_name, model_path=model_path)
    print(locals())
    print(model.run(prompt))


"""
p modeling.py test_model --model_name causal --model_path gpt2
p modeling.py test_model --model_name llama --model_path decapoda-research/llama-7b-hf
p modeling.py test_model --model_name llama --model_path chavinlo/alpaca-native
"""


if __name__ == "__main__":
    Fire()
