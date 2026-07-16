FINAL_EXAM_MCQ = [
    {"id": "q1", "question": "Which technique converts an ambiguous follow-up query into a standalone query?",
     "options": {"A": "Query Rewriting", "B": "Named Entity Recognition", "C": "Tokenization", "D": "Stemming"},
     "correct": "A", "points": 1},
    {"id": "q2", "question": "Which retrieval method matches queries and documents by exact keyword overlap?",
     "options": {"A": "Dense Retrieval", "B": "BM25", "C": "BERT embeddings", "D": "ConvDR"},
     "correct": "B", "points": 1},
    {"id": "q3", "question": "What does NDCG primarily measure in a retrieval system?",
     "options": {"A": "Ranking quality with graded relevance", "B": "Query latency", "C": "Model size", "D": "Training speed"},
     "correct": "A", "points": 1},
    {"id": "q4", "question": "In RAG (Retrieval-Augmented Generation), what is retrieved before generation?",
     "options": {"A": "Model weights", "B": "Relevant documents/passages", "C": "User credentials", "D": "Training labels"},
     "correct": "B", "points": 1},
    {"id": "q5", "question": "Which component decides whether to ask a clarifying question or answer directly?",
     "options": {"A": "Dialogue Policy", "B": "Tokenizer", "C": "Retriever", "D": "Knowledge Graph"},
     "correct": "A", "points": 1},
]

FINAL_EXAM_WRITTEN = [
    {"id": "w1", "question": "Explain how Retrieval-Augmented Generation (RAG) improves factual accuracy compared to a standalone LLM.",
     "rubric": "Explains that RAG retrieves external documents before generation (3 points). Explains this grounds the response in real evidence rather than the model's memory (3 points). Mentions this reduces hallucination (3 points).",
     "max_points": 9},
    {"id": "w2", "question": "Describe the difference between mixed-initiative dialogue and passive question-answering systems.",
     "rubric": "Defines mixed-initiative dialogue as the system proactively guiding the conversation, not just responding (3 points). Contrasts with passive QA which only reacts to explicit queries (3 points). Gives a concrete example (3 points).",
     "max_points": 9},
    {"id": "w3", "question": "Explain the role of dense retrieval embeddings in overcoming vocabulary mismatch.",
     "rubric": "Explains vocabulary mismatch problem in lexical retrieval (3 points). Explains dense retrieval encodes semantic meaning into vectors (3 points). Explains why semantically similar text ends up close in vector space regardless of exact words (3 points).",
     "max_points": 9},
    {"id": "w4", "question": "Discuss why conversational search evaluation requires different metrics than single-turn search evaluation.",
     "rubric": "Explains single-turn metrics assume independent queries (3 points). Explains conversational search must account for context carried across turns (3 points). Mentions a relevant metric or evaluation consideration (e.g. session-level success, coreference resolution accuracy) (3 points).",
     "max_points": 9},
    {"id": "w5", "question": "Explain how a Dialogue Manager uses belief state tracking to handle a multi-turn conversation.",
     "rubric": "Explains belief state as a running representation of the conversation (3 points). Explains it's updated after each turn (3 points). Explains how it's used to resolve context in follow-up queries (3 points).",
     "max_points": 9},
]

