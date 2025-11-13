# Twitch Ollama Assistant

Connect your Twitch channel to a local Ollama LLM instance with an admin web UI for configuration, chat logging, and file-based generation.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```

2. Create a `.env` file:
   ```
   TWITCH_OAUTH_TOKEN=oauth:your_token
   TWITCH_CHANNEL=your_channel
   ADMIN_PASSWORD=admin123
   OLLAMA_BASE_URL=http://localhost:11434
   ```

3. Run:
   ```bash
   python -m twitch_ollama.main
   ```

4. Open http://localhost:8000/admin to configure prompts and models.

## Development

- Lint: `ruff check src tests`
- Typecheck: `mypy src`
- Test: `pytest`

## License

MIT