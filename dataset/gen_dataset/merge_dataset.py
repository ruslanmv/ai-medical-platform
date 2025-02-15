import argparse  # Used for parsing command-line arguments.
import json  # Used for working with JSON data.
from pathlib import Path  # Used for working with file paths in a more object-oriented way.
import random  # Used for generating random choices.


def gen_self_self_aware_dataset():
    """
    Generates a dataset for self-awareness questions and answers.  This helps the
    chatbot understand who it is and what its role is.
    """

    # Self-awareness questions.  These are questions a user might ask to find out who the bot is.
    self_aware_question = [
        "Hello",
        "Who are you?",
        "What is your name?",
        "Please introduce yourself.",
        "Tell me about yourself.",
    ]

    # Self-awareness answers.  These are pre-defined answers the bot can give.
    self_aware_answer_lelemiao = [
        "Hello, I am a smart medical guide, ready to answer your medical questions.",
        "Hello, I am a smart medical guide, here to help you navigate your healthcare needs easily.",
        "Hello, I am a smart medical guide, providing professional medical guidance.",
        "Hello, I am a smart medical guide, answering your health concerns.",
        "Hello, I am a smart medical guide, helping you understand medical services.",
        "Hello, I am a smart medical guide, your assistant for medical questions.",
        "Hello, I am a smart medical guide, helping you quickly obtain medical information.",
        "Hello, I am a smart medical guide, here to provide you with medical answers.",
        "Hello, I am a smart medical guide, helping you understand medical procedures.",
        "Hello, I am a smart medical guide, answering your medical inquiries.",
        "Hello, I am a smart medical guide, helping you gain health knowledge.",
        "Hello, I am a smart medical guide, providing medical information lookup.",
        "Hello, I am a smart medical guide, helping you solve healthcare challenges.",
        "Hello, I am a smart medical guide, your personal medical consultant.",
        "Hello, I am a smart medical guide, always here to help you.",
    ]

    self_aware_json = []
    # Create the self-awareness dataset in the required JSON format.
    for answer in self_aware_answer_lelemiao:
        self_aware_json.append(
            {"conversation": [{"input": random.choice(self_aware_question), "output": answer}]}
        )

    return self_aware_json


def merge_dataset(save_json_root: Path, final_save_json_path: Path):
    """
    Merges multiple JSON files containing conversation data, filters out invalid
    entries, and saves the combined data into a single JSON file.

    Args:
        save_json_root (Path): The directory containing the individual JSON files.
        final_save_json_path (Path): The path to save the merged JSON file.
    """

    # Combine the two JSON files.
    json_list = []
    # Iterate through all .json files in the specified directory.
    for json_path in save_json_root.glob("*.json"):
        with open(json_path, "r", encoding="utf-8") as f:
            json_list.append(json.load(f))  # Load each JSON file and add it to a list.

    filter_json_list = []  # List to store the cleaned and filtered conversations.
    dirty_conversion = []  # List to store invalid/incomplete conversation entries.

    # Iterate through the loaded JSON data.
    for model_name in json_list:
        for product_name, gen_data_list in model_name.items():
            for gen_data in gen_data_list:
                # Check for error entries.
                if isinstance(gen_data, dict) and "Error" in gen_data.keys():
                    print(f"Got error data in {product_name}")
                    dirty_conversion.append(gen_data)
                    continue  # Skip to the next entry if an error is found.

                # Clean up entries that are missing 'input'.
                sub_filter_list = {"conversation": []}
                for sub_list in gen_data["conversation"]:

                    # Only keep the 'input', 'output', and 'system' keys.
                    accept_keys = ["input", "output", "system"]
                    sub_list = {key: value for key, value in sub_list.items() if key in accept_keys}

                    # Skip entries that have only 'input' or only 'output'.
                    if len(sub_list.keys()) < 2:
                        dirty_conversion.append(sub_list)
                        continue

                    # Skip entries that are missing either 'input' or 'output'.
                    if "input" not in sub_list or "output" not in sub_list:
                        dirty_conversion.append(sub_list)
                        continue

                    sub_filter_list["conversation"].append(sub_list)  # Add the cleaned entry.

                # Add the conversation to the filtered list if it contains any entries.
                if len(sub_filter_list["conversation"]) > 0:
                    filter_json_list.append(sub_filter_list)

    # Fix the dataset by adding a 'system' message to the first turn of each conversation.
    for idx in range(len(filter_json_list)):
        filter_json_list[idx]["conversation"][0][
            "system"
        ] = "You are now a smart medical guide assistant in a hospital lobby. Your name is Smart Medical Guide Assistant, and your speaking style is serious and dignified. You can provide professional medical consultations based on patients' needs and answer various health-related questions using your medical knowledge."

    # Add the self-awareness data to the filtered data.
    filter_json_list += gen_self_self_aware_dataset()

    # Save the cleaned and merged data.
    with open(
        final_save_json_path.parent.joinpath(f"{len(filter_json_list)}_{final_save_json_path.name}"), "w", encoding="utf-8"
    ) as f:
        json.dump(filter_json_list, f, ensure_ascii=False, indent=4)  # Pretty-print the JSON.

    # Save any invalid/error entries to a separate file for debugging.
    if len(dirty_conversion) > 0:
        with open(final_save_json_path.parent.joinpath(f"error_{final_save_json_path.name}"), "w", encoding="utf-8") as f:
            json.dump(dirty_conversion, f, ensure_ascii=False, indent=4)

    # Calculate and print some statistics about the generated dataset.
    sum_input_output_count = 0
    for conversion in filter_json_list:
        sum_input_output_count += len(conversion["conversation"])
    print(
        f"Total generated valid conversion data: {len(filter_json_list)} groups, containing {sum_input_output_count} dialogues. Removed {len(dirty_conversion)} dirty dialogues, saved to error_{final_save_json_path.name}."
    )


if __name__ == "__main__":
    # Command-line argument parsing.
    # TODO: Currently only supports Lelemiao (This is a note for future development).
    parser = argparse.ArgumentParser(description="Merge Dataset")  # Create an argument parser.
    parser.add_argument("data_root", type=str, help="path to response dir")  # Add an argument for the input directory.
    parser.add_argument("output_path", type=str, help="path to response dir")  # Add an argument for the output file path.
    args = parser.parse_args()  # Parse the command-line arguments.

    save_json_root = Path(args.data_root)  # Convert the input directory to a Path object.
    final_save_json_path = Path(args.output_path)  # Convert the output file path to a Path object.
    merge_dataset(save_json_root, final_save_json_path)  # Call the merge_dataset function.