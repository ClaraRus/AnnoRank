#!/bin/bash

while getopts ":d:" opt; do
  case $opt in
    d)
      echo "-d was triggered, Parameter: $OPTARG" >&2
      conda run -n tool_ui python ./flask_app/db_create_pipeline.py --config_path ./configs/$OPTARG\_tutorial/config_create_db_$OPTARG.json & \
      conda run -n tool_ui python ./flask_app/app_ranking.py --config_path ./configs/$OPTARG\_tutorial/config_shortlist_$OPTARG.json & \
      conda run -n tool_ui python ./flask_app/app_ranking_compare.py --config_path ./configs/$OPTARG\_tutorial/config_compare_$OPTARG.json & \
      conda run -n tool_ui python ./flask_app/app_ranking_compare_annotate.py --config_path ./configs/$OPTARG\_tutorial/config_compare_annotate_$OPTARG.json & \
      conda run -n tool_ui python ./flask_app/app_annotate_document.py --config_path ./configs/$OPTARG\_tutorial/config_annotate_score_$OPTARG.json & \
      bigbro --filename ./dataset/$OPTARG/big_brother.log csv
      
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done