FINAL_EXAM_STUDENTS = [
    {
        "student_id": "220001",
        "name": "Layla Ahmad",  # Excellent tier
        "mcq_answers": {"q1": "A", "q2": "B", "q3": "A", "q4": "B", "q5": "A"},  # all correct
        "written_answers": {
            "w1": "RAG improves factual accuracy by retrieving relevant external documents before the generation step, rather than relying solely on the model's internal parametric memory. This grounds the response in actual retrieved evidence, so the model can cite real, up-to-date information instead of guessing. Because the output is anchored to retrieved text, hallucination is significantly reduced compared to a standalone LLM generating purely from memory.",
            "w2": "Mixed-initiative dialogue means the system actively participates in shaping the conversation, it can ask clarifying questions, suggest follow-ups, or redirect the user, not just answer whatever is asked. Passive QA systems only react: they take a query and return an answer with no proactive behavior. For example, if a user asks a vague question like 'tell me more', a mixed-initiative system might ask 'more about the pricing or the features?' while a passive QA system would just guess or fail.",
            "w3": "Vocabulary mismatch happens when a user's words don't lexically match the document's wording, even though they mean the same thing, e.g. 'how do planes fly' vs 'aerodynamic lift'. Dense retrieval solves this by encoding both queries and documents into continuous vector embeddings that capture semantic meaning rather than exact tokens. Since the embeddings represent meaning, semantically similar text ends up close together in vector space even when the surface words are completely different, which lexical methods like BM25 cannot achieve.",
            "w4": "Single-turn metrics like standard MRR or NDCG assume each query is fully independent and self-contained. Conversational search breaks this assumption because later turns depend on earlier context, like resolved pronouns or shifted topics. Evaluation therefore needs to account for whether the system correctly carries context across turns, for example by measuring session-level task success or how accurately coreference is resolved across the conversation, not just per-query relevance.",
            "w5": "The Dialogue Manager's belief state is a running internal representation of what has been discussed so far in the conversation, including entities, topics, and user intent. After every user turn, this belief state gets updated to reflect new information. When a follow-up query comes in that depends on earlier context, like a pronoun or an incomplete question, the Dialogue Manager consults the belief state to resolve what the user actually means before passing a clean query downstream."
        }
    },
    {
        "student_id": "220002",
        "name": "Omar Nasser",  # Good tier
        "mcq_answers": {"q1": "A", "q2": "B", "q3": "A", "q4": "B", "q5": "C"},  # 4/5 correct
        "written_answers": {
            "w1": "RAG retrieves documents from an external source and uses them to help generate the answer. This is better than a normal LLM because the LLM alone might not know recent facts, but with retrieval it can look things up. This reduces mistakes in the answer.",
            "w2": "Mixed-initiative means the system can also ask questions back to the user, not just answer. Passive QA only answers what it's given. An example would be a chatbot asking 'do you mean X or Y' instead of guessing.",
            "w3": "Vocabulary mismatch is when the words in the query don't match the words in the document. Dense retrieval uses embeddings to represent the meaning of text so it can match things that mean the same even if the words are different.",
            "w4": "Conversational search needs different metrics because the queries depend on each other across turns, unlike single-turn search where each query stands alone. You need to also check if context is handled correctly.",
            "w5": "The Dialogue Manager keeps track of the conversation using a belief state. It updates this after each turn and uses it to understand what the user means in follow-up questions."
        }
    },
    {
        "student_id": "220003",
        "name": "Farah Odeh",  # Average tier
        "mcq_answers": {"q1": "A", "q2": "C", "q3": "A", "q4": "B", "q5": "A"},  # 4/5 correct
        "written_answers": {
            "w1": "RAG uses retrieval to help the model answer better. It gets information from outside sources so the answers are more accurate.",
            "w2": "Mixed-initiative dialogue is when the system can lead the conversation too, not just wait for questions. QA systems just answer questions.",
            "w3": "Dense retrieval helps with vocabulary mismatch because it looks at meaning, not just words. This is different from normal keyword search.",
            "w4": "Conversational search is different because there are multiple turns and the system needs to remember what happened before.",
            "w5": "The Dialogue Manager tracks the conversation state so it knows what's going on across turns."
        }
    },
    {
        "student_id": "220004",
        "name": "Khaled Barghouti",  # Weak tier
        "mcq_answers": {"q1": "C", "q2": "B", "q3": "D", "q4": "B", "q5": "A"},  # 2/5 correct
        "written_answers": {
            "w1": "RAG retrieves information and generates answers. It is used in modern AI systems.",
            "w2": "Mixed-initiative is a type of dialogue system. It is different from normal QA.",
            "w3": "Dense retrieval uses embeddings. Embeddings are vectors that represent words.",
            "w4": "Conversational search has more than one turn so it is harder to evaluate.",
            "w5": "The Dialogue Manager manages the dialogue between the user and the system."
        }
    },
    {
        "student_id": "220005",
        "name": "Yousef Kanaan",  # Poor/incomplete tier
        "mcq_answers": {"q1": "B", "q2": "A", "q3": "C", "q4": "A", "q5": "D"},  # 0/5 correct
        "written_answers": {
            "w1": "RAG is a method used in AI.",
            "w2": "It is about dialogue systems and how they work.",
            "w3": "Dense retrieval is a retrieval method.",
            "w4": "Not sure about this one.",
            "w5": "The Dialogue Manager is a part of the system."
        }
    },
]


