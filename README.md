# SnippetDetect

This tool detects known video snippets within a given video file or live stream. It can automatically extract keyframes from snippet videos if they don’t already exist, and then continuously monitor a source for occurrences of those snippets.

## Features

- **Keyframe Extraction**: If you provide a snippet as a video file, it automatically extracts keyframes (first, last, and intermediate frames every ~1 second).
- **Multiple Snippets**: Pass multiple snippet directories or video files as arguments.
- **Time-Windowed Sequence Matching**: Matches snippet keyframes in order, ensuring they occur within a specified time window (`--time_window`).
- **Single-Image Snippet Detection**: Provide a single image file as a “snippet” and specify a minimum duration the image must appear to count as detected.
- **Cooldown Between Detections**: Avoid repeated detections of the same snippet within a short time by using `--detection_cooldown`.
- **Hash-Based Matching**: Uses OpenCV’s `img_hash` to find similar frames even under slight variations.
- **HLS Stream Processor**: Supports processing HLS live streams, extracting metadata from the M3U8 playlist, including `EXT-X-PROGRAM-DATE-TIME` for precise timestamp synchronization.
- **Optional Notification**: When a snippet is detected, the tool can send a POST request (`--notify_url`) or publish a message to an AMQP server (`--use_amqp`).
- **Health Check**: Prints a periodic health check message in stdout to confirm the process is running.
- **Display Mode**: Optionally display the video frames in real-time (`--display`).
- **Verbose Logging**: Enable `--verbose` to see more detailed logs.

## Requirements

- Python 3.6+
- [OpenCV](https://pypi.org/project/opencv-python/) (with `img_hash` module support)
- [Requests](https://pypi.org/project/requests/) for optional HTTP notifications
- [pika](https://pypi.org/project/pika/) for optional AMQP messaging (if `--use_amqp` is used)

Install the main dependencies:

```bash
pip install opencv-python requests pika
```

## Usage

1. **Prepare Snippets**:
   - If you have snippet videos (e.g., `snippet1.mp4`), the tool will automatically extract keyframes into `snippet1_frames/`.
   - If you already have a directory of keyframes (e.g., `snippet1_frames/`), just point to that directory.
   - If you have a single image (e.g., `snippet1.jpg`), you can provide that as well.

2. **Run the Detection**:

   ```bash
   python detect_clips.py \
     --source input_video.mp4 \
     --clips snippet1.mp4 snippet2_frames snippet3.jpg \
     --match_threshold 5 \
     --time_window 3.0 \
     --image_min_duration 1.5 \
     --detection_cooldown 10.0 \
     --hash_method phash \
     --notify_url http://yourserver.com/api/detect \
     --health_check_interval 15 \
     --display \
     --verbose
   ```

   ### **Key Arguments**:

   - **`--source`** (required):  
     Video file path or a streaming URL (e.g., `rtmp://...`, `http://...m3u8`).

   - **`--clips`** (required, one or more):  
     Paths to snippet videos, single images, or directories of keyframes.

   - **`--match_threshold`** (`int`, default=5):  
     Hamming distance threshold for matching frames.

   - **`--time_window`** (`float`, default=3.0):  
     Seconds to find the next keyframe in a multi-keyframe snippet.

   - **`--image_min_duration`** (`float`, default=1.0):  
     Minimum duration (in seconds) that a single image must appear to be considered “detected.”

   - **`--detection_cooldown`** (`float`, default=10.0):  
     Minimum time (in seconds) between repeated detections of the same snippet.

   - **`--hash_method`** (`phash`, `average`, `marr`, `radial`; default=`phash`):  
     Image hashing method to use.

   - **`--notify_url`** (`str`, optional):  
     If provided, the tool sends a POST request to this URL with JSON detection data.

   - **`--health_check_interval`** (`int`, default=15):  
     Prints a “health check” message every X seconds (0 to disable).

   - **`--display`** (flag):  
     If present, displays the live frames in a GUI window (press `q` to quit).

   - **`--use_amqp`** (flag):  
     If present, sends detection messages to an AMQP server (requires `pika`).

   - **`--verbose`** (flag):  
     Increases output verbosity for debugging.

## Example

If you have a snippet video `snippet1.mp4`, a directory `snippet2_frames` (containing pre-extracted frames), and a single image `snippet3.jpg`, you can run:

```bash
python detect_clips.py \
  --source input_video.mp4 \
  --clips snippet1.mp4 snippet2_frames snippet3.jpg \
  --match_threshold 5 \
  --time_window 3.0 \
  --hash_method phash \
  --notify_url http://localhost:5000/detection-event \
  --health_check_interval 10 \
  --display \
  --verbose
```

When any snippet is detected, it will:
1. Print a message like:
   ```
   [snippet1.mp4] Detected snippet! Start: 10.50s, End: 12.70s
   ```
2. Send a POST request (if `--notify_url` is provided) with JSON data:
   ```json
   {
     "clip_name": "snippet1.mp4",
     "start_time": 10.5,
     "end_time": 12.7
   }
   ```
3. Periodically show a health check message (e.g., every 10 seconds):
   ```
   [2025-01-29 12:00:05] Health check: Video processing is running fine.
   ```

## Development

- **Install Dependencies**:

  ```bash
  pip install opencv-python requests pika
  ```

- **Local Testing**:
  - Create snippet videos or frame directories.
  - Run the script with `--source` pointed to a video or stream.
  - Observe console output or any server notifications you’ve configured.

- **Tips**:
  - Use `--verbose` to see more detailed logs (frame-by-frame, hash comparisons, etc.).
  - If you only need partial frames, consider skipping frames or lowering your input resolution to improve performance.
  - For real-time streams, use `--health_check_interval` to ensure the script is still alive and processing.  
  - If you need AMQP integration, ensure `--use_amqp` is enabled and that you have a local or remote RabbitMQ instance running.

---

**Enjoy fast, hash-based snippet detection in your video or live stream!**
