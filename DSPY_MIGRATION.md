# DSPy Migration and OpenAI-Compatible API Strategy

## Current Status

- **Installed**: DSPy 2.4.9
- **Latest**: DSPy 3.1.2
- **Strategy**: Support both 2.x and 3.x APIs with unified abstraction

## Key Findings

### 1. Ollama Supports OpenAI-Compatible API ✅

```bash
# Test confirmed working:
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:3b-instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

### 2. DSPy API Evolution

#### DSPy 2.x (Current: 2.4.9)
```python
# Old way - provider-specific classes
import dspy
lm = dspy.OpenAI(model="gpt-4", api_key="...")
dspy.configure(lm=lm)

# Also available in 2.4.9:
lm = dspy.LM(model="custom")  # Generic LM class
lm = dspy.OllamaLocal(model="llama3")
```

#### DSPy 3.x (Latest: 3.1.2)
```python
# New unified API - LiteLLM-style provider prefixes
import dspy

# OpenAI
lm = dspy.LM('openai/gpt-4o-mini', api_key='...')

# Ollama
lm = dspy.LM('ollama_chat/llama3.2', api_base='http://localhost:11434')

# vLLM (Nemotron on Koyeb)
lm = dspy.LM('openai/nvidia/nemotron-3-8b-instruct', 
             api_base='https://nemotron.../v1')

dspy.configure(lm=lm)
```

### 3. Breaking Changes (2.4.9 → 3.x)

- ❌ `dspy.OpenAI()`, `dspy.Google()`, `dspy.Anthropic()` deprecated
- ✅ Use unified `dspy.LM("provider/model")` instead
- ❌ Community retrievers removed
- ❌ Python 3.9 support dropped (3.10+ required)
- ✅ Native async support added
- ✅ Better observability with MLflow 3.0

## Our Strategy: Unified OpenAI-Compatible Worker

### Implementation

Created `src/worker/openai_compatible.py`:

```python
class OpenAICompatibleWorker(LLMWorker):
    """
    Unified worker for OpenAI-compatible APIs.
    Works with: Ollama, Nemotron/Koyeb, any vLLM server
    """
    
    def __init__(self, api_url: str, model_name: str, timeout: int):
        self.api_url = api_url.rstrip("/")
        self.model_name = model_name
        
    def generate(self, prompt, system_prompt=None, temperature=0.1, 
                 max_tokens=1000, json_mode=False) -> str:
        # Uses /v1/chat/completions endpoint
        # Works for both Ollama and Nemotron!
```

### Usage

```python
from src.worker import get_worker

# Get Ollama worker (OpenAI-compatible API)
worker = get_worker(use_ollama=True, use_openai_api=True)

# Get Nemotron worker (OpenAI-compatible API)
worker = get_worker(use_ollama=False, use_openai_api=True)

# Both use the same /v1/chat/completions endpoint!
```

### Benefits

1. **Single API for both**: Same code works for Ollama and Koyeb
2. **Future-proof**: Compatible with vLLM, Ollama, OpenAI
3. **Easy testing**: Switch between local and production seamlessly
4. **Cost-effective**: Test locally, deploy to H100

## Recommended Configuration

### For Development (Local Ollama)

```python
# .env
USE_OLLAMA=true
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b-instruct
```

### For Production (Koyeb Nemotron)

```python
# .env
USE_OLLAMA=false
NEMOTRON_API_URL=https://nemotron-3-inference-dealexmachina-53d19e1c.koyeb.app
# Model name will be: nvidia/nemotron-3-8b-instruct
```

## DSPy Integration Options

### Option 1: Keep Current Custom Wrapper (2.4.9 Compatible)

```python
class DSPyLLMWrapper(dspy.LM):
    """Current implementation - works with 2.4.9"""
    def __init__(self, worker: LLMWorker):
        self.worker = worker
        super().__init__(model="custom")
```

**Pros**: Works now, no migration needed  
**Cons**: Not using DSPy's native LM clients

### Option 2: Use DSPy Native (Requires 3.x)

```python
# For Ollama
lm = dspy.LM('ollama_chat/qwen2.5:3b-instruct',
             api_base='http://localhost:11434')

# For Nemotron (vLLM)
lm = dspy.LM('openai/nvidia/nemotron-3-8b-instruct',
             api_base='https://nemotron.../v1',
             api_key='')

dspy.configure(lm=lm)
```

**Pros**: Native DSPy support, better features  
**Cons**: Requires upgrade to 3.x (breaking changes)

### Option 3: Hybrid Approach (Recommended)

Keep both:
- Our `OpenAICompatibleWorker` for direct LLM calls
- DSPy native `dspy.LM()` for DSPy-specific features

```python
# Direct calls (our abstraction)
from src.worker import get_worker
worker = get_worker(use_ollama=True, use_openai_api=True)
response = worker.generate("prompt")

# DSPy-enhanced calls (native)
import dspy
lm = dspy.LM('ollama_chat/qwen2.5:3b-instruct', 
             api_base='http://localhost:11434')
dspy.configure(lm=lm)
```

## Migration Plan

### Phase 1: Current (Iteration 1) ✅
- Use DSPy 2.4.9 with custom wrapper
- Use our `OpenAICompatibleWorker` for consistency
- Both Ollama and Nemotron use same endpoint format

### Phase 2: Iteration 2 (Optional)
- Upgrade to DSPy 3.1.2
- Migrate to `dspy.LM("provider/model")` format
- Test DSPy optimization features

### Phase 3: Iteration 3 (Production)
- Use DSPy native LM for observability
- Integrate MLflow tracking
- Use DSPy optimizers (GRPO, SIMBA)

## Testing Strategy

### Unit Tests
```python
# Mock HTTP responses - works for both
@patch("httpx.Client")
def test_worker(mock_client):
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "test"}}]
    }
```

### Integration Tests
```python
# Use real Ollama with OpenAI API
@pytest.mark.ollama
def test_with_real_ollama():
    worker = get_worker(use_ollama=True, use_openai_api=True)
    result = worker.generate("test")
```

## Verification

✅ Ollama `/v1/chat/completions` endpoint working  
✅ Returns OpenAI-compatible JSON format  
✅ Same format as Nemotron/vLLM on Koyeb  
✅ Unified `OpenAICompatibleWorker` created  
✅ Factory updated with `use_openai_api` flag  
✅ Works with Ollama models (tested with qwen2.5:3b-instruct)

## Recommendation

**For Iteration 1 (Current):**
1. ✅ Use `OpenAICompatibleWorker` for all LLM calls
2. ✅ Keep DSPy 2.4.9 (stable, working)
3. ✅ Use our custom `DSPyLLMWrapper` for DSPy signatures
4. ✅ Both Ollama and Nemotron use `/v1/chat/completions`

**For Iteration 2:**
- Consider upgrading to DSPy 3.1.2
- Migrate to native `dspy.LM()` API
- Benefit from async support and optimizers

**For Production:**
- DSPy 3.x with MLflow observability
- Native LM clients for better tracking
- Use DSPy optimizers for prompt tuning
