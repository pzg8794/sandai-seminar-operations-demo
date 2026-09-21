"""Notebook-only presentation adapters. Campaign calculations remain in core."""
from html import escape

from IPython.display import HTML, display

from .student_experience import READINESS_PROMPTS, ACTION_LIBRARY


def illustrated_example(scenario):
    """A concrete, equivalent-text storyboard; no external media is required."""
    examples = {
        'Campus/community': ('Run every workshop at noon.', 'Does noon work for commuters?', 'Ask about availability.', 'Pilot one time; compare turnout.'),
        'Career/data': ('Send every keyword match.', 'Does a keyword prove qualification?', 'Check skills and location.', 'Review five matches with students.'),
        'Teaching/education': ('Give everyone the same lesson.', 'Does one example fit everyone?', 'Ask learners to explain it.', 'Offer a model, then a short try.'),
    }
    lines = examples[scenario]
    headings = ['AI PROPOSES', 'YOU QUESTION', 'YOU CHECK', 'YOU IMPROVE']
    symbols = ['✦', '?', '✓', '↗']
    colors = ['#284e72', '#8b4e21', '#176c70', '#514080']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="0 0 960 290" style="width:100%;background:#f6f8fb;font-family:system-ui;border-radius:16px"><title>A worked example: AI proposes, you question, check, and improve</title>']
    for i, (heading, line, symbol, color) in enumerate(zip(headings, lines, symbols, colors)):
        x = 16 + i * 238
        parts.append(f'<rect x="{x}" y="20" width="220" height="242" rx="15" fill="white" stroke="#d4dfe8"/><circle cx="{x+110}" cy="78" r="34" fill="{color}"/><text x="{x+110}" y="90" text-anchor="middle" fill="white" font-size="34">{symbol}</text><text x="{x+110}" y="142" text-anchor="middle" font-size="14" font-weight="700" fill="{color}">{heading}</text>')
        import textwrap
        for j, chunk in enumerate(textwrap.wrap(line, 24)):
            parts.append(f'<text x="{x+110}" y="{178+j*24}" text-anchor="middle" font-size="16" fill="#183247">{escape(chunk)}</text>')
        if i < 3:
            parts.append(f'<path d="M{x+223} 78 h10 m-4 -4 4 4 -4 4" fill="none" stroke="#566f80" stroke-width="2"/>')
    parts.append('</svg>')
    parts.append('<p style="font:15px/1.6 system-ui;color:#183247">' + ' → '.join(f'<b>{h.title()}:</b> {escape(line)}' for h,line in zip(headings,lines)) + '</p>')
    return HTML(''.join(parts))


def cards(items):
    """Render readable, copyable cards; all supplied content is escaped."""
    return HTML('<div style="font:16px/1.6 system-ui;color:#183247;display:flex;flex-wrap:wrap;gap:12px">' + ''.join(
        '<div style="flex:1 1 230px;background:#f3f7fa;border:1px solid #c7d5df;border-top:4px solid #237f85;border-radius:10px;padding:18px">'
        f'<div style="font-size:14px;font-weight:700">{escape(str(label))}</div>'
        f'<div style="white-space:pre-wrap;margin-top:8px">{escape(str(value))}</div></div>'
        for label, value in items) + '</div>')


def pathway(items, *, active=0, title='Your route'):
    """Calm, color-independent pathway inspired by Piter's teaching notebooks."""
    steps = []
    for index, (label, detail) in enumerate(items):
        state = 'YOU ARE HERE' if index == active else f'STEP {index + 1}'
        border = '#1b6670' if index == active else '#b7c7d2'
        steps.append(
            f'<div style="flex:1 1 145px;border:2px solid {border};border-radius:12px;padding:14px;background:#fff">'
            f'<div style="font-size:12px;font-weight:800;letter-spacing:.04em">{escape(state)}</div>'
            f'<div style="font-size:17px;font-weight:750;margin-top:5px">{escape(label)}</div>'
            f'<div style="font-size:14px;margin-top:5px">{escape(detail)}</div></div>'
        )
    return HTML(
        f'<section aria-label="{escape(title)}" style="font:15px/1.45 system-ui;color:#183247">'
        f'<h3 style="margin:8px 0">{escape(title)}</h3><div style="display:flex;flex-wrap:wrap;gap:9px">'
        + ''.join(steps) + '</div></section>'
    )


