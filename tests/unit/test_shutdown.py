import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.main import main


@pytest.mark.asyncio
async def test_graceful_shutdown_timeout():
    """Test that shutdown completes even if polling task hangs."""
    with patch('bot.main.get_settings') as mock_settings, \
         patch('bot.main.setup_logging'), \
         patch('bot.main.start_metrics_server'), \
         patch('bot.main.Bot') as mock_bot, \
         patch('bot.main.Dispatcher') as mock_dp, \
         patch('bot.main.GitHubFileStore'):
        
        mock_settings.return_value = MagicMock(
            bot_token="test",
            log_level="INFO",
            log_json=False,
            metrics_addr="0.0.0.0:9123",
            allowed_users=[]
        )
        
        mock_bot_instance = MagicMock()
        mock_bot_instance.session.close = AsyncMock()
        mock_bot.return_value = mock_bot_instance
        
        mock_dp_instance = MagicMock()
        
        # Simulate a polling task that doesn't stop immediately
        async def slow_polling(*args, **kwargs):
            await asyncio.sleep(10)  # Longer than timeout
        
        mock_dp_instance.start_polling = AsyncMock(side_effect=slow_polling)
        mock_dp.return_value = mock_dp_instance
        
        # Run main with immediate shutdown signal
        task = asyncio.create_task(main())
        await asyncio.sleep(0.1)  # Let it start
        
        # Send shutdown signal
        import signal
        import os
        os.kill(os.getpid(), signal.SIGTERM)
        
        # Should complete within reasonable time despite slow polling
        try:
            await asyncio.wait_for(task, timeout=7.0)
        except asyncio.TimeoutError:
            pytest.fail("Shutdown took too long")
        
        # Verify bot session was closed
        mock_bot_instance.session.close.assert_called_once()
