# generate_four_of_a_kind_all.py
"""
Generate four‑of‑a‑kind composites for all ranks (7 through Ace) plus three special
Spade combinations. Cards in four‑of‑a‑kind hands are ordered Diamonds→Clubs→Hearts→Spades.
Use --max_size to constrain the output dimensions while preserving aspect ratio.
Requires Pillow: pip install pillow.
"""

import argparse
import os
from typing import List
from PIL import Image

# Base rotations and offsets for four‑card hands
ANGLES = [12, 6, -3, -15]
X_OFFSETS = [0, 100, 190, 240]

def compose_cards(card_paths: List[str],
                  angles: List[float],
                  x_offsets: List[int],
                  margin: int = 40) -> Image.Image:
    """Compose several cards into a fanned hand with a transparent margin."""
    assert len(card_paths) == len(angles) == len(x_offsets), \
        "card_paths, angles and x_offsets must be the same length"

    rotated_cards = []
    for path, angle in zip(card_paths, angles):
        with Image.open(path) as card:
            rotated = card.rotate(angle,
                                  resample=Image.Resampling.BICUBIC,
                                  expand=True)
            rotated_cards.append(rotated)

    widths = [img.width for img in rotated_cards]
    heights = [img.height for img in rotated_cards]
    base_width = x_offsets[-1] + widths[-1]
    base_height = max(heights)

    # Paste cards on a transparent canvas aligned at the bottom
    base = Image.new("RGBA", (base_width, base_height), (255, 255, 255, 0))
    for img, x in zip(rotated_cards, x_offsets):
        y = base_height - img.height
        base.paste(img, (x, y), img)

    # Crop empty space and add a margin
    bbox = base.getbbox()
    cropped = base.crop(bbox) if bbox else base
    result = Image.new("RGBA",
                       (cropped.width + margin * 2,
                        cropped.height + margin * 2),
                       (255, 255, 255, 0))
    result.paste(cropped, (margin, margin), cropped)
    return result

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate four‑of‑a‑kind images and special Spade combos.")
    parser.add_argument("--cards_dir", default="selected_cards2",
                        help="Directory containing individual card images")
    parser.add_argument("--output_dir", default="four_of_a_kind_auto",
                        help="Directory to save the generated images")
    parser.add_argument(
        "--max_size",
        type=int,
        default=None,
        help=("Maximum pixel dimension for the output images. "
              "If set, images are scaled so that their largest side equals "
              "max_size while preserving aspect ratio."),
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Four‑of‑a‑kind ranks
    ranks = ["7", "8", "9", "10", "jack", "queen", "king", "ace"]
    for rank in ranks:
        # Order cards as Diamond→Club→Heart→Spade
        files = [
            f"{rank}_of_diamonds.png",
            f"{rank}_of_clubs.png",
            f"{rank}_of_hearts.png",
            f"{rank}_of_spades.png",
        ]
        paths = [os.path.join(args.cards_dir, f) for f in files]
        composite = compose_cards(paths, ANGLES, X_OFFSETS)

        # Apply max_size if requested
        if args.max_size is not None:
            w, h = composite.size
            max_dim = max(w, h)
            if max_dim > args.max_size:
                scale = args.max_size / max_dim
                new_size = (int(w * scale), int(h * scale))
                composite = composite.resize(new_size, Image.Resampling.LANCZOS)

        out_path = os.path.join(args.output_dir, f"{rank}_four_of_a_kind.png")
        composite.save(out_path)
        print(f"Saved {rank} four‑of‑a‑kind to {out_path}")

    # Special Spade combos
    specials = {
        "spades_10_J_Q_K_A.png": [
            "10_of_spades.png",
            "jack_of_spades.png",
            "queen_of_spades.png",
            "king_of_spades.png",
            "ace_of_spades.png",
        ],
        "spades_J_Q_K_A.png": [
            "jack_of_spades.png",
            "queen_of_spades.png",
            "king_of_spades.png",
            "ace_of_spades.png",
        ],
        "spades_Q_K_A.png": [
            "queen_of_spades.png",
            "king_of_spades.png",
            "ace_of_spades.png",
        ],
    }
    # Angle/offset presets for combos of different lengths
    angle_presets = {
        5: [15, 7, 0, -7, -15],
        4: ANGLES,
        3: [10, 0, -10],
    }
    offset_presets = {
        5: [0, 80, 160, 240, 320],
        4: X_OFFSETS,
        3: [0, 100, 200],
    }

    for filename, files in specials.items():
        n = len(files)
        angles = angle_presets[n]
        offsets = offset_presets[n]
        paths = [os.path.join(args.cards_dir, f) for f in files]
        composite = compose_cards(paths, angles, offsets)

        if args.max_size is not None:
            w, h = composite.size
            max_dim = max(w, h)
            if max_dim > args.max_size:
                scale = args.max_size / max_dim
                new_size = (int(w * scale), int(h * scale))
                composite = composite.resize(new_size, Image.Resampling.LANCZOS)

        out_path = os.path.join(args.output_dir, filename)
        composite.save(out_path)
        print(f"Saved special combo to {out_path}")

if __name__ == "__main__":
    main()
