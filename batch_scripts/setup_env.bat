call cd ..
call conda env create -f environment.yml
call conda activate satip_dev
call ipython kernel install --user --name=satip_dev
pause