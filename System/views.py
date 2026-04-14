from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum,Avg
from .models import (CustomUser, Course, Material, MaterialView, Enrollment,
                     Meeting, MeetingParticipant, Notification,
                     Exam, Question, ExamAttempt, StudentAnswer,
                     SupportTicket, SupportMessage)
from .forms import (RegisterForm, LoginForm, CourseForm, MaterialForm,
                    MeetingForm, ProfileForm, PaymentProofForm,
                    ExamForm, QuestionForm, SupportTicketForm, SupportReplyForm)
from django.http import Http404
# ─── Auth Views ────────────────────────────────────────────────────────────────

def home(request):
    courses = Course.objects.filter(is_published=True).order_by('-created_at')[:6]
    teachers = CustomUser.objects.filter(role='teacher')[:4]
    return render(request, 'System/home.html', {'courses': courses, 'teachers': teachers})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'مرحباً {user.get_full_name()}! تم إنشاء حسابك بنجاح.')
        return redirect('dashboard')
    return render(request, 'System/auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'System/auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    if user.is_admin_user():
        courses = Course.objects.all().order_by('-created_at')[:5]
        total_students = CustomUser.objects.filter(role='student').count()
        total_teachers = CustomUser.objects.filter(role='teacher').count()
        total_courses = Course.objects.count()
        pending_enrollments = Enrollment.objects.filter(status='pending')
        open_tickets = SupportTicket.objects.filter(status='open').count()
        ctx = {
            'courses': courses,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_courses': total_courses,
            'pending_enrollments': pending_enrollments,
            'open_tickets': open_tickets,
        }
    elif user.is_teacher():
        courses = Course.objects.filter(teacher=user)
        upcoming_meetings = Meeting.objects.filter(teacher=user, status__in=['scheduled', 'live']).order_by('scheduled_at')[:5]
        
        # التعديل هنا: إضافة status='approved' لعد الطلاب المقبولين فقط
        total_students = Enrollment.objects.filter(course__teacher=user, status='approved').values('student').distinct().count()
        
        # جلب الطلبات المعلقة للمدرس
        pending_enrollments = Enrollment.objects.filter(course__teacher=user, status='pending')
        ctx = {
            'courses': courses,
            'upcoming_meetings': upcoming_meetings,
            'total_students': total_students,
            'pending_enrollments': pending_enrollments,
        }
    else:
        enrollments = Enrollment.objects.filter(student=user, is_active=True).select_related('course')
        enrolled_courses = [e.course for e in enrollments]
        upcoming_meetings = Meeting.objects.filter(course__in=enrolled_courses, status__in=['scheduled', 'live']).order_by('scheduled_at')[:5]
        ctx = {
            'enrollments': enrollments,
            'upcoming_meetings': upcoming_meetings,
        }
    notifications = Notification.objects.filter(user=user, is_read=False)[:5]
    ctx['notifications'] = notifications
    return render(request, 'System/dashboard.html', ctx)


# ─── Course Views ───────────────────────────────────────────────────────────────

def course_list(request):
    q = request.GET.get('q', '')
    courses = Course.objects.filter(is_published=True)
    if q:
        courses = courses.filter(Q(title__icontains=q) | Q(description__icontains=q))
    return render(request, 'System/courses/list.html', {'courses': courses, 'query': q})


def course_detail(request, pk):
    # 1. نجيب الكورس بغض النظر هو منشور ولا لأ
    course = get_object_or_404(Course, pk=pk)
    
    # 2. لو الكورس مش منشور، نمنع أي حد يشوفه ما عدا المدرس صاحب الكورس
    if not course.is_published and request.user != course.teacher:
        messages.error(request, 'هذا الكورس غير متاح حالياً.')
        return redirect('course_list') # أو ممكن ترجعه للـ dashboard

    # تهيئة المتغيرات (باقي الكود بتاعك زي ما هو بالظبط من أول هنا)
    is_enrolled = False
    enrollment_status = None
    viewed_material_ids = set()
    attempted_exam_ids = set()
    
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        if enrollment:
            enrollment_status = enrollment.status
            is_enrolled = (enrollment_status == 'approved')
        
        if is_enrolled:
            viewed_material_ids = set(
                MaterialView.objects.filter(
                    student=request.user, material__course=course
                ).values_list('material_id', flat=True)
            )
            attempted_exam_ids = set(
                ExamAttempt.objects.filter(
                    student=request.user, exam__course=course, submitted_at__isnull=False
                ).values_list('exam_id', flat=True)
            )
            
    materials = course.materials.all() if is_enrolled or request.user == course.teacher else []
    meetings = course.meetings.filter(status__in=['scheduled', 'live']).order_by('scheduled_at')
    exams = course.exams.filter(is_published=True) if is_enrolled else (
        course.exams.all() if request.user == course.teacher else []
    )
    
    return render(request, 'System/courses/detail.html', {
        'course': course,
        'is_enrolled': is_enrolled,
        'enrollment_status': enrollment_status,
        'materials': materials,
        'meetings': meetings,
        'exams': exams,
        'viewed_material_ids': viewed_material_ids,
        'attempted_exam_ids': attempted_exam_ids,
    })


@login_required
def course_create(request):
    if not request.user.is_teacher():
        messages.error(request, 'فقط المدرسون يمكنهم إنشاء كورسات.')
        return redirect('dashboard')
    form = CourseForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        course = form.save(commit=False)
        course.teacher = request.user
        course.save()
        messages.success(request, 'تم إنشاء الكورس بنجاح!')
        return redirect('course_detail', pk=course.pk)
    return render(request, 'System/courses/form.html', {'form': form, 'action': 'إنشاء'})


@login_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk, teacher=request.user)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم تحديث الكورس.')
        return redirect('course_detail', pk=course.pk)
    return render(request, 'System/courses/form.html', {'form': form, 'action': 'تعديل', 'course': course})


