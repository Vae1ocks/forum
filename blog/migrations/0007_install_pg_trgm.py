from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_alter_article_slug'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            reverse_sql="DROP EXTENSION IF EXISTS pg_trgm;",
        ),
    ]