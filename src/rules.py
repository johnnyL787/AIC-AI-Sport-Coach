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
}

# How far above the nose the contact boundary line sits (torso lengths).
CONTACT_BOUNDARY_ABOVE_NOSE = 0.25