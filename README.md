## Phase II — Model Selection & Optimization

### 1. Model Selection
We selected **Qwen2.5-1.5B-Instruct** (`qwen2.5:1.5b`), quantized at **Q4_K_M** (986 MB footprint).
* **Rationale:** It strictly adheres to the 0.5B–4B parameter restriction while remaining fast and responsive on CPU architectures without requiring GPU offloading. Its instruction-tuning provides high fidelity to negative constraints and conversational guardrails.

### 2. Context Memory Management Scheme
To keep the prompt bounded within CPU inference constraints:
* **Initial Intent Anchoring:** Turns 0 and 1 (user's initial vehicle/booking intent and the assistant's initial response) are permanently preserved at the head of the dialogue history.
* **Sliding Window:** As the session exceeds `max_history_turns = 5` (10 messages), the system retains the anchored initial pair and trims older turns, keeping only the most recent 8 messages.
* **State Injection:** Core parameters (e.g., active rental stage) are injected into the delimited `<dialogue_state>` system prompt rather than relying on an unbounded raw text append.

### 3. Latency Benchmarks (CPU Hardware)
* Processor / Machine: Intel Core i7
* Time to First Token (TTFT): 8942.81 ms
* Generated Tokens : 509
* Tokens Per Second: 9.36 tokens/sec
* Quantization Format: Q4_K_M via Ollama runtime