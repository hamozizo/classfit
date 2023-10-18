#!/bin/bash

if [ "$UPDATE_DATA" = "true" ]
then
  python scrapy.py
  python vector_data.py
fi

streamlit run classfit_chatbot_api.py
