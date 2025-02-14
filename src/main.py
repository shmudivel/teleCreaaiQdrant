from dotenv import load_dotenv
from crewai import Crew
from tasks import contentSocialMediaTasks
from agents import contentSocialMediaAgents


from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OpenAIEmbeddings
import qdrant_client
import os
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI
# from pinecone import Pinecone
# import os

# def init_pinecone():
#     """Initialize Pinecone client"""
#     pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
#     # Create or get existing index
#     index_name = "content-index"
#     if index_name not in pc.list_indexes().names():
#         pc.create_index(
#             name=index_name,
#             dimension=1536,  # OpenAI embeddings dimension
#             metric="cosine"
#         )
#     return pc.Index(index_name)

def get_vector_store():
    client = qdrant_client.QdrantClient(
        os.getenv("QDRANT_HOST"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

    embeddings = OpenAIEmbeddings()
    
    vectorstore = Qdrant(
        client=client,
        collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
        embeddings=embeddings
    )

    return vectorstore


def main():
    load_dotenv()

    # create vector store
    vector_store = get_vector_store()

    #create the chain
    qa = RetrievalQA.from_chain_type(
      llm=OpenAI(),
      chain_type="stuff",
      retriever=vector_store.as_retriever()
    )
    
    print("## Команда Сергея Черненко ")
    print('-------------------------------')
    # meeting_participants = input("What are the emails for the participants (other than you) in the meeting?\n")
    # meeting_context = input("What is the context of the meeting?\n")
    # meeting_objective = input("What is your objective for this meeting?\n")
    query_context_script_video_youtube = input("Введите текст, скрипт для видео на YouTube?\n")
    query_target_audience = input("Кто ваш целевая аудитория?\n")

    #need print to check wheather the query is retriving from vector store
    # print("query_context_script_video_youtube: ", query_context_script_video_youtube)
    # print("query_target_audience: ", query_target_audience)

    # # Run the queries and print the retrieved context
    # text_context_script_video_youtube = qa.run(query_context_script_video_youtube)
    # print("Retrieved context for script video YouTube: ", text_context_script_video_youtube)

    # target_audience = qa.run(query_target_audience)
    # print("Retrieved context for target audience: ", target_audience)
    # # objective_goal = input("Что вы хотите достичь на этой обсужении?\n")

    # tasks = MeetingPrepTasks()
    # agents = MeetingPrepAgents()
    tasks = contentSocialMediaTasks()
    agents = contentSocialMediaAgents()
    
    # create agents
    general_content_social_media_agent = agents.general_content_social_media_agent()
    editor_social_media_agent = agents.editor_social_media_agent()
    # meeting_strategy_agent = agents.meeting_strategy_agent()
    # summary_and_briefing_agent = agents.summary_and_briefing_agent()
    
    # Create tasks first
    research_task = tasks.research_task(general_content_social_media_agent, query_context_script_video_youtube, query_target_audience)
    industry_analysis_task = tasks.industry_analysis_task(editor_social_media_agent, query_context_script_video_youtube, query_target_audience)
    
    # Then set the context
    industry_analysis_task.context = [research_task]
    
    # meeting_strategy_task = tasks.meeting_strategy_task(meeting_strategy_agent, target_audience, objective_goal)
    # summary_and_briefing_task = tasks.summary_and_briefing_task(summary_and_briefing_agent, target_audience, objective_goal)
    
    # meeting_strategy_task.context = [research_task, industry_analysis_task]
    # summary_and_briefing_task.context = [research_task, industry_analysis_task, meeting_strategy_task]
    
    crew = Crew(
      agents=[
        general_content_social_media_agent,
        editor_social_media_agent,
        # meeting_strategy_agent,
        # summary_and_briefing_agent
      ],
      tasks=[
        research_task,
        industry_analysis_task,
        # meeting_strategy_task,
        # summary_and_briefing_task
      ]
    )
    
    result = crew.kickoff()
        
    print(result)
    
if __name__ == "__main__":
    main()