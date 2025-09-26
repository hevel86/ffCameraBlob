from PIL import Image
import os

def crop_image(input_path, output_path, box):
    """
    Crops a specified area from an image and saves the result as a new file.

    Args:
        input_path (str): The file path of the original image.
        output_path (str): The file path where the cropped image will be saved.
        box (tuple): A 4-tuple defining the left, upper, right, and lower
                     pixel coordinates of the area to be cropped.
    
    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    # Check if the input file exists
    if not os.path.exists(input_path):
        print(f"Error: The file at {input_path} was not found.")
        return False

    try:
        # Open the image file
        with Image.open(input_path) as img:
            # The .crop() method returns a new Image object.
            # The original image object (img) is not modified.
            cropped_img = img.crop(box)
            
            # Save the new cropped image
            cropped_img.save(output_path)
            print(f"Successfully cropped and saved the image to {output_path}")
            return True

    except IOError as e:
        print(f"An error occurred while handling the image file: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    # --- Example Usage ---
    
    # First, let's create a dummy bitmap image to work with.
    # This is not part of the core function but makes the script
    # runnable out of the box.
    try:
        dummy_img = Image.new('RGB', (200, 200), color='white')
        
        # Draw a red rectangle in the center for demonstration
        from PIL import ImageDraw
        draw = ImageDraw.Draw(dummy_img)
        draw.rectangle([50, 50, 150, 150], fill="red")
        
        # Save the dummy image
        input_file = "test_image.bmp"
        dummy_img.save(input_file)
        print(f"Created a dummy image named '{input_file}' for the example.")
        
        # Define the area to crop (the red square)
        # The box is a 4-tuple: (left, upper, right, lower)
        # Note: The 'right' and 'lower' coordinates are exclusive.
        crop_box = (50, 50, 150, 150)
        
        # Define the output file path
        output_file = "cropped_image.bmp"
        
        # Call the function to crop the image
        if crop_image(input_file, output_file, crop_box):
            print("Cropping process completed successfully.")
            
    except ImportError:
        print("Pillow is not installed. Please run 'pip install Pillow' and try again.")
    except Exception as e:
        print(f"An error occurred during the example execution: {e}")
