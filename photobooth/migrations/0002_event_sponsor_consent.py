from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add sponsorship and marketing consent fields to the Event model.
    """

    dependencies = [
        ('photobooth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='sponsor_logo',
            field=models.ImageField(blank=True, null=True, upload_to='events/sponsors/'),
        ),
        migrations.AddField(
            model_name='event',
            name='requires_consent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='consent_text',
            field=models.CharField(blank=True, default='I consent to the use of my image for marketing purposes.', max_length=200),
        ),
    ]