# Build: sudo docker build -t <project_name> .
# Run: sudo docker run -v $(pwd):/workspace/project --gpus all -it --rm <project_name>
docs/requirements.txt

FROM ubuntu:latest


ENV CONDA_ENV_NAME=satip
ENV PYTHON_VERSION=3.12


# Basic setup
RUN apt update && apt install -y bash \
                   build-essential \
                   git \
                   curl \
                   ca-certificates \
                   wget \
                   libaio-dev \
                   && rm -rf /var/lib/apt/lists

# Install Miniconda and create main env
ADD https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh miniconda3.sh
RUN /bin/bash miniconda3.sh -b -p /conda \
    && echo export PATH=/conda/bin:$PATH >> .bashrc \
    && rm miniconda3.sh
ENV PATH="/conda/bin:${PATH}"
RUN conda create -n ${CONDA_ENV_NAME} python=${PYTHON_VERSION} cartopy eccodes numpy matplotlib rasterio satpy[all] -c conda-forge

# Switch to bash shell
SHELL ["/bin/bash", "-c"]

# Install requirements
COPY requirements.txt ./
RUN source activate ${CONDA_ENV_NAME} \
    && pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt


# Set ${CONDA_ENV_NAME} to default virutal environment
RUN echo "source activate ${CONDA_ENV_NAME}" >> ~/.bashrc

# Cp in the development directory and install
COPY . ./
RUN source activate ${CONDA_ENV_NAME} && pip install -e .

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "satip", "/bin/bash", "-c"]

# Example commnad that can be used, need to set API_KEY, API_SECRET and SAVE_DIR
CMD ["conda", "run", "--no-capture-output", "-n", "satip", "python", "-u","near_now/notebooks/satip/app.py"]