@login_required
def enroll(request, pk):
    course = get_object_or_404(Course, pk=pk, is_published=True)
    
    if request.user.is_teacher():
        messages.error(request, 'المدرسون لا يمكنهم الاشتراك في الكورسات.')
        return redirect('course_detail', pk=pk)

    existing_enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    
    if existing_enrollment:
        if existing_enrollment.status == 'pending':
            messages.info(request, 'طلب اشتراكك قيد المراجعة من قبل المدرس.')
            return redirect('course_detail', pk=pk)
        elif existing_enrollment.status == 'approved':
            messages.info(request, 'أنت مشترك بالفعل في هذا الكورس.')
            return redirect('course_detail', pk=pk)

    if course.is_free or course.price == 0:
        if existing_enrollment and existing_enrollment.status == 'rejected':
            existing_enrollment.status = 'approved'
            existing_enrollment.is_active = True
            existing_enrollment.save()
        else:
            Enrollment.objects.create(student=request.user, course=course, status='approved', is_active=True)
        messages.success(request, f'تم الاشتراك في "{course.title}" بنجاح!')
        return redirect('course_detail', pk=pk)

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            if existing_enrollment and existing_enrollment.status == 'rejected':
                existing_enrollment.payment_receipt = form.cleaned_data['payment_receipt']
                existing_enrollment.status = 'pending'
                existing_enrollment.save()
            else:
                enrollment = form.save(commit=False)
                enrollment.student = request.user
                enrollment.course = course
                enrollment.status = 'pending'
                enrollment.is_active = False
                enrollment.save()

            Notification.objects.create(
                user=course.teacher,
                title='طلب اشتراك جديد',
                message=f'الطالب {request.user.get_full_name()} رفع إيصال دفع لكورس "{course.title}"',
                link='/dashboard/' 
            )
            messages.success(request, 'تم رفع الإيصال بنجاح. في انتظار موافقة المدرس.')
            return redirect('course_detail', pk=pk)
    else:
        form = PaymentProofForm()

    return render(request, 'System/courses/payment.html', {'course': course, 'form': form})