ASSIGNMENT_1 = {
    "type": "Assignment 1",
    "questions": [
        {"id": "a1q1", "question": "Explain the difference between BM25 and Dense Retrieval.",
         "rubric": "Explains BM25 as lexical/keyword-based matching (2 points). Explains Dense Retrieval as semantic vector-based matching (2 points). States a key trade-off or use case difference (1 point).",
         "max_points": 5},
        {"id": "a1q2", "question": "What is Dialogue State Tracking and why is it important?",
         "rubric": "Defines Dialogue State Tracking as maintaining the belief state across turns (2 points). Explains why it's necessary for resolving context-dependent queries (2 points). Gives an example (1 point).",
         "max_points": 5},
    ]
}

ASSIGNMENT_2 = {
    "type": "Assignment 2",
    "questions": [
        {"id": "a2q1", "question": "Explain how Query Rewriting resolves ellipsis in conversational queries.",
         "rubric": "Defines ellipsis in the context of conversation (2 points). Explains how Query Rewriting fills in the missing information using dialogue history (2 points). Gives an example (1 point).",
         "max_points": 5},
        {"id": "a2q2", "question": "Explain NDCG as an evaluation metric for retrieval systems.",
         "rubric": "Explains NDCG accounts for ranking position (2 points). Explains it uses graded relevance, not just binary relevant/not-relevant (2 points). Mentions why this is useful compared to simpler metrics (1 point).",
         "max_points": 5},
    ]
}

ASSIGNMENT_STUDENTS = [
    {
        "student_id": "220001", "name": "Layla Ahmad",
        "answers": {
            "a1q1": "BM25 is a lexical retrieval method that ranks documents based on exact keyword overlap and term frequency statistics. Dense Retrieval instead encodes queries and documents into continuous vector embeddings and matches based on semantic similarity. The key trade-off is that BM25 is fast and interpretable but fails on vocabulary mismatch, while dense retrieval handles meaning-based matching but requires more computation and training data.",
            "a1q2": "Dialogue State Tracking is the process of maintaining a running belief state that captures what's been discussed so far in a conversation, including entities and user intent. It's important because without it, the system can't resolve context-dependent follow-up queries like 'what about the second one?'. For example, if a user asks about 'Data Science' then asks 'is it offered here?', the state tracker is what lets the system know 'it' refers to Data Science.",
            "a2q1": "Ellipsis is when a speaker omits words that are understood from context, like asking 'what skills are required?' after already discussing a topic. Query Rewriting resolves this by using the conversation history to fill in the missing subject, turning it into a standalone query like 'what skills are required for Data Science?'. This lets the retriever work with a complete, unambiguous query.",
            "a2q2": "NDCG (Normalized Discounted Cumulative Gain) evaluates ranking quality by rewarding relevant documents appearing higher in the results and using graded relevance levels rather than simple binary relevant/not-relevant labels. This is more useful than simpler metrics because it captures both how relevant a result is and where it appears in the ranking, which better reflects real user satisfaction."
        }
    },
    {
        "student_id": "220003", "name": "Farah Odeh",
        "answers": {
            "a1q1": "BM25 looks for matching keywords. Dense retrieval uses vectors to find meaning instead of just words.",
            "a1q2": "Dialogue State Tracking keeps track of the conversation. It helps the system understand context in later questions.",
            "a2q1": "Ellipsis is when something is left out of a sentence. Query rewriting adds the missing part back using history.",
            "a2q2": "NDCG measures how good the ranking is. It considers relevance and position in the results."
        }
    },
    {
        "student_id": "220005", "name": "Yousef Kanaan",
        "answers": {
            "a1q1": "BM25 and dense retrieval are both retrieval methods.",
            "a1q2": "It tracks the dialogue state.",
            "a2q1": "Query rewriting fixes queries.",
            "a2q2": "NDCG is a metric for retrieval."
        }
    },
]


