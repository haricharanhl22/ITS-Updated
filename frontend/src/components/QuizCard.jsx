/**
 * QuizCard — a single MCQ option with selection, correct, and wrong states.
 *
 * Props:
 *   index        {number}  0-based option index
 *   text         {string}  option text
 *   selected     {boolean} is this option currently selected?
 *   onSelect     {fn}      callback when option is clicked
 *   submitted    {boolean} quiz has been submitted
 *   isCorrect    {boolean} this option is the correct answer
 */
export default function QuizCard({ index, text, selected, onSelect, submitted, isCorrect }) {
  const letters = ['A', 'B', 'C', 'D']

  let stateClass = ''
  if (submitted) {
    if (isCorrect)            stateClass = 'quiz-opt-correct'
    else if (selected)        stateClass = 'quiz-opt-wrong'
    else                      stateClass = 'quiz-opt-dim'
  } else if (selected) {
    stateClass = 'quiz-opt-selected'
  }

  return (
    <button
      className={`quiz-option ${stateClass}`}
      onClick={() => !submitted && onSelect(index)}
      disabled={submitted}
      aria-pressed={selected}
      aria-label={`Option ${letters[index]}: ${text}`}
      id={`quiz-opt-${index}`}
    >
      <span className="quiz-opt-letter">{letters[index]}</span>
      <span className="quiz-opt-text">{text}</span>
      {submitted && isCorrect  && <span className="quiz-opt-icon">✓</span>}
      {submitted && selected && !isCorrect && <span className="quiz-opt-icon">✗</span>}
    </button>
  )
}
