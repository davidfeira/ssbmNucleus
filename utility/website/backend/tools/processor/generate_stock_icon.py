#!/usr/bin/env python3
"""
Stock Icon Generation Module

Generates stock icons by applying color palette from CSPs to stock icon templates.
Uses dominant color extraction and hue/saturation adjustment for simple but effective results.
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageEnhance, ImageStat
import colorsys
import numpy as np
from collections import Counter

def extract_dominant_colors(image_path, num_colors=5):
    """
    Extract dominant colors from an image using simple color quantization.

    Args:
        image_path: Path to the image file
        num_colors: Number of dominant colors to extract

    Returns:
        List of RGB tuples representing dominant colors
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize for faster processing
            img = img.resize((100, 100))

            # Get all pixels
            pixels = list(img.getdata())

            # Count colors
            color_counts = Counter(pixels)

            # Get most common colors
            dominant_colors = [color for color, count in color_counts.most_common(num_colors)]

            return dominant_colors

    except Exception as e:
        print(f"Error extracting colors from {image_path}: {e}")
        return []

def calculate_average_hue_saturation(colors):
    """
    Calculate average hue and saturation from a list of RGB colors.

    Args:
        colors: List of RGB tuples

    Returns:
        Tuple of (average_hue, average_saturation)
    """
    if not colors:
        return 0, 0

    hues = []
    saturations = []

    for r, g, b in colors:
        # Convert RGB to HSV
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        # Only consider colors with reasonable saturation and brightness
        if s > 0.1 and v > 0.1:
            hues.append(h)
            saturations.append(s)

    if not hues:
        return 0, 0

    # Calculate averages
    avg_hue = sum(hues) / len(hues)
    avg_saturation = sum(saturations) / len(saturations)

    return avg_hue, avg_saturation

def adjust_image_hue_saturation(image, target_hue, target_saturation, strength=0.7):
    """
    Adjust an image's hue and saturation towards target values.

    Args:
        image: PIL Image object
        target_hue: Target hue (0-1)
        target_saturation: Target saturation (0-1)
        strength: How strongly to apply the adjustment (0-1)

    Returns:
        Adjusted PIL Image
    """
    # Preserve original alpha channel if it exists
    original_alpha = None
    if image.mode == 'RGBA':
        original_alpha = image.split()[-1]  # Extract alpha channel

    # Convert to HSV (this will remove alpha)
    hsv_image = image.convert('HSV')
    hsv_data = np.array(hsv_image)

    # Extract H, S, V channels
    h_channel = hsv_data[:, :, 0].astype(float)
    s_channel = hsv_data[:, :, 1].astype(float)
    v_channel = hsv_data[:, :, 2]

    # Apply hue shift towards target
    target_hue_255 = target_hue * 255
    hue_diff = target_hue_255 - h_channel

    # Handle hue wrapping (hue is circular)
    hue_diff = ((hue_diff + 128) % 256) - 128

    # Apply adjustment with strength
    h_channel = (h_channel + hue_diff * strength) % 256

    # Apply saturation adjustment
    target_saturation_255 = target_saturation * 255
    s_channel = s_channel + (target_saturation_255 - s_channel) * strength * 0.5
    s_channel = np.clip(s_channel, 0, 255)

    # Reconstruct HSV image
    hsv_data[:, :, 0] = h_channel.astype(np.uint8)
    hsv_data[:, :, 1] = s_channel.astype(np.uint8)

    adjusted_hsv = Image.fromarray(hsv_data, 'HSV')
    result = adjusted_hsv.convert('RGB')

    # Restore alpha channel if original had one
    if original_alpha:
        result = result.convert('RGBA')
        result.putalpha(original_alpha)

    return result

def find_stock_template(character_name):
    """
    Find the stock icon template for a given character.

    Args:
        character_name: Name of the character

    Returns:
        Path to stock template or None if not found
    """
    # Get path relative to this script
    script_dir = Path(__file__).parent
    csp_base_path = script_dir / "csp_data"
    template_path = csp_base_path / character_name / "stock.png"

    if template_path.exists():
        return str(template_path)
    return None

def find_default_csp(character_name):
    """
    Find the default CSP for a given character.

    Args:
        character_name: Name of the character

    Returns:
        Path to default CSP or None if not found
    """
    # Get path relative to this script
    script_dir = Path(__file__).parent
    csp_base_path = script_dir / "csp_data"
    default_path = csp_base_path / character_name / "DEFAULT.png"

    if default_path.exists():
        return str(default_path)
    return None

