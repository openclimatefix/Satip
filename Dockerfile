FROM continuumio/miniconda3:latest

COPY environment.yml .
COPY satip /satip
COPY setup.py .

RUN conda env create -f environment.yml

# The name satip_dev is specified in environment.yml
RUN echo "source activate satip_dev" > ~/.bashrc

ENV PATH /opt/conda/envs/satip_dev/bin:$PATH
