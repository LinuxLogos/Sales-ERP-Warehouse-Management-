from django.db import migrations


def copy_unit_cost(apps, schema_editor):
    Unit = apps.get_model('pos', 'Unit')
    for unit in Unit.objects.filter(cout_unitaire_reel=0).exclude(actual_unit_cost=0):
        unit.cout_unitaire_reel = unit.actual_unit_cost
        unit.save(update_fields=['cout_unitaire_reel'])


class Migration(migrations.Migration):
    dependencies = [('pos', '0003_sale_cost_snapshot')]
    operations = [migrations.RunPython(copy_unit_cost, migrations.RunPython.noop)]
