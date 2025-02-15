import argparse
from pathlib import Path

import cv2
import numpy as np
import yaml

from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
from openai import OpenAI


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Get OCR result for images directory")
    parser.add_argument("--image_dir", type=str, required=True, help="Images directory.")
    parser.add_argument("--ocr_output_dir", type=str, default="./ocr_output", help="OCR result output directory.")

    parser.add_argument(
        "--instruction_output_dir", type=str, default="./instructions", help="Instructions result output directory."
    )
    parser.add_argument("--data_yaml", type=str, default="../../configs/conversation_cfg.yaml", help="data setting file path")
    parser.add_argument("--api_yaml", type=str, default="../../configs/api_cfg.yaml", help="api setting file path")

    args = parser.parse_args()
    return args


# def create_slices(image_path, slices_save_dir: Path):
#     image = cv2.imread(image_path)
#     height, width, _ = image.shape

#     ratio_thres = 2  # Ratio threshold, slicing will be performed if larger than 2 times
#     wh_ratio = max(width / height, height / width)
#     if wh_ratio < ratio_thres:
#         return [image_path]

#     if height > width:
#         direction = "vertical"
#         max_side = height
#         step = width
#     else:
#         direction = "horizontal"
#         step = height
#         max_side = width

#     slices = []

#     # TODO Sliding window overlap rate 0.1
#     for i in range(0, max_side, step):

#         if i + step > max_side:
#             # If the last slice exceeds the single slice step, merge the current slice with the previous one
#             if direction == "vertical":
#                 # Vertical
#                 slices[-1]["img"] = np.concatenate((slices[-1]["img"], image[i:height, :]), axis=0)
#             else:
#                 # Horizontal
#                 slices[-1]["img"] = np.concatenate((slices[-1]["img"], image[:, i:width]), axis=1)
#             break

#         if direction == "vertical":
#             # Vertical slicing
#             top_left = [0, i]
#             slice = image[i : i + step, :]
#         else:
#             # Horizontal slicing
#             top_left = [i, 0]
#             slice = image[:, i : i + step, :]

#         # Image pixel coordinates, top-left corner [x, y]
#         slices.append({"img": slice, "top_left": top_left})

#     slice_path_list = []
#     # Save images, change to
#     for idx, slice in enumerate(slices):
#         slice_path = f"{slices_save_dir / str(idx)}.png"
#         cv2.imwrite(str(slice_path), slice["img"])
#         slice_path_list.append({"img": slice_path, "top_left": slice["top_left"]})

#     return slice_path_list

def create_slices(image_path, slices_save_dir: Path):
    image = cv2.imread(image_path)
    height, width, _ = image.shape

    ratio_thres = 2  # Ratio threshold, slicing will be performed if larger than 2 times
    wh_ratio = max(width / height, height / width)
    if wh_ratio < ratio_thres:
        return [{"img": image_path, "top_left": (0, 0)}]  # Returns a list containing a dictionary

    if height > width:
        direction = "vertical"
        max_side = height
        step = width
    else:
        direction = "horizontal"
        step = height
        max_side = width

    slices = []

    # TODO Sliding window overlap rate 0.1
    for i in range(0, max_side, step):

        if i + step > max_side:
            # If the last slice exceeds the single slice step, merge the current slice with the previous one
            if direction == "vertical":
                # Vertical
                slices[-1]["img"] = np.concatenate((slices[-1]["img"], image[i:height, :]), axis=0)
            else:
                # Horizontal
                slices[-1]["img"] = np.concatenate((slices[-1]["img"], image[:, i:width]), axis=1)
            break

        if direction == "vertical":
            # Vertical slicing
            top_left = [0, i]
            slice = image[i : i + step, :]
        else:
            # Horizontal slicing
            top_left = [i, 0]
            slice = image[:, i : i + step, :]

        # Image pixel coordinates, top-left corner [x, y]
        slices.append({"img": slice, "top_left": top_left})

    slice_path_list = []
    # Save images, change to
    for idx, slice in enumerate(slices):
        slice_path = f"{slices_save_dir / str(idx)}.png"
        cv2.imwrite(str(slice_path), slice["img"])
        slice_path_list.append({"img": slice_path, "top_left": slice["top_left"]})

    return slice_path_list


