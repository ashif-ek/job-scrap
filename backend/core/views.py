from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import User, UserProfile, Job, ApplicationTracker, ScrapeTask
from .serializers import UserSerializer, UserProfileSerializer, JobSerializer, ApplicationTrackerSerializer, ScrapeTaskSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import google.generativeai as genai
import os

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        
        if not username or not password or not email:
            return Response({'error': 'Please provide username, password and email'}, status=status.HTTP_400_BAD_REQUEST)
            
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
        
    def get_object(self):
        return self.request.user.profile

class JobViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Job.objects.all().order_by('-posted_date')
    serializer_class = JobSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Basic filtering
        role = self.request.query_params.get('role', None)
        location = self.request.query_params.get('location', None)
        if role:
            queryset = queryset.filter(title__icontains=role)
        if location:
            queryset = queryset.filter(location__icontains=location)
        return queryset

class ApplicationTrackerViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApplicationTrackerSerializer

    def get_queryset(self):
        return ApplicationTracker.objects.filter(user=self.request.user).order_by('-updated_at')

    @action(detail=True, methods=['post'])
    def generate_cover_letter(self, request, pk=None):
        application = self.get_object()
        job = application.job
        profile = request.user.profile
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return Response({'error': 'AI API key not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Write a professional and engaging cover letter for the following job.
            
            Job Title: {job.title}
            Company: {job.company}
            Job Description: {job.description}
            
            Applicant Skills: {', '.join(profile.extracted_skills)}
            Applicant Experience: {profile.experience}
            
            The cover letter should highlight how the applicant's specific skills and experience match the job requirements. Keep it concise, under 400 words.
            """
            
            response = model.generate_content(prompt)
            cover_letter_text = response.text
            
            application.generated_cover_letter = cover_letter_text
            application.save()
            
            return Response({'cover_letter': cover_letter_text})
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

