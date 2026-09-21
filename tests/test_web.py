import json
import pytest
from django.test import RequestFactory
from web.server import student_plan
from sandai_artifacts.student_experience import StudentLearningProfile, StudentSeminarExperience
from scripts.export_web_data import payload, ROOT

def test_export_matches_live_models():
    assert json.loads((ROOT/'web/src/campaign.json').read_text()) == payload()
    assert payload()['weekly'][-1]['cumulative_attendance'] == 183
    assert payload()['weekly'][2]['attendees'] == 18

def test_student_plan_reuses_domain():
    scores = dict(strength_story=1, role_direction=1, portfolio_evidence=0, verification=2, learning_plan=1, ask_for_help=1)
    request = RequestFactory().post('/api/student-plan',data=json.dumps(dict(minutes=30,direction='Data',scores=scores)),content_type='application/json')
    response=student_plan(request)
    expected=StudentSeminarExperience(StudentLearningProfile('Participant',(),'Data','Build one explainable artifact',30,'Worked example'),scores).weekly_plan()
    assert response.status_code == 200
    assert json.loads(response.content)['plan'] == json.loads(expected.to_json(orient='records'))

def test_bad_budget_fails():
    response=student_plan(RequestFactory().post('/api/student-plan',data='{"minutes":-1}',content_type='application/json'))
    assert response.status_code == 400


def test_each_week_reuses_domain_decision_without_future_history():
    from sandai_artifacts.core import build_decision_snapshot
    from sandai_artifacts.management import CampaignMonitor
    monitor = CampaignMonitor.from_workspace(ROOT)
    exported = payload()
    assert exported['targets'] == {'weekly': 20, 'campaign': 160, 'weeks': 8}
    for row in exported['weekly_decisions']:
        expected = build_decision_snapshot(monitor.weekly, {**monitor.settings, 'current_week': row['week']})
        assert row == expected
        # Later observations cannot change the selected week's forecasting inputs/results.
        earlier = monitor.weekly.loc[monitor.weekly['week'] <= row['week']]
        assert row == build_decision_snapshot(earlier, {**monitor.settings, 'current_week': row['week']})


@pytest.mark.parametrize('patch', [
    {'minutes': 30.5}, {'minutes': '30'}, {'minutes': True},
    {'direction': ''}, {'direction': ['Data']}, {'scores': []},
    {'scores': {'strength_story': 1}},
])
def test_invalid_student_input_is_a_readable_400(patch):
    scores = dict(strength_story=1, role_direction=1, portfolio_evidence=0, verification=2, learning_plan=1, ask_for_help=1)
    value = {'minutes': 30, 'direction': 'Data', 'scores': scores, **patch}
    response = student_plan(RequestFactory().post('/api/student-plan', data=json.dumps(value), content_type='application/json'))
    assert response.status_code == 400
    assert json.loads(response.content)['error']


def test_learning_budget_and_focus_are_explicit():
    scores = dict(strength_story=1, role_direction=1, portfolio_evidence=0, verification=2, learning_plan=1, ask_for_help=1)
    response = student_plan(RequestFactory().post('/api/student-plan', data=json.dumps({'minutes': 10, 'direction': 'Data', 'scores': scores}), content_type='application/json'))
    result = json.loads(response.content)
    assert result['planned_minutes'] <= result['available_minutes'] == 10
    assert result['recommended_focus'][0] == 'Show one small project or artifact'


def test_student_plan_rejects_non_object_and_get():
    assert student_plan(RequestFactory().get('/api/student-plan')).status_code == 405
    assert student_plan(RequestFactory().post('/api/student-plan', data='null', content_type='application/json')).status_code == 400
