"""
Core functions for image to PDF conversion.
Extracted from the CLI script for reuse in the web app.
"""

from pathlib import Path
from typing import List, Tuple
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import sys
import tempfile
import io


def split_by_semicolon(image_files: List[Path]) -> Tuple[List[Path], List[Path]]:
    """
    Split image files into two groups based on whether filename contains ';'.
    
    Args:
        image_files: List of image file paths
        
    Returns:
        Tuple of (group1_with_semicolon, group2_without_semicolon)
    """
    group1 = [f for f in image_files if ';' in f.name]
    group2 = [f for f in image_files if ';' not in f.name]
    
    return group1, group2


def sort_by_priority(files: List[Path], priority_list: List[str]) -> List[Path]:
    """
    Sort files based on priority list.
    
    Files are sorted by their position in the priority list. Files not in the
    priority list maintain their relative order and appear after prioritized files.
    
    Args:
        files: List of file paths to sort
        priority_list: Ordered list of keywords or filenames for priority matching
        
    Returns:
        Sorted list of file paths
    """
    def get_priority_index(file_path: Path) -> int:
        """
        Get the priority index for a file.
        Returns the index of the first matching priority keyword,
        or a large number if no match found.
        """
        filename = file_path.name
        
        for idx, priority_item in enumerate(priority_list):
            # Check if priority item matches the filename or is contained in it
            if priority_item == filename or priority_item in filename:
                return idx
        
        # No match found - assign large index to maintain relative order
        return len(priority_list) + files.index(file_path)
    
    return sorted(files, key=get_priority_index)


def create_pdf_with_images(image_files: List[Path], output_path: Path, 
                           page_size=letter):
    """
    Create a PDF with each image on its own page and filename as heading.
    
    Args:
        image_files: Ordered list of image files to include
        output_path: Path where the PDF should be saved
        page_size: PDF page size (default: letter)
    """
    if not image_files:
        print("Warning: No images to process")
        return
    
    c = canvas.Canvas(str(output_path), pagesize=page_size)
    page_width, page_height = page_size
    
    for img_path in image_files:
        try:
            # Draw black background rectangle for heading
            c.setFillColorRGB(0, 0, 0)  # Black background
            rect_x = 40
            rect_y = page_height - 65
            rect_width = page_width - 80
            rect_height = 35
            c.rect(rect_x, rect_y, rect_width, rect_height, fill=1, stroke=0)
            
            # Add filename as heading at the top (without extension) in yellow
            c.setFillColorRGB(1, 1, 0)  # Yellow text
            c.setFont("Helvetica-Bold", 16)
            text_x = 50
            text_y = page_height - 50
            # Replace underscores with spaces for display
            display_name = img_path.stem.replace('_', ' ')
            c.drawString(text_x, text_y, display_name)
            
            # Reset fill color to black for image drawing
            c.setFillColorRGB(0, 0, 0)
            
            # Load image and get dimensions
            img = Image.open(img_path)
            
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_width, img_height = img.size
            
            # Calculate available space (leaving room for heading and margins)
            available_width = page_width - 100  # 50pt margins on each side
            available_height = page_height - 150  # Top margin (including heading) + bottom margin
            
            # Calculate scaling to fit image on page while maintaining aspect ratio
            width_ratio = available_width / img_width
            height_ratio = available_height / img_height
            scale_ratio = min(width_ratio, height_ratio, 1.0)  # Don't upscale
            
            scaled_width = img_width * scale_ratio
            scaled_height = img_height * scale_ratio
            
            # Resize image to target dimensions to reduce file size
            # Convert points to pixels at 72 DPI
            target_pixel_width = int(scaled_width * 2)  # Back to 2x for better quality
            target_pixel_height = int(scaled_height * 2)
            
            if img_width > target_pixel_width or img_height > target_pixel_height:
                img = img.resize((target_pixel_width, target_pixel_height), Image.LANCZOS)
            
            # Save to temporary JPEG with higher quality for better clarity
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=92, optimize=True)
            img_buffer.seek(0)
            
            # Center the image horizontally on the page
            img_x = (page_width - scaled_width) / 2
            # Position image below the heading
            img_y = page_height - 100 - scaled_height
            
            # Draw the compressed image using ImageReader
            img_reader = ImageReader(img_buffer)
            c.drawImage(img_reader, img_x, img_y, 
                       width=scaled_width, height=scaled_height,
                       preserveAspectRatio=True)
            
            # Start new page for next image
            c.showPage()
            
            print(f"Added: {img_path.name}")
            
        except Exception as e:
            print(f"Error processing {img_path.name}: {e}", file=sys.stderr)
            continue
    
    # Save the PDF
    c.save()
    print(f"\nPDF created successfully: {output_path}")


def parse_priority_list(priority_str: str) -> List[str]:
    """
    Parse priority list from comma-separated string.
    
    Args:
        priority_str: Comma-separated list of keywords/filenames
        
    Returns:
        List of priority items
    """
    if not priority_str:
        return []
    
    return [item.strip() for item in priority_str.split(',') if item.strip()]
