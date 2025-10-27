import streamlit as st
import json
import random
import string

# -----------------
# Helper functions
# -----------------

def normalize_text(s: str) -> str:
    """
    Basic normalization so we can accept 'beku.' and 'beku'
    and ignore capitalization / trailing punctuation.
    """
    if not isinstance(s, str):
        return ""
    s = s.strip().lower()
    # remove trailing punctuation like . ! ?
    return s.strip().strip(string.punctuation)

def load_quiz(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def load_reactions(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["reactions"]

def get_random_reaction(reactions: dict, is_correct: bool):
    """Get a random reaction based on whether answer is correct."""
    reaction_type = "positive" if is_correct else "negative"
    return random.choice(reactions[reaction_type])

def get_sampled_questions(all_qs, num, exclude_indices=None):
    """
    Randomly sample questions without replacement.
    If exclude_indices is provided, will only sample from questions not in that list.
    """
    if exclude_indices is None:
        exclude_indices = []
    
    # Get available questions (not yet asked)
    available_qs = [q for i, q in enumerate(all_qs) if i not in exclude_indices]
    
    # If not enough available questions, return all available
    if len(available_qs) < num:
        return available_qs
    
    # Sample from available questions
    return random.sample(available_qs, k=num)

def init_session_state():
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None
    if "selected_questions" not in st.session_state:
        st.session_state.selected_questions = []
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "user_answer" not in st.session_state:
        st.session_state.user_answer = None
    if "show_results" not in st.session_state:
        st.session_state.show_results = False
    if "num_to_ask" not in st.session_state:
        st.session_state.num_to_ask = None
    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
    if "asked_questions" not in st.session_state:
        st.session_state.asked_questions = []


def reset_quiz(sample_count=None):
    """Reset quiz round but keep loaded quiz data."""
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.user_answer = None
    st.session_state.show_results = False
    st.session_state.quiz_started = True

    if sample_count is not None and st.session_state.quiz_data:
        st.session_state.num_to_ask = sample_count
        
        # Get questions and their indices for tracking
        all_questions = st.session_state.quiz_data["questions"]
        
        # Check if we need to reset asked history (all questions exhausted)
        total_questions = len(all_questions)
        available_questions = total_questions - len(st.session_state.asked_questions)
        
        if available_questions < sample_count:
            # Not enough unasked questions - reset the asked history
            st.session_state.asked_questions = []
        
        # Sample questions that haven't been asked yet
        sampled = get_sampled_questions(all_questions, sample_count, 
                                       exclude_indices=st.session_state.asked_questions)
        st.session_state.selected_questions = sampled
        
        # Track these questions as asked by finding their indices
        for q in sampled:
            # Find the index of this question in the full question pool
            try:
                idx = all_questions.index(q)
                if idx not in st.session_state.asked_questions:
                    st.session_state.asked_questions.append(idx)
            except ValueError:
                # Question not found in all_questions (shouldn't happen)
                pass
    else:
        st.session_state.selected_questions = []


def grade_answer(question, user_answer):
    """
    Returns (is_correct: bool, explanation: str, correct_value: str)
    Supports:
      - multiple_choice
      - fill_in_blank_text
      - fill_in_blank_choice
      - build_from_parts
      - match_pairs
      - true_false
      - scenario
    """
    qtype = question["type"]

    # multiple_choice
    if qtype in ["multiple_choice", "scenario"]:
        # We assume exactly one correct index for now
        correct_indexes = question["correct"]
        correct_idx = correct_indexes[0]
        correct_value = question["options"][correct_idx]

        is_correct = (user_answer == correct_idx)

        return is_correct, question.get("explanation", ""), correct_value

    # fill_in_blank_text
    if qtype == "fill_in_blank_text":
        valid_answers = [normalize_text(a) for a in question["answer_variants"]]
        is_correct = normalize_text(user_answer) in valid_answers
        correct_value = question["answer_variants"][0] if question["answer_variants"] else ""
        return is_correct, question.get("explanation", ""), correct_value
    
    # fill_in_blank_choice
    if qtype == "fill_in_blank_choice":
        # user_answer is the index of the selected choice
        correct_indexes = question["correct"]
        is_correct = user_answer in correct_indexes
        correct_value = question["choices"][correct_indexes[0]] if correct_indexes else ""
        return is_correct, question.get("explanation", ""), correct_value
    
    # build_from_parts
    if qtype == "build_from_parts":
        # user_answer is the list of selected parts in order
        expected = question["correct_sequence"]
        # Check if user_answer is valid list
        if not isinstance(user_answer, list):
            return False, question.get("explanation", ""), " ".join(expected)
        is_correct = user_answer == expected
        correct_value = " ".join(expected)
        return is_correct, question.get("explanation", ""), correct_value
    
    # match_pairs
    if qtype == "match_pairs":
        # user_answer is the mapping dict {left_item: right_item}
        expected_map = question["correct_map"]
        # Check if user_answer is valid dict
        if not isinstance(user_answer, dict):
            correct_strs = [f"{k} ↔ {v}" for k, v in expected_map.items()]
            return False, question.get("explanation", ""), "\n".join(correct_strs)
        
        # Remove "(Select)" entries before comparing
        cleaned_answer = {k: v for k, v in user_answer.items() if v != "(Select)"}
        if len(cleaned_answer) != len(expected_map):
            # Not all items matched
            correct_strs = [f"{k} ↔ {v}" for k, v in expected_map.items()]
            return False, question.get("explanation", ""), "\n".join(correct_strs)
        
        is_correct = cleaned_answer == expected_map
        # Build a string representation of correct matches
        correct_strs = [f"{k} ↔ {v}" for k, v in expected_map.items()]
        correct_value = "\n".join(correct_strs)
        return is_correct, question.get("explanation", ""), correct_value
    
    # true_false
    if qtype == "true_false":
        expected = question["correct"]
        is_correct = user_answer == expected
        correct_value = "True" if expected else "False"
        return is_correct, question.get("explanation", ""), correct_value

    # default fallback
    return False, "Unsupported question type in grader.", ""


# -----------------
# Streamlit UI
# -----------------

st.title("Kannada Practice Quiz - Introductory Level 🗣️")
st.write("Reinforce verbs, simple sentence formation, -ing form, first party tenses, daily life vocabulary.")
st.caption("Works best to reinforce learning after attending level 1 classes by https://kannadagottilla.com")

init_session_state()

# Try to load quiz from JSON file
try:
    quiz_file_path = "quiz.json"  # Assuming quiz.json is in the same directory
    st.session_state.quiz_data = load_quiz(quiz_file_path)
    # st.success(f"Loaded quiz: {st.session_state.quiz_data.get('title', 'Untitled Quiz')}")
except FileNotFoundError:
    st.error("Quiz file 'quiz.json' not found. Please ensure the file exists in the same directory as this script.")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"Error parsing quiz JSON file: {e}")
    st.stop()
except Exception as e:
    st.error(f"Error loading quiz file: {e}")
    st.stop()

# Try to load reactions from JSON file
try:
    reactions_file_path = "reactions.json"
    reactions = load_reactions(reactions_file_path)
except FileNotFoundError:
    st.error("Reactions file 'reactions.json' not found. Please ensure the file exists in the same directory as this script.")
    reactions = None
except json.JSONDecodeError as e:
    st.error(f"Error parsing reactions JSON file: {e}")
    reactions = None
except Exception as e:
    st.error(f"Error loading reactions file: {e}")
    reactions = None

# If quiz not loaded yet, stop here
if not st.session_state.quiz_data:
    st.stop()

questions_available = len(st.session_state.quiz_data["questions"])

# Step 2: Let user choose number of questions and start
# Only show setup if quiz hasn't started yet OR if we're in replay mode
if not st.session_state.quiz_started or st.session_state.show_results:
#    st.subheader("Setup")
#    st.write(f"There are {questions_available} questions available.")

    if st.session_state.selected_questions == [] and not st.session_state.show_results:
        # Only show selector if we haven't started a round
        num_to_ask = st.number_input(
            "How many questions do you want this round?",
            min_value=1,
            max_value=questions_available,
            value=min(5, questions_available),
            step=1
        )

        if st.button("Start Quiz"):
            reset_quiz(sample_count=num_to_ask)
            st.rerun()

# If still no sampled questions (user hasn't clicked start), stop
if st.session_state.selected_questions == [] and not st.session_state.show_results:
    st.stop()

# If quiz finished already, we'll render results below
if st.session_state.show_results:
    st.subheader("Round complete ✅")
    total = len(st.session_state.selected_questions)
    score = st.session_state.score
    st.write(f"Your score: **{score} / {total}**")

    if score == total:
        st.success("Perfect score. Super! 🎉")
    elif score / total >= 0.6:
        st.info("Nice work. You're getting comfortable with patterns.")
    else:
        st.warning("Keep going. Kannada sticks with repetition, not talent.")

    if st.button("Play again"):
        # Reset quiz_started to show setup again for replay
        st.session_state.quiz_started = False
        st.session_state.selected_questions = []
        st.session_state.show_results = False
        st.rerun()

    st.stop()

# -----------------
# Active question view
# -----------------

idx = st.session_state.current_index
question = st.session_state.selected_questions[idx]
qtype = question["type"]

st.markdown(f"### **Question {idx+1} of {len(st.session_state.selected_questions)}**")

# Render question based on type
user_answer_input = None

# multiple_choice / scenario
if qtype in ["multiple_choice", "scenario"]:
    if qtype == "multiple_choice":
        st.write("Translate / Choose the best answer:")
        st.write(f"**{question['prompt']}**")
        if question.get("prompt_lang") == "kn":
            st.caption("Above is Kannada. Pick the English meaning.")
    else:
        st.write("Situation:")
        st.write(f"**{question['situation']}**")

    # We'll index the options
    options = question["options"]
    # Create radio with enumerate labels
    option_labels = [f"{i+1}. {opt}" for i, opt in enumerate(options)]
    selected_label = st.radio(
        "Pick one:",
        option_labels,
        index=None,
        key=f"q_radio_{idx}"
    )
    if selected_label is not None:
        # Convert back to index
        user_answer_input = option_labels.index(selected_label)

# fill_in_blank_text
elif qtype == "fill_in_blank_text":
    st.write("Complete the sentence in Kannada:")
    st.write(f"**{question['sentence_template']}**")
    if "english_hint" in question and question["english_hint"]:
        st.caption(f"Hint: {question['english_hint']}")
    user_answer_input = st.text_input(
        "Your answer:",
        key=f"q_text_{idx}"
    )

# fill_in_blank_choice
elif qtype == "fill_in_blank_choice":
    st.write("Fill in the blank by choosing from the options:")
    st.write(f"**{question['sentence_template'].replace('___', '_____')}**")
    if "english_hint" in question and question["english_hint"]:
        st.caption(f"Hint: {question['english_hint']}")
    
    choices = question["choices"]
    choice_labels = [f"{i+1}. {choice}" for i, choice in enumerate(choices)]
    selected_choice_label = st.radio(
        "Choose one:",
        choice_labels,
        index=None,
        key=f"q_blank_choice_{idx}"
    )
    if selected_choice_label is not None:
        user_answer_input = choice_labels.index(selected_choice_label)

# build_from_parts
elif qtype == "build_from_parts":
    st.write("Build the sentence from the parts below:")
    st.write(f"**{question['target_translation']}**")
    
    # Initialize session state for this question's parts
    sequence_key = f"part_sequence_{idx}"
    available_key = f"available_parts_{idx}"
    selectbox_key = f"select_part_{idx}"
    
    # Initialize session state if not exists
    if sequence_key not in st.session_state:
        st.session_state[available_key] = question["parts_pool"].copy()
        st.session_state[sequence_key] = []
    
    # Show the sentence being built
    st.write("**Your sentence:**")
    if st.session_state[sequence_key]:
        st.write(" ".join(st.session_state[sequence_key]))
    else:
        st.write("*No parts added yet*")
    
    # Allow user to select from available parts
    available = st.session_state[available_key]
    if available:
        # Create selectbox
        selected_part = st.selectbox(
            "Add a part:",
            ["(Select)"] + available,
            key=selectbox_key
        )
        
        cols = st.columns(2)
        with cols[0]:
            if st.button("Add part", key=f"add_{idx}"):
                # Get the current value from the selectbox
                current_selection = st.session_state[selectbox_key]
                if current_selection and current_selection != "(Select)":
                    # Add to sequence
                    st.session_state[sequence_key].append(current_selection)
                    # Remove from available
                    st.session_state[available_key].remove(current_selection)
                    st.rerun()
                else:
                    st.warning("Please select a part first!")
        
        with cols[1]:
            if st.button("Reset", key=f"reset_{idx}"):
                st.session_state[available_key] = question["parts_pool"].copy()
                st.session_state[sequence_key] = []
                st.rerun()
    else:
        st.info("All parts used!")
    
    # Set user_answer_input to the sequence when submitting
    user_answer_input = st.session_state[sequence_key].copy()

# match_pairs
elif qtype == "match_pairs":
    st.write("Match each item on the left with its meaning on the right:")
    
    left_items = question["left_items"]
    right_items = question["right_items"]
    
    # Store user's matching
    matching_key = f"matching_{idx}"
    if matching_key not in st.session_state:
        st.session_state[matching_key] = {}
    
    # Create UI for matching
    for i, left_item in enumerate(left_items):
        current_match = st.session_state[matching_key].get(left_item, "(Select)")
        selected = st.selectbox(
            f"**{left_item}** →",
            ["(Select)"] + right_items,
            index=0 if current_match == "(Select)" else right_items.index(current_match) + 1,
            key=f"match_{idx}_{i}"
        )
        st.session_state[matching_key][left_item] = selected
    
    # Set user_answer_input to the matching dict
    user_answer_input = st.session_state[matching_key].copy()

# true_false
elif qtype == "true_false":
    st.write("True or False:")
    st.write(f"**{question['statement']}**")
    
    user_answer_input = st.radio(
        "Your answer:",
        [True, False],
        format_func=lambda x: "True" if x else "False",
        index=None,
        key=f"tf_{idx}"
    )

else:
    st.error(f"Question type '{qtype}' not yet implemented in UI.")
    st.stop()

# Submit / Check button
if st.button("Check answer"):
    # Validate user answer based on question type
    if qtype == "build_from_parts":
        if not user_answer_input or len(user_answer_input) == 0:
            st.warning("Please build a sentence before checking.")
            st.stop()
    elif qtype == "match_pairs":
        if not user_answer_input:
            st.warning("Please complete all matches before checking.")
            st.stop()
        # Check if all matches are selected
        if any(v == "(Select)" for v in user_answer_input.values()):
            st.warning("Please complete all matches before checking.")
            st.stop()
    elif user_answer_input is None or user_answer_input == "":
        st.warning("Please answer before checking.")
        st.stop()

    is_correct, explanation, correct_value = grade_answer(question, user_answer_input)
    st.session_state.answered = True
    st.session_state.user_answer = user_answer_input

    if is_correct:
        st.success("✅ Correct!")
        st.session_state.score += 1
        
        # Show random reaction if available
        if reactions:
            reaction = get_random_reaction(reactions, True)
            st.markdown(f"**{reaction['kn']}**")
            st.caption(f"*{reaction['en']}*")
    else:
        st.error("❌ Not correct.")
        
        # Show random reaction if available
        if reactions:
            reaction = get_random_reaction(reactions, False)
            st.markdown(f"**{reaction['kn']}**")
            st.caption(f"*{reaction['en']}*")
        
        st.write(f"Correct answer: **{correct_value}**")
        if explanation:
            st.caption(explanation)

# Next button
if st.session_state.answered:
    # Show Next / Finish
    at_last_question = (st.session_state.current_index == len(st.session_state.selected_questions) - 1)
    if at_last_question:
        if st.button("See my score"):
            st.session_state.show_results = True
            st.rerun()
    else:
        if st.button("Next question"):
            # Move to next question and reset state
            st.session_state.current_index += 1
            st.session_state.answered = False
            st.session_state.user_answer = None
            # Force rerun to show new question immediately
            st.rerun()
