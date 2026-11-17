import cv2
import numpy as np
import csv
import math

max_distance = 120
max_lost = 6
lock_frames = 10
min_radius = 15
max_radius = 80
max_radius_change = 15
min_motion = 40


def detect_circles(frame):
    """Find round yellow and blue blobs, which is the volleyball in this video."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    yellow = cv2.inRange(hsv, (8, 130, 130), (32, 255, 255))
    blue = cv2.inRange(hsv, (100, 90, 50), (130, 255, 255))
    mask = cv2.bitwise_or(yellow, blue)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

    height, width = mask.shape
    count, _, stats, centers = cv2.connectedComponentsWithStats(mask)
    circles = []
    for i in range(1, count):
        area = int(stats[i, cv2.CC_STAT_AREA])
        x, y, w, h = [int(stats[i, k]) for k in range(4)]
        center_x, center_y = int(centers[i][0]), int(centers[i][1])
        if center_y > height * 0.62 or center_x < 80 or center_x > width - 80:
            continue
        if area < 800 or area > 15000 or w > 160 or h > 160 or w < 25 or h < 25:
            continue
        if w / h < 0.6 or w / h > 1.6:
            continue
        radius = int(round((w + h) / 4))
        if radius < min_radius or radius > max_radius:
            continue
        circles.append((int(centers[i][0]), int(centers[i][1]), radius))
    return circles


def predicted_center(track):
    points = track["points"]
    x, y = points[-1][1], points[-1][2]
    if len(points) >= 2:
        vx = points[-1][1] - points[-2][1]
        vy = points[-1][2] - points[-2][2]
        step = track["missed"] + 1
        x += vx * step
        y += vy * step
    return x, y


def update_tracks(tracks, circles, frame_index):
    unused = set(range(len(circles)))
    ordered = sorted(tracks, key=lambda track: len(track["points"]), reverse=True)
    for track in ordered:
        last = track["points"][-1]
        px, py = predicted_center(track)
        best_i = None
        best_d = min(max_distance + track["missed"] * 20, 200)
        for i in unused:
            x, y, r = circles[i]
            if abs(r - last[3]) > max_radius_change:
                continue
            dist = math.hypot(x - px, y - py)
            if dist < best_d:
                best_d = dist
                best_i = i
        if best_i is None:
            track["missed"] += 1
        else:
            x, y, r = circles[best_i]
            track["points"].append((frame_index, x, y, r))
            track["missed"] = 0
            unused.remove(best_i)
    for i in unused:
        x, y, r = circles[i]
        tracks.append({"points": [(frame_index, x, y, r)], "missed": 0})
    return [track for track in tracks if track["missed"] <= max_lost]


def choose_ball(tracks, frame_index):
    """Pick the colored blob that keeps moving, and ignore circles that stay still."""
    best_track = None
    best_motion = 0
    for track in tracks:
        points = track["points"]
        if len(points) < 5 or frame_index - points[-1][0] > 3:
            continue
        radii = [point[3] for point in points]
        if max(radii) - min(radii) > max_radius_change:
            continue
        steps = [math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in zip(points, points[1:])]
        moving_steps = sum(step >= 8 for step in steps)
        vertical = abs(points[-1][2] - points[0][2])
        horizontal = abs(points[-1][1] - points[0][1])
        motion = math.hypot(horizontal, vertical)
        if moving_steps < 3 or motion < min_motion or vertical < horizontal:
            continue
        if motion > best_motion:
            best_motion = motion
            best_track = track
    return best_track


def blank_row(frame_index):
    return [frame_index, "", "", "", "", "", "", "", 0]


def position_row(frame_index, x, y):
    return [frame_index, int(x), int(y), "", "", "", "", "", 1]


def motion_row(frame_index, x, y, vx, vy, detected, fps):
    speed = math.hypot(vx, vy)
    angle = math.degrees(math.atan2(-vy, vx))
    return [frame_index, int(x), int(y), int(vx), int(vy),
            round(speed, 2), round(speed * fps, 2), round(angle, 1), detected]


def fill_window(track, start_frame, end_frame, fps):
    """Write every frame from the chosen track, and fill short gaps from its velocity."""
    points = [point for point in track["points"] if start_frame <= point[0] < end_frame]
    rows = []
    point_i = 0
    prev = None
    for frame_index in range(start_frame, end_frame):
        point = None
        if point_i < len(points) and points[point_i][0] == frame_index:
            point = points[point_i]
            point_i += 1
        if point is not None:
            if prev is not None and frame_index - prev[0] <= max_lost:
                gap = frame_index - prev[0]
                vx = int(round((point[1] - prev[1]) / gap))
                vy = int(round((point[2] - prev[2]) / gap))
                rows.append(motion_row(frame_index, point[1], point[2], vx, vy, 1, fps))
            else:
                rows.append(position_row(frame_index, point[1], point[2]))
            prev = point
            continue

        nxt = points[point_i] if point_i < len(points) else None
        if prev is not None and nxt is not None and nxt[0] - prev[0] <= max_lost:
            gap = nxt[0] - prev[0]
            step = frame_index - prev[0]
            vx = (nxt[1] - prev[1]) / gap
            vy = (nxt[2] - prev[2]) / gap
            rows.append(motion_row(
                frame_index,
                prev[1] + vx * step,
                prev[2] + vy * step,
                int(round(vx)),
                int(round(vy)),
                0,
                fps))
            continue

        earlier = [item for item in points if prev is not None and item[0] < prev[0]]
        if prev is not None and nxt is None and earlier and frame_index - prev[0] <= max_lost:
            gap = prev[0] - earlier[-1][0]
            vx = (prev[1] - earlier[-1][1]) / gap
            vy = (prev[2] - earlier[-1][2]) / gap
            step = frame_index - prev[0]
            rows.append(motion_row(
                frame_index,
                prev[1] + vx * step,
                prev[2] + vy * step,
                int(round(vx)),
                int(round(vy)),
                0,
                fps))
            continue
        rows.append(blank_row(frame_index))
    radius = points[-1][3] if points else None
    return rows, radius


def state_from_rows(rows, radius):
    trailing = 0
    last = None
    for row in reversed(rows):
        if row[1] == "":
            trailing += 1
            continue
        last = row
        break
    if last is None or radius is None or trailing > max_lost:
        return None
    have_vel = last[3] != ""
    return {
        "x": int(last[1]),
        "y": int(last[2]),
        "vx": int(last[3]) if have_vel else 0,
        "vy": int(last[4]) if have_vel else 0,
        "r": int(radius),
        "lost": trailing,
        "have_vel": have_vel,
    }


def draw_ball(frame, x, y, r, detected):
    color = (0, 255, 0) if detected else (0, 255, 255)
    cv2.circle(frame, (int(x), int(y)), int(r), color, 4)


def track_video(video, fps):
    track_data = []
    tracks = []
    state = None
    mode = "lock"
    next_row = 0
    current_frame = 0

    while True:
        ret, frame = video.read()
        if not ret:
            break
        circles = detect_circles(frame)

        if mode == "lock":
            tracks = update_tracks(tracks, circles, current_frame)
            for x, y, r in circles:
                cv2.circle(frame, (x, y), r, (0, 255, 255), 2)
            if current_frame + 1 >= lock_frames:
                chosen = choose_ball(tracks, current_frame)
                if chosen is not None:
                    rows, radius = fill_window(chosen, next_row, current_frame + 1, fps)
                    state = state_from_rows(rows, radius)
                    if state is not None:
                        track_data.extend(rows)
                        next_row = current_frame + 1
                        mode = "track"
                        current = rows[-1]
                        if current[1] != "":
                            draw_ball(frame, current[1], current[2], radius, current[8])
        else:
            px = state["x"] + state["vx"]
            py = state["y"] + state["vy"]
            best = None
            best_d = min(max_distance + state["lost"] * 20, 200)
            for x, y, r in circles:
                if abs(r - state["r"]) > max_radius_change:
                    continue
                dist = math.hypot(x - px, y - py)
                if dist < best_d:
                    best_d = dist
                    best = (x, y, r)
            if best is not None:
                x, y, r = best
                vx = int(x - state["x"])
                vy = int(y - state["y"])
                if state["have_vel"] or state["lost"] == 0:
                    track_data.append(motion_row(current_frame, x, y, vx, vy, 1, fps))
                    state["vx"], state["vy"] = vx, vy
                    state["have_vel"] = True
                else:
                    track_data.append(position_row(current_frame, x, y))
                state["x"], state["y"], state["r"] = x, y, r
                state["lost"] = 0
                draw_ball(frame, x, y, r, 1)
            else:
                state["lost"] += 1
                height, width = frame.shape[:2]
                x = int(state["x"] + state["vx"])
                y = int(state["y"] + state["vy"])
                inside = 0 <= x < width and 0 <= y < height
                if state["lost"] <= max_lost and state["have_vel"] and inside:
                    track_data.append(motion_row(
                        current_frame, x, y, state["vx"], state["vy"], 0, fps))
                    state["x"], state["y"] = x, y
                    draw_ball(frame, x, y, state["r"], 0)
                else:
                    track_data.append(blank_row(current_frame))
                    if state["lost"] > max_lost:
                        mode = "lock"
                        tracks = []
                        state = None
            next_row = current_frame + 1

        cv2.imshow("Ball Tracking", frame)
        if cv2.waitKey(25) & 0xFF == ord("q"):
            break
        current_frame += 1

    if mode == "lock" and current_frame > next_row:
        chosen = choose_ball(tracks, current_frame - 1) if current_frame else None
        if chosen is not None:
            rows, radius = fill_window(chosen, next_row, current_frame, fps)
            if state_from_rows(rows, radius) is not None:
                track_data.extend(rows)
                next_row = current_frame
        while next_row < current_frame:
            track_data.append(blank_row(next_row))
            next_row += 1
    return track_data


def main():
    video_path = input("Enter the path of the video file: ")
    output_file = "ball_tracking.csv"
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print("Error: Could not open video file.")
        return
    fps = video.get(cv2.CAP_PROP_FPS) or 30
    track_data = track_video(video, fps)
    video.release()
    cv2.destroyAllWindows()

    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Frame", "X", "Y", "VX", "VY", "Speed", "Speed(px/s)", "Angle", "Detected"])
        writer.writerows(track_data)
    print(f"Tracking data has been saved to {output_file}")


if __name__ == "__main__":
    main()
