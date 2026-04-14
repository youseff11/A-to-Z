from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Course, Material, Enrollment, Meeting, MeetingParticipant, Notification, SupportTicket, SupportMessage


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'payment_number', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات إضافية', {'fields': ('role', 'bio', 'profile_picture', 'phone', 'payment_number')}),
    )

    def save_model(self, request, obj, form, change):
        # السوبريوزر دايماً أدمن
        if obj.is_superuser:
            obj.role = 'admin'
        super().save_model(request, obj, form, change)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'price', 'is_free', 'is_published', 'created_at']
    list_filter = ['is_published', 'is_free']
    search_fields = ['title', 'teacher__username', 'teacher__first_name', 'teacher__last_name']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'material_type', 'order']
    list_filter = ['material_type']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    # تم إضافة status للعرض عشان تشوف الطلبات المعلقة والمقبولة بسهولة
    list_display = ['student', 'course', 'status', 'is_active', 'enrolled_at']
    # تم إضافة الفلترة بحالة الدفع
    list_filter = ['status', 'is_active']
    # إضافة خاصية البحث عن طالب أو كورس
    search_fields = ['student__username', 'student__first_name', 'course__title']
    # لعرض صورة الإيصال في شاشة تفاصيل الاشتراك
    readonly_fields = ['enrolled_at']


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'teacher', 'scheduled_at', 'status']
    list_filter = ['status']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_read', 'created_at']
    list_filter = ['is_read']

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'status', 'created_at', 'updated_at']
    list_filter = ['status']
    search_fields = ['subject', 'user__username']


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'sender', 'is_admin_reply', 'created_at']
    list_filter = ['is_admin_reply']
