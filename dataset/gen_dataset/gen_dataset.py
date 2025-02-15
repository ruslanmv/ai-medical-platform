import argparse
from copy import deepcopy
import json
import random
import re
from http import HTTPStatus
from pathlib import Path

import dashscope
import requests
import yaml
from tqdm import tqdm

def set_api_key(api_type, api_yaml_path):
    """Sets the API key

    Args:
        api_type (str): API type
        api_yaml_path (str): Path to the API YAML file
    """
    # Read the YAML file
    with open(api_yaml_path, "r", encoding="utf-8") as f:
        api_yaml = yaml.safe_load(f)

    # Set the API key
    if api_type == "qwen":
        api_key = api_yaml["ali_qwen_api_key"]
        dashscope.api_key = api_key
    elif api_type == "ernie":
        api_key = api_yaml["baidu_ernie_api_key"]
    else:
        raise ValueError("api_type must be qwen or ernie")

    return api_key


def call_qwen_message(content_str, model_type=dashscope.Generation.Models.qwen_turbo):
    """Calls the Qwen model to generate a message.

    Args:
        content_str (str): The input content string (prompt).
        model_type (str, optional): The specific Qwen model type to use.
            Defaults to dashscope.Generation.Models.qwen_turbo (Qwen Turbo model).

    Returns:
        str: The generated text response from the Qwen model, or "Error" on failure.
    """
    try:
        response = dashscope.Generation.call(model_type, prompt=content_str)
    except Exception as e:
        print(f"Maybe connect error, try again: {e}")
        response = dashscope.Generation.call(model_type, prompt=content_str)

    if response.status_code == HTTPStatus.OK:
        print("Used token: ", response.usage)
        response_str = response.output.text
    else:
        print(
            "Request id: %s, Status code: %s, error code: %s, error message: %s"
            % (
                response.request_id,
                response.status_code,
                response.code,
                response.message,
            )
        )
        response_str = "Error"

    return response_str