def find_character_masks(character_name):
    """
    Find character-specific mask files for region-based processing.

    Args:
        character_name: Name of the character

    Returns:
        Dictionary with 'csp_mask' and 'stock_mask' paths, or None if masks don't exist
    """
    # Get path relative to this script
    script_dir = Path(__file__).parent
    csp_base_path = script_dir / "csp_data"
    csp_mask_path = csp_base_path / character_name / "csp_mask.png"
    stock_mask_path = csp_base_path / character_name / "stock_mask.png"

    if csp_mask_path.exists() and stock_mask_path.exists():
        return {
            'csp_mask': str(csp_mask_path),
            'stock_mask': str(stock_mask_path)
        }
    return None

def find_color_mappings(costume_csp_path, default_csp_path, num_colors=8):
    """
    Compare costume CSP with default CSP to find color mappings.

    Args:
        costume_csp_path: Path to the costume CSP
        default_csp_path: Path to the default CSP
        num_colors: Number of dominant colors to extract

    Returns:
        Dictionary mapping old colors to new colors: {(r1,g1,b1): (r2,g2,b2)}
    """
    try:
        # Extract dominant colors from both images
        costume_colors = extract_dominant_colors(costume_csp_path, num_colors)
        default_colors = extract_dominant_colors(default_csp_path, num_colors)

        # print(f"Costume colors: {costume_colors}")
        # print(f"Default colors: {default_colors}")

        if not costume_colors or not default_colors:
            print("Could not extract colors from one or both images")
            return {}

        # Better mapping strategy: map most prominent colors directly
        color_mappings = {}

        # Skip black and white (background colors)
        def is_background_color(color):
            r, g, b = color
            # Skip pure black, pure white, and very dark colors
            return (r == 0 and g == 0 and b == 0) or (r > 240 and g > 240 and b > 240) or (r + g + b < 30)

        # Filter out background colors
        filtered_default = [c for c in default_colors if not is_background_color(c)]
        filtered_costume = [c for c in costume_colors if not is_background_color(c)]

        # print(f"Filtered default colors: {filtered_default}")
        # print(f"Filtered costume colors: {filtered_costume}")

        # Map the most prominent non-background colors
        max_mappings = min(len(filtered_default), len(filtered_costume), 3)  # Limit to top 3 colors

        for i in range(max_mappings):
            if i < len(filtered_default) and i < len(filtered_costume):
                default_color = filtered_default[i]
                costume_color = filtered_costume[i]

                # Calculate distance to see if it's a significant change
                distance = sum((a - b) ** 2 for a, b in zip(default_color, costume_color)) ** 0.5

                # print(f"  Mapping #{i+1}: {default_color} -> {costume_color} (distance: {distance:.1f})")

                if distance > 20:  # Lower threshold since we're mapping prominent colors
                    color_mappings[default_color] = costume_color
                    # print(f"    -> Added to mappings")
                # else:
                    # print(f"    -> Skipped (too similar)")

        return color_mappings

    except Exception as e:
        # print(f"Error finding color mappings: {e}")
        return {}

def rgb_to_lab(rgb):
    """Convert RGB to LAB color space for better color manipulation."""
    from PIL import ImageCms

    # Create RGB and LAB profiles
    rgb_profile = ImageCms.createProfile('sRGB')
    lab_profile = ImageCms.createProfile('LAB')

    # Create transform
    transform = ImageCms.buildTransform(rgb_profile, lab_profile, 'RGB', 'LAB')

    return ImageCms.applyTransform(rgb, transform)

def lab_to_rgb(lab):
    """Convert LAB back to RGB color space."""
    from PIL import ImageCms

    # Create LAB and RGB profiles
    lab_profile = ImageCms.createProfile('LAB')
    rgb_profile = ImageCms.createProfile('sRGB')

    # Create transform
    transform = ImageCms.buildTransform(lab_profile, rgb_profile, 'LAB', 'RGB')

    return ImageCms.applyTransform(lab, transform)

