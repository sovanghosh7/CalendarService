from django.contrib.auth import authenticate, login, logout
from django.db.models import Count
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.routers import APIRootView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import mixins
from .models import Event, create_event, update_event, User, UserAvailability
from .serializers import EventSerializer, EventCreateSerializer, EventUpdateSerializer, UserSerializer, \
    UserLoginSerializer, UserAvailabilitySerializer, AvailabilitySerializer


def test_redirect(request):
    return HttpResponseRedirect("/api/")


class CalenderApiRootView(APIRootView):
    permission_classes = []


class EventViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_queryset(self):
        query_params = self.request.query_params
        filter_dict = dict()
        filter_dict['users__user__id'] = self.request.user.id
        if query_params.get('future') == 'true':
            filter_dict["time_slot__gt"] = timezone.now()
        if query_params.get('status') is not None:
            filter_dict["status"] = query_params.get('status')

        events_list = list(Event.objects.filter(**filter_dict).values_list('id', flat=True))
        event_queryset = Event.objects.filter(id__in=events_list).order_by('time_slot').annotate(
            user_count=Count('users')).filter(user_count__gt=1).prefetch_related('users__user')
        return event_queryset

    def create(self, request, *args, **kwargs):
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        try:
            event = create_event(data.get('title'), data.get('description'), data.get('time_slot'),
                                 data.get('participants'), request.user.id)
            headers = self.get_success_headers(serializer.data)
            return Response({"response": self.get_serializer(event).data}, status=status.HTTP_201_CREATED,
                            headers=headers)
        except Exception as e:
            return Response(e.message_dict, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        participants = []
        for i in instance.users.all().select_related('user'):
            participants.append(i.user)
            if i.is_organiser:
                instance.organiser = i.user.id
        instance.participants = participants
        serializer = EventUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            event = update_event(instance, serializer.validated_data)
            if getattr(event, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            return Response({"response": self.get_serializer(event).data})
        except Exception as e:
            return Response(e.message_dict, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    @action(methods=['get'], detail=False, permission_classes=[])
    def get_detail(self, request):
        if request.method == 'GET':
            if request.user.is_authenticated:
                return Response({
                    "is_authenticated": True,
                    "user": UserSerializer(request.user).data,
                    "auth_token": request.user.auth_token.key
                })
            else:
                return Response({"err_message": "You are not an authenticated user"},
                                status=status.HTTP_401_UNAUTHORIZED)

    @action(methods=['post'], detail=False, permission_classes=[])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        username = data.get('username')
        password = data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"err_message": "Credentials were not correct"},
                            status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        return Response({
            "is_authenticated": True,
            "user": UserSerializer(user).data,
            "auth_token": user.auth_token.key
        })

    @action(methods=['post'], detail=False, permission_classes=[])
    def sign_up(self, request):
        data = request.data
        user_serializer = UserSerializer(data=data)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()
        return Response(user_serializer.data)

    @action(methods=['get'], detail=False, permission_classes=[IsAuthenticated])
    def logout(self, request):
        logout(request)
        return Response({"logged_out": True})

    @action(methods=['post'], detail=False, permission_classes=[IsAuthenticated])
    def block_slots(self, request):
        request.data["user_id"] = request.user.id
        serializer = UserAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"response": serializer.data})

    @action(methods=['get'], detail=False, permission_classes=[IsAuthenticated])
    def get_available_slots(self, request):
        data = request.query_params
        serializer = AvailabilitySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.validated_data["user"] if "user" in serializer.validated_data else request.user
            obj = UserAvailability.objects.get(user_id=user.id, date=serializer.validated_data["date"])
            return Response(UserAvailabilitySerializer(obj).data)
        except ObjectDoesNotExist:
            obj = UserAvailability(user=user, date=serializer.validated_data["date"], blocked_slots=[])
            return Response(UserAvailabilitySerializer(obj).data)
