from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import DetailView, CreateView
from django.views.generic.list import ListView

from .forms import QuestionForm, AnswerForm
from .models import Question, Answer, Comment
from .utilities import cast_vote, save_text_help


class QuestionsView(ListView):
    model = Question
    template_name = 'forum/questions.html'
    context_object_name = "quests"
    paginate_by = 5

    def get_queryset(self):
        qs = super(QuestionsView, self).get_queryset()

        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(title__icontains=search)

        qs = qs.order_by("-id")
        qs = qs.annotate(count_of_answers=Count('answer'))
        return qs


class QuestionDetailView(DetailView):
    model = Question
    template_name = 'forum/detail.html'
    context_object_name = 'quest'

    def get_context_data(self, **kwargs):
        context = super(QuestionDetailView, self).get_context_data(**kwargs)

        context['tags'] = self.object.tags.split(',')
        answers = Answer.objects.filter(question=self.object).order_by('-vote_score')
        comments = []
        for answer in answers:
            comments.append(Comment.objects.filter(answer=answer))
        context['answers_comments'] = zip(answers, comments)

        return context

    def get_queryset(self):
        qs = super(QuestionDetailView, self).get_queryset()
        qs = qs.annotate(count_of_answers=Count('answer'))

        return qs


class AskForm(SuccessMessageMixin, CreateView):
    template_name = 'forum/ask-question.html'
    model = Question
    form_class = QuestionForm
    success_message = 'Success!'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.save()
        return super(AskForm, self).form_valid(form)


class AnswerForm(SuccessMessageMixin, CreateView):
    template_name = 'forum/answer-question.html'
    model = Answer
    form_class = AnswerForm
    success_message = 'Success!'

    def form_valid(self, form, pk=None):
        form.instance.question_id = self.kwargs['pk']
        form.instance.user = self.request.user
        form.save()
        return super().form_valid(form)


class WriteCommentAnswerView(View):
    def post(self, request):
        text = request.POST['text']
        id = request.POST['id']
        text_type = request.POST['type']
        user = request.user

        if text_type == "comment":
            return render(request, 'forum/includes/single_comment.html',
                          {'comment': save_text_help(text, id, text_type, user)})
        else:
            return render(request, 'forum/includes/single_answer.html',
                          {'answer': save_text_help(text, id, text_type, user)})


class SaveVoteView(LoginRequiredMixin, View):
    def post(self, request):
        id = request.POST['id']
        user_id = request.user.id
        vote_to = request.POST['vote_to']
        vote_type = request.POST['vote_type']

        return JsonResponse({'bool': cast_vote(vote_type, vote_to, user_id, id)})
