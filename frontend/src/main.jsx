import React, { useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const extensions = ['pdf', 'ppt', 'pptx', 'doc', 'docx'];
function App() {
  const [file, setFile] = useState(null), [count, setCount] = useState(10), [difficulty, setDifficulty] = useState('medium');
  const [quiz, setQuiz] = useState(null), [answers, setAnswers] = useState({}), [submitted, setSubmitted] = useState(false);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [drag, setDrag] = useState(false);
  const input = useRef(null), controller = useRef(null);
  function selectFile(value) {
    setError('');
    if (!value) return;
    if (!extensions.includes(value.name.split('.').pop().toLowerCase())) { setError('Choose a PDF, PowerPoint, or Word document.'); return; }
    if (value.size > 10 * 1024 * 1024) { setError('Your file must be 10 MB or smaller.'); return; }
    setFile(value);
  }
  async function generate() {
    setBusy(true); setError('');
    const data = new FormData(); data.append('file', file); data.append('question_count', count); data.append('difficulty', difficulty);
    controller.current = new AbortController();
    try {
      const response = await fetch('/api/quiz', { method: 'POST', body: data, signal: controller.current.signal });
      const result = await response.json().catch(() => ({ detail: 'The server could not process the upload. Please try again.' }));
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Check your document and quiz settings.');
      setQuiz(result); setAnswers({}); setSubmitted(false); window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) { if (e.name !== 'AbortError') setError(e.message || 'Could not reach the server. Please try again.'); }
    finally { setBusy(false); }
  }
  const answered = Object.keys(answers).length;
  const score = quiz?.questions.filter((q, i) => answers[i] === q.correct_answer).length || 0;
  function reset() { setQuiz(null); setSubmitted(false); setAnswers({}); setError(''); }
  return <><header><a className="brand" href="/" onClick={e => { e.preventDefault(); if (!busy) reset(); }}><span className="brand-icon">N</span> NoteWise</a><span className="header-note">A little practice. A lot more confidence.</span><span className="gemini"><span/> Powered by Gemini</span></header>
  <main>{!quiz ? <><div className="intro"><span className="eyebrow">YOUR NEXT STUDY SESSION, SIMPLIFIED</span><h1>Your notes.<br/><span>Your next great quiz.</span></h1><p>Turn what you’re learning into questions that make it stick.<br className="desktop"/> Upload your notes, take a quiz, and see what you know.</p></div>
  <div className="workspace"><section className="card upload-card"><div className="section-heading"><span className="step">01</span><div><h2>Bring your study notes</h2><p>One document is all you need.</p></div></div>
  <input ref={input} type="file" accept=".pdf,.ppt,.pptx,.doc,.docx" aria-label="Upload study notes" disabled={busy} onChange={e => selectFile(e.target.files[0])}/>
  <button className={`dropzone ${drag ? 'drag' : ''} ${file ? 'selected' : ''}`} disabled={busy} onClick={() => input.current.click()} onDragOver={e => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={e => { e.preventDefault(); setDrag(false); if (!busy) selectFile(e.dataTransfer.files[0]); }}><span className="upload-icon">{file ? '✓' : '↑'}</span><strong>{file ? file.name : 'Drop your notes here'}</strong><span>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB · Click to replace` : <>or <u>browse files</u> to get started</>}</span><small>PDF, PowerPoint, or Word · up to 10 MB</small></button>
  <div className="ocr-note"><span>✦</span><div><strong>Scanned PDF? We’ve got you.</strong><p>English text is read automatically from scanned pages.</p></div></div>
  <div className="privacy">Your document is used for this quiz and removed after processing. Extracted notes are sent to Gemini.</div></section>
  <section className="card settings-card"><div className="section-heading"><span className="step">02</span><div><h2>Make it your own</h2><p>A quick check or a deeper challenge.</p></div></div><fieldset disabled={busy}><legend>Number of questions</legend><div className="segments">{[5,10,15].map(n => <button key={n} aria-pressed={count===n} className={count===n?'active':''} onClick={()=>setCount(n)}>{n}<small>{n===5?'Quick':n===10?'Balanced':'Thorough'}</small></button>)}</div></fieldset><fieldset disabled={busy}><legend>Difficulty</legend><div className="difficulty">{['easy','medium','hard'].map(d=><button key={d} aria-pressed={difficulty===d} className={difficulty===d?'active':''} onClick={()=>setDifficulty(d)}><span>{d==='easy'?'◔':d==='medium'?'◑':'●'}</span>{d[0].toUpperCase()+d.slice(1)}</button>)}</div></fieldset><button className="primary generate" disabled={!file || busy} onClick={generate}>{busy ? <><span className="spinner"/> Creating your quiz…</> : <>Generate my quiz <span>↗</span></>}</button><p className="button-note" aria-live="polite">{busy ? 'Reading notes and writing questions. Scans may take a few minutes.' : 'Questions, answers, and explanations. All from your notes.'}</p>{busy && <button className="text-button" onClick={()=>controller.current?.abort()}>Cancel</button>}</section></div>
  {error && <div className="error" role="alert">{error}</div>}
  <div className="how"><span>FROM NOTES TO KNOWLEDGE</span><div><b>1</b> Upload your notes <i>→</i> <b>2</b> Make it a quiz <i>→</i> <b>3</b> Learn as you go</div></div></> : <div className="quiz-view"><button className="text-button" onClick={reset}>← Create another quiz</button><div className="quiz-heading"><span className="eyebrow">{submitted ? 'YOUR STUDY SESSION, COMPLETE' : 'LET’S PUT YOUR KNOWLEDGE TO WORK'}</span><h1>{quiz.title}</h1><p>{quiz.source.filename} · {quiz.questions.length} questions · {quiz.difficulty}{quiz.source.ocr_pages > 0 && ` · ${quiz.source.ocr_pages} pages read with OCR`}</p></div>
  {submitted ? <div className="score card" role="status"><div className="score-number">{score}<span> / {quiz.questions.length}</span></div><div><h2>{score===quiz.questions.length?'You’ve got this!':score>=quiz.questions.length*.6?'Good progress. Keep it going.':'Every question is a chance to learn.'}</h2><p>{Math.round(score/quiz.questions.length*100)}% correct · Review the explanations below.</p></div><button className="secondary" onClick={()=>{setAnswers({});setSubmitted(false);window.scrollTo({top:0,behavior:'smooth'});}}>Try again</button></div> : <div className="progress"><span>{answered} of {quiz.questions.length} answered</span><progress max={quiz.questions.length} value={answered}/></div>}
  {quiz.questions.map((q,i)=><section className="question card" key={i}><span className="question-number">QUESTION {String(i+1).padStart(2,'0')}</span><h2 id={`q${i}`}>{q.question}</h2><div className="options" role="radiogroup" aria-labelledby={`q${i}`}>{q.options.map((option,j)=><label key={j} className={`option ${answers[i]===j?'chosen':''} ${submitted && j===q.correct_answer?'correct':''} ${submitted && answers[i]===j && j!==q.correct_answer?'incorrect':''}`}><input type="radio" name={`question-${i}`} checked={answers[i]===j} disabled={submitted} onChange={()=>setAnswers({...answers,[i]:j})}/><span className="option-letter">{'ABCD'[j]}</span><span>{option}</span>{submitted && j===q.correct_answer && <strong className="answer-mark">✓</strong>}</label>)}</div>{submitted && <div className="explanation"><strong>{answers[i]===q.correct_answer?'Correct — nice work.':'Here’s what to remember.'}</strong><p>{q.explanation}</p></div>}</section>)}
  {!submitted && <div className="submit-bar"><p>Answer all questions to see your score.</p><button className="primary" disabled={answered!==quiz.questions.length} onClick={()=>{setSubmitted(true);window.scrollTo({top:0,behavior:'smooth'});}}>Check my answers →</button></div>}</div>}</main><footer><span>NoteWise</span><span>Small steps. Stronger understanding.</span></footer></>;
}
createRoot(document.getElementById('root')).render(<App/>);
