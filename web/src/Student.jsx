import React, {useState, useRef, useEffect} from 'react';
import {ArrowRight, Check, Compass, Copy, Download} from 'lucide-react';
import {download} from './components';
import {readinessLabels, scenarios, newPractice, reviewComplete, StudentTakeaway} from './models';

const steps = ['Reflect', 'Practice', 'Check', 'Build', 'Plan'];
const questions = {
  assumption: 'What assumption did the response make?',
  evidence: 'What evidence would you check?',
  keep: 'What would you keep?',
  change: 'What would you change?',
  explain: 'Why is your change better?',
};

export default function Student() {
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState('Data and AI');
  const [reflected, setReflected] = useState(false);
  const [scenario, setScenario] = useState('Community');
  const [minutes, setMinutes] = useState(30);
  const [scores, setScores] = useState(Object.fromEntries(Object.keys(readinessLabels).map(key => [key, 1])));
  const [practices, setPractices] = useState(Object.fromEntries(Object.keys(scenarios).map(key => [key, newPractice(key)])));
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState('');
  const [planConfirmed, setPlanConfirmed] = useState(false);
  const planRequest = useRef(0);
  const current = practices[scenario];
  const example = scenarios[scenario];
  const reviewed = reviewComplete(current.answers);
  const takeaway = new StudentTakeaway({direction, scenario, practice: current, plan, minutes});
  const completion = [reflected && Boolean(direction.trim()), current.reviewed && Boolean(current.prompt.trim()), reviewed, takeaway.ready, Boolean(plan) && planConfirmed];
  const completedCount = completion.filter(Boolean).length;
  const suggestedKey = Object.keys(scores).sort((a, b) => scores[a] - scores[b])[0];

  function updatePractice(patch) {
    setPractices(previous => ({...previous, [scenario]: {...previous[scenario], ...patch}}));
  }
  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(''), 4000);
    return () => clearTimeout(timer);
  }, [copied]);
  function clearPlan() { planRequest.current += 1; setLoading(false); setPlan(null); setPlanConfirmed(false); setError(''); }
  async function copy(text, label) {
    try { await navigator.clipboard.writeText(text); setCopied(label); }
    catch { setCopied('Select the text and use your device’s copy command.'); }
  }
  async function makePlan() {
    const requestId = ++planRequest.current;
    setLoading(true); setError(''); setPlanConfirmed(false);
    try {
      const response = await fetch('/api/student-plan', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({minutes, direction, scores}),
      });
      const result = await response.json();
      if (requestId !== planRequest.current) return;
      if (!response.ok) throw Error(result.error || 'Planning is unavailable. Your notes are still here; try again.');
      setPlan(result.plan);
    } catch (failure) {
      if (requestId !== planRequest.current) return;
      setError(failure.message === 'Failed to fetch' ? 'The planning service is unavailable. Download your work below and try again later.' : failure.message);
    } finally { if (requestId === planRequest.current) setLoading(false); }
  }

  return <>
    <div className="eyebrow">STUDENT EXPERIENCE / AI CAREER LAB</div>
    <div className="page-heading"><div><h1>Make something<br/><em>you can explain.</em></h1><p>One practice activity. One piece of evidence. One manageable next step.</p></div><div className="time">25–40 minutes<br/><small>At your own pace · breaks welcome</small></div></div>
    <div className="student-intro"><div><b>See one → try one → check one</b><p>Choose an example, question the response, and turn your thinking into a takeaway.</p></div><div><b>{completedCount} of 5 steps complete</b><progress aria-label="Completed workshop steps" value={completedCount} max={5}/><small>Move freely. Your place is saved while this page stays open.</small></div></div>
    <nav className="steps" aria-label="Learning steps">{steps.map((label, index) => <button key={label} className={`${step === index ? 'selected' : ''} ${completion[index] ? 'step-complete' : ''}`} onClick={() => setStep(index)} aria-current={step === index ? 'step' : undefined}><span>{completion[index] ? <Check size={13}/> : index + 1}</span>{label}<small>{completion[index] ? 'Complete' : 'To do'}</small></button>)}</nav>
    <div className="learning-layout"><section className="card lesson"><div className="eyebrow">STEP {step + 1} OF 5 · {steps[step].toUpperCase()}</div>
      {step === 0 && <>
        <h2>Start where you are.</h2><p>Pick a direction and a useful starting point. These are reflections, not grades or hiring scores.</p>
        <label>What would you like to explore?<input maxLength={300} value={direction} onChange={event => {setDirection(event.target.value); setReflected(false); clearPlan();}}/></label>
        <div className="readiness">{Object.entries(readinessLabels).map(([key, label]) => <label key={key}>{label}<select value={scores[key]} onChange={event => {setScores({...scores, [key]: Number(event.target.value)}); setReflected(false); clearPlan();}}><option value={0}>0 · Start here</option><option value={1}>1 · Practice next</option><option value={2}>2 · Ready to show evidence</option></select><div className="readiness-dots" aria-hidden="true">{[0, 1, 2].map(value => <span key={value} className={value === scores[key] ? 'active' : ''}/>)}</div></label>)}</div>
        <div className="action"><Compass size={25}/><div><b>A useful starting point: {readinessLabels[suggestedKey].toLowerCase()}</b><p>This is one of your lowest self-reflections. You can choose a different focus if it matters more today.</p></div></div>
        <label className="check-control"><input type="checkbox" checked={reflected} onChange={event => setReflected(event.target.checked)}/>I reviewed my direction and all six areas.</label>
        <p className="done">Done when you have a direction and an honest starting point. You can change both later.</p>
      </>}
      {step === 1 && <>
        <h2>Ask with a purpose.</h2><p>Choose one small problem. Use the example prompt or adapt it to a question that interests you.</p>
        <div className="scenario-choices">{Object.entries(scenarios).map(([key, value]) => <button className={scenario === key ? 'selected' : ''} onClick={() => setScenario(key)} key={key}><b>{key}</b><small>{value.title}</small></button>)}</div>
        <h3>Your challenge</h3><p>{example.problem}</p>
        <label>Your prompt <small>Editable · copied prompts can be used in a tool of your choice</small><textarea className="prompt-editor" value={current.prompt} onChange={event => updatePractice({prompt: event.target.value, reviewed: false, evidenceReviewed: false})}/></label>
        <button className="secondary compact" onClick={() => copy(current.prompt, 'Prompt copied')}><Copy size={15}/>Copy prompt</button>
        <h3>Sample AI response</h3><p className="sample">{example.response}</p><p className="small muted">This is a supplied example, not a live response to your edits. The workshop does not call an AI service.</p>
        <details><summary>Explore more: what makes a useful prompt?</summary><p>Name the task, specify the output, and state what must not be invented. Then ask what assumptions need checking.</p></details>
        <label className="check-control"><input type="checkbox" checked={current.reviewed} onChange={event => updatePractice({reviewed: event.target.checked, evidenceReviewed: false})}/>I can explain the problem and have reviewed or adapted my prompt.</label>
        <p className="done">Done when you know what you are asking for—not just which tool you are using. Each scenario keeps its own notes.</p>
      </>}
      {step === 2 && <>
        <h2>Keep your judgment in the loop.</h2><p>You are checking the <b>{scenario.toLowerCase()}</b> example. Identify what is useful, what is uncertain, and one change.</p>
        <div className="routine">ASK → CHECK → CHOOSE → CHANGE → EXPLAIN</div>
        <div className="worked-example"><h3>See one: a modeled review</h3><div><b>Assumption</b><p>{example.check}</p></div><div><b>Evidence to check</b><p>{example.evidence}</p></div><div><b>A small improvement</b><p>{example.improvement}</p></div></div>
        <h3>Your turn · short notes or bullets are enough</h3>
        {Object.entries(questions).map(([key, label]) => <label key={key}>{label}<textarea maxLength={3000} value={current.answers[key]} onChange={event => updatePractice({answers: {...current.answers, [key]: event.target.value}, evidenceReviewed: false})} placeholder="Write, dictate, or use a few bullet points."/></label>)}
        <p className="done">{reviewed ? '✓ All five reflections captured. Next, review what the evidence statement can truthfully claim.' : `${Object.values(current.answers).filter(value => value.trim()).length} of 5 reflections captured. Return to any answer whenever you need.`}</p>
      </>}
      {step === 3 && <>
        <h2>Turn practice into evidence.</h2><p>A useful artifact shows your thinking, not just an AI response.</p>
        <div className="evidence-card"><div className="eyebrow">YOUR WORKSHOP ARTIFACT</div><h3>{direction || 'Your direction'} · {scenario}</h3><p>{example.problem}</p><b>What you changed</b><p>{current.answers.change || 'Your improvement will appear here after Check.'}</p><b>Why you changed it</b><p>{current.answers.explain || 'Your reasoning will appear here after Check.'}</p></div>
        {reviewed && current.reviewed && current.prompt.trim() ? <>
          <h3>Evidence-statement draft</h3><blockquote className="copy-block">{takeaway.statement}</blockquote>
          <button className="secondary compact" onClick={() => copy(takeaway.statement, 'Evidence draft copied')}><Copy size={15}/>Copy draft</button>
          <p className="small">This describes reviewing a supplied sample. It does not claim a deployed project, measured impact, or professional credential. Adapt it before using it on a résumé.</p>
          <label className="check-control"><input type="checkbox" checked={current.evidenceReviewed} onChange={event => updatePractice({evidenceReviewed: event.target.checked})}/>I reviewed this statement and it accurately describes my work.</label>
        </> : <div className="notice">Your evidence statement is not ready. Review the example in Practice and finish the five reflections in Check. Sample output alone is not your accomplishment.<div className="button-row"><button onClick={() => setStep(current.reviewed ? 2 : 1)}>Return to {current.reviewed ? 'Check' : 'Practice'}</button></div></div>}
        <p className="done">Done when you can explain your decision and the statement truthfully describes your own work.</p>
      </>}
      {step === 4 && <>
        <h2>One next step is enough.</h2><p>Choose a realistic practice budget. Your readiness reflection guides the recommendation.</p>
        <label>Minutes available this week<input type="number" min="10" max="120" step="1" value={minutes} onChange={event => {setMinutes(event.target.value === '' ? '' : Number(event.target.value)); clearPlan();}}/></label>
        <button disabled={loading || !Number.isInteger(minutes) || minutes < 10 || minutes > 120 || !direction.trim()} onClick={makePlan}>{loading ? 'Building your plan…' : 'Build my one-week plan'}<ArrowRight size={16}/></button>
        {error && <p role="alert">{error}</p>}
        {plan && <><h3>Your next seven days · {plan.reduce((total, item) => total + item.Minutes, 0)} planned minutes</h3>{plan.map(item => <div className="plan" key={item.Focus}><b>{item.Focus}</b><p>{item.Action}</p><span>{item.Minutes} minutes · Save a note or artifact showing what you tried.</span></div>)}<label className="check-control"><input type="checkbox" checked={planConfirmed} onChange={event => setPlanConfirmed(event.target.checked)}/>This is a realistic next step for my week.</label></>}
        <div className="takeaway-card"><div className="eyebrow">MY SEMINAR TAKEAWAY</div><h3>{completedCount === 5 ? 'A small step. Something real to show.' : 'Keep what you have built so far.'}</h3><dl><dt>I explored</dt><dd>{direction || 'Not yet selected'} · {scenario}</dd><dt>I checked</dt><dd>{current.answers.assumption || 'Not yet captured'}</dd><dt>I created</dt><dd>{takeaway.ready ? 'A reviewed evidence-statement draft' : 'Work in progress — finish Practice, Check and Build'}</dd><dt>My next move</dt><dd>{plan?.[0]?.Action || 'Generate a weekly plan above'}</dd></dl><button onClick={() => download('My-Seminar-Takeaway.txt', takeaway.text())}><Download size={17}/>{completedCount === 5 ? 'Download my takeaway' : 'Download work in progress'}</button></div>
        <p className="done">Done when you have one realistic next action and a copy of your takeaway. No perfect ending required.</p>
      </>}
      <div className="lesson-nav"><button className="secondary" disabled={step === 0} onClick={() => setStep(step - 1)}>Back</button>{step < 4 && <button onClick={() => setStep(step + 1)}>Next: {steps[step + 1]}<ArrowRight size={16}/></button>}</div>
    </section><aside className="card guidance"><Compass size={30}/><h2>Your path, your pace.</h2><p>Read one example.<br/>Try one small task.<br/>Explain one decision.</p><hr/><h3>You will leave with</h3><p>01 · A reviewed AI response</p><p>02 · An evidence statement</p><p>03 · A realistic weekly plan</p><details><summary>Need a different way to respond?</summary><p>Use bullets, a short paragraph, or your device’s speech-to-text. Take a break and return to the same numbered step.</p></details><hr/><button className="secondary compact" onClick={() => download('My-Seminar-Notes.txt', takeaway.text())}><Download size={15}/>Save my notes now</button><p className="muted small">Switching workspaces keeps your progress. Reloading or closing this tab clears it; download before leaving.</p></aside></div>
    <div className="notice small">Reflection notes stay in this tab. Generating a plan sends only your direction, six readiness values, and time budget to the planning service; there is no account or saved learner record.</div>
    <p className="copy-status" role="status">{copied}</p>
  </>;
}
