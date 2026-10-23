"""Build a narrated, edited demo from actual local browser recording.

Optional video dependencies: FFmpeg, edge-tts for synthesis separately.
This script is offline and never operates any shopping or cloud account.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
    parser.add_argument('--recording', type=Path, default=Path('artifacts/review-final/recording.json'))
    parser.add_argument('--voice', type=Path, default=Path('artifacts/review-voice'))
    parser.add_argument('--output', type=Path, default=Path('docs/video/demo.mp4'))
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.error('Supply --ffmpeg or install FFmpeg')
    staging = args.output.with_name(args.output.stem + '.pending.mp4')
    recording = json.loads(args.recording.read_text())
    assert recording['actual_ui'] and not recording['errors']
    assert recording['playback_speed'] == .5
    measurements = []
    for i, scene in enumerate(json.loads((args.voice/'script.json').read_text()), 1):
        audio = args.voice/f'{i}.mp3'
        info = subprocess.run([args.ffmpeg, '-hide_banner', '-i', str(audio)], capture_output=True, text=True).stderr
        m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', info)
        seconds = int(m[1])*3600 + int(m[2])*60 + float(m[3])
        target = scene['duration'] - 2
        # Slow short narration only moderately; preserve a quiet reading interval.
        tempo = max(.85, seconds/target)
        if tempo > 1.3:
            raise ValueError(f'Scene {i} needs shorter narration')
        run([args.ffmpeg, '-y', '-i', str(audio), '-af',
             f'atempo={tempo:.8f},loudnorm=I=-16:TP=-1.5:LRA=11,adelay=1000:all=1,apad',
             '-t', str(scene['duration']), '-ar', '48000', '-ac', '2', str(args.voice/f'{i}.wav')])
        measurements.append({'scene': i, 'start': scene['start'], 'duration': scene['duration'],
                             'speech_source_seconds': seconds, 'tempo': tempo})
    concat = args.voice/'concat.txt'
    concat.write_text(''.join(f"file '{i}.wav'\n" for i in range(1,7)))
    combined = args.voice/'narration.wav'
    run([args.ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c:a', 'pcm_s16le', str(combined)])
    run([args.ffmpeg, '-y', '-ss', '1', '-i', recording['raw'], '-i', str(combined),
         '-map', '0:v:0', '-map', '1:a:0', '-vf', 'setpts=2*PTS,fps=20,format=yuv420p',
         '-map_metadata', '-1', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
         '-c:a', 'aac', '-b:a', '160k', '-t', '300', '-movflags', '+faststart',
         '-metadata', 'title=Torob post-submission UX review - synthetic Persian narration', str(staging)])
    decode = subprocess.run([args.ffmpeg, '-v', 'error', '-i', str(staging), '-f', 'null', '-'], capture_output=True, text=True)
    if decode.returncode or decode.stderr.strip():
        raise RuntimeError('Full MP4 decode reported errors')
    probe = subprocess.run([args.ffmpeg, '-hide_banner', '-i', str(staging)], capture_output=True, text=True).stderr
    duration = re.search(r'Duration: (\d+):(\d+):([\d.]+)', probe)
    actual_seconds = int(duration[1])*3600 + int(duration[2])*60 + float(duration[3])
    assert 295 <= actual_seconds <= 305 and '1920x1080' in probe and 'Audio: aac' in probe
    staging.replace(args.output)
    qa = {'actual_ui_recorded': True, 'source_records_fabricated': False,
          'browser_errors': recording['errors'], 'duration_seconds': actual_seconds,
          'capture_seconds': recording['seconds'], 'playback_speed': .5,
          'edited_for_readability_not_performance_benchmark': True,
          'resolution': '1920x1080', 'video': 'H264', 'audio': 'AAC synthetic Persian narration',
          'voice': 'fa-IR-FaridNeural', 'synthetic_voice_disclosed': True,
          'post_submission_update_disclosed': True, 'full_decode_passed': True,
          'video_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
          'bytes': args.output.stat().st_size, 'narration_segments': measurements}
    Path('DEMO_QA.json').write_text(json.dumps(qa, indent=2)+'\n')
    print(json.dumps(qa, indent=2))


if __name__ == '__main__':
    main()