def call_ernie_message(content_str, access_token):
    """Calls the Ernie model to generate a message.

    Args:
        content_str (str): The input content string (prompt).
        access_token (str): Access token for Ernie API.

    Returns:
        str: The generated text response from the Ernie model, or "Error" on failure.
    """
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={access_token}"

    payload = json.dumps(
        {
            "messages": [
                {"role": "user", "content": content_str},
            ],
            "disable_search": False,
            "enable_citation": False,
        }
    )
    headers = {"Content-Type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == HTTPStatus.OK:

        # Get data from the response body
        response_json = response.json()

        print("Used token: ", response_json["usage"])
        response_str = response_json["result"]
    else:
        response_str = "Error"

    return response_str


def format_json_from_response(func, content_str, func_args, model_name):
    """Formats JSON from the raw string response of an API call.

    Args:
        func (function): The API calling function (e.g., call_qwen_message, call_ernie_message).
        content_str (str): The input content string (prompt) passed to the API.
        func_args: Arguments to be passed to the API calling function (model_type for Qwen, access_token for Ernie).
        model_name (str): Name of the model being used ("qwen" or "ernie").

    Returns:
        tuple: A tuple containing:
            - format_json (dict): The formatted JSON object.
            - response (str): The original raw string response from the API.
    """
    response = func(content_str, func_args)

    if "```json" in response:
        response = re.findall(r"`json(.*)`", response, flags=re.DOTALL)[0]

    # Remove characters that cause JSON formatting to fail
    response = response.replace("\\", "\\\\").replace("\n\n", "\n").replace("”", '"').replace("“", '"')

    if model_name == "qwen":
        # Qwen needs to check if there are " in the text and replace them with single quotes '

        # Find the first occurrence of the string '"output": "'
        output_start = response.find('"output": "')
        if output_start != -1:
            # Find the position of the second occurrence of '}' after the first '"output": "'
            output_end = response.find("}", output_start + 1)
            if output_end != -1:
                response = list(response)
                # Extract the substring within the second "output"
                check_len = len(response[output_start + len('"output": "') : output_end - 10])
                for idx in range(check_len):
                    str_idx = output_start + len('"output": "') + idx
                    if response[str_idx] == '"':
                        response[str_idx] = "'"

                response = "".join(response)

    # Add strict=False to solve "decode Invalid control character" error during JSON loading
    format_json = json.loads(response, strict=False)

    return format_json, response


def process_request(func, content_str, func_args, model_name):
    """Processes the request to an API and handles potential JSON formatting errors.

    Args:
        func (function): The API calling function (e.g., call_qwen_message, call_ernie_message).
        content_str (str): The input content string (prompt) to be passed to the API.
        func_args: Arguments to be passed to the API calling function (model_type for Qwen, access_token for Ernie).
        model_name (str): Name of the model being used ("qwen" or "ernie").

    Returns:
        dict: The formatted JSON response, or a dictionary with {"Error": "Error"} in case of persistent errors.
    """

    try:
        format_json, response = format_json_from_response(func, content_str, func_args, model_name)
    except Exception as e:
        try:
            # Try again
            print(f"\n Got error, try again <== {e} \n")
            if isinstance(e, json.decoder.JSONDecodeError):
                print(f"JSONDecodeError doc 1: {str(e.doc)} \n")
            format_json, response = format_json_from_response(func, content_str, func_args, model_name)
        except Exception as e:
            print(f"\n Got error <== {e} \n")
            if isinstance(e, json.decoder.JSONDecodeError):
                print(f"JSONDecodeError doc 2: {str(e.doc)} \n")
            with open(f"error-{model_name}.log", "a+", encoding="utf-8") as f_error:
                if isinstance(e, json.decoder.JSONDecodeError):
                    f_error.write(f"JSONDecodeError doc: {str(e.doc)} \n")
                f_error.write(str(e))
                f_error.flush()

            format_json = {"Error": "Error"}

    return format_json


def gen_product_highlights(dastset_yaml_path, api_yaml_path):
    """Generates product highlight descriptions based on a product YAML file.

    Args:
        dastset_yaml_path (str): Path to the dataset YAML file.
        api_yaml_path (_type_): Path to the API YAML file.
    """

    # Read the YAML file
    with open(dastset_yaml_path, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    set_api_key("qwen", api_yaml_path)

    for _, products in dataset_yaml["product_list"].items():
        for product_class, product in products.items():
            product_str = str(product).replace("'", "")
            print(f"Process: {product_str}")

            product_highlights = call_qwen_message(
                content_str=product_str,
                system_str="You are now proficient in all things in the hospital. Please help me list six advantages or characteristics of each detailed treatment method in five detailed professional treatment methods in each department, and then output in python-dic format: {class name: [feature 1, feature 2, ...]}, remove the words 1 and 2, and do not output anything other than the python dictionary, and do not have any warning messages.",
                model_type=dashscope.Generation.Models.qwen_turbo,
            )

            code_block = re.findall(r"`python(.*)`", product_highlights, flags=re.DOTALL)[0]
            if " = " in code_block[:20]:
                code_block = code_block.split(" = ")[1]

            products[product_class] = eval(re.findall(r"`python(.*)`", product_highlights, flags=re.DOTALL)[0])

    # Save the YAML file
    with open(f"{dastset_yaml_path}", "w", encoding="utf-8") as f:
        yaml.dump(dataset_yaml, f, allow_unicode=True)


def gen_dataset(dastset_yaml_path: str, api_yaml_path: str, save_json_root: Path, model_name: str, specific_name=""):
    """Generates a conversation dataset based on a dataset YAML file and specified model.

    Args:
        dastset_yaml_path (str): Path to the dataset YAML file.
        api_yaml_path (str): Path to the API YAML file.
        save_json_root (Path): Path to the directory where generated JSON datasets will be saved.
        model_name (str): Name of the model to use ("qwen" or "ernie").
        specific_name (str, optional):  If specified, only generate dataset for the role type with this name. Defaults to "".
    """

    # Ensure the output directory exists
    save_json_root.mkdir(parents=True, exist_ok=True)

    # Read the YAML file
    with open(dastset_yaml_path, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    if specific_name != "":
        assert (
            specific_name in dataset_yaml["role_type"]
        ), f"{specific_name} not in dataset_yaml['role_type'] ({dataset_yaml['role_type']}), pls check dataset yaml!"

    # Set the API key
    api_key = set_api_key(model_name, api_yaml_path)

    data_gen_setting = dataset_yaml["data_generation_setting"]
    gen_num = data_gen_setting["each_product_gen"]
    each_pick_hightlight = data_gen_setting["each_pick_hightlight"]
    each_pick_question = data_gen_setting["each_pick_question"]

    # Qwen model type configuration, ensure at least one is the strongest model
    # gen_model_type = [dashscope.Generation.Models.qwen_plus] * (gen_num - 2)
    # gen_model_type += [dashscope.Generation.Models.qwen_max] * 2
    qwen_model_type = [dashscope.Generation.Models.qwen_max] * gen_num

    for role_type, role_character in dataset_yaml["role_type"].items():

        if specific_name != "" and role_type != specific_name:
            # Only generate data for the specific character
            print(f"specific_name = {specific_name}, skipping for {role_type}")
            continue

        gen_json = dict()

        save_json_path = save_json_root.joinpath(f"{model_name}_{role_type}_train.json")
        bk_json_path = save_json_root.joinpath(f"{model_name}_{role_type}_train.json.bk")

        # Load previously generated JSON data if it exists
        if save_json_path.exists():
            with open(save_json_path, "r", encoding="utf-8") as f:
                gen_json = json.load(f)

        # If loading is successful, delete the backup JSON if it exists
        if bk_json_path.exists():
            bk_json_path.unlink()

        # Iterate through all products to facilitate progress bar display
        list_product = [
            product_name
            for _, products in dataset_yaml["product_list"].items()
            for _, product_name_list in products.items()
            for product_name in product_name_list.keys()
        ]

        # Generate character description
        character = "、".join(role_character)

        pbar = tqdm(total=len(list_product))

        # Iterate through product categories and products within each category
        for _, products in dataset_yaml["product_list"].items():
            for _, product_name_list in products.items():
                for product, hightlights in product_name_list.items():
                    pbar.set_description(product)

                    if product in gen_json:
                        # Skip already generated products
                        pbar.update(1)
                        continue

                    gen_json.update({product: []})

                    # Generate data for the current product
                    for idx in range(gen_num):

                        # Randomly pick ${each_pick_hightlight} product highlights
                        if each_pick_hightlight >= len(hightlights):
                            # If exceeding, shuffle to increase randomness
                            hightlights_list = hightlights[:]
                            random.shuffle(hightlights_list)
                        else:
                            hightlights_list = random.sample(hightlights, each_pick_hightlight)
                        hightlight_str = "、".join(hightlights_list)

                        # Randomly pick ${each_pick_question} customer question types
                        if each_pick_question >= len(dataset_yaml["customer_question_type"]):
                            # If exceeding, shuffle to increase randomness
                            customer_question_type_list = dataset_yaml["customer_question_type"][:]
                            random.shuffle(customer_question_type_list)
                        else:
                            customer_question_type_list = random.sample(dataset_yaml["customer_question_type"], each_pick_question)
                        customer_question_str = "、".join(customer_question_type_list)

                        # Product information string construction
                        product_info_str = dataset_yaml["product_info_struct"][0].replace("{name}", product)
                        product_info_str += dataset_yaml["product_info_struct"][1].replace("{highlights}", hightlight_str)

                        content_str = (
                            data_gen_setting["dataset_gen_prompt"]
                            .replace("{role_type}", role_type)
                            .replace("{character}", character)
                            .replace("{product_info}", product_info_str)
                            .replace("{customer_question}", customer_question_str)
                            .replace("{each_conversation_qa}", str(data_gen_setting["each_conversation_qa"]))
                            .replace(
                                "{dataset_json_format}",
                                data_gen_setting["dataset_json_format"].replace("{product_info}", product_info_str),
                            )
                        )

                        print(f"\n Request [ {model_name} ] {idx + 1}/{gen_num} ==> {content_str} \n")
                        if model_name == "qwen":
                            format_json = process_request(call_qwen_message, content_str, qwen_model_type[idx], model_name)
                        elif model_name == "ernie":
                            format_json = process_request(call_ernie_message, content_str, api_key, model_name)
                        else:
                            raise ValueError(f"model_name {model_name} not support")

                        if "conversation" in format_json and len(format_json["conversation"]) > 0:

                            # For the first result, to save tokens, need to put system and input back
                            conversation_setting = deepcopy(dataset_yaml["conversation_setting"])
                            system_str = (
                                conversation_setting["system"].replace("{role_type}", role_type).replace("{character}", character)
                            )
                            input_str = conversation_setting["first_input"].replace("{product_info}", product_info_str)

                            # Add necessary information to the first conversation turn
                            format_json["conversation"][0] = {
                                "system": system_str,
                                "input": input_str,
                                "output": format_json["conversation"][0]["output"],
                            }
                        else:
                            format_json = {"Error": "Error"}

                        print(f"\n Response [ {model_name} ] {idx + 1}/{gen_num} <== {format_json} \n")
                        gen_json[product].append(format_json)

                    pbar.update(1)

                    # Backup the old JSON file
                    if save_json_path.exists():
                        save_json_path.rename(bk_json_path)

                    # Save the generated JSON data to file
                    with open(save_json_path, "w", encoding="utf-8") as f:
                        json.dump(gen_json, f, indent=4, ensure_ascii=False)

                    # If saving is successful, delete the old backup file
                    if bk_json_path.exists():
                        bk_json_path.unlink()


if __name__ == "__main__":

    # Example: Generate data for all characters using Qwen API
    # cd /path/to/Streamer-Sales/dataset/gen_dataset
    # python gen_dataset.py qwen

    # Command line argument parsing
    parser = argparse.ArgumentParser(description="Gen Dataset")
    parser.add_argument("model_name", type=str, choices=["qwen", "ernie"], help="Model name for data generation")
    parser.add_argument("--data_yaml", type=str, default="../../configs/conversation_cfg.yaml", help="data setting file path")
    parser.add_argument("--api_yaml", type=str, default="../../configs/api_cfg.yaml", help="api setting file path")
    parser.add_argument("--output_dir", type=str, default="./train_dataset/response", help="generation json output dir")
    parser.add_argument("--specific_name", type=str, default="", help="Character name for data generation")
    args = parser.parse_args()

    # Generate product highlights - optional
    # gen_product_highlights(args.data_yaml, args.api_yaml)

    # Generate conversation dataset
    gen_dataset(
        args.data_yaml, args.api_yaml, Path(args.output_dir), model_name=args.model_name, specific_name=args.specific_name
    )