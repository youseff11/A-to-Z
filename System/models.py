from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'مدرس'),
        ('student', 'طالب'),
        ('admin', 'مدير'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # الحقل الجديد: رقم تحويل الأموال الخاص بالمدرس
    payment_number = models.CharField(max_length=20, blank=True, null=True, help_text="رقم فودافون كاش أو المحفظة الإلكترونية (للمدرسين)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'

    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # السوبريوزر دايماً يبقى أدمن
        if self.is_superuser and self.role != 'admin':
            self.role = 'admin'
        super().save(*args, **kwargs)

    @property
    def unread_notifs_count(self):
         return self.notifications.filter(is_read=False).count()

class Course(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=200)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def get_enrolled_count(self):
        return self.enrollments.filter(status='approved').count()

class Material(models.Model):
    MATERIAL_TYPES = (
        ('video', 'فيديو'),
        ('pdf', 'PDF'),
        ('document', 'مستند'),
        ('link', 'رابط'),
        ('image', 'صورة'),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES)
    file = models.FileField(upload_to='materials/', blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} - {self.course.title}"

class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد المراجعة'),
        ('approved', 'مقبول'),
        ('rejected', 'مرفوض'),
    )
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    payment_receipt = models.ImageField(upload_to='receipts/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} → {self.course.title} ({self.get_status_display()})"

class Meeting(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'مجدول'),
        ('live', 'مباشر الآن'),
        ('ended', 'انتهى'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='meetings')
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='hosted_meetings')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    room_code = models.CharField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.room_code:
            self.room_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.course.title}"

    def is_joinable(self):
        now = timezone.now()
        start = self.scheduled_at
        end = start + timezone.timedelta(minutes=self.duration_minutes)
        return start <= now <= end or self.status == 'live'

class MeetingParticipant(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('meeting', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.meeting.title}"

class MaterialView(models.Model):
    """تتبع فتح الطالب للمواد التعليمية"""
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='views')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='material_views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('material', 'student')

    def __str__(self):
        return f"{self.student.username} شاهد {self.material.title}"


class Exam(models.Model):
    """الامتحانات التي يضعها المدرس"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=30, help_text="مدة الامتحان بالدقائق")
    pass_score = models.PositiveIntegerField(default=50, help_text="درجة النجاح من 100")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"

    def get_total_marks(self):
        return self.questions.aggregate(total=models.Sum('marks'))['total'] or 0


class Question(models.Model):
    """أسئلة الامتحان"""
    QUESTION_TYPES = (
        ('mcq', 'اختيار من متعدد'),
        ('true_false', 'صح أو خطأ'),
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='mcq')
    option_a = models.CharField(max_length=300, blank=True, null=True)
    option_b = models.CharField(max_length=300, blank=True, null=True)
    option_c = models.CharField(max_length=300, blank=True, null=True)
    option_d = models.CharField(max_length=300, blank=True, null=True)
    correct_answer = models.CharField(max_length=10)  # 'A','B','C','D' or 'true','false'
    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"سؤال {self.order}: {self.text[:50]}"


class ExamAttempt(models.Model):
    """محاولات الطالب في الامتحان"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='exam_attempts')
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_marks = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('exam', 'student')

    def __str__(self):
        return f"{self.student.username} - {self.exam.title} ({self.percentage}%)"


class StudentAnswer(models.Model):
    """إجابات الطالب"""
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=10)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"إجابة: {self.answer} ({'صح' if self.is_correct else 'خطأ'})"


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.user.username}"

# ─── الدعم الفني ──────────────────────────────────────────────────────────────

class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('open', 'مفتوح'),
        ('answered', 'تم الرد'),
        ('closed', 'مغلق'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.subject} - {self.user.username}"

    def last_message(self):
        return self.messages.order_by('-created_at').first()


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    body = models.TextField()
    is_admin_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"رسالة من {self.sender.username} في تذكرة #{self.ticket.pk}"
