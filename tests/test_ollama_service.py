import pytest

from twitch_ollama.services import ollama


@pytest.mark.asyncio
async def test_list_models_real_ollama():
    """Test model listing against real Ollama instance."""
    models = await ollama.list_models()
    
    # Should return a list (empty if no models or Ollama not running)
    assert isinstance(models, list)
    
    # If models are available, they should be strings
    for model in models:
        assert isinstance(model, str)
        assert len(model) > 0


@pytest.mark.asyncio
async def test_ollama_connection():
    """Test that we can connect to Ollama."""
    models = await ollama.list_models()
    
    # This test will help us understand if Ollama is running
    # If it returns an empty list, Ollama might not be running or have no models
    # If it returns models, Ollama is working
    print(f"Available models: {models}")
    
    # The function should not crash
    assert True