# def ocr_pred(ocr_model, image_path: Path, output_dir: Path, show_res=False):

#     work_dir = output_dir.joinpath("work_dir", image_path.stem)
#     work_dir.mkdir(parents=True, exist_ok=True)

#     show_dir = output_dir.joinpath("work_dir", image_path.stem + "_show")

#     # If it's too large, slice the image
#     # Create horizontal slices
#     iamge_slices = create_slices(str(image_path), work_dir)

#     result = []
#     print(type(img_info), img_info)
#     for img_info in iamge_slices:
        
#         img_path = img_info["img"]
def ocr_pred(ocr_model, image_path: Path, output_dir: Path, show_res=False):

    work_dir = output_dir.joinpath("work_dir", image_path.stem)
    work_dir.mkdir(parents=True, exist_ok=True)

    show_dir = output_dir.joinpath("work_dir", image_path.stem + "_show")
    if not show_dir.exists():
        show_dir.mkdir(parents=True, exist_ok=True)

    # If the image is too large, slice the image
    # Create horizontal slices
    image_slices = create_slices(str(image_path), work_dir)  # Ensure correct variable name is used here

    result = []
    for img_info in image_slices:  # Use the correct variable name
        print(type(img_info), img_info)  # This line of code is for debugging, to view the type and content of img_info

        img_path = img_info["img"]  # Ensure correct key is used here
        # Inference
        ocr_res = ocr_model.ocr(img_path, cls=True)[0]
        if ocr_res is None:
            continue

        # Regress to original image coordinates based on the top-left corner
        # res = [ [text box], [recognition result, confidence] ]
        # left_top = img_info["top_left"]
        # for res in ocr_res:
        #     for points in res[0]:
        #         points[0] += left_top[0]
        #         points[1] += left_top[1]
        #     result.append(res)

        result += ocr_res

        if show_res:
            # Display results
            image = Image.open(img_path).convert("RGB")

        # Inference
        ocr_res = ocr_model.ocr(img_path, cls=True)[0]
        if ocr_res == None:
            continue

        # Regress to original image coordinates based on the top-left corner
        # res = [ [text box], [recognition result, confidence] ]
        # left_top = img_info["top_left"]
        # for res in ocr_res:
        #     for points in res[0]:
        #         points[0] += left_top[0]
        #         points[1] += left_top[1]
        #     result.append(res)

        result += ocr_res

        if not show_res:
            continue

        if not show_dir.exists():
            show_dir.mkdir(parents=True, exist_ok=True)

        # Display results
        image = Image.open(img_path).convert("RGB")
        boxes = [line[0] for line in ocr_res]
        txts = [line[1][0] for line in ocr_res]
        scores = [line[1][1] for line in ocr_res]
        im_show = draw_ocr(image, boxes, txts, scores, font_path="./fonts/simfang.ttf")
        im_show = Image.fromarray(im_show)
        im_show.save(str(show_dir.joinpath("result_" + Path(img_path).name)))

    # Delete intermediate files
    # shutil.rmtree(work_dir)

    return result


