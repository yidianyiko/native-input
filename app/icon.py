"""Tray icon generation."""

from pathlib import Path

from PIL import Image, ImageDraw


def create_default_icon(size: int = 64) -> Image.Image:
    """Create a simple default tray icon."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw a filled circle (green for "running")
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(46, 204, 113, 255),
        outline=(39, 174, 96, 255),
        width=2,
    )

    # Draw "A" in the center
    text = "A"
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - margin
    draw.text((x, y), text, fill=(255, 255, 255, 255))

    return image


def get_icon() -> Image.Image:
    """Get the tray icon, creating default if needed."""
    asset_path = Path(__file__).parent / "assets" / "icon.png"
    if asset_path.exists():
        return Image.open(asset_path)
    return create_default_icon()