def apply_statistical_color_transfer(image, default_csp_path, costume_csp_path):
    """
    Statistical color transfer inspired by Reinhard et al. (2001)
    Transfers the color statistics from costume CSP to stock icon
    while preserving luminance structure.
    """
    try:
        # Load CSPs
        default_csp = Image.open(default_csp_path).convert('RGB')
        costume_csp = Image.open(costume_csp_path).convert('RGB')

        # Convert all to LAB color space for better perceptual uniformity
        default_lab = rgb_to_lab(default_csp)
        costume_lab = rgb_to_lab(costume_csp)

        # Convert stock to LAB
        if image.mode == 'RGBA':
            alpha = image.split()[-1]
            rgb_image = image.convert('RGB')
        else:
            alpha = None
            rgb_image = image

        stock_lab = rgb_to_lab(rgb_image)

        # Convert to numpy arrays
        default_array = np.array(default_lab).reshape(-1, 3).astype(float)
        costume_array = np.array(costume_lab).reshape(-1, 3).astype(float)
        stock_array = np.array(stock_lab).reshape(-1, 3).astype(float)

        # Filter out background pixels from CSPs
        def filter_background(arr):
            # Remove very dark and very bright pixels
            l_channel = arr[:, 0]
            mask = (l_channel > 20) & (l_channel < 90)
            return arr[mask]

        default_filtered = filter_background(default_array)
        costume_filtered = filter_background(costume_array)

        if len(default_filtered) == 0 or len(costume_filtered) == 0:
            print("No valid pixels found in CSPs")
            return image

        # Calculate statistics for each channel
        default_mean = np.mean(default_filtered, axis=0)
        default_std = np.std(default_filtered, axis=0)
        costume_mean = np.mean(costume_filtered, axis=0)
        costume_std = np.std(costume_filtered, axis=0)

        print(f"Default LAB stats: L={default_mean[0]:.1f}±{default_std[0]:.1f}, A={default_mean[1]:.1f}±{default_std[1]:.1f}, B={default_mean[2]:.1f}±{default_std[2]:.1f}")
        print(f"Costume LAB stats: L={costume_mean[0]:.1f}±{costume_std[0]:.1f}, A={costume_mean[1]:.1f}±{costume_std[1]:.1f}, B={costume_mean[2]:.1f}±{costume_std[2]:.1f}")

        # Apply statistical transfer to stock icon
        # Only transfer A and B channels (preserve L for texture)
        result_array = stock_array.copy()

        # Create mask for non-background pixels in stock
        l_channel = stock_array[:, 0]
        stock_mask = (l_channel > 10) & (l_channel < 95)

        # Transfer A and B channel statistics
        for channel in [1, 2]:  # A and B channels only
            if default_std[channel] > 0.1:  # Avoid division by zero
                # Normalize to default, then scale and shift to costume
                result_array[stock_mask, channel] = (
                    (stock_array[stock_mask, channel] - default_mean[channel]) / default_std[channel]
                    * costume_std[channel] + costume_mean[channel]
                )
                # Clamp to valid LAB ranges
                result_array[:, channel] = np.clip(result_array[:, channel], 0, 255)

        pixels_changed = np.sum(stock_mask)
        print(f"Applied statistical color transfer to {pixels_changed} pixels")

        # Reshape back to image
        height, width = stock_lab.size[1], stock_lab.size[0]
        result_lab_array = result_array.reshape(height, width, 3).astype(np.uint8)
        result_lab = Image.fromarray(result_lab_array, 'LAB')

        # Convert back to RGB
        result_rgb = lab_to_rgb(result_lab)

        # Restore alpha
        if alpha:
            result_rgb = result_rgb.convert('RGBA')
            result_rgb.putalpha(alpha)

        return result_rgb

    except Exception as e:
        print(f"Statistical color transfer failed: {e}")
        return apply_color_mappings_simple(image, {})

