#!/usr/bin/env python3
"""
Convert yml animation data to Maya .anim format
Bakes a specific frame's pose into frame 0 of the output animation
"""
import yaml
import sys

def interpolate_value_at_frame(keys, target_frame):
    """
    Interpolate the animation value at a specific frame.
    Handles constant, linear, and spline interpolation.
    """
    if not keys:
        return 0

    # If only one key, return its value
    if len(keys) == 1:
        return keys[0].get('value', 0)

    # Find the keys before and after target frame
    before_key = None
    after_key = None

    for i, key in enumerate(keys):
        frame = key.get('frame', 0)
        if frame <= target_frame:
            before_key = key
        if frame >= target_frame and after_key is None:
            after_key = key
            break

    # If target frame is before all keys, use first key's value
    if before_key is None:
        return keys[0].get('value', 0)

    # If target frame is after all keys, use last key's value
    if after_key is None:
        return keys[-1].get('value', 0)

    # If we're exactly on a key, return that value
    if before_key.get('frame') == target_frame:
        return before_key.get('value', 0)

    # For constant interpolation, use before_key value
    interp_type = before_key.get('interpolationType', 'HSD_A_OP_CON')
    if interp_type == 'HSD_A_OP_CON':
        return before_key.get('value', 0)

    # For linear/spline, interpolate between keys
    before_frame = before_key.get('frame', 0)
    after_frame = after_key.get('frame', 0)
    before_value = before_key.get('value', 0)
    after_value = after_key.get('value', 0)

    if after_frame == before_frame:
        return before_value

    # Linear interpolation
    t = (target_frame - before_frame) / (after_frame - before_frame)
    return before_value + t * (after_value - before_value)

# Joint track type to Maya attribute mapping
TRACK_TYPE_MAP = {
    'HSD_A_J_SCAX': ('scale', 'scaleX'),
    'HSD_A_J_SCAY': ('scale', 'scaleY'),
    'HSD_A_J_SCAZ': ('scale', 'scaleZ'),
    'HSD_A_J_ROTX': ('rotate', 'rotateX'),
    'HSD_A_J_ROTY': ('rotate', 'rotateY'),
    'HSD_A_J_ROTZ': ('rotate', 'rotateZ'),
    'HSD_A_J_TRAX': ('translate', 'translateX'),
    'HSD_A_J_TRAY': ('translate', 'translateY'),
    'HSD_A_J_TRAZ': ('translate', 'translateZ'),
}

# Interpolation type mapping
INTERP_MAP = {
    'HSD_A_OP_CON': 'step',
    'HSD_A_OP_LIN': 'linear',
    'HSD_A_OP_SPL': 'spline',
    'HSD_A_OP_SPL0': 'spline',
}

def convert_yml_to_anim(yml_path, anim_path):
    with open(yml_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'animation' not in data:
        print("No animation data found in yml")
        return

    # Get the target frame from the yml (the frame with the pose we want)
    target_frame = data.get('frame', 0)
    print(f"Target frame for pose: {target_frame}")

    anim_data = data['animation']
    frame_count = anim_data.get('frameCount', 1)
    nodes = anim_data.get('nodes', [])

    with open(anim_path, 'w') as f:
        # Write header - we'll create a single-frame animation at frame 0
        f.write("animVersion 1.1;\n")
        f.write("mayaVersion 2018;\n")
        f.write("timeUnit ntscf;\n")
        f.write("linearUnit cm;\n")
        f.write("angularUnit deg;\n")
        f.write(f"startTime 0;\n")
        f.write(f"endTime 5;\n")  # Short animation, pose at frame 0 and held

        # Process each node
        anim_index = 0
        for node_idx, node in enumerate(nodes):
            tracks = node.get('tracks', [])

            for track in tracks:
                track_type = track.get('jointTrackType')
                if not track_type or track_type not in TRACK_TYPE_MAP:
                    continue

                attr_group, attr_name = TRACK_TYPE_MAP[track_type]
                keys = track.get('keys', [])

                if not keys:
                    continue

                # Determine output type matching Fox format
                output_type = 'unitless'
                if 'rotate' in attr_name:
                    output_type = 'angular'
                elif 'translate' in attr_name:
                    output_type = 'linear'

                # Write animation curve
                # Key count is actual number of keys (2 for our held animation)
                f.write(f"anim {attr_group}.{attr_name} {attr_name} JOBJ_{node_idx} 0 2 {anim_index};\n")
                f.write("animData {\n")
                f.write("  input time;\n")
                f.write(f"  output {output_type};\n")
                f.write("  weighted 0;\n")
                f.write("  preInfinity constant;\n")
                f.write("  postInfinity constant;\n")
                f.write("  keys {\n")

                # Get the value at the target frame and bake it as frame 0
                baked_value = interpolate_value_at_frame(keys, target_frame)

                # Write two keys matching Fox format exactly:
                # Frame 0: fixed fixed with 11 parameters (full tangent data)
                # Frame 5: auto auto with 7 parameters (shorter format)
                f.write(f"    0 {baked_value} fixed fixed 1 0 0 0 1 0 1;\n")
                f.write(f"    5 {baked_value} auto auto 1 0 0;\n")

                f.write("  }\n")
                f.write("}\n")

                anim_index += 1

    print(f"Converted {len(nodes)} nodes with {anim_index} animation curves")
    print(f"Output: {anim_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python yml_to_anim.py <input.yml> <output.anim>")
        sys.exit(1)

    convert_yml_to_anim(sys.argv[1], sys.argv[2])
