"""Behavior checks for the notebook interaction layer."""
from sandai_artifacts import StudentLearningProfile, StudentSeminarExperience
from sandai_artifacts.presentation import StudentWorkshopView, cards, pathway


def experience(minutes=5):
    return StudentSeminarExperience(StudentLearningProfile('Participant', (), 'Education', 'Check a claim', minutes, 'Checklist'),
        dict(strength_story=1, role_direction=1, portfolio_evidence=0, verification=1, learning_plan=1, ask_for_help=1))


def test_focus_override_and_short_time_budget():
    workshop = StudentWorkshopView(experience(), focus='Checking AI')
    workshop.plan()
    assert workshop.minutes == 5
    assert 'claim' in workshop.action
    assert workshop.action.startswith('Begin a small part')
    assert 'one useful sentence' in workshop.finish


def test_empty_review_never_becomes_completed():
    workshop = StudentWorkshopView(experience())
    workshop.takeaway('', 'evidence', 'keep', 'change', 'reason', completed=True)
    assert not workshop.ready


def test_custom_prompt_and_response_are_preserved():
    workshop = StudentWorkshopView(experience(), scenario='Teaching/education')
    workshop.practice('My prompt', 'My response')
    assert workshop.prompt == 'My prompt'
    workshop.takeaway('assumption', 'evidence', 'keep', 'change', 'reason', completed=True)
    assert workshop.ready
    assert 'teaching/education' in workshop.bullet


def test_student_text_is_rendered_as_text():
    assert '&lt;script&gt;' in cards([('Example', '<script>')]).data


def test_pathway_marks_position_without_color_only():
    html = pathway([('Reflect', 'Begin'), ('Practice', 'Try')], active=1).data
    assert 'YOU ARE HERE' in html
    assert 'Practice' in html


def test_review_feedback_does_not_set_completion_state():
    workshop = StudentWorkshopView(experience())
    workshop.check_feedback('a', 'b', 'c', 'd', 'e', completed=True)
    assert not hasattr(workshop, 'ready')