def apply_luminance_preserving_color_transfer(image, color_mappings):
    """
    Smart color transfer that preserves luminance/texture while dramatically changing colors.
    Works for all characters by finding the biggest color change and applying it properly.
    """
    if not color_mappings:
        return image

    try:
        # Find the most significant color change (biggest distance)
        best_mapping = None
        best_distance = 0

        for old_color, new_color in color_mappings.items():
            distance = sum((a - b) ** 2 for a, b in zip(old_color, new_color)) ** 0.5
            if distance > best_distance:
                best_distance = distance
                best_mapping = (old_color, new_color)

        if not best_mapping:
            return image

        old_color, new_color = best_mapping
        # print(f"Using biggest color change: {old_color} -> {new_color} (distance: {best_distance:.1f})")

        # Convert to HSV to separate hue/saturation from value (brightness/texture)
        if image.mode == 'RGBA':
            alpha = image.split()[-1]
            rgb_image = image.convert('RGB')
        else:
            alpha = None
            rgb_image = image

        hsv_image = rgb_image.convert('HSV')
        hsv_array = np.array(hsv_image)

        # Extract H, S, V channels
        h_channel = hsv_array[:, :, 0].astype(float)
        s_channel = hsv_array[:, :, 1].astype(float)
        v_channel = hsv_array[:, :, 2]  # PRESERVE THIS - it's the texture!

        # Convert old and new colors to HSV to understand the transformation
        old_hsv = np.array(Image.new('RGB', (1, 1), old_color).convert('HSV'))[0, 0]
        new_hsv = np.array(Image.new('RGB', (1, 1), new_color).convert('HSV'))[0, 0]

        # Calculate hue and saturation shifts (handle overflow carefully)
        hue_diff = int(new_hsv[0]) - int(old_hsv[0])
        hue_shift = ((hue_diff + 128) % 256) - 128  # Proper wrapping for signed values
        sat_shift = int(new_hsv[1]) - int(old_hsv[1])

        # print(f"HSV transformation: Hue shift = {hue_shift}, Saturation shift = {sat_shift}")

        # Create mask for pixels that should be transformed
        # Find pixels similar to the old color's characteristics
        old_h, old_s, old_v = old_hsv

        # Universal approach: find pixels that match the dominant color characteristic
        rgb_image_array = np.array(rgb_image)

        # Determine what type of color we're looking for
        old_r, old_g, old_b = old_color

        if old_g > old_r and old_g > old_b:  # Green dominant
            # Find all green-dominant pixels
            transform_mask = (rgb_image_array[:,:,1] > rgb_image_array[:,:,0]) & \
                           (rgb_image_array[:,:,1] > rgb_image_array[:,:,2]) & \
                           (rgb_image_array[:,:,1] > 30)
            # print(f"Using GREEN-dominant matching")

        elif old_r > old_g and old_r > old_b:  # Red dominant
            # Find all red-dominant pixels
            transform_mask = (rgb_image_array[:,:,0] > rgb_image_array[:,:,1]) & \
                           (rgb_image_array[:,:,0] > rgb_image_array[:,:,2]) & \
                           (rgb_image_array[:,:,0] > 30)
            # print(f"Using RED-dominant matching")

        elif old_b > old_r and old_b > old_g:  # Blue dominant
            # Find all blue-dominant pixels
            transform_mask = (rgb_image_array[:,:,2] > rgb_image_array[:,:,0]) & \
                           (rgb_image_array[:,:,2] > rgb_image_array[:,:,1]) & \
                           (rgb_image_array[:,:,2] > 30)
            # print(f"Using BLUE-dominant matching")

        else:
            # For neutral/gray colors, use broader RGB similarity matching
            tolerance = 60
            old_array = np.array(old_color)
            rgb_diff = np.abs(rgb_image_array - old_array)
            transform_mask = np.all(rgb_diff <= tolerance, axis=2) & \
                           (np.sum(rgb_image_array, axis=2) > 90)  # Skip very dark pixels
            # print(f"Using NEUTRAL color matching with tolerance {tolerance}")

        pixels_found = np.sum(transform_mask)
        # print(f"Found {pixels_found} pixels to transform")

        if pixels_found > 0:
            # Apply transformation while PRESERVING V channel (brightness/texture)
            new_hue = (h_channel[transform_mask] + hue_shift) % 256
            new_sat = np.clip(s_channel[transform_mask] + sat_shift, 0, 255)

            h_channel[transform_mask] = new_hue
            s_channel[transform_mask] = new_sat
            # V channel stays completely unchanged!

            # Reconstruct HSV image
            hsv_array[:, :, 0] = h_channel.astype(np.uint8)
            hsv_array[:, :, 1] = s_channel.astype(np.uint8)
            # hsv_array[:, :, 2] stays the same (preserves texture)

            result_hsv = Image.fromarray(hsv_array, 'HSV')
            result_rgb = result_hsv.convert('RGB')

            # Restore alpha
            if alpha:
                result_rgb = result_rgb.convert('RGBA')
                result_rgb.putalpha(alpha)

            return result_rgb

        else:
            print("No matching pixels found for transformation")
            return image

    except Exception as e:
        print(f"Luminance-preserving color transfer failed: {e}")
        return image

