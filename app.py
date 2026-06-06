import os
import streamlit as st
from rag_utility import process_document_to_chroma_db, answer_question, working_dir

# Set the working dir
working_dir = os.getcwd()

st.title("Q&A PDF")

# File uploader widget
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    # Define save path
    save_path = os.path.join(working_dir, uploaded_file.name)

    # Save the file
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    with st.spinner("Processing document, please wait..."):
        process_document = process_document_to_chroma_db(uploaded_file.name)

    if process_document == 0:
        st.success("Document processed successfully!")
    else:
        st.error("Failed to process the document. Please try again.")

# Text widget to get user input
user_question = st.text_area("Ask your question about the document...")

if st.button("Answer"):
    if not user_question.strip():
        st.warning("Please enter a question before clicking Answer.")
    else:
        with st.spinner("Thinking..."):
            answer = answer_question(user_question)
        st.markdown("**Bot Response**")
        st.markdown(answer, unsafe_allow_html=True)
























# import os
# import streamlit as st
# from rag_utility import process_document_to_chroma_db, answer_question, working_dir
#
# # Set the working dir
# working_dir = os.getcwd()
#
# st.title("Q&A PDF")
#
# # File uploader widget
# uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
#
# if uploaded_file is not None:
#     # Define save path
#     save_path = os.path.join(working_dir, uploaded_file.name)
#     # Save the file
#     with open(save_path, "wb") as f:
#         f.write(uploaded_file.getbuffer())
#
#     process_document = process_document_to_chroma_db(uploaded_file.name)
#     st.info("Document Processed_Successfully!")
#
# # text widget to get user input
# user_question = st.text_area("Ask your question about the document...")
#
# if st.button("Answer"):
#     answer = answer_question(user_question)
#
#     st.markdown("Bot Response")
#     st.markdown(answer, unsafe_allow_html=True)




