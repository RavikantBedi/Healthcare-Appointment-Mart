# Healthcare Appointment Mart

## AI Providers

This project supports multiple AI backends for summarizing the aggregated, privacy-safe metrics payload. The architecture guarantees true provider portability.

### 1. Mock (Default)
- **Backend:** `AI_BACKEND=mock`
- **Description:** Deterministic, offline, and instant. Uses hardcoded string generation.
- **Requirements:** None. Works completely offline.

### 2. Ollama
- **Backend:** `AI_BACKEND=ollama`
- **Description:** Connects to a local instance of Ollama (HTTP API).
- **Requirements:** Requires Ollama to be running locally.
- **Configuration:**
  - `OLLAMA_HOST=http://localhost:11434`
  - `OLLAMA_MODEL=llama3.2:1b`

### 3. Google Gemini
- **Backend:** `AI_BACKEND=gemini`
- **Description:** Cloud-based provider using Google's official `google-genai` Python SDK.
- **Requirements:** Needs the `google-genai` package and an active API key.
- **Configuration:**
  - `GEMINI_API_KEY=your_key_here`
  - `GEMINI_MODEL=gemini-3.8-flash`

### 4. xAI Grok
- **Backend:** `AI_BACKEND=grok`
- **Description:** Cloud-based provider using the OpenAI-compatible xAI API.
- **Requirements:** Needs the `openai` package and an active API key.
- **Configuration:**
  - `XAI_API_KEY=your_key_here`
  - `GROK_MODEL=grok-3-mini`

### 5. NVIDIA
- **Backend:** `AI_BACKEND=nvidia`
- **Description:** Cloud-based provider using the NVIDIA API (via OpenAI client).
- **Requirements:** Needs the `openai` package and an active API key.
- **Configuration:**
  - `NVIDIA_API_KEY=your_key_here`
  - `NVIDIA_MODEL=z-ai/glm-5.3`

### Privacy Enforcement
All AI models, regardless of the configured backend, must pass through the **same** Privacy Validator (`src.ai.privacy.validate_privacy`). If any forbidden personal fields (such as `patient_id` or `date_of_birth`) are detected in the payload, the pipeline will immediately halt with a `ValueError: PRIVACY VIOLATION`, completely blocking the external API request.

### Testing
- **Unit Tests:** The Pytest suite strictly uses mocking to prevent real API calls. This ensures no API credits are consumed and tests can run fully offline.
- **Manual Integration Tests:** If you wish to test real API connectivity, you can use the optional test scripts:
  - `python -m scripts.test_gemini`
  - `python -m scripts.test_grok`
  - Ensure the appropriate API keys are configured in your environment before running.