def apply_color_mappings_simple(image, color_mappings):
    """
    Simplified fallback color mapping that blends more gently.
    """
    if not color_mappings:
        return image

    # Convert image to RGBA for processing
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    img_array = np.array(image)

    # Find green colors and apply gentle transformation
    green_colors = [color for color in color_mappings.keys() if color[1] > color[0] and color[1] > color[2]]

    if len(green_colors) > 0:
        primary_costume_color = list(color_mappings.values())[0]

        # Match green pixels
        green_mask = (img_array[:,:,1] > img_array[:,:,0]) & (img_array[:,:,1] > img_array[:,:,2]) & (img_array[:,:,1] > 30)
        green_pixels_found = np.sum(green_mask)

        print(f"Simple color replacement -> {primary_costume_color}: found {green_pixels_found} pixels")

        if np.any(green_mask):
            # Gentle color blending that preserves more of the original shading
            for i in range(3):  # RGB channels
                current_values = img_array[green_mask, i].astype(float)
                # Much gentler blend - 60% new color, 40% original
                adjusted_values = current_values * 0.4 + primary_costume_color[i] * 0.6
                img_array[green_mask, i] = np.clip(adjusted_values, 0, 255).astype(np.uint8)

    return Image.fromarray(img_array, 'RGBA')

def generate_stock_icon(csp_path, character_name, output_path):
    """
    Generate a stock icon by applying CSP colors to the stock template.

    Args:
        csp_path: Path to the generated CSP image
        character_name: Name of the character
        output_path: Where to save the generated stock icon

    Returns:
        Path to generated stock icon or None if failed
    """
    try:
        # Find stock template
        template_path = find_stock_template(character_name)
        if not template_path:
            # print(f"No stock template found for {character_name}")
            return None

        # Check if default CSP exists for color mapping
        default_csp_path = find_default_csp(character_name)

        # Load stock template
        with Image.open(template_path) as template:
            adjusted_stock = None

            if default_csp_path:
                # Use new color mapping approach with default CSP
                # print(f"Using color mapping with default CSP: {default_csp_path}")
                color_mappings = find_color_mappings(csp_path, default_csp_path)

                if color_mappings:
                    # print(f"Found {len(color_mappings)} color mappings:")
                    # for old_color, new_color in color_mappings.items():
                    #     print(f"  {old_color} -> {new_color}")
                    # Use luminance-preserving color transfer
                    adjusted_stock = apply_luminance_preserving_color_transfer(template, color_mappings)
                else:
                    # print(f"No significant color mappings found, using fallback method")
                    adjusted_stock = None

            # Fallback to original hue/saturation method if no default CSP or color mappings
            if adjusted_stock is None:
                # print(f"Using fallback hue/saturation method")
                # Extract dominant colors from CSP
                dominant_colors = extract_dominant_colors(csp_path, num_colors=5)
                if not dominant_colors:
                    # print(f"Could not extract colors from CSP: {csp_path}")
                    return None

                # Calculate target hue and saturation
                target_hue, target_saturation = calculate_average_hue_saturation(dominant_colors)

                # Apply color adjustment
                adjusted_stock = adjust_image_hue_saturation(
                    template,
                    target_hue,
                    target_saturation,
                    strength=0.6  # Moderate adjustment strength
                )

            # Save the result
            adjusted_stock.save(output_path)
            # print(f"Generated stock icon: {output_path}")
            return output_path

    except Exception as e:
        # print(f"Error generating stock icon: {e}")
        return None

def main():
    """Test the stock icon generation functionality."""
    if len(sys.argv) < 4:
        print("Usage: python generate_stock_icon.py <csp_path> <character_name> <output_path>")
        print("Example: python generate_stock_icon.py PlMsLv_csp.png Marth PlMsLv_stock.png")
        sys.exit(1)

    csp_path = sys.argv[1]
    character_name = sys.argv[2]
    output_path = sys.argv[3]

    result = generate_stock_icon(csp_path, character_name, output_path)

    if result:
        print(f"Stock icon generated successfully: {result}")
    else:
        print("Failed to generate stock icon")

if __name__ == "__main__":
    main()