def bars(title, labels, values, *, target=None, suffix='', maximum=None, colors=None):
    """Accessible SVG bars with explicit values, labels and target annotation."""
    limit = max(max(values, default=1), target or 0, maximum or 0, 1) * 1.12
    height = 80 + 48 * len(values)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(title)}" viewBox="0 0 880 {height}" style="width:100%;max-width:1000px;background:#fff;color:#183247;font:15px system-ui">',
             f'<title>{escape(title)}</title><text x="18" y="28" font-size="20" font-weight="700">{escape(title)}</text>']
    for i, (label, value) in enumerate(zip(labels, values)):
        y = 60 + 48 * i
        color = colors[i] if colors else '#237f85'
        parts += [f'<text x="18" y="{y+20}">{escape(str(label))}</text>',
                  f'<rect x="315" y="{y}" width="{480*float(value)/limit}" height="28" rx="4" fill="{color}"/>',
                  f'<text x="{325+480*float(value)/limit}" y="{y+20}">{value:g}{escape(suffix)}</text>']
    if target is not None:
        x = 315 + 480 * target / limit
        parts += [f'<path d="M{x} 47 V{height-20}" stroke="#183247" stroke-dasharray="5 4"/>',
                  f'<text x="{x+6}" y="46">Target {target:g}{escape(suffix)}</text>']
    return HTML(''.join(parts) + '</svg>')


class ManagementView:
    def __init__(self, monitor):
        self.monitor = monitor

    def decision(self):
        d = self.monitor.decision
        status_text = {'RED': 'recovery required', 'YELLOW': 'watch and strengthen confirmations', 'GREEN': 'on track'}
        display(cards([
            ('STATUS · T−3 forecast', f"{d['risk_status']} — {status_text[d['risk_status']]}"),
            ('Decision week', d['week']), ('Observed attendance', d['weekly_attendance']),
            ('Weekly target', self.monitor.settings['weekly_attendance_target']),
            ('Cumulative through decision week', d['cumulative_attendance']),
            ('Forecast before intervention', f"{d['forecast_expected_attendance']:.1f} attendees"),
            ('Chance of reaching 20 before intervention', f"{d['forecast_probability_at_least_20']:.0%}"),
            ('ACTION · Piter', d['recommended_intervention']),
            ('NEXT CHECK', 'T−1: review confirmations and rerun the forecast.'),
        ]))

    def performance(self):
        w = self.monitor.weekly
        labels = [f"Week {i}" + (' · miss' if i == 3 else ' · recovery' if i == 4 else '') for i in w.week]
        display(bars('Weekly attendance · eight-week demo scenario', labels, list(w.attendees), target=20,
                     colors=['#a54534' if n < 20 else '#237f85' for n in w.attendees]))
        actual = list(w.cumulative_attendance)
        target = [int(i)*20 for i in w.week]
        pts = lambda vals: ' '.join(f'{65+i*95},{240-v/200*190}' for i,v in enumerate(vals))
        svg = '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cumulative attendance versus target" viewBox="0 0 840 310" style="width:100%;background:white;font:15px system-ui;color:#183247">'
        svg += '<title>Cumulative attendance versus target trajectory</title><text x="20" y="25" font-size="20">Cumulative progress · goal 160</text>'
        svg += f'<polyline points="{pts(target)}" fill="none" stroke="#637887" stroke-width="3" stroke-dasharray="7 5"/><polyline points="{pts(actual)}" fill="none" stroke="#237f85" stroke-width="3"/>'
        for i,v in enumerate(actual):
            x,y = 65+i*95,240-v/200*190
            svg += f'<circle cx="{x}" cy="{y}" r="5" fill="#237f85"/><text x="{x-10}" y="{y-12}">{v}</text><text x="{x-10}" y="263">W{i+1}</text>'
        svg += '<text x="20" y="294">Solid: sample attendance · Dashed: 20 per week (20, 40, 60, 80, 100, 120, 140, 160)</text></svg>'
        display(HTML(svg))

    def recovery(self):
        r = self.monitor.recovery_scenario()
        rows = list(r.to_dict('records'))
        panels = []
        for label, row, color in zip(['BEFORE · T−3', 'AFTER · PLANNED RECOVERY'], rows, ['#994633', '#176c70']):
            panels.append(f'<div style="flex:1;padding:24px;border-radius:16px;background:#f3f7fa;border-top:5px solid {color}"><b>{label}</b><div style="font-size:46px;font-weight:800;color:{color}">{row["Expected attendance"]:.1f}</div><div>expected attendees · target 20</div><div style="font-size:24px;margin-top:15px">{row["P(attendance ≥20)"]:.0%} chance of reaching 20</div><b>{escape(str(row["Risk"]))}</b></div>')
        display(HTML('<section style="font:16px/1.5 system-ui;color:#183247"><h3>Detect → intervene → reforecast</h3><div style="display:flex;gap:16px;flex-wrap:wrap">' + ''.join(panels) + '</div><p><b>Intervention:</b> activate a secondary partner and strengthen confirmations. These are modeled outcomes, not measured causal effects.</p></section>'))
        display(cards([(str(row['Scenario']), f"Expected {row['Expected attendance']} · P(≥20) {row['P(attendance ≥20)']:.0%} · {row['Risk']}") for _,row in r.iterrows()]))

    def channels(self):
        c = self.monitor.channel_summary()
        display(bars('Which channels bring attendees?', list(c.channel), list(c.attendees)))

    def funnel(self):
        f = self.monitor.conversion_funnel()
        values = list(f['Synthetic count'])
        labels = ['Attended', 'Opted in', 'Qualified', 'Approved conversion']
        widths = [600 * float(v) / max(values) for v in values]
        svg = '<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="0 0 900 350" style="width:100%;background:white;font:17px system-ui"><title>Free seminar to voluntary follow-on opportunity</title>'
        for i,(label,value,width) in enumerate(zip(labels,values,widths)):
            x,y=300+(600-width)/2, 20+i*78
            svg += f'<text x="16" y="{y+39}" fill="#183247">{label}: {value}</text><rect x="{x}" y="{y}" width="{width}" height="64" rx="10" fill="{["#284e72","#236779","#267c7d","#514080"][i]}"/>'
        display(HTML(svg+'</svg><p>Sample pathway counts. Revenue depends on the agreed offer, price, and conversion terms.</p>'))

    def student_value(self):
        """Show learning-format signals without turning them into a student ranking."""
        summary = self.monitor.program_improvement_summary().copy()
        labels = list(summary['preferred_learning_format'].str.replace('_', ' ').str.title())
        display(bars('Learning-format engagement · sample scenario', labels,
                     list(summary['mean_engagement_score']), maximum=100, suffix='%'))
        display(cards([
            ('WHY', 'The seminar must leave students with evidence they can use, not only produce attendance.'),
            ('ACTION', 'Preserve worked examples and checklists; test a shorter visual or video-supported entry route.'),
            ('NEXT CHECK', 'Compare completion and support signals after the next bounded design change.'),
        ]))

    def details(self, title, frame):
        display(HTML(f'<details><summary style="font:600 16px system-ui;padding:12px">{escape(title)}</summary>{frame.to_html(index=False, escape=True)}</details>'))


