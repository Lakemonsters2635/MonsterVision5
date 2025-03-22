# no idea if this works
"""
#!/bin/bash 
# Get the script's directory 
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" 
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt" 
# Check if requirements.txt exists 
if [ ! -f "$REQUIREMENTS_FILE" ]; then 
    echo "Error: requirements.txt not found in the same directory." 
    exit 1 
fi 
# Install modules using pip 
echo "Installing modules from requirements.txt..." 
python3 -m pip install -r "$REQUIREMENTS_FILE" 
# Check if installation was successful 
if [ $? -eq 0 ]; then 
    echo "All modules installed successfully!" 
else 
    echo "Failed to install some modules. Check the error messages above." 
fi
"""