import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from utils import *
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate


## OpenAi API key 
openai_api_key = "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"

## loading input data
DATA_STORE_DIR = 'vector_data_store/'
if os.path.exists(DATA_STORE_DIR):
  vector_store = FAISS.load_local(
      DATA_STORE_DIR,
      OpenAIEmbeddings(openai_api_key= openai_api_key)
  )
else:
  print(f"Missing files. Upload index.faiss and index.pkl files to {DATA_STORE_DIR} directory first")


## initiate the prompt template useful for guiding our chatbot 
_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.
If you don't know the answer, just say EXACTLY to the letter the following message : 'I don't know' and don't try to make up an answer. 
Please answer with as much detail as possible.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""

qa_prompt = PromptTemplate.from_template(_template)

## initiate chat_history
chat_history = []
## initiate llm
llm = ChatOpenAI( model_name='gpt-3.5-turbo', temperature= 0.1, openai_api_key= openai_api_key, 
             max_tokens= 1028)


## initiate the retriever
retriever = vector_store.as_retriever(search_type = "similarity", 
                                      search_kwargs = {"k" : 3} )
stage = 0 
if __name__ == '__main__':
    print("Welcome to Classfit AI Q&A chatbot! You can ask me any questions. If you want to exit, just type 'exit'.")
    ## create the ConversationalRetrievalChain
    qa = ConversationalRetrievalChain.from_llm(llm, 
                                           retriever, 
                                           condense_question_prompt = qa_prompt,
                                           return_source_documents = True)

    while True:
        ## user input query 
        user_input = input("Your question: ")
        if user_input.lower() == 'exit':
            print("Thank you for using the ClassFit chatbot. Have a great day!")
            break
                

        chat_history, answer, open_ticket = process_query_bis(qa, user_input , chat_history, vector_store)



        if not open_ticket : 
          user_input = input('Did that answer your question ? (Yes / No)')
          if user_input.lower() == 'yes' :
            print('Great - Can I help you with any other questions?') 
          else : 
            print('Oh no! Can you please try asking the question in a different way?')
            user_input = input('Your question: ')
            chat_history, answer, open_ticket = process_query_bis(qa, user_input, chat_history, vector_store)
            if not open_ticket : 
              user_input = input('Did that answer your question ? (Yes / No)')
              if user_input.lower() == 'yes' : 
                print('Great - Can I help you with any other questions?')
              else : 
                user_input = input("Oh no! Would you like me to raise a ticket for you and one of our team will get back to you as soon as possible?")
                if user_input.lower()== 'yes' : 
                  email = input('Please enter your email: ')
                  create_ticket(user_input.lower(), user_input, email) 
            else :
              print("I'm really sorry but I don't have the answer to that question. Would you like me to raise a ticket for you and one of our humans will get back to you as soon as possible?")
              user_input = input('Yes/No: ')
              if user_input.lower() == 'yes' : 
                 email = input('Please enter your email: ')
                 create_ticket(user_input.lower(), user_input, email) 

        else :
          print("Oh no! Can you please try asking the question in a different way?")
          user_input = input('Your question: ')
          chat_history, answer, open_ticket = process_query_bis(qa, user_input, chat_history, vector_store)
          if not open_ticket : 
            user_input = input('Did that answer your questions? (Yes/No)')
            if user_input == 'yes' : 
               print('Great - Can I help you with any other questions?')
            else :
                user_input = input("Oh no! Would you like me to raise a ticket for you and one of our team will get back to you as soon as possible?")
                if user_input.lower()== 'yes' : 
                  email = input('Please enter your email: ')
                  create_ticket(user_input.lower(), user_input, email) 
          else : 
              print("I'm really sorry but I don't have the answer to that question. Would you like me to raise a ticket for you and one of our humans will get back to you as soon as possible?")
              user_input = input('Yes/No: ')
              if user_input.lower()== 'yes' : 
                 email = input('Please enter your email: ')
                 create_ticket(user_input.lower(), user_input, email)             
        
            
        # # If the chatbot doesn't know the answer
        # if open_ticket : 
        #     user_input = input("Would you like to open a ticket? ")
        #     if is_affirmative(user_input, openai_api_key).lower() == 'affirmative':
        #         email = input("Please enter your email: ")
        #         create_ticket("User question", user_input, email)



