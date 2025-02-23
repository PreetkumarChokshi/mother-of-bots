from dataclasses import dataclass

# need to choose common features here between ollama API
# and openwebUI API

# ollama schema example 
# {
#   "models": [
#     {
#       "name": "codellama:13b",
#       "modified_at": "2023-11-04T14:56:49.277302595-07:00",
#       "size": 7365960935,
#       "digest": "9f438cb9cd581fc025612d27f7c1a6669ff83a8bb0ed86c94fcf4c5440555697",
#       "details": {
#         "format": "gguf",
#         "family": "llama",
#         "families": null,
#         "parameter_size": "13B",
#         "quantization_level": "Q4_0"
#       }
#     }
# ]
# }

# openwebui schema example
# {
#   "data": [
#     {
#       "id": "llava:latest",
#       "name": "llava:latest",
#       "object": "model",
#       "created": 1739075156,
#       "owned_by": "ollama",
#       "ollama": {
#         "name": "llava:latest",
#         "model": "llava:latest",
#         "modified_at": "2025-01-29T02:25:19.238242652Z",
#         "size": 4733363377,
#         "digest": "8dd30f6b0cb19f555f2c7a7ebda861449ea2cc76bf1f44e262931f45fc81d081",
#         "details": {
#           "parent_model": "",
#           "format": "gguf",
#           "family": "llama",
#           "families": [
#             "llama",
#             "clip"
#           ],
#           "parameter_size": "7B",
#           "quantization_level": "Q4_0"
#         },
#         "urls": [
#           0
#         ]
#       }
#     }
#   ]
# }
@dataclass
class AIModel():
    name: str
    parameter_size: str = "Unknown"  # Default to "Unknown"

    def parse_size(self, size_str: str) -> str:
        """Convert various size formats to a standardized format"""
        # Remove spaces and convert to lowercase
        size_str = size_str.lower().replace(" ", "")
        
        # Common size patterns
        if any(size in size_str for size in ["3b", "3bil", "3billion"]):
            return "3B"
        elif any(size in size_str for size in ["7b", "7bil", "7billion"]):
            return "7B"
        elif any(size in size_str for size in ["11b", "11bil", "11billion"]):
            return "11B"
        elif any(size in size_str for size in ["13b", "13bil", "13billion"]):
            return "13B"
        elif any(size in size_str for size in ["27b", "27bil", "27billion"]):
            return "27B"
        elif any(size in size_str for size in ["70b", "70bil", "70billion"]):
            return "70B"
        
        # If no match found
        return "Unknown"

    def __post_init__(self):
        """Clean up parameter size after initialization"""
        if self.parameter_size:
            self.parameter_size = self.parse_size(self.parameter_size)

