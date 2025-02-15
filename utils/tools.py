import cv2


def resize_image(image_path, max_height):
    """
    Resize the image, maintain aspect ratio, and adjust the image height to the specified maximum height.

    Parameters:
    - image_path: The path to the image file.
    - max_height: The specified maximum height value.

    Returns:
    - resized_image: The resized image.
    """

    # Read the image
    image = cv2.imread(image_path)
    height, width = image.shape[:2]

    # Calculate the new width, maintaining aspect ratio
    new_width = int(width * max_height / height)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, max_height))

    return resized_image