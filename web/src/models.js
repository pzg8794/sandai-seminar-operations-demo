/** Presentation-only models. Campaign and learning calculations stay in Python. */
export const readinessLabels = {
  strength_story: 'Explain a strength', role_direction: 'Choose a direction',
  portfolio_evidence: 'Show an artifact', verification: 'Check AI outputs',
  learning_plan: 'Plan realistic practice', ask_for_help: 'Ask for support',
};

export const scenarios = {
  Community: {
    title: 'Bring people together',
    problem: 'A campus workshop has low attendance.',
    prompt: 'Suggest three small ways to improve attendance at a campus workshop. For each, give an assumption, evidence to check, and one tradeoff. Do not invent survey results.',
    response: 'Try shorter sessions, publish a beginner-friendly agenda, and clarify what materials are provided.',
    check: 'Shorter sessions might help, but we do not yet know whether timing is the barrier.',
    evidence: 'Compare sign-ups with attendance; ask one optional question about timing.',
    improvement: 'Test one shorter session before changing the whole series.',
  },
  Career: {
    title: 'Explore a career direction',
    problem: 'You want to compare internship opportunities.',
    prompt: 'Help me compare five internship descriptions I provide. Organize the skills and requirements in a table. Mark missing information. Do not infer qualifications or guarantee a match.',
    response: 'Group roles by repeated skills and rank the roles with the most matching keywords.',
    check: 'Keyword similarity is not evidence that a person is qualified; requirements need human review.',
    evidence: 'Check each requirement against the original listing and an example of your work.',
    improvement: 'Replace the keyword ranking with a comparison showing evidence and unanswered questions.',
  },
  Teaching: {
    title: 'Make learning clearer',
    problem: 'Students need a clearer introduction to a difficult topic.',
    prompt: 'Propose a short introduction to a difficult topic using a worked example, a practice task, and a check for understanding. State what learner context you need before adapting it.',
    response: 'Start with a visual example, ask learners to try a similar problem, then explain their reasoning.',
    check: 'One visual example may not be accessible or meaningful to every learner.',
    evidence: 'Ask learners to explain one idea in words, a sketch, or a worked step.',
    improvement: 'Pair the visual model with a plain-language explanation and a choice of response formats.',
  },
};

export const emptyAnswers = () => ({assumption: '', evidence: '', keep: '', change: '', explain: ''});
export const newPractice = scenario => ({prompt: scenarios[scenario].prompt, answers: emptyAnswers(), reviewed: false, evidenceReviewed: false});
export const reviewComplete = answers => Object.values(answers).every(value => value.trim().length > 0);

export class CampaignViewModel {
  constructor(data) { this.data = data; }
  get final() { return this.data.weekly.at(-1); }
  get metWeeks() { return this.data.weekly.filter(row => row.weekly_goal_met).length; }
  get missedWeeks() { return this.data.weekly.filter(row => !row.weekly_goal_met); }
  get recoveredWeeks() {
    return this.data.weekly.filter((row, index) => index > 0 && row.weekly_goal_met && !this.data.weekly[index - 1].weekly_goal_met);
  }
  decision(week) { return this.data.weekly_decisions.find(row => row.week === week); }
  nextCheck(week) {
    return week === this.final.week
      ? 'T+1 campaign closeout: review the missed week, opt-in follow-ups, and lessons for the next cycle.'
      : `T−3 before Week ${week + 1}: review registrations, confirmations, and the next attendance forecast.`;
  }
}

export class StudentTakeaway {
  constructor({direction, scenario, practice, plan, minutes}) {
    Object.assign(this, {direction, scenario, practice, plan, minutes});
  }
  get ready() { return Boolean(this.practice.prompt.trim()) && reviewComplete(this.practice.answers) && this.practice.reviewed && this.practice.evidenceReviewed; }
  get statement() {
    return `Reviewed a sample AI-assisted ${this.scenario.toLowerCase()} solution, identified an assumption, specified evidence to check, and documented an improvement: ${this.practice.answers.change.trim()}`;
  }
  text() {
    return [
      'MY SEMINAR TAKEAWAY', this.ready ? 'Reviewed evidence-statement draft' : 'Work in progress — not a completion record',
      `Direction: ${this.direction}`, `Scenario: ${scenarios[this.scenario].problem}`,
      `My prompt:\n${this.practice.prompt}`, `Sample response reviewed:\n${scenarios[this.scenario].response}`,
      ...Object.entries(this.practice.answers).map(([key, value]) => `${key}: ${value || 'Not yet completed'}`),
      `Evidence statement: ${this.ready ? this.statement : 'Not ready — finish your review and confirm the wording first.'}`,
      'Next 7 days:', this.plan ? this.plan.map(row => `${row.Action} (${row.Minutes} minutes)`).join('\n') : 'Not yet planned',
      `Available practice budget: ${this.minutes} minutes`,
      'This workshop uses a supplied example, not a live AI service. No project deployment, measured impact, or credential is claimed.',
    ].join('\n\n');
  }
}
