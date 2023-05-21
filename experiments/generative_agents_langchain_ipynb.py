import math
from datetime import datetime, timedelta
from typing import List

import faiss
from langchain.chat_models import ChatOpenAI
from langchain.docstore import InMemoryDocstore
from langchain.embeddings import OpenAIEmbeddings
from langchain.experimental.generative_agents import GenerativeAgent, GenerativeAgentMemory
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain.vectorstores import FAISS
from termcolor import colored

USER_NAME = "Person A"  # The name you want to use when interviewing the agent.
LLM = ChatOpenAI(max_tokens=1500)  # Can be any LLM you want.


def relevance_score_fn(score: float) -> float:
    """Return a similarity score on a scale [0, 1]."""
    # This will differ depending on a few things:
    # - the distance / similarity metric used by the VectorStore
    # - the scale of your embeddings (OpenAI's are unit norm. Many others are not!)
    # This function converts the euclidean norm of normalized embeddings
    # (0 is most similar, sqrt(2) most dissimilar)
    # to a similarity function (0 to 1)
    return 1.0 - score / math.sqrt(2)


def create_new_memory_retriever():
    """Create a new vector store retriever unique to the agent."""
    # Define your embedding model
    embeddings_model = OpenAIEmbeddings()
    # Initialize the vectorstore as empty
    embedding_size = 1536
    index = faiss.IndexFlatL2(embedding_size)
    vectorstore = FAISS(
        embeddings_model.embed_query, index, InMemoryDocstore({}), {}, relevance_score_fn=relevance_score_fn
    )
    return TimeWeightedVectorStoreRetriever(vectorstore=vectorstore, other_score_keys=["importance"], k=15)


tommies_memory = GenerativeAgentMemory(
    llm=LLM,
    memory_retriever=create_new_memory_retriever(),
    verbose=False,
    reflection_threshold=8,  # we will give this a relatively low number to show how reflection works
)

tommie = GenerativeAgent(
    name="Tommie",
    age=25,
    traits="anxious, likes design, talkative",  # You can add more persistent traits here
    status="looking for a job",
    # When connected to a virtual world, we can have the characters update their status
    memory_retriever=create_new_memory_retriever(),
    llm=LLM,
    memory=tommies_memory,
)

# The current "Summary" of a character can't be made because the agent hasn't made
# any observations yet.
print(tommie.get_summary())

# We can add memories directly to the memory object
tommie_observations = [
    "Tommie remembers his dog, Bruno, from when he was a kid",
    "Tommie feels tired from driving so far",
    "Tommie sees the new home",
    "The new neighbors have a cat",
    "The road is noisy at night",
    "Tommie is hungry",
    "Tommie tries to get some rest.",
]
for observation in tommie_observations:
    tommie.memory.add_memory(observation)

# Now that Tommie has 'memories', their self-summary is more descriptive, though still rudimentary.
# We will see how this summary updates after more observations to create a more rich description.
print(tommie.get_summary(force_refresh=True))


def interview_agent(agent: GenerativeAgent, message: str) -> str:
    """Help the notebook user interact with the agent."""
    new_message = f"{USER_NAME} says {message}"
    return agent.generate_dialogue_response(new_message)[1]


interview_agent(tommie, "What do you like to do?")

interview_agent(tommie, "What are you looking forward to doing today?")

interview_agent(tommie, "What are you most worried about today?")

