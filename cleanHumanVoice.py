import sounddevice as sd
import numpy as np
import webrtcvad
import collections
import contextlib
import io
import wave


FS_MS = 30
SCALE = 6e-5
THRESHOLD = 0.3
sample_rate = 16000  # Adjust according to your microphone
sample_rate_playback = 44100  # Adjust according to your microphone
duration = 5  # Set the desired duration for audio capture in seconds

def energy_vad(audio_data, sampling_rate, energy_threshold=1000, frame_duration_ms=20):
    frame_size = int(sampling_rate * (frame_duration_ms / 1000.0))
    num_frames = len(audio_data) // frame_size

    # Calculate energy for each frame
    energies = [np.sum(np.square(audio_data[i * frame_size:(i + 1) * frame_size])) for i in range(num_frames)]

    # Apply VAD using the energy threshold
    vad_segments = [i for i, energy in enumerate(energies) if energy > energy_threshold]

    return vad_segments


def create_audio_stream_wave(audio, sample_rate):
    """create audio stream.
    Takes PCM audio data, and sample rate.
    """
    audio_stream = io.BytesIO()
    with contextlib.closing(wave.open(audio_stream, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)

    audio_stream.seek(0)
    audio_data = np.frombuffer(audio_stream.read(), dtype=np.int16)
    return audio_data, sample_rate


class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.
    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n

def vad_collector(sample_rate, frame_duration_ms,
                  padding_duration_ms, vad, frames):
    """Filters out non-voiced audio frames.
    Given a webrtcvad.Vad and a source of audio frames, yields only
    the voiced audio.
    Uses a padded, sliding window algorithm over the audio frames.
    When more than 90% of the frames in the window are voiced (as
    reported by the VAD), the collector triggers and begins yielding
    audio frames. Then the collector waits until 90% of the frames in
    the window are unvoiced to detrigger.
    The window is padded at the front and back to provide a small
    amount of silence or the beginnings/endings of speech around the
    voiced frames.
    Arguments:
    sample_rate - The audio sample rate, in Hz.
    frame_duration_ms - The frame duration in milliseconds.
    padding_duration_ms - The amount to pad the window, in milliseconds.
    vad - An instance of webrtcvad.Vad.
    frames - a source of audio frames (sequence or generator).
    Returns: A generator that yields PCM audio data.
    """
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        #  sys.stdout.write('1' if is_speech else '0')
        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])
            # If we're NOTTRIGGERED and more than 90% of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
                # We want to yield all the audio we see from now until
                # we are NOTTRIGGERED, but we have to start with the
                # audio that's already in the ring buffer.
                for f, _ in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data
            # and add it to the ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                triggered = False
                yield [b''.join([f.bytes for f in voiced_frames]),
                       voiced_frames[0].timestamp, voiced_frames[-1].timestamp]
                ring_buffer.clear()
                voiced_frames = []
    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield [b''.join([f.bytes for f in voiced_frames]),
               voiced_frames[0].timestamp, voiced_frames[-1].timestamp]

""""
# Start recording
print("Recording...")
audio_data = sd.rec(int(sample_rate * duration), channels=1, dtype='int16')
sd.wait()
print("Recording complete.")

print("Playback...")

# Play back the recorded audio
sd.play(audio_data, samplerate=sample_rate_playback)
sd.wait()

print("Playback finished.")
"""

def clean_human_voice(audio_data,sample_rate):
    frames = frame_generator(FS_MS, audio_data, sample_rate)
    frames = list(frames)
    # Initialize the VAD (Voice Activity Detection) object
    vad = webrtcvad.Vad()
    # Set the VAD aggressiveness (0: least aggressive, 3: most aggressive)
    vad.set_mode(3)

    # Process each audio frame
    """
    for frame in frames:
        # Your processing logic for each frame goes here
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        if(is_speech): 
            print("Processing frame:", frame ," Human voice detected.")
        else:
            print("Processing frame:", frame ," No human voice detected.")
            """

    segments = vad_collector(sample_rate, FS_MS, 300, vad, frames)
    merge_segments = list()
    timestamp_start = 0.0
    timestamp_end = 0.0

    # removing start, end, and long sequences of sils
    for i, segment in enumerate(segments):
                    merge_segments.append(segment[0])
                    if i and timestamp_start:
                        sil_duration = segment[1] - timestamp_end
                        if sil_duration > THRESHOLD:
                            merge_segments.append(int(THRESHOLD / SCALE)*(b'\x00'))
                        else:
                            merge_segments.append(int((sil_duration / SCALE))*(b'\x00'))
                    timestamp_start = segment[1]
                    timestamp_end = segment[2]
    segment = b''.join(merge_segments)
    audio_data, sample_rate=create_audio_stream_wave( segment, sample_rate)


    """
    # Play back the recorded audio
    if len(audio_data) == 0:
        print("Audio data is empty.")
    else:
        print("Playback again...Length: ", len(audio_data))
        sd.play(audio_data, samplerate=sample_rate_playback)
        sd.wait()
        print("Playback finished.")
    """
    
    # Apply energy-based VAD
    vad_segments = energy_vad(audio_data.flatten(), sample_rate)

    # Print segments with speech
    #print("Speech segments detected:", vad_segments)

    # Get the data type
    #data_type = type(vad_segments)

    # Print the data type
    #print(data_type)

    return vad_segments