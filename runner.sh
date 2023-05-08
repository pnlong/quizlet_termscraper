#!/bin/bash

# sh ~/Desktop/Coding/quizlet_termscraper/runner.sh output_directory software_directory termslist_prefix course_name driver_address

output=${1}
software=${2}
termslist_prefix=${3}
course_name=${4}
driver_address=${5}

for i in $(seq $(ls $(dirname $termslist_prefix) | wc -l))
do
	echo starting unit${i}...
	
	# get the raw terms and definitions quizlet data with quizlet_termscraper.sh
	sh $software/quizlet_termscraper.sh ${output} ${software} ${termslist_prefix} ${i} ${course_name} ${driver_address}

	# filter down the raw terms and definitions data and format into .pdf format with filter_pdf.sh
	sh $software/filter_pdf.sh ${output} ${software} ${i}

	echo unit${i} done

done