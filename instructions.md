i want to develop the telegram bot with qdrant vector database (evething already uploaded to the database)
i will use crewai for the ai agent 
all the files should be ready to scale and deploy on the server
all the code should be clean and readable with comments 

# Project overview
You are building a telegram bot agent where the user Sergey can get analytics of different questions based on his context stored in vector database, where he can ask about creating telegram posts, post on dzen, vc.ru exetra;

You will be using Python, TelegramBot, Qdrant, LangChain, CrewAI, openai api, and something for the server so that telegram bot agent will be available 24/7 and answer the questions instantly

# Core functionalities
1. Query the Sergey questions based on his initial input
    1.1 Input can be text, audio, image, voice message
    1.2 Answer using agentic RAG of CrewAI based on context from Qdrant vector database
    1.3 Answer should be in the telegram bot interface
    1.4 Answer should be in the russian language

# Doc, packages, tools
For ai powered agentic rag telegram framework will be used python-telegram-bot 

# Current file structure
xxxx


Sergey_140225_bot - is the name of the bot