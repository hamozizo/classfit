## importing needed libraries and packages
import pandas as pd 
import os
from langchain.docstore.document import Document
from IPython.display import display, Markdown
from langchain.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate,ChatPromptTemplate
from langchain.chains import RetrievalQAWithSourcesChain, ConversationalRetrievalChain
import requests
import json
import openai
import pprint


def remove_newlines(serie):
    serie = serie.replace('\n{2,}', '\n', regex=True)
    serie = serie.str.replace('  ', ' ')
    serie = serie.str.replace('Title: Title:', ' ')
    serie = serie.str.replace('If you need any further help with this, please email hello@classfit.com.',' ')
    serie = serie.str.replace('\xa0', '')
    serie = serie.str.replace("If you need any further help with this", " ")
    serie = serie.str.replace('please email', ' ')
    serie = serie.str.replace('hello@classfit.com',' ')
    return serie

def create_dataframe_from_files(folder_path):
    data = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as file:
                url = file.readline().strip()
                title = file.readline().strip()
                title = title.replace('_',' ')
                text = file.read().strip()
                text = '\n'.join([title, text])
                # text = '\n'.join([url, text])
                data.append([title, text, url])
    df = pd.DataFrame(data, columns=['title', 'text', 'url'])
    df['text'] = remove_newlines(df.text)
    return df



def create_documents_from_dataframe(df):
    documents = []
    for _, row in df.iterrows():
        page_content =  row['text']
        metadata = {"source": row['url'] , "title" :row['title']}
        documents.append(Document(page_content=page_content, metadata=metadata))
    return documents




def print_result(result, query):
    output_text = f"""
    ### Question: 
    {query}
    ### Answer: 
    {result['answer']}
    # ### Sources: 
    {result['sources']}
    {list(set([doc.metadata['source'] for doc in result['source_documents']]))[0]}
    """

    print(output_text)

# def print_result_bis(result, query, vector_store):
#     output_text = f"""
#     ### Question: 
#     {query}
#     ### Answer: 
#     {result['answer']}
#     ### For more information, here are some useful links :  
#     -  {list(set([doc.metadata['source'] for doc in result['source_documents']]))[0]}
#     -  {list(set([doc.metadata['source'] for doc in result['source_documents']]))[1]}
#     """

#     print(output_text)


def print_result_bis(result, query, vector_store):
    output_text = f"""
    ### Question: 
    {query}
    ### Answer: 
    {result['answer']}
    ### Please see our knowledgebase tutorial on this for more information here : 
        - {vector_store._similarity_search_with_relevance_scores(
    query = result['answer'])[0][0].metadata['source']}
    """

    print(output_text)


def display_answer_streamlit(result, vector_store):
    output_text = f"""
    {result['answer']}
    ---------------------------
    Please see our knowledgebase tutorial on this for more information here :\n  
    {vector_store._similarity_search_with_relevance_scores(
    query = result['answer'])[0][0].metadata['source']}
    """
    return output_text
    

def print_result_unkown(query) : 
    output_text = f"""
    ### Question: 
    {query}
    ### Answer: 
    I'm really sorry but I don't have the answer to that question. Would you like me to raise a ticket for you and one of our humans will get back to you as soon as possible?
    """

    print(output_text)




def process_query(query, messages, vector_store, llm):
    messages.append(HumanMessagePromptTemplate.from_template(query))
    prompt = ChatPromptTemplate.from_messages(messages)

    chain_type_kwargs = {"prompt": prompt}
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_type = "similarity", 
                                            search_kwargs = {"k" : 1}),
        return_source_documents=True,
        chain_type_kwargs=chain_type_kwargs
    )

    result = chain(query)
    print_result(result, query)

    # Add the answer to the conversation context
    messages.append(SystemMessagePromptTemplate.from_template(result['answer']))

    return messages, result['answer']



def create_ticket(subject, description, email):
    domain = "https://classfit.freshdesk.com"
    api_key = "xBYxbhSZhlpH2om5HiK"
    password = "x"  # Dummy password, not used for anything but required by the API

    ticket = {
        "subject": subject,
        "description": description,
        "email": email,
        "priority": 1,
        "status": 2,
    }

    response = requests.post(
        f"{domain}/api/v2/tickets",
        auth=(api_key, password),
        headers={"Content-Type": "application/json"},
        data=json.dumps(ticket),
    )

    if response.status_code != 201:
        raise Exception(
            f"Failed to create ticket: {response.status_code}, {response.text}"
        )
    print("Ticket created successfully!")

def is_affirmative(response, openai_api_key):
    
    openai.api_key = openai_api_key
    
    model_engine = "text-davinci-003"
    prompt = f"Is the following response affirmative or negative? {response}?\
            Answer exactly and in one single word by 'affirmative' if yes and by 'negative' if not"

    # Generate a response
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=5,
        n=1,
        stop=None,
        temperature=0
    )

    response = completion.choices[0].text
    return response.strip() 


def process_query_bis(qa, query, chat_history, vector_store) : 
    open_ticket = False 
    query_ = query.lower()
    query_ = query_.replace('punchpass', 'class pack')
    query_ = query_.replace('punch pass', 'class pack')

    query_plus = f""" If you don't know the answer, please say 'I don't know'. Answer with all possible level of detail.
    {query_}
    """
    result = qa({"question": query_plus, "chat_history": chat_history})

    answer = result['answer']
    if "I'm sorry, I don't have that information" in answer: 
        open_ticket = True
        # print_result_unkown(query)

    elif "I'm sorry" in answer : 
        open_ticket = True
        # print_result_unkown(query)
    
    elif "I don't have that information" in answer: 
        open_ticket = True
        # print_result_unkown(query)

    elif "don't know" in answer : 
        open_ticket = True
        # print_result_unkown(query)

    elif 'The given context does not provide' in answer: 
        open_ticket = True
    elif 'context does not contain' in answer: 
        open_ticket = True
        
    else : 
        print_result_bis(result, query, vector_store)


    chat_history = [(query, result["answer"])]
    return chat_history, result['answer'], open_ticket


def process_query_streamlit(qa, query, chat_history) : 
    open_ticket = False 
    query_ = query.lower()
    query_ = query_.replace('punchpass', 'class pack')
    query_ = query_.replace('punch pass', 'class pack')

    query_plus = f""" If you don't know the answer, please say 'I don't know'. Answer with all possible level of detail.
    {query_}
    """
    result = qa({"question": query_plus, "chat_history": chat_history})

    answer = result['answer']
    if "I'm sorry, I don't have that information" in answer: 
        open_ticket = True
        # print_result_unkown(query)

    elif "I'm sorry" in answer : 
        open_ticket = True
        # print_result_unkown(query)
    
    elif "I don't have that information" in answer: 
        open_ticket = True
        # print_result_unkown(query)

    elif "don't know" in answer : 
        open_ticket = True
        # print_result_unkown(query)

    elif 'The given context does not provide' in answer: 
        open_ticket = True
    elif 'context does not contain' in answer: 
        open_ticket = True
    elif 'does not provide' in answer : 
        open_ticket = True
    

    chat_history = [(query, result["answer"])]
    return chat_history, result, open_ticket
