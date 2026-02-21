from click.testing import CliRunner

from cli.package_auto_assembler import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0, result.output
    assert "Usage:" in result.output
    assert "make-package" in result.output

# def test_cli_paa_test_install():
#     """Test paa can test-install itself twice without errors."""

#     result = subprocess.run(
#             [ sys.executable, "-m", "pip", "install", "package-auto-assembler"], 
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True  # Capture output as text
#         )

#     # for _ in range(2):
#     #     result = subprocess.run(
#     #         [ sys.executable, "-m", "paa", "test-install", "package-auto-assembler", "--skip-deps-install", "--build-mkdocs"], 
#     #         stdout=subprocess.PIPE,
#     #         stderr=subprocess.PIPE,
#     #         text=True  # Capture output as text
#     #     )

#     expected_output = "Module package-auto-assembler installed in local environment, overwriting previous version!"

#     # Assert that the command ran successfully
#     assert expected_output in result.stdout

# def test_cli_paa_make_package():
#     """Test if paa can make package without errors."""


#     result1 = subprocess.run(
#             [ sys.executable, "-m", "paa", "make-package", "package-auto-assembler"],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True  # Capture output as text
#         )


#     result2 = subprocess.run(
#         [ sys.executable, "-m", "paa", "test-install", "package-auto-assembler", "--skip-deps-install", "--build-mkdocs"], 
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         text=True  # Capture output as text
#     )


#     expected_output1 = "Module package-auto-assembler prepared as a package."
#     expected_output2 = "Module package-auto-assembler installed in local environment, overwriting previous version!"

#     # Assert that the command ran successfully
#     assert expected_output1 in result1.stdout
#     assert expected_output2 in result2.stdout