@login_required
def approve_enrollment(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, pk=enrollment_id, course__teacher=request.user)
    action = request.GET.get('action')

    if action == 'approve':
        enrollment.status = 'approved'
        enrollment.is_active = True
        enrollment.save()
        messages.success(request, f'تم قبول الطالب {enrollment.student.get_full_name()} بنجاح.')
        Notification.objects.create(
            user=enrollment.student,
            title='تم قبول اشتراكك!',
            message=f'تم قبول اشتراكك في كورس "{enrollment.course.title}"',
            link=f'/courses/{enrollment.course.pk}/'
        )
    elif action == 'reject':
        enrollment.status = 'rejected'
        enrollment.is_active = False
        enrollment.save()
        messages.error(request, 'تم رفض طلب الاشتراك.')
        Notification.objects.create(
            user=enrollment.student,
            title='تم رفض اشتراكك',
            message=f'عذراً، تم رفض إيصال الدفع لكورس "{enrollment.course.title}". يرجى مراجعة الإيصال ورفعه مرة أخرى.',
        )

    return redirect('dashboard')


# ─── Material Views ─────────────────────────────────────────────────────────────

@login_required
def material_add(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, teacher=request.user)
    form = MaterialForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        material = form.save(commit=False)
        material.course = course
        material.save()
        messages.success(request, 'تم إضافة المادة بنجاح!')
        return redirect('course_detail', pk=course_pk)
    return render(request, 'System/materials/form.html', {'form': form, 'course': course})


@login_required
def track_material_view(request, pk):
    """تسجيل فتح الطالب للمادة"""
    material = get_object_or_404(Material, pk=pk)
    # تحقق أن الطالب مشترك في الكورس
    is_enrolled = Enrollment.objects.filter(
        student=request.user, course=material.course, status='approved'
    ).exists()
    is_teacher = material.course.teacher == request.user

    if not is_enrolled and not is_teacher:
        return JsonResponse({'status': 'error', 'message': 'غير مصرح'}, status=403)

    if is_enrolled:
        obj, created = MaterialView.objects.get_or_create(
            material=material, student=request.user
        )
        return JsonResponse({'status': 'ok', 'first_time': created})

    return JsonResponse({'status': 'ok', 'first_time': False})


@login_required
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk, course__teacher=request.user)
    course_pk = material.course.pk
    material.delete()
    messages.success(request, 'تم حذف المادة.')
    return redirect('course_detail', pk=course_pk)


# ─── Meeting Views ──────────────────────────────────────────────────────────────

@login_required
def meeting_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, teacher=request.user)
    form = MeetingForm(request.POST or None)
    if form.is_valid():
        meeting = form.save(commit=False)
        meeting.course = course
        meeting.teacher = request.user
        meeting.save()
        for enrollment in course.enrollments.filter(is_active=True):
            Notification.objects.create(
                user=enrollment.student,
                title='اجتماع جديد!',
                message=f'المدرس {request.user.get_full_name()} أضاف اجتماعاً جديداً: "{meeting.title}"',
                link=f'/meetings/{meeting.pk}/'
            )
        messages.success(request, 'تم إنشاء الاجتماع بنجاح!')
        return redirect('meeting_room', pk=meeting.pk)
    return render(request, 'System/meetings/form.html', {'form': form, 'course': course})


