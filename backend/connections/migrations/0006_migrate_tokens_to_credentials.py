from django.db import migrations


def move_tokens(apps, schema_editor):
    """Move each existing TokenSet into a ProviderCredential and link it."""
    TokenSet = apps.get_model('connections', 'TokenSet')
    ProviderCredential = apps.get_model('connections', 'ProviderCredential')
    for ts in TokenSet.objects.select_related('connection').all():
        conn = ts.connection
        cred = ProviderCredential.objects.create(
            client_org_id=conn.client_org_id,
            provider_id=conn.provider_id,
            enc_refresh_token=ts.enc_refresh_token,
            enc_access_token=ts.enc_access_token,
            access_expires_at=ts.access_expires_at,
        )
        conn.credential = cred
        conn.save(update_fields=['credential'])


def unmove(apps, schema_editor):
    ProviderCredential = apps.get_model('connections', 'ProviderCredential')
    ProviderCredential.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('connections', '0005_providercredential_connection_credential'),
    ]
    operations = [migrations.RunPython(move_tokens, unmove)]
