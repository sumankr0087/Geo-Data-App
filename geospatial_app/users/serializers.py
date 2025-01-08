from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'user_name', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Save user with a hashed password
        validated_data['password'] = self.hash_password(validated_data['password'])
        return super().create(validated_data)

    def hash_password(self, password):
        from django.contrib.auth.hashers import make_password
        return make_password(password)

class LoginSerializer(serializers.Serializer):
    user_name = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        from django.contrib.auth.hashers import check_password
        try:
            user = User.objects.get(user_name=data['user_name'])
            if not check_password(data['password'], user.password):
                raise serializers.ValidationError("Invalid credentials")
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")
