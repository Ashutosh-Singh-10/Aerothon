from django.shortcuts import render
from email.message import  EmailMessage
import ssl
import smtplib
import random


from django.http import JsonResponse,HttpResponseRedirect,HttpRequest
from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework import status 
from rest_framework.parsers import MultiPartParser
from rest_framework.reverse import reverse
from django.db.models import Q


from .models import *
from .serializers import *
from userprofile.models import *
from rest_framework_simplejwt.authentication import JWTAuthentication 

from rest_framework.views import APIView
from rest_framework.response import Response
# from datetime import datetime
import datetime
import pytz
utc=pytz.UTC



from rest_framework_simplejwt.views import(
    TokenObtainPairView,
    TokenRefreshView,
)



def sendMail(email_receiver,otp):
    email_sender="ashutoshsinghas2409@gmail.com"
    email_password='ueflvrqkwtmeggpp'
    subject="OTP generation"
    body="Your otp for registration is "+str(otp)
    em=EmailMessage()
    em["From"]=email_sender
    em["To"]=email_receiver
    em['Subject']=subject
    em.set_content(body)
    context=ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
        smtp.login(email_sender,email_password)
        smtp.sendmail(email_sender,email_receiver,em.as_string())




class OTPView(APIView):
    def post(self,request):
        if "email" in request.data:
            email=request.data["email"]
        else:
            return Response({"message":"Please enter a valid email"},status=status.HTTP_400_BAD_REQUEST)
        obj=User.objects.filter(email=email).first()
        if obj:
            return Response({"message":"User already exist with this email"},status=status.HTTP_406_NOT_ACCEPTABLE)
        otp=random.randint(100000,999999)
        try:
            sendMail(email,otp)

            data={"email":email,"otp":otp}
            otpObj=OTP.objects.filter(email=email).first()
            if otpObj:
                otpObj.otp=otp
                otpObj.save()
            else:
                serializer=OTPSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
        except:
            return Response({"message":"Email is unvalid or try after sometime"},status=status.HTTP_400_BAD_REQUEST)
        return Response({"otp":otp})

class CreateUserView(APIView):
    def post(self,request):
        if "email" not in request.data and "otp" not in request.data or "username" not in request.data:
            return Response({"message":"can not create the user without the email"})
        email=request.data["email"]
        userobj=User.objects.filter(Q(username=request.data["username"]) | Q(email=email)).first()
        if userobj:
            return Response({"message":"user with this email or username already exist"})
        otp=request.data["otp"]
        otpObj=OTP.objects.filter(email=email).first()
        if not otpObj:
            return Response({"message":"otp has not been generated yet."})
        if otpObj.otp!=otp:
            return Response({"message":"the otp is wrong"})
        now=datetime.datetime.now(tz=utc)
        delta=datetime.timedelta(minutes=5)
        if now-otpObj.generatedAt>delta:
            return Response({"message":"Otp has been expoired"})


        user=UserSerializer(data=request.data)        
        if  user.is_valid():
            userobj=user.save()
            userobj.set_password(request.data["password"])
            userobj.save()
            profileObj=UserProfile(profileuser=userobj)
            profileObj.save()
            return Response()
        else :
            return Response({"message":"Something went wrong"},status=status.HTTP_406_NOT_ACCEPTABLE)

            
class DeleteUserView(APIView):
    authentication_classes=[JWTAuthentication]
    def post(self,request):
        user=request.user
        if user:
            user.delete()
            return Response()
        return Response(status=status.HTTP_403_FORBIDDEN)
        
  