# Let's have Tommie start going through a day in the life.
observations = [
    "Tommie wakes up to the sound of a noisy construction site outside his window.",
    "Tommie gets out of bed and heads to the kitchen to make himself some coffee.",
    "Tommie realizes he forgot to buy coffee filters and starts rummaging through his moving boxes to find some.",
    "Tommie finally finds the filters and makes himself a cup of coffee.",
    "The coffee tastes bitter, and Tommie regrets not buying a better brand.",
    "Tommie checks his email and sees that he has no job offers yet.",
    "Tommie spends some time updating his resume and cover letter.",
    "Tommie heads out to explore the city and look for job openings.",
    "Tommie sees a sign for a job fair and decides to attend.",
    "The line to get in is long, and Tommie has to wait for an hour.",
    "Tommie meets several potential employers at the job fair but doesn't receive any offers.",
    "Tommie leaves the job fair feeling disappointed.",
    "Tommie stops by a local diner to grab some lunch.",
    "The service is slow, and Tommie has to wait for 30 minutes to get his food.",
    "Tommie overhears a conversation at the next table about a job opening.",
    "Tommie asks the diners about the job opening and gets some information about the company.",
    "Tommie decides to apply for the job and sends his resume and cover letter.",
    "Tommie continues his search for job openings and drops off his resume at several local businesses.",
    "Tommie takes a break from his job search to go for a walk in a nearby park.",
    "A dog approaches and licks Tommie's feet, and he pets it for a few minutes.",
    "Tommie sees a group of people playing frisbee and decides to join in.",
    "Tommie has fun playing frisbee but gets hit in the face with the frisbee and hurts his nose.",
    "Tommie goes back to his apartment to rest for a bit.",
    "A raccoon tore open the trash bag outside his apartment, and the garbage is all over the floor.",
    "Tommie starts to feel frustrated with his job search.",
    "Tommie calls his best friend to vent about his struggles.",
    "Tommie's friend offers some words of encouragement and tells him to keep trying.",
    "Tommie feels slightly better after talking to his friend.",
]

# Let's send Tommie on their way. We'll check in on their summary every few observations to watch it evolve
for i, observation in enumerate(observations):
    _, reaction = tommie.generate_reaction(observation)
    print(colored(observation, "green"), reaction)
    if ((i + 1) % 20) == 0:
        print("*" * 40)
        print(
            colored(
                f"After {i + 1} observations, Tommie's summary is:\n{tommie.get_summary(force_refresh=True)}", "blue"
            )
        )
        print("*" * 40)

interview_agent(tommie, "Tell me about how your day has been going")

interview_agent(tommie, "How do you feel about coffee?")

interview_agent(tommie, "Tell me about your childhood dog!")

eves_memory = GenerativeAgentMemory(
    llm=LLM, memory_retriever=create_new_memory_retriever(), verbose=False, reflection_threshold=5
)

eve = GenerativeAgent(
    name="Eve",
    age=34,
    traits="curious, helpful",  # You can add more persistent traits here
    status="N/A",  # When connected to a virtual world, we can have the characters update their status
    llm=LLM,
    daily_summaries=[
        (
            "Eve started her new job as a career counselor last week and received her first assignment, a client "
            "named Tommie."
        )
    ],
    memory=eves_memory,
)

yesterday = (datetime.now() - timedelta(days=1)).strftime("%A %B %d")
eve_observations = [
    "Eve overhears her colleague say something about a new client being hard to work with",
    "Eve wakes up and hear's the alarm",
    "Eve eats a boal of porridge",
    "Eve helps a coworker on a task",
    "Eve plays tennis with her friend Xu before going to work",
    "Eve overhears her colleague say something about Tommie being hard to work with",
]
for observation in eve_observations:
    eve.memory.add_memory(observation)

print(eve.get_summary())

interview_agent(eve, "How are you feeling about today?")

interview_agent(eve, "What do you know about Tommie?")

interview_agent(eve, "Tommie is looking to find a job. What are are some things you'd like to ask him?")

interview_agent(
    eve,
    "You'll have to ask him. He may be a bit anxious, so I'd appreciate it if you keep the conversation going and "
    "ask as many questions as possible.",
)


def run_conversation(agents: List[GenerativeAgent], initial_observation: str) -> None:
    """Runs a conversation between agents."""
    _, observation = agents[1].generate_reaction(initial_observation)
    print(observation)
    turns = 0
    while True:
        break_dialogue = False
        for agent in agents:
            stay_in_dialogue, observation = agent.generate_dialogue_response(observation)
            print(observation)
            # observation = f"{agent.name} said {reaction}"
            if not stay_in_dialogue:
                break_dialogue = True
        if break_dialogue:
            break
        turns += 1


agents = [tommie, eve]
run_conversation(
    agents,
    "Tommie said: Hi, Eve. Thanks for agreeing to meet with me today. I have a bunch of questions and am not sure "
    "where to start. Maybe you could first share about your experience?",
)

# We can see a current "Summary" of a character based on their own perception of self
# has changed
print(tommie.get_summary(force_refresh=True))

print(eve.get_summary(force_refresh=True))

interview_agent(tommie, "How was your conversation with Eve?")

interview_agent(eve, "How was your conversation with Tommie?")

interview_agent(eve, "What do you wish you would have said to Tommie?")
