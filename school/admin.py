from django.contrib import admin
from .models import Course, CourseModule, QuizQuestion, QuizChoice


class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 1
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "sort_order")
    list_filter = ("is_published",)
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CourseModuleInline]


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "is_published", "sort_order")
    list_filter = ("course", "is_published")
    search_fields = ("title", "intro", "body")
    prepopulated_fields = {"slug": ("title",)}


class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 3


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "module", "sort_order")
    list_filter = ("module__course", "module")
    search_fields = ("question", "explanation")
    inlines = [QuizChoiceInline]


@admin.register(QuizChoice)
class QuizChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct", "sort_order")
    list_filter = ("is_correct", "question__module")
    search_fields = ("text",)


