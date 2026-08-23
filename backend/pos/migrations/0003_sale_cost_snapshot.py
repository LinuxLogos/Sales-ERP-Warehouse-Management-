from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0002_permission_role_lot_actual_unit_cost_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='cout_unitaire_reel',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='saledetail',
            name='source_type',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='saledetail',
            name='source_id',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
        migrations.AddField(
            model_name='saledetail',
            name='montant_vente_net',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='saledetail',
            name='cout_unitaire_reel',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='saledetail',
            name='cout_total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='saledetail',
            name='marge_brute',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='saledetail',
            name='taux_marge',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.AddField(
            model_name='saledetail',
            name='cout_statut',
            field=models.CharField(default='NON_RECONCILIE', max_length=20),
        ),
    ]
