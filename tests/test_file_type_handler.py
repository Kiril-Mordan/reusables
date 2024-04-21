import pytest
import yaml
import dill
from python_modules.parameterframe import FileTypeHandler

# A list of tuples, each containing the paths to an input YAML file and its expected output YAML file
YAML_FILE_PATHS = [
    ("tests/parameterframe/example_configs/param_1.yaml", "tests/parameterframe/example_configs_output/param_1.yaml"),
    ("tests/parameterframe/example_configs/param_2.yaml", "tests/parameterframe/example_configs_output/param_2.yaml"),
    ("tests/parameterframe/example_configs/param_3.yaml", "tests/parameterframe/example_configs_output/param_3.yaml"),
    ("tests/parameterframe/example_configs/param_4.yaml", "tests/parameterframe/example_configs_output/param_4.yaml"),
    ("tests/parameterframe/example_configs/param_5.yaml", "tests/parameterframe/example_configs_output/param_5.yaml")

]

TXT_FILE_PATHS = [
    ("tests/parameterframe/example_configs/param_6.txt", "tests/parameterframe/example_configs_output/param_6.txt"),
    ("tests/parameterframe/example_configs/param_7.txt", "tests/parameterframe/example_configs_output/param_7.txt"),
    ("tests/parameterframe/example_configs/param_8.txt", "tests/parameterframe/example_configs_output/param_8.txt"),
    ("tests/parameterframe/example_configs/param_9.txt", "tests/parameterframe/example_configs_output/param_9.txt"),
    ("tests/parameterframe/example_configs/param_10.txt", "tests/parameterframe/example_configs_output/param_10.txt")
]

DILL_FILE_PATHS = [
    ("tests/parameterframe/example_configs/param_11.dill", "tests/parameterframe/example_configs_output/param_11.dill"),
    ("tests/parameterframe/example_configs/param_12.dill", "tests/parameterframe/example_configs_output/param_12.dill"),
    ("tests/parameterframe/example_configs/param_13.dill", "tests/parameterframe/example_configs_output/param_13.dill"),
    ("tests/parameterframe/example_configs/param_14.dill", "tests/parameterframe/example_configs_output/param_14.dill"),
    ("tests/parameterframe/example_configs/param_15.dill", "tests/parameterframe/example_configs_output/param_15.dill")
]

OTHER_FILE_PATHS = [
    ("tests/parameterframe/example_configs/param_16", "tests/parameterframe/example_configs_output/param_16"),
    ("tests/parameterframe/example_configs/param_17", "tests/parameterframe/example_configs_output/param_17"),
    ("tests/parameterframe/example_configs/param_18", "tests/parameterframe/example_configs_output/param_18"),
    ("tests/parameterframe/example_configs/param_19", "tests/parameterframe/example_configs_output/param_19"),
    ("tests/parameterframe/example_configs/param_20", "tests/parameterframe/example_configs_output/param_20"),
    ("tests/parameterframe/example_configs/param_21.ipynb", "tests/parameterframe/example_configs_output/param_21.ipynb"),
    ("tests/parameterframe/example_configs/param_22.zip", "tests/parameterframe/example_configs_output/param_22.zip"),
    ("tests/parameterframe/example_configs/param_23.csv", "tests/parameterframe/example_configs_output/param_23.csv"),
    ("tests/parameterframe/example_configs/param_24.pdf", "tests/parameterframe/example_configs_output/param_24.pdf"),
    ("tests/parameterframe/example_configs/param_25.html", "tests/parameterframe/example_configs_output/param_25.html")
]


def load_yaml_file(file_path):
    """Utility function to load a YAML file and return its content."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

@pytest.mark.parametrize("input_path,expected_output_path", YAML_FILE_PATHS)
def test_compare_yaml_files(input_path, expected_output_path):
    """
    Test function to compare the content of two yaml files.
    """

    fth = FileTypeHandler(file_path = input_path)
    fth.process_file()

    parameter_id = fth.parameter_id
    parameter_attributes_list = fth.parameter_attributes_list
    attribute_values_list = fth.attribute_values_list

    fth2 = FileTypeHandler()

    fth2.reconstruct_file(
        file_path = expected_output_path,
        parameter_id = parameter_id,
        parameter_attributes_list = parameter_attributes_list,
        attribute_values_list = attribute_values_list
    )


    input_content = load_yaml_file(input_path)
    expected_output_content = load_yaml_file(expected_output_path)

    assert input_content == expected_output_content, f"yaml content mismatch between {input_path} and {expected_output_path}"

@pytest.mark.parametrize("input_path,expected_output_path", TXT_FILE_PATHS)
def test_compare_txt_files(input_path, expected_output_path):
    """
    Test function to compare the content of two txt files.
    """

    fth = FileTypeHandler(file_path = input_path)
    fth.process_file()

    parameter_id = fth.parameter_id
    parameter_attributes_list = fth.parameter_attributes_list
    attribute_values_list = fth.attribute_values_list

    fth2 = FileTypeHandler()

    fth2.reconstruct_file(
        file_path = expected_output_path,
        parameter_id = parameter_id,
        parameter_attributes_list = parameter_attributes_list,
        attribute_values_list = attribute_values_list
    )

    with open(input_path, 'r') as file:
        input_content = file.read()

    with open(expected_output_path, 'r') as file:
        expected_output_content = file.read()

    assert input_content == expected_output_content, f"txt content mismatch between {input_path} and {expected_output_path}"

@pytest.mark.parametrize("input_path,expected_output_path", DILL_FILE_PATHS)
def test_compare_dill_files(input_path, expected_output_path):
    """
    Test function to compare the content of two dill files.
    """

    fth = FileTypeHandler(file_path = input_path)
    fth.process_file()

    parameter_id = fth.parameter_id
    parameter_attributes_list = fth.parameter_attributes_list
    attribute_values_list = fth.attribute_values_list

    fth2 = FileTypeHandler()

    fth2.reconstruct_file(
        file_path = expected_output_path,
        parameter_id = parameter_id,
        parameter_attributes_list = parameter_attributes_list,
        attribute_values_list = attribute_values_list
    )


    with open(input_path, 'rb') as file:
        input_content = dill.load(file)

    with open(expected_output_path, 'rb') as file:
        expected_output_content = dill.load(file)

    assert input_content == expected_output_content, f"dill content mismatch between {input_path} and {expected_output_path}"

@pytest.mark.parametrize("input_path,expected_output_path", OTHER_FILE_PATHS)
def test_compare_unknown_files(input_path, expected_output_path):
    """
    Test function to compare the content of two dill files.
    """

    fth = FileTypeHandler(file_path = input_path)
    fth.process_file()

    parameter_id = fth.parameter_id
    parameter_attributes_list = fth.parameter_attributes_list
    attribute_values_list = fth.attribute_values_list

    fth2 = FileTypeHandler()

    fth2.reconstruct_file(
        file_path = expected_output_path,
        parameter_id = parameter_id,
        parameter_attributes_list = parameter_attributes_list,
        attribute_values_list = attribute_values_list
    )

    with open(input_path, 'rb') as file:
        input_content = file.read()

    with open(expected_output_path, 'rb') as file:
        expected_output_content = file.read()

    assert input_content == expected_output_content, f"content mismatch between {input_path} and {expected_output_path}"

