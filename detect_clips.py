import cv2
import glob
import numpy as np
import argparse
import os
import requests

def extract_keyframes_from_video(snippet_video_path, output_dir):
    """
    Extracts the first frame, the last frame, and a frame approx every 1s based on video FPS.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cap = cv2.VideoCapture(snippet_video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open snippet video: {snippet_video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0:
        fps = 30.0  # fallback if unknown

    # One frame per second approx
    frame_interval = int(round(fps))
    if frame_interval < 1:
        frame_interval = 1

    # Extract first frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(os.path.join(output_dir, "frame_000001.jpg"), frame)

    # Extract intermediate frames
    current_frame = frame_interval
    while current_frame < total_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imwrite(os.path.join(output_dir, f"frame_{current_frame:06d}.jpg"), frame)
        current_frame += frame_interval

    # Extract last frame if not already done
    if total_frames > 1:
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(os.path.join(output_dir, f"frame_{total_frames:06d}.jpg"), frame)

    cap.release()
    print(f"Extracted keyframes to {output_dir}")


def load_or_extract_snippet(snippet_path, hash_method, match_threshold):
    """
    If snippet_path is a directory with frames, load them.
    If snippet_path is a video file, extract frames if needed.
    """
    if os.path.isfile(snippet_path):
        # It's a video file, extract frames if necessary
        base_name = os.path.splitext(os.path.basename(snippet_path))[0]
        frames_dir = base_name + "_frames"
        if not os.path.exists(frames_dir) or len(glob.glob(frames_dir + "/*.jpg")) == 0:
            extract_keyframes_from_video(snippet_path, frames_dir)
        return load_snippet_keyframes(frames_dir, hash_method, match_threshold)
    else:
        # Assume it's a directory of frames
        return load_snippet_keyframes(snippet_path, hash_method, match_threshold)


def load_snippet_keyframes(snippet_frames_dir, hash_method, match_threshold):
    """Load and hash all keyframes from a frames directory."""
    frame_paths = sorted(glob.glob(f"{snippet_frames_dir}/*.jpg"))
    if not frame_paths:
        raise ValueError(f"No keyframe images found in {snippet_frames_dir}.")

    known_hashes = []
    for fpath in frame_paths:
        img = cv2.imread(fpath, cv2.IMREAD_COLOR)
        if img is None:
            continue
        h = hash_method.compute(img)
        known_hashes.append(h)
    if not known_hashes:
        raise ValueError(f"No valid keyframes loaded from {snippet_frames_dir}")
    return known_hashes


def frame_matches_keyframe(frame, keyframe_hash, hash_method, threshold):
    frame_hash = hash_method.compute(frame)
    xor_val = np.bitwise_xor(frame_hash, keyframe_hash)
    hamming_distance = np.count_nonzero(xor_val)
    return hamming_distance < threshold


def reset_snippet_state(snippet):
    snippet['current_keyframe_index'] = 0
    snippet['start_time_for_current_keyframe'] = None
    snippet['start_snippet_time'] = None


def check_and_update_snippet(snippet, frame, current_timestamp, hash_method, match_threshold, time_window, fps):
    # If we've started matching but haven't found the next keyframe in time, reset
    if snippet['current_keyframe_index'] > 0 and snippet['start_time_for_current_keyframe'] is not None:
        if (current_timestamp - snippet['start_time_for_current_keyframe']) > time_window:
            reset_snippet_state(snippet)

    # Check frame against the current needed keyframe
    if frame_matches_keyframe(frame, snippet['known_hashes'][snippet['current_keyframe_index']], hash_method, match_threshold):
        if snippet['current_keyframe_index'] == 0:
            snippet['start_snippet_time'] = current_timestamp

        snippet['current_keyframe_index'] += 1
        snippet['start_time_for_current_keyframe'] = current_timestamp

        # All keyframes matched
        if snippet['current_keyframe_index'] == len(snippet['known_hashes']):
            start_time = snippet['start_snippet_time']
            end_time = current_timestamp
            reset_snippet_state(snippet)
            return True, start_time, end_time

    return False, None, None


def notify_server(url, clip_name, start_time, end_time):
    data = {
        "clip_name": clip_name,
        "start_time": start_time,
        "end_time": end_time
    }
    try:
        response = requests.post(url, json=data)
        print(f"Notification sent to {url}, response status: {response.status_code}")
    except Exception as e:
        print(f"Failed to notify server at {url}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Detect multiple known snippets in a video or stream, extracting keyframes if needed.")
    parser.add_argument("--source", required=True, help="Video file path or stream URL (RTMP/HLS).")
    parser.add_argument("--clips", nargs='+', required=True, help="Paths to snippet directories or videos. If video is given, keyframes are extracted automatically.")
    parser.add_argument("--match_threshold", type=int, default=5, help="Hamming distance threshold for frame matching.")
    parser.add_argument("--time_window", type=float, default=2.0, help="Time window (in seconds) to find next keyframe.")
    parser.add_argument("--hash_method", type=str, default="phash", choices=["phash","average","marr","radial"], help="Image hash method.")
    parser.add_argument("--notify_url", type=str, help="If provided, POST detection results to this URL.")
    args = parser.parse_args()

    # Select hash method
    if args.hash_method == "phash":
        hash_method = cv2.img_hash.PHash_create()
    elif args.hash_method == "average":
        hash_method = cv2.img_hash.AverageHash_create()
    elif args.hash_method == "marr":
        hash_method = cv2.img_hash.MarrHildrethHash_create()
    elif args.hash_method == "radial":
        hash_method = cv2.img_hash.RadialVarianceHash_create()

    # Load all snippets
    snippets = {}
    for clip_path in args.clips:
        known_hashes = load_or_extract_snippet(clip_path, hash_method, args.match_threshold)
        snippets[clip_path] = {
            'known_hashes': known_hashes,
            'current_keyframe_index': 0,
            'start_time_for_current_keyframe': None,
            'start_snippet_time': None
        }

    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        raise IOError(f"Could not open video source {args.source}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0  # fallback if fps not available

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                # End of video or no stream data
                break

            current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
            current_timestamp = current_frame / fps

            # Check each snippet
            for snippet_name, snippet in snippets.items():
                detected, start_time, end_time = check_and_update_snippet(
                    snippet, frame, current_timestamp, hash_method, args.match_threshold, args.time_window, fps
                )
                if detected:
                    print(f"[{snippet_name}] Detected snippet! Start: {start_time:.2f}s, End: {end_time:.2f}s")
                    if args.notify_url:
                        notify_server(args.notify_url, snippet_name, start_time, end_time)

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
