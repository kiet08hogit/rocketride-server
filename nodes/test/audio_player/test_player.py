import sys
import os
import time
import pytest
import threading
import queue
from unittest.mock import patch, MagicMock

# Add the audio_player node to sys.path so we can import player
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/nodes/audio_player')))

from player import Player


@pytest.fixture
def player_instance():
    return Player(lock=threading.Lock())


@patch('player.sd.OutputStream')
@patch('player.sd.query_devices')
def test_start_success(mock_query, mock_stream, player_instance):
    """Test start() succeeds if there is a valid output device."""
    mock_query.return_value = [{'max_output_channels': 2}]
    
    with patch('player.AudioReader.start') as mock_super_start:
        player_instance.start()
        
    mock_query.assert_called_once()
    mock_stream.assert_called_once()
    mock_super_start.assert_called_once()


@patch('player.sd.query_devices')
def test_start_no_hardware(mock_query, player_instance):
    """Test start() raises RuntimeError if no devices have max_output_channels > 0."""
    mock_query.return_value = [{'max_output_channels': 0}]
    
    with pytest.raises(RuntimeError, match='No audio output hardware detected'):
        player_instance.start()


@patch('player.sd.query_devices')
def test_start_library_error(mock_query, player_instance):
    """Test start() raises generic library RuntimeError if query_devices() fails."""
    mock_query.side_effect = Exception("PortAudio broken")
    
    with pytest.raises(RuntimeError, match='library encountered an error checking for audio hardware'):
        player_instance.start()


def test_stop_normal(player_instance):
    """Test stop() normal behavior with no hangs."""
    player_instance._stream = MagicMock()
    # Simulate normal playback finished state
    player_instance._playback_finished = True
    
    with patch('player.AudioReader.stop') as mock_super_stop:
        player_instance.stop()
        
    mock_super_stop.assert_called_once()
    player_instance._stream.stop.assert_called_once()
    player_instance._stream.close.assert_called_once()
    player_instance._stream.abort.assert_not_called()


@patch('time.sleep', return_value=None)
@patch('time.monotonic')
def test_stop_timeout(mock_monotonic, mock_sleep, player_instance):
    """Test stop() times out and aborts stream if callback hangs."""
    player_instance._stream = MagicMock()
    # Simulate hang (playback finished never set)
    player_instance._playback_finished = False
    
    # 0 for start_wait_time, 0 for loop checks, 11 for timeout triggers
    mock_monotonic.side_effect = [0, 0, 11, 11]
    
    with patch('player.AudioReader.stop'):
        player_instance.stop()
        
    player_instance._stream.abort.assert_called_once()
    player_instance._stream.close.assert_called_once()
    player_instance._stream.stop.assert_not_called()
