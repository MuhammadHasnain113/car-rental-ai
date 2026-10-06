import time
import httpx

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"

TEST_PROMPT = (
    "A customer wants to rent a compact SUV for 4 days with full insurance. "
    "Provide a detailed daily cost breakdown and explain the damage waiver policy."
)

def run_benchmark():
    payload = {
        "model": MODEL_NAME,
        "prompt": TEST_PROMPT,
        "stream": True,
        "options": {"temperature": 0.2}
    }
    
    start_time = time.perf_counter()
    first_token_time = None
    total_tokens = 0

    print(f"Benchmarking model: {MODEL_NAME} on local CPU...\n")
    
    with httpx.Client(timeout=60.0) as client:
        with client.stream("POST", OLLAMA_GENERATE_URL, json=payload) as response:
            for line in response.iter_lines():
                if not line:
                    continue
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                total_tokens += 1

    end_time = time.perf_counter()

    ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else 0
    total_duration = end_time - start_time
    generation_duration = end_time - first_token_time if first_token_time else total_duration
    tokens_per_sec = total_tokens / generation_duration if generation_duration > 0 else 0

    print("=" * 45)
    print("           BENCHMARK RESULTS")
    print("=" * 45)
    print(f"Time to First Token (TTFT): {ttft_ms:.2f} ms")
    print(f"Total Response Time       : {total_duration:.2f} s")
    print(f"Generated Tokens          : {total_tokens}")
    print(f"Inference Speed           : {tokens_per_sec:.2f} tokens/sec")
    print("=" * 45)

if __name__ == "__main__":
    run_benchmark()