def get_ocr_res(image_dir: str, output_dir: str, show_res=True):
    """Gets OCR results for images in a directory.

    Args:
        image_dir (str): Path to the image directory.
        output_dir (str): Path to the directory for saving OCR output.
        show_res (bool, optional): Whether to display and save visualization of OCR results. Defaults to True.
    """

    # Check if the image path exists
    image_dir = Path(image_dir)
    if not image_dir.exists():
        raise FileNotFoundError(f"Cannot find image dir: {image_dir}")

    # Initialize the model
    ocr_model = PaddleOCR(use_angle_cls=True, lang="ch")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for img_path in Path(image_dir).iterdir():
        print(f"processing ocr result for {str(img_path)}")

        if img_path.suffix.lower() not in [".png", ".jpeg", ".jpg", ".bmp"]:
            continue

        result_list = ocr_pred(ocr_model, img_path, output_dir, show_res)

        # Write the results to a file
        with open(output_dir.joinpath(img_path.stem + ".txt"), "w", encoding="utf-8") as f:
            for res in result_list:
                # res = [ [text box], [recognition result, confidence] ]
                f.write(res[1][0])


def gen_instructions_according_ocr_res(ocr_txt_root, instruction_save_root, api_yaml_path, data_yaml_path):
    """Generates instructions based on OCR results using an API.

    Args:
        ocr_txt_root (str): Path to the directory containing OCR text files.
        instruction_save_root (str): Path to the directory for saving generated instructions.
        api_yaml_path (str): Path to the API YAML configuration file.
        data_yaml_path (str): Path to the data YAML configuration file.
    """

    instruction_save_root = Path(instruction_save_root)
    instruction_save_root.mkdir(parents=True, exist_ok=True)

    # Read the YAML file
    with open(api_yaml_path, "r", encoding="utf-8") as f:
        api_yaml = yaml.safe_load(f)

    client = OpenAI(
        api_key=api_yaml["ali_qwen_api_key"],
        base_url="https://api.moonshot.cn/v1"
    )

    # Read the YAML file
    with open(data_yaml_path, "r", encoding="utf-8") as f:
        data_yaml = yaml.safe_load(f)

    for txt_path in Path(ocr_txt_root).iterdir():

        print("Processing txt: ", txt_path.name)

        if txt_path.suffix not in [".txt"]:
            continue

        file_object = client.files.create(file=txt_path, purpose="file-extract")

        # Get results
        # file_content = client.files.retrieve_content(file_id=file_object.id)
        # Note that the previous retrieve_content API is marked as warning in the latest version, the following line can be used instead
        # If it is an older version, you can use retrieve_content
        file_content = client.files.content(file_id=file_object.id).text

        # Put it in the request
        messages = [
            {
                "role": "system",
                "content": "You are Kimi, an AI assistant provided by Moonshot AI. You are better at Chinese and English conversations. You will provide users with safe, helpful, and accurate answers. At the same time, you will refuse all answers involving terrorism, racism, pornography, violence and other issues. Moonshot AI is a proper noun and cannot be translated into other languages.",
            },
            {
                "role": "system",
                "content": file_content,
            },
            {
                "role": "user",
                "content": data_yaml["instruction_generation_setting"]["dataset_gen_prompt"],
            },
        ]

        # Then call chat-completion to get Kimi's answer
        completion = client.chat.completions.create(
            model="moonshot-v1-32k",
            messages=messages,
            temperature=0.3,
        )

        res_msg = completion.choices[0].message

        with open(instruction_save_root.joinpath(txt_path.stem + ".md"), "w", encoding="utf-8") as f:
            f.write(res_msg.content)


# if __name__ == "__main__":
#     args = parse_args()

#     # Use OCR to recognize text in images
#     get_ocr_res(args.image_dir, args.ocr_output_dir)

#     # Call kimi API to summarize
#     gen_instructions_according_ocr_res(args.ocr_output_dir, args.instruction_output_dir, args.api_yaml, args.data_yaml)

#     print("All done !")
if __name__ == "__main__":
    args = parse_args()

    try:
        # Use OCR to recognize text in images
        get_ocr_res(args.image_dir, args.ocr_output_dir)

        # Call API to summarize
        gen_instructions_according_ocr_res(args.ocr_output_dir, args.instruction_output_dir, args.api_yaml, args.data_yaml)

        print("All done !")
    except Exception as e:
        print(f"An error occurred: {e}")