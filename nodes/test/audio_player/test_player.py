import sys
import os
import pytest
import threading
import numpy as np
from unittest.mock import patch, MagicMock

# Add the audio_player node to sys.path so we can import player
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/nodes/audio_player')))

from player import Player


def _advancing_clock(start=0.0, step=None):
    """Return a monotonic() stand-in that advances on every call.

    Default step is past STOP_TIMEOUT so the wait loop trips regardless of
    how many monotonic() reads stop() makes.
    """
    if step is None:
        step = Player.STOP_TIMEOUT + 1.0
    now = start

    def _clock():
        nonlocal now
        current = now
        now += step
        return current

    return _clock


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
    stream = MagicMock()
    player_instance._stream = stream
    # Simulate normal playback finished state
    player_instance._playback_finished = True

    with patch('player.AudioReader.stop') as mock_super_stop:
        player_instance.stop()

    mock_super_stop.assert_called_once()
    stream.stop.assert_called_once()
    stream.close.assert_called_once()
    stream.abort.assert_not_called()
    assert player_instance._stream is None


@patch('player.warning')
@patch('time.sleep', return_value=None)
@patch('time.monotonic')
def test_stop_timeout(mock_monotonic, mock_sleep, mock_warning, player_instance):
    """Test stop() times out and aborts stream if callback hangs."""
    stream = MagicMock()
    player_instance._stream = stream
    # Simulate hang (playback finished never set)
    player_instance._playback_finished = False

    mock_monotonic.side_effect = _advancing_clock()

    with patch('player.AudioReader.stop'):
        player_instance.stop()

    stream.abort.assert_called_once()
    stream.close.assert_called_once()
    stream.stop.assert_not_called()
    mock_warning.assert_called_once()
    assert player_instance._stream is None


@patch('player.sd.OutputStream')
@patch('player.sd.query_devices')
@patch('player.warning')
@patch('time.sleep', return_value=None)
@patch('time.monotonic')
def test_start_after_stop_timeout_plays_audio(
    mock_monotonic, mock_sleep, mock_warning, mock_query, mock_stream, player_instance
):
    """A timed-out stop() must not leave a stale sentinel that mutes the next stream."""
    stream = MagicMock()
    player_instance._stream = stream
    player_instance._playback_finished = False
    mock_monotonic.side_effect = _advancing_clock()

    with patch('player.AudioReader.stop'):
        player_instance.stop()

    stream.abort.assert_called_once()
    mock_query.return_value = [{'max_output_channels': 2}]
    with patch('player.AudioReader.start'):
        player_instance.start()

    frames = 1024
    required_bytes = frames * player_instance.CHANNELS * 2
    player_instance._play_queue.put(bytes(required_bytes * 2))

    outdata = np.zeros((frames, player_instance.CHANNELS), dtype=np.int16)
    player_instance._audio_callback(outdata, frames, None, None)

    assert player_instance._playback_finished is False
    assert player_instance._play_queue.empty()
    assert len(player_instance._play_callback_buffer) == required_bytes
