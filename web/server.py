"""Small MVC delivery layer; all learning decisions stay in existing domain objects."""
import json
import os
from pathlib import Path
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from whitenoise import WhiteNoise
from sandai_artifacts.student_experience import READINESS_PROMPTS, StudentLearningProfile, StudentSeminarExperience

ROOT = Path(__file__).resolve().parent

@csrf_exempt
def student_plan(request):
    if request.method != 'POST':
        return JsonResponse({'error':'Use POST'}, status=405)
    try:
        value = json.loads(request.body)
        if not isinstance(value, dict):
            raise ValueError('Send a learning profile object')
        minutes = value['minutes']
        if type(minutes) is not int:
            raise ValueError('Choose a whole number of minutes')
        if minutes < 10 or minutes > 120:
            raise ValueError('Choose 10–120 minutes')
        direction = value['direction']
        if not isinstance(direction, str) or not direction.strip() or len(direction) > 300:
            raise ValueError('Enter a direction of 1–300 characters')
        scores = value['scores']
        if not isinstance(scores, dict) or set(scores) != set(READINESS_PROMPTS):
            raise ValueError('Review all six readiness areas')
        if any(type(score) is not int or score not in {0, 1, 2} for score in scores.values()):
            raise ValueError('Each readiness value must be 0, 1 or 2')
        profile = StudentLearningProfile('Participant', (), direction.strip(),
            'Build one explainable artifact', minutes, 'Worked example')
        experience = StudentSeminarExperience(profile, scores)
        plan = experience.weekly_plan()
        return JsonResponse({
            'plan': json.loads(plan.to_json(orient='records')),
            'recommended_focus': [READINESS_PROMPTS[key] for key in experience.focus_keys()],
            'planned_minutes': int(plan['Minutes'].sum()),
            'available_minutes': minutes,
        })
    except (ValueError, KeyError, TypeError) as error:
        return JsonResponse({'error':str(error)}, status=400)

urlpatterns = [path('api/student-plan', student_plan)]
if not settings.configured:
    settings.configure(DEBUG=False, SECRET_KEY=os.environ.get('DJANGO_SECRET_KEY','stateless-demo-no-auth'),
        ROOT_URLCONF=__name__, ALLOWED_HOSTS=['*'], MIDDLEWARE=[], DATA_UPLOAD_MAX_MEMORY_SIZE=16384)
application = WhiteNoise(get_wsgi_application(), root=ROOT/'dist', index_file=True)
