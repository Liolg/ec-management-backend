from django.db.models.deletion import ProtectedError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Account, Entry
from .serializers import AccountSerializer, EntryReadSerializer, EntryWriteSerializer
from .services import update_entry

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': 'Account cannot be deleted because it is referenced.'},
                status=status.HTTP_409_CONFLICT,
            )


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.select_related(
        'sale', 'purchase', 'expense', 'payment',
    ).prefetch_related('lines__account').all()

    @staticmethod
    def _is_generated(entry):
        return any(
            getattr(entry, source_type, None) is not None
            for source_type in ('sale', 'purchase', 'expense', 'payment')
        )

    def _generated_conflict(self):
        return Response(
            {'detail': 'Transaction-generated entries must be changed through the business API.'},
            status=status.HTTP_409_CONFLICT,
        )

    def update(self, request, *args, **kwargs):
        if self._is_generated(self.get_object()):
            return self._generated_conflict()
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if self._is_generated(self.get_object()):
            return self._generated_conflict()
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return EntryReadSerializer
        else:
            return EntryWriteSerializer

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     if serializer.is_valid(raise_exception=True):
    #         serializer.save()
    #         # entry=create_update_entry(data=serializer.validated_data)
    #         return Response(serializer.data,status=status.HTTP_200_OK)
    #     #TODO: fix_me
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)

    # def update(self, request, pk):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data)
    #     if serializer.is_valid(raise_exception=True):
    #         # entry=create_update_entry(instance=instance, data=serializer.validated_data)
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        entry = self.get_object()
        if self._is_generated(entry):
            return self._generated_conflict()
        entry.voided = True
        entry.save(update_fields=['voided', 'last_modified_at'])
        return Response({'status': 'voided'})
