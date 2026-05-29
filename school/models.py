from django.db import models


class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    audience = models.CharField(max_length=200, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="school/courses/", blank=True, null=True)
    is_published = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    intro = models.TextField(blank=True)
    body = models.TextField()
    video_url = models.URLField(blank=True)
    reflection_prompt = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title"]
        unique_together = ["course", "slug"]

    def __str__(self):
        return f"{self.course}: {self.title}"

class QuizQuestion(models.Model):
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name="quiz_questions")
    question = models.TextField()
    explanation = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.question[:80]


class QuizChoice(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.text


