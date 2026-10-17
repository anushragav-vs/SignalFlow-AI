# SignalFlow AI - Troubleshooting Guide

Common issues, root causes, and verified fixes for SignalFlow AI.

---

## 1. Google Gemini API Issues

### Issue: `status: error_missing_key`
- **Cause**: `GEMINI_API_KEY` is not present in `.env` or system environment variables.
- **Fix**: Open `.env` and verify the variable name is exactly `GEMINI_API_KEY`. Check that you activated your virtual environment before running the command.

### Issue: `ClientError: 404 NOT_FOUND` (Model deprecated)
- **Cause**: Older models such as `gemini-2.5-flash` or `gemini-1.5-flash` may be deprecated for new API keys in Google AI Studio.
- **Fix**: Update `GEMINI_MODEL_ID` in `.env` to `gemini-3.5-flash-lite` or `gemini-3.8-flash`.

### Issue: `ClientError: 429 Resource Exhausted / Quota Exceeded`
- **Cause**: Free tier Google AI Studio accounts have a 15 Requests Per Minute (RPM) quota.
- **Fix**: The pipeline automatically includes rate pacing. In `demo.py` and `app.py`, avoid triggering rapid batch runs. Wait 30 seconds before re-running live API tests.

### Issue: `error_timeout`
- **Cause**: Network handshake latency exceeded the configured timeout.
- **Fix**: Increase `GEMINI_TIMEOUT_SEC=60` in `.env`. SignalFlow AI configures `types.HttpOptions(timeout=...)` in milliseconds.

---

## 2. Strands Decider 2B & Local CPU Issues

### Issue: PyTorch warning about symlinks on Windows
- **Cause**: Windows requires Developer Mode or Administrator privileges to create symlinks in Hugging Face Hub cache.
- **Fix**: SignalFlow AI automatically sets `HF_HUB_DISABLE_SYMLINKS_WARNING=1`. This does not affect inference accuracy.

### Issue: In-process load time takes 10-15 seconds
- **Cause**: On CPU, PyTorch upcasts half-precision weights to `float32` via `SystemOneEngine._upcast_torso_for_cpu()` to utilize vector instructions (AVX/ARM).
- **Fix**: This one-time loading cost happens only at startup. Subsequent inferences run in ~950 ms per headline. Alternatively, run the standalone HTTP server:
  ```powershell
  strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --device cpu --port 8000
  ```

---

## 3. SQLite & Database Issues

### Issue: `PermissionError: [WinError 32] The process cannot access the file`
- **Cause**: On Windows, SQLite database files cannot be deleted or re-opened while an active connection handle remains unclosed.
- **Fix**: SignalFlow AI uses connection pooling and caches in-memory connections (`:memory:`) in unit tests to prevent Windows file locks.

---

## 4. Streamlit Dashboard Issues

### Issue: `Port 8501 is already in use`
- **Cause**: A previous Streamlit instance is still running in the background.
- **Fix**: Launch on an alternative port:
  ```powershell
  streamlit run app.py --server.port 8502
  ```
