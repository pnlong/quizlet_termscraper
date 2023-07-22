# Quizlet Termscraper
Input a list of terms --> Scrape [quizlet](https://quizlet.com) for definitions to each term --> Output a markdown file.

I used this program to help automate my 1279 AP US History terms that I had to do for summer homework going into my Junior year of high school.

- Python packages `selenium`, `numpy`, `re`, `random`, `time`, and `sys` are required to run.

## **quizlet_termscraper_webdriver.py**
Scrapes [quizlet](https://quizlet.com) for a list of terms. Uses selenium webdriver. Outputs a markdown file, which can later be converted to a pdf. Run with:
```
cat terms | awk '{$1=$1};1' | python quizlet_termscraper_webdriver.py driver_address course_name prioritize_definitions_method maximum_number_of_definitions > terms_definitions.md
```
where:
- `terms` is a list of terms. See [samples/terms.txt](https://github.com/pnlong/quizlet_termscraper/blob/main/samples/terms.txt) for reference.
- `driver_address` is the filepath to Selenium Chrome Web Driver. The Chrome Web Driver can be downloaded at (https://chromedriver.chromium.org/downloads). **Note that Chrome Driver version must match the version of Chrome installed on the computer**. This argument is necessary.
- `course_name` is the name of the course for which `terms` relates to (in my case, A.P. United States History). Preferably, this argument is provided as the most commonly-used name for the course (APUSH). This argument is necessary (though you could provide it as ` `).
- `prioritize_definitions_method` is the method for prioritizing definitions found on various quizlet sites for a term; either `long` (to sort *longer* definitions first) or `short` (to sort *shorter* definitions first). This argument is necessary.
- `maximum_number_of_definitions` is the maximum number of definitions to output per term (`-1` to output all definitions found). Defaults to `-1`. This argument is *not* necessary.
- `terms_definitions.md` is the output file. See [samples/terms_definitions.md](https://github.com/pnlong/quizlet_termscraper/blob/main/samples/terms_definitions.md) for reference.

## **quizlet_termscraper.sh**
Bash script for running `quizlet_termscraper_webdriver.py`. Run with:
```
sh ~/quizlet_termscraper/quizlet_termscraper.sh output_directory software_directory termslist_prefix i course_name driver_address
```
where:
- `output_directory` is the directory to output the markdown file.
- `software_directory` is the directory in which `quizlet_termscraper_webdriver.py` is stored.
- `termslist_prefix` is the file prefix for the file containing the list of terms.
- `i` is an iterator used when running this program on multiple lists of terms.
- `course_name` is the same as the aforementioned `course_name` argument. The value provided here will be passed onto `quizlet_termscraper_webdriver.py`.
- `driver_address` is the same as the aforementioned `driver_address` argument. The value provided here will be passed onto `quizlet_termscraper_webdriver.py`.

## **change_maximum_number_of_definitions.py**
This program changes the number of definitions displayed in the [samples/terms_definitions.md](https://github.com/pnlong/quizlet_termscraper/blob/main/samples/terms_definitions.md) file to something like what is displayed in [samples/terms_definitions_filtered.md](https://github.com/pnlong/quizlet_termscraper/blob/main/samples/terms_definitions_filtered.md), which shows only a maximum of three terms. If I previously provided `-1` as the `maximum_number_of_definitions` argument to `quizlet_termscraper_webdriver.py`, I can use this program to only display the top three definitions. This is useful for when a lot of terms have five or more (too many) definitions to read through. Run with:
```
cat quizlet_termscraper_output | python ~/quizlet_termscraper/change_maximum_number_of_definitions.py maximum_number_of_definitions > terms_definitions_filtered.md
```
where:
- `quizlet_termscraper_output` is the input file; that is, the markdown file that has too many definitions per term at the moment. See [samples/terms_definitions.md](https://github.com/pnlong/quizlet_termscraper/blob/main/samples/terms_definitions.md) for reference.
- `maximum_number_of_definitions` is the maximum number of definitions to display per term. I usually set this argument to `3`.
- `terms_definitions_filtered.md` is the output file. See [samples/terms_definitions_filtered.md](https://github.com/pnlong/quizlet_termscraper/blob/main/samples/terms_definitions_filtered.md) for reference.

## **filter_pdf.sh**
Bash script for running `change_maximum_number_of_definitions.py`. Using `pandoc`, this script also converts the markdown files into PDF format using **latex**; delete line 24 if you want to remove this functionality. Run with:
```
sh ~/Desktop/Coding/quizlet_termscraper/filter_pdf.sh output_directory software_directory i
```
where:
- `output_directory` is the directory to output the filtered markdown file.
- `software_directory` is the directory in which `change_maximum_number_of_definitions.py` is found.
- `i` is an iterator used when running this program on multiple lists of terms.

## **runner.sh**
Bash script to run everything that has been mentioned so far together. Run with:
```
sh ~/Desktop/Coding/quizlet_termscraper/runner.sh output_directory software_directory termslist_prefix course_name driver_address
```
where:
- `output_directory` is the same as the aforementioned `output_directory` argument.
- `software_directory` is the same as the aforementioned `software_directory` argument.
- `termslist_prefix` is the same as the aforementioned `termslist_prefix` argument (see `quizlet_termscraper.sh` section).
- `course_name` is the same as the aforementioned `course_name` argument.
- `driver_address` is the same as the aforementioned `driver_address` argument.

---

Hopefully you find this program as useful as I did. Best of luck!
