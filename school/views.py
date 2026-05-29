from django.shortcuts import get_object_or_404, render
from .models import Course, CourseModule


def course_catalog(request):
    courses = Course.objects.filter(is_published=True)
    return render(request, "school/course_catalog.html", {"courses": courses})


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    modules = course.modules.filter(is_published=True)
    return render(request, "school/course_detail.html", {
        "course": course,
        "modules": modules,
    })


def module_detail(request, course_slug, module_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    module = get_object_or_404(
        CourseModule,
        course=course,
        slug=module_slug,
        is_published=True,
    )

    modules = list(course.modules.filter(is_published=True))
    current_index = modules.index(module)
    previous_module = modules[current_index - 1] if current_index > 0 else None
    next_module = modules[current_index + 1] if current_index < len(modules) - 1 else None

    quiz_questions = module.quiz_questions.prefetch_related("choices")

    return render(request, "school/module_detail.html", {
        "course": course,
        "module": module,
        "quiz_questions": quiz_questions,
        "previous_module": previous_module,
        "next_module": next_module,
    })

def completion_page(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    return render(request, "school/completion_page.html", {"course": course})