SCENARIOS = {
    'Campus/community': ('A campus workshop has low attendance. Students mention timing, unclear skill level, and uncertainty about materials.', 'Test a shorter session and publish a beginner-friendly materials checklist.', 'A shorter session will fit everyone’s schedule.'),
    'Career/data': ('A career club wants students to find relevant internship listings. Listings vary in location, required skills, and clarity.', 'Organize listings by skills and location, then ask students to review five matches.', 'A keyword match means the student is qualified.'),
    'Teaching/education': ('A study group wants a clearer introduction to a difficult topic. Learners request examples, smaller steps, and practice.', 'Show one worked example, offer a short practice task, and check understanding.', 'Every learner needs the same example.'),
}


class StudentWorkshopView:
    """A lightweight interaction/presentation layer over the existing experience."""
    def __init__(self, experience, scenario='Campus/community', focus='Suggested starting point'):
        self.experience = experience
        self.scenario = scenario
        self.focus = focus

    def orient(self, entry_route='Visual walkthrough'):
        routes = {
            'Visual walkthrough': 'Follow the five-card map and the model outputs. Read only the short action prompts.',
            'Read the quick guide': 'Use the What, Why, Example, Your turn, and Done when cues in each step.',
            'Talk then write': 'Talk through each prompt with a partner or aloud, then save one short summary.',
        }
        display(pathway([
            ('Reflect', 'Choose a useful starting point.'),
            ('Practice', 'ASK with a clear task.'),
            ('Check', 'Question and improve the response.'),
            ('Build', 'Save evidence you can explain.'),
            ('Plan', 'Choose one realistic next move.'),
        ], title='Your workshop map'))
        display(cards([
            ('Your chosen entry route', entry_route),
            ('How to use it', routes.get(entry_route, routes['Visual walkthrough'])),
            ('Need a pause?', 'Stop after any step. Use the numbered headings or table of contents to re-enter.'),
            ('Your first move', 'See the illustrated example in Practice, then adapt it to your own scenario.'),
        ]))

    def reflect(self):
        e = self.experience
        display(bars('Your reflection · a starting point, not a grade', ['Strength story','Career direction','Portfolio evidence','Checking AI','Learning plan','Asking for help'], list(e.self_check.values()), maximum=2))
        key = e.focus_keys(1)[0]
        display(cards([('Your best starting point', READINESS_PROMPTS[key]),
                       ('Your choice', self.focus if self.focus != 'Suggested starting point' else READINESS_PROMPTS[key]),
                       ('How to use this', '0 — Start here · 1 — Practice next · 2 — Ready to show evidence. Choose another area if it matters more today.'),
                       ('Your practice route', {'Worked example': 'Read the model, change one part, then explain your change.', 'Checklist': 'Ask → check one assumption → keep one useful part → change → explain.', 'Talk then write': 'Talk through the idea with a partner or aloud, then record a short summary.'}.get(e.profile.preferred_format, 'Choose the route that helps you begin.'))]))

    def practice(self, prompt='', response_text=''):
        challenge, response, assumption = SCENARIOS[self.scenario]
        display(illustrated_example(self.scenario))
        self.prompt = prompt.strip() or f'Act as a thinking partner. {challenge} Suggest one small improvement. Explain your reasoning, assumptions, evidence needed, and one downside. Do not invent results.'
        display(cards([('Your challenge', challenge), ('Your prompt · copy and adapt', self.prompt),
                       ('Response you provided' if response_text.strip() else 'Sample response · no live AI call', response_text.strip() or response),
                       ('Worked check', f'Possible assumption: {assumption} Ask the people affected before expanding the idea.')]))

    def check_feedback(self, assumption, evidence, keep, change, explanation, completed=False):
        entries = [assumption, evidence, keep, change, explanation]
        score = sum(bool(str(item).strip()) for item in entries)
        display(bars('Your review record · five parts', ['Assumption', 'Evidence', 'Keep', 'Change', 'Explain'],
                     [1 if str(item).strip() else 0 for item in entries], maximum=1,
                     colors=['#237f85' if str(item).strip() else '#b7c7d2' for item in entries]))
        message = 'Five parts recorded. Confirm completion only after these are your own notes.' if score == 5 else f'{score} of 5 parts recorded. Complete the missing parts before claiming the activity.'
        display(cards([('CHECK FOR UNDERSTANDING', message),
                       ('Your confirmation', 'Confirmed as my work' if completed and score == 5 else 'Not yet confirmed')]))

    def takeaway(self, assumption, evidence, keep, change, explanation, completed=False):
        notes = [assumption, evidence, keep, change, explanation]
        ready = completed and all(str(v).strip() for v in notes)
        e = self.experience
        display(cards([('Review status', 'Your activity record — confirmed by you' if ready else 'Worked example / draft — replace the examples and confirm completion before claiming this work.'),
                       ('I checked', assumption), ('Evidence I would seek', evidence),
                       ('I would keep', keep), ('I would change', change), ('Why', explanation)]))
        bullet = f'Evaluated an AI-supported {self.scenario.lower()} proposal, documented an assumption and evidence needs, and revised the proposal with an explanation.'
        display(cards([('Evidence statement / résumé draft', bullet if ready else 'After completing this activity, you could say: ' + bullet),
                       ('Reviewable artifact · copy this record', '\n'.join(f'{k}: {v}' for k,v in zip(['Assumption','Evidence','Keep','Change','Reason'], notes)))]))
        self.ready = ready
        self.bullet = bullet

    def plan(self, next_action='', finish_signal=''):
        e = self.experience
        proposed = e.weekly_plan().iloc[0]
        choices = dict(zip(['Strength story', 'Career direction', 'Portfolio evidence', 'Checking AI', 'Learning plan', 'Asking for help'], READINESS_PROMPTS))
        if self.focus in choices:
            key = choices[self.focus]
            minutes, action = ACTION_LIBRARY[key]
            proposed = {'Focus': READINESS_PROMPTS[key], 'Minutes': minutes, 'Action': action}
        self.action = next_action.strip() or str(proposed['Action'])
        self.finish = finish_signal.strip() or 'One saved note or artifact that I can explain to someone else.'
        self.minutes = min(int(proposed['Minutes']), e.profile.weekly_minutes)
        if not next_action.strip() and self.minutes < ACTION_LIBRARY[choices.get(self.focus, e.focus_keys(1)[0])][0]:
            self.action = 'Begin a small part of this task: ' + self.action
            if not finish_signal.strip():
                self.finish = 'Save one useful sentence or question; continue another day.'
        display(cards([('Your next 7 days · focus', self.focus if self.focus != 'Suggested starting point' else str(proposed['Focus'])),
                       ('One action', self.action), ('Time to reserve', f'{self.minutes} minutes, within your {e.profile.weekly_minutes}-minute budget'),
                       ('Done when', self.finish)]))

    def finish_card(self):
        display(cards([('My Seminar Takeaway · I explored', self.experience.profile.career_direction),
                       ('I practiced', 'ASK → CHECK → CHOOSE → CHANGE → EXPLAIN'),
                       ('My artifact', 'Prompt + review notes + evidence-statement draft' if self.ready else 'Example review record to replace with my own responses'),
                       ('My next move', self.action), ('Finish signal', self.finish),
                       ('Time I committed', f'{self.minutes} minutes this week')]))