ATTENDANCE = [
    {"student_id": "220001", "name": "Layla Ahmad", "score": 10},
    {"student_id": "220002", "name": "Omar Nasser", "score": 9},
    {"student_id": "220003", "name": "Farah Odeh", "score": 7},
    {"student_id": "220004", "name": "Khaled Barghouti", "score": 6},
    {"student_id": "220005", "name": "Yousef Kanaan", "score": 4},
]



MIDTERM_2_MCQ = [
    {"id": "m1", "question": "Which model introduced bidirectional contextual word representations?",
     "options": {"A": "RNN", "B": "BERT", "C": "BM25", "D": "TF-IDF"}, "correct": "B", "points": 2},
    {"id": "m2", "question": "What is the primary weakness of lexical retrieval like BM25?",
     "options": {"A": "Too slow", "B": "Vocabulary mismatch", "C": "Requires GPUs", "D": "No ranking"}, "correct": "B", "points": 2},
    {"id": "m3", "question": "Which dataset hides the source document from the user during conversation?",
     "options": {"A": "CoQA", "B": "SQuAD", "C": "QuAC", "D": "GLUE"}, "correct": "C", "points": 2},
    {"id": "m4", "question": "What does the Dialogue Policy decide?",
     "options": {"A": "Word embeddings", "B": "Next system action", "C": "Tokenization rules", "D": "Index structure"}, "correct": "B", "points": 2},
    {"id": "m5", "question": "Which technique transforms an ambiguous query into a standalone one?",
     "options": {"A": "Query Rewriting", "B": "Stemming", "C": "Lemmatization", "D": "POS Tagging"}, "correct": "A", "points": 2},
    {"id": "m6", "question": "What does ConvDR primarily encode?",
     "options": {"A": "Only the current query", "B": "Conversation history plus current query", "C": "Document titles only", "D": "User metadata"}, "correct": "B", "points": 2},
    {"id": "m7", "question": "Which component stores past turns to resolve context-dependent questions?",
     "options": {"A": "Retriever", "B": "Conversation Memory", "C": "Tokenizer", "D": "Knowledge Graph"}, "correct": "B", "points": 2},
    {"id": "m8", "question": "Adversarial examples are used in QA evaluation mainly to test:",
     "options": {"A": "Speed", "B": "Robustness to misleading input", "C": "Memory usage", "D": "Compression"}, "correct": "B", "points": 2},
    {"id": "m9", "question": "What is the main advantage of RAG over a standalone LLM?",
     "options": {"A": "Smaller model size", "B": "Grounded, less hallucinated answers", "C": "Faster training", "D": "No need for a retriever"}, "correct": "B", "points": 2},
    {"id": "m10", "question": "Which best describes a modern CIR system?",
     "options": {"A": "Keyword matching only", "B": "Combines retrieval, dialogue management, and generation", "C": "Static FAQ lookup", "D": "Rule-based only"}, "correct": "B", "points": 2},
]

MIDTERM_2_STUDENTS = [
    {"student_id": "220001", "name": "Layla Ahmad", "answers": {"m1":"B","m2":"B","m3":"C","m4":"B","m5":"A","m6":"B","m7":"B","m8":"B","m9":"B","m10":"B"}},  # 10/10
    {"student_id": "220002", "name": "Omar Nasser", "answers": {"m1":"B","m2":"B","m3":"C","m4":"B","m5":"A","m6":"A","m7":"B","m8":"B","m9":"B","m10":"A"}},  # 8/10
    {"student_id": "220003", "name": "Farah Odeh", "answers": {"m1":"B","m2":"A","m3":"C","m4":"B","m5":"A","m6":"B","m7":"A","m8":"B","m9":"C","m10":"B"}},  # 6/10
    {"student_id": "220004", "name": "Khaled Barghouti", "answers": {"m1":"A","m2":"B","m3":"A","m4":"C","m5":"A","m6":"B","m7":"B","m8":"A","m9":"B","m10":"C"}},  # 5/10
    {"student_id": "220005", "name": "Yousef Kanaan", "answers": {"m1":"A","m2":"C","m3":"A","m4":"A","m5":"C","m6":"A","m7":"C","m8":"A","m9":"A","m10":"B"}},  # 1/10
]
