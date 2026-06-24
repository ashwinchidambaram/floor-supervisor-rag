# Problem: 
A plant operator wants floor supervisors to get answers from the right documentation. The system should intelligently route questions to the appropriate source (safety procedures, maintenance manuals, or quality control standards) and provide accurate answers.

# Notes:
- Core User: Floor Supervisor
- Goal: Floor Supervisor to be able to get right answers from the right documentation. 
- Data Soruces: Saftey procedures, Maintenance manuals, or Quality control standards; Documets wll not change frequently
- Tentative Solution: RAG 

# Components
- Agentic System Design 
- UI Design for User 

# Boundries:

# User Flow:
1. Supervisor has a question and opens the QA portal
2. Superviosir asks a multi-part question
3. [Agent] Will analyze the question asked, break it into question boundries 
4. [Agent] Will retrieve relevant chunks from the Vector DB 
5. [Agent][Judge] Will review the question + retreived chunks to ensure that they are relevant and grounded 
6. [Agent] Will assemble the relevant retreived chunks into a cohesive answer and output to the Supervisor 
7. Loop continues until Supervisor ends conversation

# Potential Agents:
1. LLM as Judge - goal is to review the asked question as well as retrieved chunks to ensure that they are relevant and grounded 
2. RAG/Assembly Agent - will collate the relevant retrieved chunks and write a response 
3. Q/A Agent - will take input from user, break it into the relevant questions that are being asked, and output response to user 

# Other Reqs:
- Conversation state memory retained during a conversation 
- Prompt Chacheing: store prompts within Reddis for faster repeat retrival 

# UI Design:
- Q/A Platform so there needs to be a simple question answer capability 