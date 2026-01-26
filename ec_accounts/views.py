from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Account, Entry
from .serializers import AccountSerializer, EntrySerializer
from .services import create_update_entry

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.prefetch_related('lines__account').all()
    serializer_class = EntrySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            entry=create_update_entry(data=serializer.validated_data)
            return Response(serializer.data,status=status.HTTP_200_OK)
        #TODO: fix_me
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            entry=create_update_entry(instance=instance, data=serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        entry = self.get_object()
        entry.voided = True
        entry.save()
        return Response({'status': 'voided'})