@login_required
def meeting_room(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    user = request.user
    is_teacher = meeting.teacher == user
    
    # منع الطلاب من دخول اجتماع منتهي
    if meeting.status == 'ended' and not is_teacher:
        messages.error(request, 'هذا الاجتماع قد انتهى.')
        return redirect('course_detail', pk=meeting.course.pk)

    # التحقق من الاشتراك (للطلاب فقط)
    is_enrolled = Enrollment.objects.filter(student=user, course=meeting.course, status='approved').exists()
    if not is_teacher and not is_enrolled:
        messages.error(request, 'يجب الاشتراك في الكورس للانضمام للاجتماع.')
        return redirect('course_detail', pk=meeting.course.pk)
    
    # تسجيل دخول المشارك (سواء مدرس أو طالب)
    if meeting.status == 'live' or is_teacher:
        MeetingParticipant.objects.get_or_create(meeting=meeting, user=user)
    
    # تحسين: إذا دخل المدرس، نجعل الاجتماع "مباشر" تلقائياً
    if is_teacher and meeting.status == 'scheduled':
        meeting.status = 'live'
        meeting.save()
        
    participants = meeting.participants.select_related('user').all()
    return render(request, 'System/meetings/room.html', {
        'meeting': meeting,
        'is_teacher': is_teacher,
        'participants': participants,
    })


@login_required
def meeting_end(request, pk):
    # نتحقق أن المدرس هو صاحب الاجتماع
    meeting = get_object_or_404(Meeting, pk=pk, teacher=request.user)
    meeting.status = 'ended'
    meeting.save()
    
    # تحديث وقت الخروج لكل المشاركين
    MeetingParticipant.objects.filter(meeting=meeting, left_at__isnull=True).update(left_at=timezone.now())
    
    return JsonResponse({'status': 'success', 'message': 'Meeting ended'})


# ─── Profile ────────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم تحديث الملف الشخصي.')
        return redirect('profile')
    return render(request, 'System/profile.html', {'form': form})


def teacher_profile(request, pk):
    teacher = get_object_or_404(CustomUser, pk=pk, role='teacher')
    courses = Course.objects.filter(teacher=teacher, is_published=True)
    return render(request, 'System/teacher_profile.html', {'teacher': teacher, 'courses': courses})


# ─── Notifications ──────────────────────────────────────────────────────────────

@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'ok'})

@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        # تحويل كل إشعارات اليوزر الغير مقروءة إلى مقروءة
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# ─── Exam Views ─────────────────────────────────────────────────────────────────

@login_required
def exam_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, teacher=request.user)
    form = ExamForm(request.POST or None)
    if form.is_valid():
        exam = form.save(commit=False)
        exam.course = course
        exam.save()
        messages.success(request, 'تم إنشاء الامتحان! يمكنك الآن إضافة الأسئلة.')
        return redirect('exam_edit', pk=exam.pk)
    return render(request, 'System/exams/create.html', {'form': form, 'course': course})


@login_required
def exam_edit(request, pk):
    exam = get_object_or_404(Exam, pk=pk, course__teacher=request.user)
    form = ExamForm(request.POST or None, instance=exam)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ التعديلات.')
        return redirect('exam_edit', pk=exam.pk)
    questions = exam.questions.all()
    return render(request, 'System/exams/edit.html', {
        'exam': exam, 'form': form, 'questions': questions
    })


@login_required
def question_add(request, exam_pk):
    exam = get_object_or_404(Exam, pk=exam_pk, course__teacher=request.user)
    form = QuestionForm(request.POST or None)
    if form.is_valid():
        q = form.save(commit=False)
        q.exam = exam
        q.save()
        messages.success(request, 'تم إضافة السؤال بنجاح!')
        return redirect('exam_edit', pk=exam.pk)
    return render(request, 'System/exams/question_form.html', {
        'form': form, 'exam': exam, 'action': 'إضافة'
    })


@login_required
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk, exam__course__teacher=request.user)
    exam_pk = question.exam.pk
    question.delete()
    messages.success(request, 'تم حذف السؤال.')
    return redirect('exam_edit', pk=exam_pk)


