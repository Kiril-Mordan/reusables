install_and_clean(){

    local module_name=$1
    local module_name=$(basename "$module_name" .py)

    python3 tools/test_install_package.py "$module_name"
    pip install --force-reinstall dist/*0.0.0-py3-none-any.whl

    rm -rf build
    rm -rf dist
    rm -rf "$module_name"
    rm -rf "$module_name".egg-info
}

install_and_clean "$@"