#!/usr/bin/env python3
#
# Hi; I know this is inefficient;
# Hi; I know it even hangs on run;
# Hi; You know this is insufficient;
# Hey, but you know it runs!
#
#
import argparse
import cv2
import numpy as np
import pyaudio
import wave
import os
from collections import deque
import time

# for convolution and threading
#
from scipy.signal import fftconvolve
from concurrent.futures import ThreadPoolExecutor

import soundfile as sf

from gesture_dsp.dsp_effects import (
    mid_side,
    convolution_reverb,
    bitcrush,
    filters,
    spectral_freeze,
    delay,
    pitch_shift,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gesture-based DSP demo: apply DSP effects via camera gestures."
    )
    parser.add_argument(
        "wav",
        help="Path to input stereo WAV file"
    )
    parser.add_argument(
        "--ir",
        help="Path to impulse response WAV file (for convolution reverb)",
        default=None
    )
    return parser.parse_args()


# :::
# :::: WRAPPERS FOR THE FO(UR)TRAN MODULES ::::
# ::::: ::::::::::::::::::::::::::::::::::: :::::
#
# NOTE: most of the f2-y wrappers want outbuffa as return
#

def apply_mid_side(audio_in: np.ndarray, side_gain: float) -> np.ndarray:
    n = audio_in.size // 2
    out = np.empty_like(audio_in, dtype=np.float64)
    out = mid_side.mid_side(audio_in, side_gain, n)
    return out


def apply_bitcrush(audio_in: np.ndarray, bit_depth: int = 8) -> np.ndarray:
    out = bitcrush.bitcrush_mod.bitcrush(
        audio_in,
        bit_depth
    )
    return out


def apply_lp_filter(audio_in: np.ndarray, cutoff: float, fs: float) -> np.ndarray:
    out = filters.filters_mod.lp_filter(audio_in, cutoff, fs)
    return out


def apply_hp_filter(audio_in: np.ndarray, cutoff: float, fs: float) -> np.ndarray:
    out = filters.filters_mod.hp_filter(audio_in, cutoff, fs)
    return out


def apply_delay(audio_in: np.ndarray, delay_samps: int = 4410, feedback: float = 0.5) -> np.ndarray:
    out = delay.delay_mod.delay(audio_in, delay_samps, feedback)
    return out


def apply_convolution_reverb(audio_in: np.ndarray, ir: np.ndarray) -> np.ndarray:
    return fftconvolve(audio_in, ir, mode='same')


def apply_spectral_freeze(audio_in: np.ndarray) -> np.ndarray:
    n = audio_in.size
    out = np.empty(n, dtype=np.float64)
    out = spectral_freeze.spectral_freeze_mod.spectral_freeze(audio_in, n)
    return out


def apply_pitch_shift(audio_in: np.ndarray, semitones: int = 4) -> np.ndarray:
    n = audio_in.size
    out = np.empty(n, dtype=np.float64)
    out = pitch_shift.pitch_shift_mod.pitch_shift(audio_in, semitones)
    return out


# effect name -> (callable, default params)
EFFECTS = [
    ("mid_side",    lambda buf, fs, ir, p: apply_mid_side(buf, side_gain=min(max(p*2.0, 0.0), 2.0))),
    ("bitcrush",    lambda buf, fs, ir, p: apply_bitcrush(buf, bit_depth=int((p**3)*32)+1)),
    ("lowpass",     lambda buf, fs, ir, p: apply_lp_filter(buf, cutoff=p*6000+400, fs=fs)),
    ("highpass",    lambda buf, fs, ir, p: apply_hp_filter(buf, cutoff=p*6000+200, fs=fs)),
    ("delay",       lambda buf, fs, ir, p: apply_delay(buf, delay_samps=int(fs * (0.2 + 0.6 * p)), feedback=0.3 + (0.6 * p))),
    ("reverb",      lambda buf, fs, ir, p: apply_convolution_reverb(buf, ir)),
    ("spectral_freeze", lambda buf, fs, ir, p: apply_spectral_freeze(buf)),
    ("pitch_shift", lambda buf, fs, ir, p: apply_pitch_shift(buf, semitones=int(p*60-30))),
]
EFFECT_NAMES = [name for name, _ in EFFECTS]


