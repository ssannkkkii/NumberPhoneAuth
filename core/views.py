from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import PhoneOTP, CustomUser
from .serializers import SendOTPSerializer, VerifyOTPSerializer, UserProfileSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ObjectDoesNotExist

class SendOTPView(APIView):
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone_number']

        otp_obj, created = PhoneOTP.objects.get_or_create(phone_number=phone)
        otp_obj.generate_otp()

        print(f"[DEBUG] OTP for {phone}: {otp_obj.otp}")

        return Response({'message': 'OTP sent successfully.'}, status=200)

class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone_number']
        otp = serializer.validated_data['otp']

        try:
            otp_obj = PhoneOTP.objects.get(phone_number=phone)
        except ObjectDoesNotExist:
            return Response({'error': 'OTP not requested.'}, status=400)

        if otp_obj.is_expired():
            otp_obj.delete()
            return Response({'error': 'OTP expired.'}, status=400)

        if otp_obj.otp != otp:
            return Response({'error': 'Invalid OTP.'}, status=400)

        user, created = CustomUser.objects.get_or_create(phone_number=phone)
        otp_obj.delete()

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
        }, status=200)

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
