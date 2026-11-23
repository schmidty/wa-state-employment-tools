# Washington State Employment PDF Application
This application will fill out the PDF found at [esd.wa.gov/job-search-log](https://esd.wa.gov/media/pdf/1045/esd-job-search-log-251110-accessiblepdf/).

- It requires Python 3.10+ to run.
- It requires having a clean, empty `ESD-job-search-log-251110 Accessible.pdf` document in the same folder.

## Load Python 3 Requirements
```
pip install -r requirements.txt
```

## Run Application
```
python create.py -h
```

## Run Tests
Run this from the root directory of the application.
```
python -m pytest
```

## Run a Specific Test
Run this from the root directory of the application.
```
python -m pytest -k 'test_get_start_of_week_no_input'
```