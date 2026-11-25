# None means the bound has not been set yet.
POSE_RULES = {
    "knee_forward_torso_lengths": {"min": None, "max": None},
    "left_knee_lead_torso_lengths": {"min": None, "max": None},
    "torso_lean_deg": {"min": None, "max": None},
}

# Praneet adds the hand and ball-contact ranges here.
CONTACT_RULES = {
    "hands_level_torso_lengths": {"min": 0.0, "max": 0.20},
    "hands_forward_torso_lengths": {"min": 0.05, "max": 0.45},
    "hands_above_head_torso_lengths": {"min": 0.0, "max": 0.50},
    "contact_to_face_torso_lengths": {"min": 0.20, "max": 0.80},
    "contact_angle_deg": {"min": 0, "max": 40},
    "follow_through_above_head_torso_lengths": {"min": 0.40, "max": None},
}

# Johnny: elbow checks. Starting guesses, tune them on the test clips.
ELBOW_RULES = {
    "elbow_angle_deg": {"min": 90, "max": 130},              # bend at contact
    "elbow_above_shoulder_torso_lengths": {"min": 0.0, "max": None},
    "elbow_extension_deg": {"min": 40, "max": None},         # opens after contact
    "elbow_symmetry_deg": {"min": 0, "max": 20},             # left vs right
}

# Skip a joint when MediaPipe's visibility score is below this.
MIN_VISIBILITY = 0.5

# How many frames on each side of contact to average (1 = 3 frames total).
ELBOW_AVERAGE_FRAMES = 1

# How far above the nose the contact boundary line sits (torso lengths).
CONTACT_BOUNDARY_ABOVE_NOSE = 0.25

# How far sideways from the head the ball can be and still count (torso lengths).
CONTACT_BALL_NEAR_HEAD = 1.5