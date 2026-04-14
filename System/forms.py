from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Course, Material, Meeting, Enrollment, Exam, Question


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الأول'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم العائلة'}))
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المستخدم'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'كلمة المرور'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'تأكيد كلمة المرور'})


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المستخدم'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'كلمة المرور'}))


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'thumbnail', 'price', 'is_free', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الكورس'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'وصف الكورس'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['title', 'material_type', 'file', 'url', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان المادة'}),
            'material_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['title', 'description', 'scheduled_at', 'duration_minutes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الاجتماع'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_picture', 'phone','payment_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_number': forms.TextInput(attrs={'class': 'form-control'}),

        }

class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['payment_receipt']
        labels = {
            'payment_receipt': 'صورة إيصال التحويل (فودافون كاش، انستا باي، إلخ...)'
        }
        widgets = {
            'payment_receipt': forms.ClearableFileInput(attrs={'class': 'form-control', 'required': 'required'})
        }

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'description', 'duration_minutes', 'pass_score', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الامتحان'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'وصف الامتحان (اختياري)'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'pass_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'عنوان الامتحان',
            'description': 'الوصف',
            'duration_minutes': 'المدة (دقائق)',
            'pass_score': 'درجة النجاح (%)',
            'is_published': 'نشر الامتحان',
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'marks', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'نص السؤال'}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'option_a': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاختيار أ'}),
            'option_b': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاختيار ب'}),
            'option_c': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاختيار ج'}),
            'option_d': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاختيار د'}),
            'correct_answer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: A أو true'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        labels = {
            'text': 'نص السؤال',
            'question_type': 'نوع السؤال',
            'option_a': 'الاختيار أ',
            'option_b': 'الاختيار ب',
            'option_c': 'الاختيار ج',
            'option_d': 'الاختيار د',
            'correct_answer': 'الإجابة الصحيحة',
            'marks': 'الدرجة',
            'order': 'الترتيب',
        }


from .models import SupportTicket, SupportMessage

class SupportTicketForm(forms.ModelForm):
    first_message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'اكتب رسالتك هنا...'}),
        label='الرسالة'
    )

    class Meta:
        model = SupportTicket
        fields = ['subject']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'موضوع الرسالة'}),
        }
        labels = {
            'subject': 'الموضوع',
        }


class SupportReplyForm(forms.ModelForm):
    class Meta:
        model = SupportMessage
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'اكتب ردك هنا...'}),
        }
        labels = {
            'body': 'الرد',
        }