class GestureDSP:
    def __init__(self, wav_path: str, ir_path: str = None):

        self.wf = wave.open(wav_path, 'rb')
        assert self.wf.getnchannels() == 2, "Need stereo WAV"
        self.fs = self.wf.getframerate()
        self.p = pyaudio.PyAudio()

        self.frames_per_buffer = 4096
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=self.fs,
            output=True,
            frames_per_buffer=self.frames_per_buffer,
            stream_callback=self._callback
        )

        num_channels = self.wf.getnchannels()
        max_samples = self.frames_per_buffer * num_channels
        self._in_buffer = np.empty(max_samples, dtype=np.float64)
        self._f64_clip_buffer = np.empty(max_samples, dtype=np.float64)
        self._int16_out_buffer = np.empty(max_samples, dtype=np.int16)

        # load IR if provided
        if ir_path and os.path.exists(ir_path):
            try:
                with wave.open(ir_path, 'rb') as ir_wf:
                    data = ir_wf.readframes(ir_wf.getnframes())
                    self.ir = np.frombuffer(data, dtype=np.int16).astype(np.float64)
            except wave.Error:
                # fallback for non-PCM WAV formats
                data, sr = sf.read(ir_path, dtype='float64')

                # flatten multi-channel IR
                if data.ndim > 1:
                    data = data.flatten()

                # convert float [-1,1] to int16 range
                self.ir = (data * 32767).astype(np.float64)
        else:
            self.ir = np.zeros(1, dtype=np.float64)

        # out the getgo with number one (or zero if that 
        # floats your boat...)
        self.current_idx = 0
        self.current_param = 0.5

    def _callback(self, in_data, frame_count, time_info, status):
        raw = self.wf.readframes(frame_count)
        if not raw:
            return (raw, pyaudio.paComplete)

        # convert int16 input into pre-allocated float buffer
        in_int16 = np.frombuffer(raw, dtype=np.int16)
        self._in_buffer[:in_int16.size] = in_int16.astype(np.float64)

        # apply DSP
        _, func = EFFECTS[self.current_idx]
        audio_out = func(self._in_buffer, self.fs, self.ir, self.current_param)

        # clip and convert to int16 into pre-allocated buffer
        np.clip(audio_out, -32768, 32767, out=self._f64_clip_buffer)
        self._int16_out_buffer[:audio_out.size] = self._f64_clip_buffer.astype(np.int16)

        return (self._int16_out_buffer.tobytes(), pyaudio.paContinue)

    def start(self):
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.wf.close()
        self.p.terminate()

    def set_effect_by_zone(self, x_center: float, frame_w: int):
        """Divide frame into N vertical zones to pick effect."""
        zone_width = frame_w / len(EFFECT_NAMES)
        idx = int(x_center // zone_width)
        self.current_idx = max(0, min(idx, len(EFFECT_NAMES)-1))


# :::
# :::: HAND-DETECTION HELPERS ::::
# ::::: :::::::::::::::::::::: :::::
#

# god this is ugly;
# god; forgive me;
# god; and I don't
# even believe in you;
# ;
def is_hand_raised(frame):
    blur = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    lb1, ub1 = np.array([140,50,50]), np.array([179,255,255])
    lb2, ub2 = np.array([0,50,50]),  np.array([10,255,255])
    m1 = cv2.inRange(hsv, lb1, ub1)
    m2 = cv2.inRange(hsv, lb2, ub2)
    mask = cv2.morphologyEx(
        cv2.bitwise_or(m1, m2),
        cv2.MORPH_OPEN,
        np.ones((2,2), np.uint8)
    )

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None

    c = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(c) < 8:
        return None

    x,y,w,h = cv2.boundingRect(c)
    if (y + h/2) < frame.shape[0] * 0.70:
        return (x, y, w, h)
    return None

def is_second_glove_raised(frame):
    blur = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    lb = np.array([35, 50, 50])
    ub = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lb, ub)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2,2), np.uint8))

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None

    # pick the largest contour to avoid multiple detections
    c = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(c) < 100:
        return None

    x, y, w, h = cv2.boundingRect(c)
    return (x, y, w, h)

 
