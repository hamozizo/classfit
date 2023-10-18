# ------------------------------------------- #
## Importing Packages

import streamlit as st 
from streamlit_chat import message
import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from utils import *
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
import uuid
from langchain import PromptTemplate
# ------------------------------------------- #

# ------------------------------------------- #
## Loading data

## OpenAi API key 
openai_api_key = "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"

## import vector data
DATA_STORE_DIR = 'vector_data_store/'
if os.path.exists(DATA_STORE_DIR):
  vector_store = FAISS.load_local(
      DATA_STORE_DIR,
      OpenAIEmbeddings(openai_api_key= openai_api_key)
  )
else:
  print(f"Missing files. Upload index.faiss and index.pkl files to {DATA_STORE_DIR} directory first")
# ------------------------------------------- #


# ------------------------------------------- #
## Chatbot build

## initiate the prompt template useful for guiding our chatbot 
_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.
If you don't know the answer, just say EXACTLY to the letter the following message : 'I don't know' and don't try to make up an answer. 
Please answer with as much detail as possible.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""

qa_prompt = PromptTemplate.from_template(_template)

## store chat history 
chat_history = []
## initiate llm
llm = ChatOpenAI( model_name='gpt-3.5-turbo', temperature= 0.1, openai_api_key= openai_api_key, 
             max_tokens= 1028)
## define retriever
retriever = vector_store.as_retriever(search_type = "similarity", 
                                      search_kwargs = {"k" : 3} )
qa = ConversationalRetrievalChain.from_llm(llm, 
                                           retriever, 
                                           condense_question_prompt = qa_prompt,
                                           return_source_documents = True)
# ------------------------------------------- #



# ------------------------------------------- #
## Streamlit sessions states 
st.title('Classfit Expert')

## Storing the chat 
if 'generated' not in st.session_state : 
    st.session_state['generated'] = []

if 'past' not in st.session_state : 
    st.session_state['past'] = []

if 'stage' not in st.session_state:
    st.session_state['stage'] = 'initial'

def get_text(text = "Hello, how can I help you", k = 'input'):
    input_text = st.text_input(text, key =k) 
    return input_text
# ------------------------------------------- #



# ------------------------------------------- #
## Using the application
user_input = get_text()



if user_input: 
    if st.session_state['stage'] == 'initial':
        chat_history, result, open_ticket = process_query_streamlit(qa, user_input, chat_history)
        output = display_answer_streamlit(result, vector_store)
        output = '\n'.join([output, "Did that answer your question ? (Yes / No)"])
        if not open_ticket : 
            st.session_state.past.append(user_input)
            st.session_state.generated.append(output)
            st.session_state['stage'] = "confirm_first_answer"

        else :
            st.session_state.past.append(user_input)
            st.session_state.generated.append('Oh no! Can you please try asking the question in a different way?')
            st.session_state['stage'] = "reask"

        ticket_subject = user_input
        print(ticket_subject)

    elif st.session_state['stage'] == "confirm_first_answer" : 
        if user_input.lower() in ['yes', 'yes ', 'yeah', ' yes', 'yess'] :
            st.session_state.past.append(user_input)
            st.session_state.generated.append('Great - Can I help you with any other questions?')            
            st.session_state['stage'] = 'initial'
        else : 
            st.session_state.past.append(user_input)
            st.session_state.generated.append('Oh no! Can you please try asking the question in a different way?')
            st.session_state['stage'] = 'reask'


    elif st.session_state['stage'] == "reask" :
        chat_history, result, open_ticket = process_query_streamlit(qa, user_input, chat_history)
        output = display_answer_streamlit(result, vector_store)
        output = '\n'.join([output, "Did that answer your question ? (Yes / No)"])
        if not open_ticket : 
            st.session_state.past.append(user_input)
            st.session_state.generated.append(output)
            st.session_state['stage'] = 'confirm_second_answer'
        else : 
            st.session_state.past.append(user_input)
            st.session_state.generated.append('Oh no! Would you like me to raise a ticket for you and one of our team will get back to you as soon as possible?')
            st.session_state['stage'] = "confirm_ticket"

        ticket_subject = user_input
        print(ticket_subject)

    elif st.session_state['stage'] == "confirm_second_answer":
        if user_input.lower() in ['yes', 'yes ', 'yeah', ' yes', 'yess'] :
            st.session_state.past.append(user_input)
            st.session_state.generated.append('Great - Can I help you with any other questions?')            
            st.session_state['stage'] = 'initial'
        else : 
            st.session_state.past.append(user_input)
            st.session_state.generated.append('Oh no! Would you like me to raise a ticket for you and one of our team will get back to you as soon as possible?')
            st.session_state['stage'] = "confirm_ticket"


    elif st.session_state['stage'] == 'confirm_ticket':
        if user_input.lower() in ['yes', 'yes ', 'yeah', ' yes', 'yess']:
            st.session_state.past.append(user_input)
            st.session_state.generated.append('Please provide your email')
            st.session_state['stage'] = 'get_email'
        else:
            st.session_state.past.append(user_input)
            st.session_state.generated.append("Okay, no ticket was created.")
            st.session_state['stage'] = 'initial'

    elif st.session_state['stage'] == 'get_email':
        email = user_input
        ticket_subject = st.session_state['past'][-2]
        if ticket_subject is not None : 
            subject = ticket_subject
            description = "The user has requested for support"
            create_ticket(subject, description, email)
            output = "Ticket created successfully!"
            st.session_state.past.append(user_input)
            st.session_state.generated.append(output)
            st.session_state['stage'] = 'initial'

if st.session_state['generated']:
    for i in range(len(st.session_state['generated']) -1, -1, -1):
        message(st.session_state['generated'][i], key=str(i))
        message(st.session_state['past'][i], key=str(i)+'_user', is_user=True)
# ------------------------------------------- #