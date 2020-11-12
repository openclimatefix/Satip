call cd ..
call conda activate satip_dev
call python setup.py sdist bdist_wheel
call twine upload --skip-existing dist/*
pause