@login_required
def exam_take(request, pk):
    """الطالب يأخذ الامتحان"""
    exam = get_object_or_404(Exam, pk=pk, is_published=True)
    student = request.user

    if not student.is_student():
        messages.error(request, 'فقط الطلاب يمكنهم أداء الامتحانات.')
        return redirect('course_detail', pk=exam.course.pk)

    is_enrolled = Enrollment.objects.filter(
        student=student, course=exam.course, status='approved'
    ).exists()
    if not is_enrolled:
        messages.error(request, 'يجب الاشتراك في الكورس أولاً.')
        return redirect('course_detail', pk=exam.course.pk)

    # هل الطالب خضع للامتحان من قبل؟
    existing_attempt = ExamAttempt.objects.filter(exam=exam, student=student).first()
    if existing_attempt and existing_attempt.submitted_at:
        messages.info(request, 'لقد أديت هذا الامتحان من قبل.')
        return redirect('exam_result', pk=existing_attempt.pk)

    questions = exam.questions.all()
    if not questions:
        messages.error(request, 'هذا الامتحان لا يحتوي على أسئلة بعد.')
        return redirect('course_detail', pk=exam.course.pk)

    if request.method == 'POST':
        attempt, _ = ExamAttempt.objects.get_or_create(exam=exam, student=student)
        attempt.answers.all().delete()
        
        score = 0
        total_marks = exam.get_total_marks()

        for question in questions:
            answer_key = f'q_{question.pk}'
            given_answer = request.POST.get(answer_key, '').strip().upper()
            correct = question.correct_answer.strip().upper()
            is_correct = given_answer == correct
            if is_correct:
                score += question.marks
            StudentAnswer.objects.create(
                attempt=attempt,
                question=question,
                answer=given_answer,
                is_correct=is_correct
            )

        attempt.score = score
        attempt.total_marks = total_marks
        attempt.percentage = round((score / total_marks) * 100, 2) if total_marks > 0 else 0
        attempt.passed = attempt.percentage >= exam.pass_score
        attempt.submitted_at = timezone.now()
        attempt.save()

        # إشعار للمدرس
        Notification.objects.create(
            user=exam.course.teacher,
            title='طالب أدى الامتحان',
            message=f'الطالب {student.get_full_name()} أدى امتحان "{exam.title}" وحصل على {attempt.percentage}%',
            link=f'/courses/{exam.course.pk}/'
        )
        messages.success(request, f'تم تسليم الامتحان! حصلت على {attempt.percentage}%')
        return redirect('exam_result', pk=attempt.pk)

    # إنشاء محاولة جديدة إذا لم تكن موجودة
    attempt, _ = ExamAttempt.objects.get_or_create(
        exam=exam, student=student,
        defaults={'started_at': timezone.now()}
    )

    return render(request, 'System/exams/take.html', {
        'exam': exam, 'questions': questions
    })


@login_required
def exam_result(request, pk):
    """نتيجة الامتحان"""
    attempt = get_object_or_404(ExamAttempt, pk=pk)
    if attempt.student != request.user and attempt.exam.course.teacher != request.user:
        messages.error(request, 'غير مصرح.')
        return redirect('dashboard')
    answers = attempt.answers.select_related('question').all()
    return render(request, 'System/exams/result.html', {
        'attempt': attempt, 'answers': answers
    })


# ─── Student Grades ─────────────────────────────────────────────────────────────

@login_required
def student_grades(request):
    """سجل درجات الطالب"""
    if not request.user.is_student():
        messages.error(request, 'هذه الصفحة للطلاب فقط.')
        return redirect('dashboard')
    
    attempts = ExamAttempt.objects.filter(
        student=request.user,
        submitted_at__isnull=False
    ).select_related('exam', 'exam__course').order_by('-submitted_at')

    # حساب عدد الامتحانات التي اجتازها الطالب بنجاح
    passed_count = attempts.filter(passed=True).count()
    
    # حساب متوسط الدرجات (النسبة المئوية)
    avg_score = attempts.aggregate(Avg('percentage'))['percentage__avg']
    average_score = round(avg_score, 1) if avg_score else 0

    return render(request, 'System/grades.html', {
        'attempts': attempts,
        'passed_count': passed_count,
        'average_score': average_score
    })


# ─── Teacher Students List ───────────────────────────────────────────────────────

