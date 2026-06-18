from celery import shared_task
from .models import ScrapeTask, Job, UserProfile
from django.utils import timezone
import time
import google.generativeai as genai
import os
import json

@shared_task
def fetch_jobs_from_apify_task(task_id=None):
    if not task_id:
        task = ScrapeTask.objects.create(status='RUNNING')
    else:
        task = ScrapeTask.objects.get(id=task_id)
        task.status = 'RUNNING'
        task.save()
        
    try:
        # Mocking the Apify call for now since we don't have API keys set yet
        print("Starting Apify Job Scrape...")
        time.sleep(2) # Simulate network call
        
        # Mock result
        mock_jobs = [
            {
                'external_id': 'mock-1',
                'title': 'Frontend Developer',
                'company': 'Tech Corp',
                'location': 'Remote',
                'employment_type': 'Full-time',
                'salary': '$100k - $120k',
                'skills_required': ['React', 'TypeScript', 'Next.js'],
                'description': 'We are looking for a frontend developer...',
                'apply_url': 'https://example.com/apply/1',
                'posted_date': timezone.now()
            },
            {
                'external_id': 'mock-2',
                'title': 'Backend Developer',
                'company': 'Data Inc',
                'location': 'New York, NY',
                'employment_type': 'Full-time',
                'salary': '$130k - $150k',
                'skills_required': ['Python', 'Django', 'PostgreSQL'],
                'description': 'We need a backend expert...',
                'apply_url': 'https://example.com/apply/2',
                'posted_date': timezone.now()
            }
        ]
        
        added_count = 0
        for job_data in mock_jobs:
            job, created = Job.objects.get_or_create(
                external_id=job_data['external_id'],
                defaults=job_data
            )
            if created:
                added_count += 1
                
        task.status = 'COMPLETED'
        task.jobs_added = added_count
        task.completed_at = timezone.now()
        task.save()
        
    except Exception as e:
        task.status = 'FAILED'
        task.error_message = str(e)
        task.completed_at = timezone.now()
        task.save()

@shared_task
def parse_resume_task(profile_id, resume_text):
    try:
        profile = UserProfile.objects.get(id=profile_id)
        # In a real app we'd fetch the file from profile.resume_url and extract text
        
        # Mocking the LLM parsing
        print(f"Parsing resume for profile {profile_id}...")
        
        # Attempt to use Gemini if key exists
        api_key = os.environ.get('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Parse the following resume into JSON with keys: skills (list), experience (list of dicts), education (list of dicts). Resume: {resume_text}"
            response = model.generate_content(prompt)
            # Basic parsing of the response text assuming it's valid JSON for now
            try:
                parsed_data = json.loads(response.text.replace('```json', '').replace('```', ''))
                profile.extracted_skills = parsed_data.get('skills', [])
                profile.experience = parsed_data.get('experience', [])
                profile.education = parsed_data.get('education', [])
                profile.save()
            except json.JSONDecodeError:
                pass
        else:
            # Fallback mock
            profile.extracted_skills = ["Python", "Django", "React", "Next.js"]
            profile.experience = [{"title": "Software Engineer", "company": "MockCompany", "duration": "2 years"}]
            profile.education = [{"degree": "B.S. Computer Science", "school": "Mock University"}]
            profile.save()
            
    except Exception as e:
        print(f"Error parsing resume: {str(e)}")
