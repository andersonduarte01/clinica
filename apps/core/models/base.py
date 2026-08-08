from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Soft Delete
# ---------------------------------------------------------------------------

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        """Soft delete em massa — nunca deleta fisicamente."""
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def with_deleted(self):
        return self.model.all_objects.all()

    def only_deleted(self):
        return self.model.all_objects.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=True
        )

    def with_deleted(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)

    def only_deleted(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=False
        )


class SoftDeleteMixin(models.Model):
    """
    Adiciona soft delete a qualquer model.
    - `objects` filtra automaticamente registros deletados.
    - `all_objects` acessa todos os registros (para admin e migrations).
    - `delete()` marca `deleted_at`; use `hard_delete()` para remoção física.
    """

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Tenant-Aware
# ---------------------------------------------------------------------------

class TenantAwareQuerySet(models.QuerySet):
    pass


class TenantAwareManager(models.Manager):
    """
    Manager padrão para models tenant-aware.
    Filtra automaticamente pelo tenant do request atual.
    Em contextos sem request (tasks, shell), retorna queryset vazio por segurança.
    Use `global_objects` para acesso sem filtro de tenant.
    """

    def get_queryset(self) -> TenantAwareQuerySet:
        from apps.platform.middleware import get_current_tenant

        qs = TenantAwareQuerySet(self.model, using=self._db)
        tenant = get_current_tenant()

        if tenant is None:
            # Sem tenant no contexto — retorna vazio para evitar vazamento de dados.
            # Em tasks/scripts, use Model.global_objects.filter(tenant=tenant_especifico).
            return qs.none()

        return qs.filter(tenant=tenant)


class TenantAwareSoftDeleteManager(TenantAwareManager):
    """Manager combinado: filtra por tenant E exclui soft-deleted."""

    def get_queryset(self) -> TenantAwareQuerySet:
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self) -> TenantAwareQuerySet:
        from apps.platform.middleware import get_current_tenant

        tenant = get_current_tenant()
        qs = TenantAwareQuerySet(self.model, using=self._db)
        if tenant is None:
            return qs.none()
        return qs.filter(tenant=tenant)


class TenantAwareModel(models.Model):
    """
    Model base para todas as entidades que pertencem a um tenant.

    Uso:
        class Paciente(TenantAwareModel, SoftDeleteMixin):
            ...

    QuerySets:
        Paciente.objects.all()           → pacientes do tenant atual
        Paciente.global_objects.all()    → todos os pacientes (superadmin/tasks)
    """

    tenant = models.ForeignKey(
        "platform.Tenant",
        on_delete=models.CASCADE,
        db_index=True,
        editable=False,
        verbose_name="Tenant",
    )

    objects = TenantAwareManager()
    global_objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Auto-preenche o tenant a partir do contexto do request se não foi definido.
        if not self.tenant_id:
            from apps.platform.middleware import get_current_tenant
            tenant = get_current_tenant()
            if tenant is None:
                raise ValueError(
                    f"Não é possível salvar {self.__class__.__name__} sem um tenant. "
                    "Defina `instance.tenant` explicitamente ou execute dentro de um request."
                )
            self.tenant = tenant
        super().save(*args, **kwargs)