@login_required
def teacher_students(request):
    """قائمة طلاب المدرس"""
    if not request.user.is_teacher():
        messages.error(request, 'هذه الصفحة للمدرسين فقط.')
        return redirect('dashboard')
    
    course_filter = request.GET.get('course', '')
    enrollments = Enrollment.objects.filter(
        course__teacher=request.user, status='approved'
    ).select_related('student', 'course').order_by('course', 'student__first_name')

    if course_filter:
        enrollments = enrollments.filter(course__pk=course_filter)

    teacher_courses = Course.objects.filter(teacher=request.user)

    # إضافة معلومات المواد المفتوحة لكل طالب
    students_data = []
    seen = set()
    for enrollment in enrollments:
        key = (enrollment.student.pk, enrollment.course.pk)
        if key not in seen:
            seen.add(key)
            
            # 1. حساب تقدم مشاهدة المواد
            viewed_count = MaterialView.objects.filter(
                student=enrollment.student,
                material__course=enrollment.course
            ).count()
            total_materials = enrollment.course.materials.count()
            
            # 2. حساب درجات الامتحانات للطالب في هذا الكورس
            exam_attempts = ExamAttempt.objects.filter(
                student=enrollment.student,
                exam__course=enrollment.course,
                submitted_at__isnull=False
            )
            
            # حساب متوسط الدرجات
            avg_exam_score = exam_attempts.aggregate(Avg('percentage'))['percentage__avg']
            average_score = round(avg_exam_score, 1) if avg_exam_score else None

            students_data.append({
                'enrollment': enrollment,
                'viewed_count': viewed_count,
                'total_materials': total_materials,
                'exam_attempts_count': exam_attempts.count(),  # عدد الامتحانات التي خاضها
                'average_score': average_score,               # متوسط درجاته
            })

    return render(request, 'System/teacher_students.html', {
        'students_data': students_data,
        'teacher_courses': teacher_courses,
        'course_filter': course_filter,
    })


# ─── Support Views ──────────────────────────────────────────────────────────────

@login_required
def support_list(request):
    """قائمة تذاكر الدعم الفني"""
    user = request.user
    if user.is_admin_user():
        # الأدمن يشوف كل التذاكر
        tickets = SupportTicket.objects.all().select_related('user').order_by('-updated_at')
    else:
        # الطالب والمدرس يشوفوا تذاكرهم بس
        tickets = SupportTicket.objects.filter(user=user).order_by('-updated_at')
    return render(request, 'System/support/list.html', {'tickets': tickets})


@login_required
def support_create(request):
    """فتح تذكرة دعم فني جديدة"""
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            # حفظ أول رسالة
            SupportMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                body=form.cleaned_data['first_message'],
                is_admin_reply=False
            )
            messages.success(request, 'تم إرسال رسالتك للدعم الفني بنجاح!')
            return redirect('support_detail', pk=ticket.pk)
    else:
        form = SupportTicketForm()
    return render(request, 'System/support/create.html', {'form': form})


@login_required
def support_detail(request, pk):
    """تفاصيل تذكرة الدعم الفني"""
    user = request.user
    if user.is_admin_user():
        ticket = get_object_or_404(SupportTicket, pk=pk)
    else:
        ticket = get_object_or_404(SupportTicket, pk=pk, user=user)

    if request.method == 'POST':
        form = SupportReplyForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ticket = ticket
            msg.sender = user
            msg.is_admin_reply = user.is_admin_user()
            msg.save()

            # تحديث حالة التذكرة
            if user.is_admin_user():
                ticket.status = 'answered'
                ticket.save()
                # إشعار للمستخدم صاحب التذكرة
                Notification.objects.create(
                    user=ticket.user,
                    title='رد جديد من الدعم الفني',
                    message=f'تم الرد على تذكرتك: "{ticket.subject}"',
                    link=f'/support/{ticket.pk}/'
                )
            else:
                ticket.status = 'open'
                ticket.save()

            messages.success(request, 'تم إرسال ردك بنجاح!')
            return redirect('support_detail', pk=ticket.pk)
    else:
        form = SupportReplyForm()

    ticket_messages = ticket.messages.all()
    return render(request, 'System/support/detail.html', {
        'ticket': ticket,
        'ticket_messages': ticket_messages,
        'form': form,
    })


@login_required
def support_close(request, pk):
    """إغلاق تذكرة دعم"""
    user = request.user
    if user.is_admin_user():
        ticket = get_object_or_404(SupportTicket, pk=pk)
    else:
        ticket = get_object_or_404(SupportTicket, pk=pk, user=user)
    ticket.status = 'closed'
    ticket.save()
    messages.success(request, 'تم إغلاق التذكرة.')
    return redirect('support_list')
