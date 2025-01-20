from django.shortcuts import render,redirect
from .models import* 
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import datetime
import face_recognition
import cv2
from twilio.rest import Client
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .forms import FaceForm, SignUpForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate

#Add yourr own credentials
account_sid = 'ACd51534a72eb42bd5d73535272f80b151'
auth_token = 'ee2f7888025199cd03b60172b906b701'
twilio_whatsapp_number = '+15705338319'

# Create your views here.
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def dashboard(request):
    return render(request,"dashboard.html")

def home(request):
    return render(request,"index.html")


def detect(request):
    video_capture = cv2.VideoCapture(0)
    
    # Initialize a flag to track if a face has been detected in the current video stream
    face_detected = False
    
    while True:
        ret, frame = video_capture.read()
        
        # Find face locations and encodings in the current frame
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        
        for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            # Compare detected face with stored face images
            for person in MissingPerson.objects.all():
                stored_image = face_recognition.load_image_file(person.image.path)
                stored_face_encoding = face_recognition.face_encodings(stored_image)[0]

                matches = face_recognition.compare_faces([stored_face_encoding], face_encoding)

                if any(matches):
                    name = person.first_name + " " + person.last_name
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

                    # Check if a face has already been detected in this video stream
                    if not face_detected:
                        print("Hi " + name + " is found")
                        
                        # Show success message
                        messages.success(request, f"{name} has been found successfully!")
                        face_detected = True  # Set the flag to True to indicate a face has been detected
                        break  # Break the loop once a match is found

            # If no match, mark as "Unknown"
            if not face_detected:
                name = "Unknown"
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # Display the resulting image
        cv2.imshow('Camera Feed', frame)

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    video_capture.release()
    cv2.destroyAllWindows()
    return render(request, "surveillance.html")


def surveillance(request):
    return render(request,"surveillance.html")


def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        father_name = request.POST.get('fathers_name')
        date_of_birth = request.POST.get('dob')
        address = request.POST.get('address')
        phone_number = request.POST.get('phonenum')
        aadhar_number = request.POST.get('aadhar_number')
        missing_from = request.POST.get('missing_date')
        email = request.POST.get('email')
        image = request.FILES.get('image')
        gender = request.POST.get('gender')
        aadhar = MissingPerson.objects.filter(aadhar_number=aadhar_number)
        
        if aadhar.exists():
            messages.info(request, 'Aadhar Number already exists')
            return redirect('/register')

        person = MissingPerson.objects.create(
            first_name=first_name,
            last_name=last_name,
            father_name=father_name,
            date_of_birth=date_of_birth,
            address=address,
            phone_number=phone_number,
            aadhar_number=aadhar_number,
            missing_from=missing_from,
            email=email,
            image=image,
            gender=gender,
        )
        person.save()
        
        # Show success message after registration
        messages.success(request, 'Case Registered Successfully')

    return render(request, "register.html")



def  missing(request):
    queryset = MissingPerson.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(aadhar_number__icontains=search_query)
    
    context = {'missingperson': queryset}
    return render(request,"missing.html",context)

def delete_person(request, person_id):
    person = get_object_or_404(MissingPerson, id=person_id)
    person.delete()
    return redirect('missing')  # Redirect to the missing view after deleting


def update_person(request, person_id):
    person = get_object_or_404(MissingPerson, id=person_id)

    if request.method == 'POST':
        # Retrieve data from the form with default values from the existing person instance
        first_name = request.POST.get('first_name', person.first_name)
        last_name = request.POST.get('last_name', person.last_name)
        father_name = request.POST.get('father_name', person.father_name)  # Correct field name
        date_of_birth = request.POST.get('date_of_birth', person.date_of_birth)  # Correct field name
        address = request.POST.get('address', person.address)
        email = request.POST.get('email', person.email)
        phone_number = request.POST.get('phone_number', person.phone_number)  # Correct field name
        aadhar_number = request.POST.get('aadhar_number', person.aadhar_number)
        missing_from = request.POST.get('missing_from', person.missing_from)  # Correct field name
        gender = request.POST.get('gender', person.gender)

        # Check if a new image is provided
        new_image = request.FILES.get('image')
        if new_image:
            person.image = new_image

        # Update the person instance
        person.first_name = first_name
        person.last_name = last_name
        person.father_name = father_name
        person.date_of_birth = date_of_birth
        person.address = address
        person.email = email
        person.phone_number = phone_number
        person.aadhar_number = aadhar_number
        person.missing_from = missing_from
        person.gender = gender

        # Save the changes
        person.save()

        return redirect('missing')  # Redirect to the missing view after editing

    return render(request, 'edit.html', {'person': person})
