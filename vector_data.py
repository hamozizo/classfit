from utils import * 
import argparse
from getpass import getpass
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path_in', type = str, default= 'scraped_data/',
                        help = 'path to scraped data directory')
    
    parser.add_argument('--path_out', type = str, default = 'vector_data_store/', 
                        help = 'path to Faiss vector based data')
    parser.add_argument('--chunk_size', type = int, default = 500, help= 'size of chunks we want to create to create our vector based data')
    parser.add_argument('--openai_key', type = str, 
                        help= 'OpenAI API key')


    args = parser.parse_args()
    path_in = args.path_in
    df = create_dataframe_from_files(path_in)

    ## create docments using langchain
    documents = create_documents_from_dataframe(df)

    ## create a text splitter and split the documents into seperate chunks 
    chunk_size_limit = args.chunk_size
    text_splitter = CharacterTextSplitter(        
        separator = "Title:",
        chunk_size = 500,
        chunk_overlap  = 0,
        length_function = len,
    )
    split_docs = text_splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(openai_api_key= args.openai_key)
    vector_store = FAISS.from_documents(split_docs, embeddings)

    DATA_STORE_DIR = args.path_out
    vector_store.save_local(DATA_STORE_DIR)