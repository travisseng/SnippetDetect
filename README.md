
# SnippetDetect

This tool detects known video snippets within a given video file or live stream. It can automatically extract keyframes from snippet videos if they don’t already exist, and then continuously monitor a source for occurrences of those snippets.

## Features

- **Keyframe Extraction**: If you provide a snippet as a video file, it automatically extracts the first, last, and intermediate frames (every ~1 second).
- **Multiple Snippets**: Pass multiple snippet directories or video files as arguments.
- **Time-Windowed Sequence Matching**: Matches snippet keyframes in order, ensuring they occur within a certain time window.
- **Hash-Based Matching**: Uses OpenCV’s `img_hash` to find similar frames even under slight variations.
- **Optional Notification**: When a snippet is detected, the tool can send a POST request with detection details to a specified server endpoint.

## Requirements

- Python 3.6+
- OpenCV with `img_hash` module support  
  Install via: `pip install opencv-python requests`

## Usage

1. **Prepare Snippets**:
   - If you have snippet videos (e.g., `snippet1.mp4`), the tool will automatically extract keyframes into `snippet1_frames/`.
   - If you already have a directory of keyframes (e.g., `snippet1_frames/`), just point to that directory.

2. **Run the Detection**:

   ```bash
   python detect_clips.py \
     --source input_video.mp4 \
     --clips snippet1.mp4 snippet2_frames \
     --match_threshold 5 \
     --time_window 2.0 \
     --hash_method phash \
     --notify_url http://yourserver.com/api/detect
   ```

   **Arguments**:
   - `--source`: Path to the input video or a stream URL (e.g., `rtmp://...` or `http://...m3u8`).
   - `--clips`: One or more paths. Each can be a snippet video file or a directory of keyframes.
   - `--match_threshold`: Hamming distance threshold for considering frames a match.
   - `--time_window`: Allowed seconds between consecutive keyframe matches.
   - `--hash_method`: Hash algorithm (`phash`, `average`, `marr`, `radial`).
   - `--notify_url`: If provided, the program sends a POST request to this URL with JSON data whenever a snippet is detected.

## Example

If you have a snippet video `snippet1.mp4` and want to detect it in `input_video.mp4`, and notify a server endpoint:

```bash
python detect_clips.py \
  --source input_video.mp4 \
  --clips snippet1.mp4 \
  --notify_url http://localhost:5000/detection-event
```

When `snippet1` is detected at, say, start_time=10.5 and end_time=12.7 seconds, it will print:
```
[snippet1.mp4] Detected snippet! Start: 10.50s, End: 12.70s
```
and send a POST request to `http://localhost:5000/detection-event` with:
```json
{
  "clip_name": "snippet1.mp4",
  "start_time": 10.5,
  "end_time": 12.7
}
```

## Development

- **Install Dependencies**:
  ```bash
  pip install opencv-python requests
  ```
- **Test**:
  Just run the script with some test videos.
