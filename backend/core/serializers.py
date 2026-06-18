from rest_framework import serializers
from .models import User, UserProfile, Job, ApplicationTracker, ScrapeTask

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['resume_url', 'extracted_skills', 'experience', 'education', 'projects', 'location_preferences', 'role_preferences']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'

class ApplicationTrackerSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all(), source='job', write_only=True)

    class Meta:
        model = ApplicationTracker
        fields = ['id', 'job', 'job_id', 'status', 'generated_cover_letter', 'applied_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ScrapeTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapeTask
        fields = '__all__'
