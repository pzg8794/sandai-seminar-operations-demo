"""Apply the product presentation to the existing thin notebooks, preserving bootstrap."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / 'notebooks'


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(text, title='Show this section'):
    return nbf.v4.new_code_cell('#@title ' + title + '\n' + text,
        metadata={'cellView': 'form', 'jupyter': {'source_hidden': True}})


def save(path, original, cells):
    original.cells = cells
    nbf.write(original, path)


sp = NB / 'Piter_Garcia_SaNDAI_Student_Seminar_Companion.ipynb'
mp = NB / 'Piter_Garcia_SaNDAI_Management_Command_Center.ipynb'
s, m = nbf.read(sp, as_version=4), nbf.read(mp, as_version=4)
sb = next(c.source for c in s.cells if c.cell_type == 'code' and 'import os, subprocess, sys' in c.source)
sb = sb[sb.index('from pathlib import Path'):]
sb = sb.split('from sandai_artifacts import StudentSeminarExperience')[0]
sb = sb.replace(
    'sys.path.insert(0, str(SOURCE_ROOT / "src"))\n\n',
    'sys.path.insert(0, str(SOURCE_ROOT / "src"))\n'
    '# Colab runtimes persist imports across notebook reloads. Clear only this package\n'
    '# so a freshly pulled GitHub revision is used without requiring a runtime restart.\n'
    'if IN_COLAB:\n'
    '    for module_name in list(sys.modules):\n'
    '        if module_name == "sandai_artifacts" or module_name.startswith("sandai_artifacts."):\n'
    '            del sys.modules[module_name]\n\n'
)
sb += 'from sandai_artifacts import StudentSeminarExperience, StudentLearningProfile\nfrom sandai_artifacts.presentation import StudentWorkshopView\nprint("Ready. Start with Reflect below.")'

save(sp, s, [
md('''# SaNDAI AI Career Lab
### Turn one AI practice activity into evidence you can explain, improve, and use.

**START → 1 REFLECT → 2 PRACTICE → 3 CHECK → 4 BUILD → 5 PLAN → FINISH**

**You’ll leave with:** one AI practice artifact · one evidence-statement or résumé draft · one realistic next step.

**About 25–40 minutes, at your pace.** Take a break whenever you need one.

**Quick path:** run setup once, then change the fields and run each step. In Colab, use the form fields; in VS Code, edit the values in the same short cells. Run all with defaults to see a worked example.

**Choose how to respond:** type short notes, use speech-to-text, or talk it through with a partner and record a brief summary. Optional extensions are labeled **Explore more**.

> **Prototype note:** The preloaded examples use sample data for demonstration. Students can replace the sample inputs with their own responses.

[Reflect](#reflect) · [Practice](#practice) · [Check](#check) · [Build](#build) · [Plan](#plan) · [Finish](#finish)'''),
code(sb, 'Start here · run once to prepare the workshop'),
md('''## Choose how you want to enter
The activity offers the same goal in more than one form. Choose the route that makes it easiest to begin; you can switch later.

✅ **Done when:** you can point to the step where you will start.'''),
code('''entry_route = "Visual walkthrough" #@param ["Visual walkthrough", "Read the quick guide", "Talk then write"]
orientation_profile = StudentLearningProfile("Sample participant", (), "Explore a career direction", "Create one explainable artifact", 25, entry_route)
orientation_experience = StudentSeminarExperience(orientation_profile, dict(strength_story=1, role_direction=1, portfolio_evidence=0, verification=1, learning_plan=1, ask_for_help=1))
StudentWorkshopView(orientation_experience).orient(entry_route)''', 'Choose your entry route · visual, quick guide, or talk then write'),
md('''<a id="reflect"></a>
## 🧭 Step 1 of 5 — Reflect
**What:** choose where you want to grow. **Why:** a useful next step starts from where you are today.

💡 **Example:** “Explore data work; practice checking an AI suggestion; reserve 25 minutes this week.”

✍️ **Your turn:** change the fields below. There is no perfect answer; you can change this later.

**0 — Start here · 1 — Practice next · 2 — Ready to show evidence**

✅ **Done when:** you have a direction, a goal, and one skill to begin with.'''),
code('''career_direction = "Explore data and AI-support roles" #@param {type:"string"}
seminar_goal = "Practice checking an AI suggestion" #@param {type:"string"}
weekly_minutes = 25 #@param {type:"slider", min:5, max:120, step:5}
preferred_format = "Worked example" #@param ["Worked example", "Checklist", "Talk then write"]
strength_story = 1 #@param [0, 1, 2] {type:"raw"}
role_direction = 1 #@param [0, 1, 2] {type:"raw"}
portfolio_evidence = 0 #@param [0, 1, 2] {type:"raw"}
verification = 1 #@param [0, 1, 2] {type:"raw"}
learning_plan = 1 #@param [0, 1, 2] {type:"raw"}
ask_for_help = 1 #@param [0, 1, 2] {type:"raw"}
focus = "Suggested starting point" #@param ["Suggested starting point", "Strength story", "Career direction", "Portfolio evidence", "Checking AI", "Learning plan", "Asking for help"]
profile = StudentLearningProfile("Sample participant", (), career_direction, seminar_goal, weekly_minutes, preferred_format)
experience = StudentSeminarExperience(profile, dict(strength_story=strength_story, role_direction=role_direction, portfolio_evidence=portfolio_evidence, verification=verification, learning_plan=learning_plan, ask_for_help=ask_for_help))
workshop = StudentWorkshopView(experience, focus=focus)
workshop.reflect()''', 'Your starting point · edit the fields, then run'),
md('''<a id="practice"></a>
## ✍️ Step 2 of 5 — Practice · ASK
**You are here:** you chose a starting point. Now give AI one clear task.

**Why:** a specific problem, evidence boundary, and requested format make a response easier to review.

💡 **See one:** “Suggest one small improvement. Explain assumptions, evidence needed, and a downside.”

✍️ **Try one:** choose a scenario. Keep the modeled prompt or write your own. Read the sample response, or try your prompt in an AI tool you already use.

✅ **Done when:** you can explain what you asked and what the response proposes.

<details><summary>⭐ Explore more · strengthen the prompt</summary>Add the audience, constraints, and how you will judge success. Compare two responses: which one makes fewer unsupported claims?</details>'''),
code('''scenario = "Campus/community" #@param ["Campus/community", "Career/data", "Teaching/education"]
my_prompt = "" #@param {type:"string"}
my_ai_response = "" #@param {type:"string"}
workshop.scenario = scenario
workshop.practice(my_prompt, my_ai_response)''', 'Choose your practice scenario'),
md('''<a id="check"></a>
## 🔎 Step 3 of 5 — Check · CHOOSE · CHANGE · EXPLAIN
**What you already did:** reviewed a prompt and a proposal. **Next:** improve the proposal using your judgment.

💡 **Worked example:** “The AI assumed students are free at lunchtime. I would ask about availability, keep the small pilot, and test one time slot before expanding.”

✍️ **Your turn:** replace the example notes below. Short phrases, a dictated summary, or notes from a partner conversation all work.

Before moving on:
- [ ] I understand the problem.
- [ ] I identified an assumption and evidence I would check.
- [ ] I chose what to keep and changed something.
- [ ] I can explain why.

✅ **Done when:** your notes explain one reasoned improvement. AI proposes; you evaluate and decide.'''),
code('''assumption = "The proposed change fits everyone's schedule." #@param {type:"string"}
evidence_needed = "Ask participants about availability before choosing a time." #@param {type:"string"}
keep = "Keep the small, measurable pilot." #@param {type:"string"}
change = "Test one option with participant feedback before expanding." #@param {type:"string"}
explanation = "This checks the assumption before committing more resources." #@param {type:"string"}
completed_my_review = False #@param {type:"boolean"}''', 'Your review notes · confirm only after doing your own review'),
code('workshop.check_feedback(assumption, evidence_needed, keep, change, explanation, completed_my_review)', 'Check your review record · immediate feedback'),
md('''<a id="build"></a>
## 🛠️ Step 4 of 5 — Build your evidence
**What:** turn your review into a small artifact. **Why:** an example you can explain is stronger than a broad claim about knowing AI.

✍️ **Your turn:** run this cell and copy the review record with your prompt into your notes. The statement is a draft; use it only if it accurately describes what you did.

✅ **Done when:** you saved the prompt and review notes and can explain your change.'''),
code('workshop.takeaway(assumption, evidence_needed, keep, change, explanation, completed_my_review)', 'Build your copy-friendly evidence record'),
md('''<a id="plan"></a>
## 🎯 Step 5 of 5 — Plan your next 7 days
**You are here:** you have a review record. Choose one useful follow-up that fits your week.

💡 **Example:** “Spend 15 minutes improving one prompt. Finish when I have saved the before/after versions and one reason for the change.”

✍️ **Your turn:** keep the suggested action, or replace it with your own action and finish signal. If you chose a different focus, adapt the action to match it.

✅ **Done when:** you know what to do, approximately how long it needs, and what finished looks like.'''),
code('''next_action = "" #@param {type:"string"}
finish_signal = "" #@param {type:"string"}
workshop.plan(next_action, finish_signal)''', 'One realistic next step · blank fields use the suggested example'),
md('''<a id="finish"></a>
## ✅ My Seminar Takeaway
Copy the parts you want to keep. You can return to any step and rerun the cells below it after changing your responses.

**Check your understanding:** explain one assumption you challenged and why your revision is better. You can say it aloud, write a sentence, or share it with a partner.'''),
code('workshop.finish_card()', 'Your takeaway'),
md('''[Back to Reflect](#reflect) · [Back to your evidence](#build)

<details><summary>⭐ Explore more · a second practice round</summary>Try another scenario. Keep the same ASK → CHECK → CHOOSE → CHANGE → EXPLAIN routine. Compare which evidence you needed and why it changed.</details>'''),
])

mb = next(c.source for c in m.cells if c.cell_type == 'code' and 'import os, subprocess, sys' in c.source)
mb = mb[mb.index('from pathlib import Path'):]
mb = mb.split('print(f"Ready:')[0].split('from sandai_artifacts.presentation import ManagementView')[0]
mb = mb.replace(
    'sys.path.insert(0, str(SOURCE_ROOT / "src"))\n\n',
    'sys.path.insert(0, str(SOURCE_ROOT / "src"))\n'
    '# Colab runtimes persist imports across notebook reloads. Clear only this package\n'
    '# so a freshly pulled GitHub revision is used without requiring a runtime restart.\n'
    'if IN_COLAB:\n'
    '    for module_name in list(sys.modules):\n'
    '        if module_name == "sandai_artifacts" or module_name.startswith("sandai_artifacts."):\n'
    '            del sys.modules[module_name]\n\n'
)
mb += 'from sandai_artifacts.presentation import ManagementView\nview = ManagementView(monitor)\nview.decision()'
if 'data_mode = "Public sample" #@param' not in mb:
    mb = 'data_mode = "Public sample" #@param ["Public sample", "Shared Drive"]\n' + mb
    mb = mb.replace('    from google.colab import drive\n    drive.mount("/content/drive", force_remount=False)', '    if data_mode == "Shared Drive":\n        from google.colab import drive\n        drive.mount("/content/drive", force_remount=False)')
    mb = mb.replace('WORKSPACE_ROOT = resolve_workspace_root(explicit_root=WORKSPACE_HINT, source_root=SOURCE_ROOT)', 'WORKSPACE_ROOT = SOURCE_ROOT if data_mode == "Public sample" else resolve_workspace_root(explicit_root=WORKSPACE_HINT, source_root=SOURCE_ROOT)\nprint(f"Data mode: {data_mode}")')
method = next(c.source for c in m.cells if c.cell_type == 'markdown' and 'Method behind' in c.source)
save(mp, m, [
md('''# SaNDAI 8-Week Seminar Growth Command Center
### Goal: 20+ attendees every week | 160+ total attendances

**STATUS → WHY → ACTION → NEXT CHECK**

Run the opening cell to see the decision. Expand supporting tables only when you need the detail.

**Reviewer:** leave **Public sample** selected and run all. **Operator:** select **Shared Drive** to use the synchronized management data.

*Demo scenario: all preloaded data is illustrative. The decision card shows the Week 4 T−3 forecast alongside its subsequently observed result; the eight-week charts show the full sample scenario.*'''),
code(mb, 'Open command center · connect data and show the current decision'),
md('''## 1. Performance · protect the weekly floor
Week 3 misses the weekly goal. Week 4 recovers. A total above 160 does not erase an individual missed week.'''),
code('view.performance()\nview.details("Explore the weekly scorecard", monitor.weekly)', 'Weekly attendance and cumulative progress'),
md('''## 2. Recovery · act before seminar day
Compare the T−3 forecast with the same model after adding the planned partner registrations and confirmations. This is a modeled intervention, not a causal claim.'''),
code('view.recovery()\nview.details("Recovery inputs and results", monitor.recovery_scenario())', 'Before → after intervention'),
md('''## 3. Growth channels · expand beyond the immediate network
Use the channels that generate attendees; inspect effort alongside volume before shifting outreach.'''),
code('view.channels()\nview.details("Channel efficiency and attribution", monitor.channel_summary())', 'Channel contribution'),
md('''## 4. Student value · leave with something useful
The companion provides **Reflect → Practice → Check → Build → Plan**: a structured prompt, an evidence review, a résumé-statement draft, and one next action.

[Open the AI Career Lab](https://colab.research.google.com/github/pzg8794/sandai-seminar-operations-demo/blob/main/notebooks/Piter_Garcia_SaNDAI_Student_Seminar_Companion.ipynb)

Support signals help choose a small improvement to the experience; they do not rank students’ ability.'''),
code('view.student_value()\nview.details("Participant support summary", monitor.student_support.weekly_summary())\nview.details("Support actions", monitor.student_support.support_queue())\nview.details("Learning-format observations and next tests", monitor.program_improvement_summary())', 'See student value, support, and program improvements'),
md('''## 5. Business value · free seminar to downstream opportunity
Keep the seminar free. Track voluntary interest and approved follow-on conversions. These counts describe the pathway; revenue requires actual offer and pricing terms.'''),
code('view.funnel()\nview.details("Funnel definitions", monitor.conversion_funnel())', 'Attendance → opt-in → qualified → approved conversion'),
md('''## 6. Ownership · recurring decision gates
Piter owns each gate. The T−3 forecast prompts recovery; T−1 checks confirmations; T+1 turns results into the next small improvement.'''),
code('display(monitor.operating_cadence())', 'Who acts, when, and on what'),
md(method.replace('## 9.', '## 7.')),
md('''### Architecture and evidence
Current Shared Drive data → validated campaign calculations → management decision.

VS Code and Colab use the same package and shared data. GitHub owns code; the RIT Shared Drive owns operational/test data and derived monitoring records.'''),
code('view.details("Assignment requirement → prototype evidence", monitor.requirement_traceability())', 'Technical traceability'),
md('''### Optional monitoring output
The next cell follows the existing output setting. Preview is the default.'''),
code('''if os.environ.get("SANDAI_WRITE_OUTPUTS", "0") == "1":
    display(write_management_outputs(WORKSPACE_ROOT, surface="colab" if IN_COLAB else "local"))
else:
    print("Preview complete. No monitoring files written.")''', 'Monitoring output'),
])