# for a description of what these do
# https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
# used semanticly meaningful names for things when possible
@dataclass
class ModelOptions():
    max_tokens: int | None = None  # num_predict in API
    temperature: float | None = None
    top_k: int | None = None
    top_p: float | None = None
    context_window_size: int | None = None  # num_ctx in API
    seed: int | None = None
    min_p: float | None = None
    typical_p: float | None = None
    repeat_last_n: int | None = None
    repeat_penalty: float | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    mirostat: int | None = None
    mirostat_tau: float | None = None
    mirostat_eta: float | None = None
    penalize_newline: bool | None = None
    stop: list[str] | None = None
    num_gpu: int | None = None
    main_gpu: int | None = None
    low_vram: bool | None = None
    num_thread: int | None = None
    num_batch: int | None = None
    num_keep: int | None = None

    def validate(self):
        if self.temperature:
            if not isinstance(self.temperature, float):
                raise TypeError(f"temperature must be of type float not type {self.temperature}.")
            if self.temperature < 0 or self.temperature > 1:
                raise ValueError(f"temperature must be between 0 and 1, {self.temperature} is not a valid value")
        
        if self.max_tokens:
            if not isinstance(self.max_tokens, int):
                raise TypeError(f"max_tokens must be of type int not type {self.max_tokens}.")
        
        if self.top_k:
            if not isinstance(self.top_k, int):
                raise TypeError(f"top_k must be of type int not type {self.top_k}.")
            if self.top_k < 0 or self.top_k > 100:
                raise ValueError(f"top_k must be between 0 and 100, {self.top_k} is not a valid value")
        
        if self.top_p:
            if not isinstance(self.top_p, float):
                raise TypeError(f"top_p must be of type float not type {self.top_p}.")
            if self.top_p < 0 or self.top_p > 1:
                raise ValueError(f"top_p must be between 0 and 1, {self.top_p} is not a valid value")
        
        if self.context_window_size:
            if not isinstance(self.context_window_size, int):
                raise TypeError(f"context_window_size must be of type int not type {self.context_window_size}.")
        
        if self.seed:
            if not isinstance(self.seed, int):
                raise TypeError(f"seed must be of type int not type {self.seed}.")
        
        if self.min_p:
            if not isinstance(self.min_p, float):
                raise TypeError(f"min_p must be of type float not type {self.min_p}.")
            if self.min_p < 0 or self.min_p > 1:
                raise ValueError(f"min_p must be between 0 and 1, {self.min_p} is not a valid value")
        
        if self.typical_p:
            if not isinstance(self.typical_p, float):
                raise TypeError(f"typical_p must be of type float not type {self.typical_p}.")
            if self.typical_p < 0 or self.typical_p > 1:
                raise ValueError(f"typical_p must be between 0 and 1, {self.typical_p} is not a valid value")
        
        if self.repeat_last_n:
            if not isinstance(self.repeat_last_n, int):
                raise TypeError(f"repeat_last_n must be of type int not type {self.repeat_last_n}.")
            if self.repeat_last_n < 0:
                raise ValueError(f"repeat_last_n must be greater than 0, {self.repeat_last_n} is not a valid value")
        
        if self.repeat_penalty:
            if not isinstance(self.repeat_penalty, float):
                raise TypeError(f"repeat_penalty must be of type float not type {self.repeat_penalty}.")
            if self.repeat_penalty < 0:
                raise ValueError(f"repeat_penalty must be greater than 0, {self.repeat_penalty} is not a valid value")
        
        if self.presence_penalty:
            if not isinstance(self.presence_penalty, float):
                raise TypeError(f"presence_penalty must be of type float not type {self.presence_penalty}.")
        
        if self.frequency_penalty:
            if not isinstance(self.frequency_penalty, float):
                raise TypeError(f"frequency_penalty must be of type float not type {self.frequency_penalty}.")
        
        if self.mirostat:
            if not isinstance(self.mirostat, int):
                raise TypeError(f"mirostat must be of type int not type {self.mirostat}.")
            if self.mirostat not in [0, 1, 2]:
                raise ValueError(f"mirostat must be 0, 1, or 2, {self.mirostat} is not a valid value")
        
        if self.mirostat_tau:
            if not isinstance(self.mirostat_tau, float):
                raise TypeError(f"mirostat_tau must be of type float not type {self.mirostat_tau}.")
            if self.mirostat_tau < 0:
                raise ValueError(f"mirostat_tau must be greater than 0, {self.mirostat_tau} is not a valid value")
        
        if self.mirostat_eta:
            if not isinstance(self.mirostat_eta, float):
                raise TypeError(f"mirostat_eta must be of type float not type {self.mirostat_eta}.")
            if self.mirostat_eta < 0:
                raise ValueError(f"mirostat_eta must be greater than 0, {self.mirostat_eta} is not a valid value")
        
        if self.penalize_newline is not None:
            if not isinstance(self.penalize_newline, bool):
                raise TypeError(f"penalize_newline must be of type bool not type {self.penalize_newline}.")
        
        if self.stop:
            if not isinstance(self.stop, list):
                raise TypeError(f"stop must be of type list not type {self.stop}.")
            if not all(isinstance(x, str) for x in self.stop):
                raise TypeError("all elements in stop must be of type str")
        
        if self.num_gpu:
            if not isinstance(self.num_gpu, int):
                raise TypeError(f"num_gpu must be of type int not type {self.num_gpu}.")
            if self.num_gpu < 0:
                raise ValueError(f"num_gpu must be greater than 0, {self.num_gpu} is not a valid value")
        
        if self.main_gpu:
            if not isinstance(self.main_gpu, int):
                raise TypeError(f"main_gpu must be of type int not type {self.main_gpu}.")
            if self.main_gpu < 0:
                raise ValueError(f"main_gpu must be greater than 0, {self.main_gpu} is not a valid value")
        
        if self.low_vram is not None:
            if not isinstance(self.low_vram, bool):
                raise TypeError(f"low_vram must be of type bool not type {self.low_vram}.")
        
        if self.num_thread:
            if not isinstance(self.num_thread, int):
                raise TypeError(f"num_thread must be of type int not type {self.num_thread}.")
            if self.num_thread < 0:
                raise ValueError(f"num_thread must be greater than 0, {self.num_thread} is not a valid value")
        
        if self.num_batch:
            if not isinstance(self.num_batch, int):
                raise TypeError(f"num_batch must be of type int not type {self.num_batch}.")
            if self.num_batch < 0:
                raise ValueError(f"num_batch must be greater than 0, {self.num_batch} is not a valid value")
        
        if self.num_keep:
            if not isinstance(self.num_keep, int):
                raise TypeError(f"num_keep must be of type int not type {self.num_keep}.")
            if self.num_keep < 0:
                raise ValueError(f"num_keep must be greater than 0, {self.num_keep} is not a valid value")
            








            