# :::
# :::: MAIN LOOP ::::
# ::::: ::::::::: :::::
#

def main():
    args = parse_args()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("🔴 Cannot open camera")
        return

    # offload hand-detection to a worker thread
    # not a clue if I'm doing this right...
    # ...yet!
    # this ain't the therac, chill with your thread shrieks
    executor = ThreadPoolExecutor(max_workers=1)
    prev_future = None

    # parameter window thresholds for mapping glove height
    param_min_ratio = 0.2
    param_max_ratio = 0.8

    # smoothing factor for parameter changes
    param_smooth = 0.2
    smoothed_param = 0.0

    player = GestureDSP(args.wav, ir_path=args.ir)
    player.start()

    # track recent effect indices for cue detection
    history = deque(maxlen=10)
    cue_mode = False

    # empty precompute cues
    # idk what i want to do with this realy
    precomputed_cues = {}
    last_cue_time = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)

            # schedule detection off the main thread
            future = executor.submit(lambda f: (is_hand_raised(f), is_second_glove_raised(f)), frame.copy())
            if prev_future and prev_future.done():
                hand_box, glove_box = prev_future.result()
            else:
                hand_box, glove_box = None, None
            prev_future = future

            if hand_box:
                x, y, w, h = hand_box
                cx = x + w/2
            else:
                cx = None
            if glove_box:
                x2, y2, w2, h2 = glove_box
                cy = y2 + h2/2
            else:
                cy = None

            if cx is not None:
                # effect selection
                player.set_effect_by_zone(cx, frame.shape[1])
                effect_idx = player.current_idx
                effect_name = EFFECT_NAMES[effect_idx]
                history.append(effect_idx)
            else:
                effect_name = "none"

            # map second glove vertical pos to parameter with clamping and smoothing
            if cy is not None:
                h = frame.shape[0]
                min_y = param_min_ratio * h
                max_y = param_max_ratio * h
                if cy <= min_y:
                    raw_param = 1.0
                elif cy >= max_y:
                    raw_param = 0.0
                else:
                    raw_param = 1.0 - (cy - min_y) / (max_y - min_y)
            else:
                raw_param = 0.5

            # exponential smoothing
            smoothed_param = param_smooth * smoothed_param + (1.0 - param_smooth) * raw_param
            player.current_param = smoothed_param

            # detect simple cue: same
            # effect selected repeatedly quickly
            # NOTE: I hate this whole thing now
            #
            now = time.time()
            if len(history) == history.maxlen and len(set(history)) == 1 and now - last_cue_time > 2:
                cue_mode = True
                last_cue_time = now
            else:
                cue_mode = False

            if True:
                # draw detection rectangles
                if hand_box:
                    x, y, w, h = hand_box
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                if glove_box:
                    x2, y2, w2, h2 = glove_box
                    cv2.rectangle(frame, (x2, y2), (x2+w2, y2+h2), (180,105,255), 2)

                # draw effect name
                cv2.putText(frame, f"Effect: {effect_name}", (10,30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                
                # draw paramabar on right
                ph = int(player.current_param * frame.shape[0])
                cv2.rectangle(frame,
                              (frame.shape[1]-50, frame.shape[0]),
                              (frame.shape[1]-10, frame.shape[0]-ph),
                              (255,0,0), -1)

                # cue overlay
                if cue_mode:
                    cv2.putText(frame, "CUE TRIGGERED", (frame.shape[1]//2-100,50),
                                cv2.FONT_HERSHEY_COMPLEX, 1.5, (0,0,255), 3)

            cv2.imshow("Gesture-DSP Demo", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                break
            if not player.stream.is_active():
                break

    finally:
        player.stop()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()