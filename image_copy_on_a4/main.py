from PIL import Image
import math

def cm_to_px(cm, dpi):
    return int(cm * dpi / 2.54)

def create_a4_with_images(
    img_path: str,
    out_path: str = "a4_output.jpg",
    dpi: int = 300,
    target_w_cm: float = 7,
    target_h_cm: float = 3.5,
    margin_cm: float = 1.0,
    page_margin_cm: float = 1.0,
    page_size_cm: tuple = (21.0, 29.7),  # A4
):
    # Convert dimensions to pixels
    target_w_px = cm_to_px(target_w_cm, dpi)
    target_h_px = cm_to_px(target_h_cm, dpi)
    margin_px   = cm_to_px(margin_cm, dpi)
    page_margin_px = cm_to_px(page_margin_cm, dpi)
    page_w_px = cm_to_px(page_size_cm[0], dpi)
    page_h_px = cm_to_px(page_size_cm[1], dpi)

    # Open and resize source image
    src = Image.open(img_path)
    img_resized = src.resize((target_w_px, target_h_px), Image.LANCZOS)

    # Prepare blank A4 page
    page = Image.new("RGB", (page_w_px, page_h_px), "white")

    # Compute how many images fit per row/column
    available_w = page_w_px - 2 * page_margin_px + margin_px
    available_h = page_h_px - 2 * page_margin_px + margin_px
    cols = math.floor(available_w / (target_w_px + margin_px))
    rows = math.floor(available_h / (target_h_px + margin_px))

    if cols < 1 or rows < 1:
        raise ValueError("Image too big or margins too large to fit even one per page.")

    # Paste images in a grid
    for r in range(rows):
        for c in range(cols):
            x = page_margin_px + c * (target_w_px + margin_px)
            y = page_margin_px + r * (target_h_px + margin_px)
            page.paste(img_resized, (x, y))

    # Save result (JPEG or PNG)
    page.save(out_path, dpi=(dpi, dpi))
    print(f"Saved A4 sheet with {rows*cols} images to '{out_path}'")

if __name__ == "__main__":
    # Example usage: adjust 'input.jpg' to your file
    create_a4_with_images(
        img_path="flag.jpeg",
        out_path="a4_sheet_5sm.jpg",
        dpi=300,
        target_w_cm=5,
        target_h_cm=2.5,
        margin_cm=1.0,
        page_margin_cm=1.0
    )
