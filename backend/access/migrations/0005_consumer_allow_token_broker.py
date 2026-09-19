from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('access', '0004_remove_grantrequest_client_org_and_more')]
    operations = [migrations.AddField(model_name='consumer', name='allow_token_broker', field=models.BooleanField(default=True))]
