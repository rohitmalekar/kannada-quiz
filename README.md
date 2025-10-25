# Kannada Practice Quiz 🗣️

An interactive Streamlit application for practicing Kannada language skills at the introductory level. This quiz helps reinforce verbs, simple sentence formation, -ing form, first party tenses, and daily life vocabulary.

## Features

- **Multiple Question Types**: 
  - Multiple choice questions
  - Fill in the blank (text and choice-based)
  - Build sentences from parts
  - Match pairs
  - True/False questions
  - Scenario-based questions

- **Interactive Learning**: 
  - Randomized question selection
  - Immediate feedback with explanations
  - Fun reactions in Kannada and English
  - Score tracking

- **Flexible Practice**: 
  - Choose how many questions to practice
  - Perfect for reinforcing learning after attending level 1 classes

## Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/kannada-quiz.git
cd kannada-quiz
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run quiz.py
```

4. Open your browser and navigate to `http://localhost:8501`

## Usage

1. **Start a Quiz**: Choose how many questions you want to practice (1 to all available questions)
2. **Answer Questions**: Use the interactive interface to answer different types of questions
3. **Get Feedback**: Receive immediate feedback with explanations and fun reactions
4. **Track Progress**: See your score at the end and play again for more practice

## File Structure

- `quiz.py` - Main Streamlit application
- `quiz.json` - Quiz questions and data
- `reactions.json` - Positive and negative reactions in Kannada and English
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Contributing

Feel free to contribute by:
- Adding more questions to `quiz.json`
- Improving the user interface
- Adding new question types
- Translating reactions to other languages

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Designed to complement learning from [kannadagottilla.com](https://kannadagottilla.com)
- Special thanks to the Kannada learning community
