#!/bin/bash

set -e  

ENV_FILE="environment.yml"
ENV_NAME=$(grep "name:" "$ENV_FILE" | awk '{print $2}')

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: The environment file '$ENV_FILE' was not found." >&2
    exit 1
fi

echo "Creating the Conda environment '$ENV_NAME' from '$ENV_FILE'..."
conda env create -f "$ENV_FILE"

echo ""
echo "-----------------------------------------------"
echo " Environment '$ENV_NAME' created successfully! "
echo "-----------------------------------------------"
echo ""
echo "To activate this environment, run:"
echo "    conda activate $ENV_NAME"
echo ""
echo "Once activated, you can run the main workflow with:"
echo "    python run_disaggregation.py"
echo ""
echo "To deactivate the environment when you are finished, run:"
echo "    conda deactivate"
echo ""